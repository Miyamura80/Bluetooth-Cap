"""Display text on the LED cap."""

import asyncio
import io
from typing import Annotated

import typer
from PIL import Image, ImageDraw, ImageFont
from rich.console import Console

from commands._resolve import resolve_device_name
from src.cli.state import is_dry_run
from src.protocol.commands import CMD_GIF_DATA, CMD_PNG_DATA
from src.protocol.connection import open_device
from src.protocol.transport import send_data

console = Console()

DISPLAY_WIDTH = 32
DISPLAY_HEIGHT = 16


def _render_static_png(
    text: str,
    width: int,
    height: int,
    fg: tuple[int, int, int],
    bg: tuple[int, int, int],
) -> bytes:
    """Render text to a fixed-size PNG for static display."""
    font_size = max(8, height - 2)
    font = ImageFont.load_default(size=font_size)

    temp = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(temp)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_h = int(bbox[3] - bbox[1])

    img = Image.new("RGB", (width, height), color=bg)
    draw = ImageDraw.Draw(img)
    y_offset = (height - text_h) // 2 - int(bbox[1])
    draw.text((1, y_offset), text, fill=fg, font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _render_scroll_gif(
    text: str,
    width: int,
    height: int,
    fg: tuple[int, int, int],
    bg: tuple[int, int, int],
    speed: int,
) -> bytes:
    """Render scrolling text as a GIF by sliding a window across the text.

    Text starts visible at position 0 and scrolls left. A single width of
    blank padding at the end provides a gap before the loop repeats.
    """
    font_size = max(8, height - 2)
    font = ImageFont.load_default(size=font_size)

    temp = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(temp)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = int(bbox[2] - bbox[0]) + 2
    text_h = int(bbox[3] - bbox[1])

    total_w = text_w + width
    full_img = Image.new("RGB", (total_w, height), color=bg)
    draw = ImageDraw.Draw(full_img)
    y_offset = (height - text_h) // 2 - int(bbox[1])
    draw.text((0, y_offset), text, fill=fg, font=font)

    step = 2
    frame_duration = max(30, 250 - speed * 3)

    frames: list[Image.Image] = []
    for x_off in range(0, total_w - width + 1, step):
        frame = full_img.crop((x_off, 0, x_off + width, height)).convert("RGBA")
        frames.append(frame)

    if not frames:
        frames.append(full_img.crop((0, 0, width, height)).convert("RGBA"))

    buf = io.BytesIO()
    frames[0].save(
        buf,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=frame_duration,
        loop=0,
        disposal=2,
        optimize=False,
    )
    return buf.getvalue()


def _parse_color(color_str: str) -> tuple[int, int, int]:
    """Parse 'ff0000' or '255,0,0' into (R, G, B)."""
    if "," in color_str:
        parts = [int(p.strip()) for p in color_str.split(",")]
        if len(parts) != 3:
            raise ValueError("Color must be R,G,B")
        return (parts[0], parts[1], parts[2])
    cleaned = color_str.lstrip("#").replace("0x", "")
    if len(cleaned) != 6:
        raise ValueError("Hex color must be 6 characters")
    return (int(cleaned[0:2], 16), int(cleaned[2:4], 16), int(cleaned[4:6], 16))


async def _send_static(
    name: str,
    text: str,
    slot: int,
    timeout: float,
    fg: tuple[int, int, int],
    bg: tuple[int, int, int],
    width: int,
    height: int,
) -> None:
    data = _render_static_png(text, width, height, fg, bg)
    console.print(
        f"[dim]Static text '{text}' -> {width}x{height} PNG ({len(data)} bytes)[/dim]"
    )

    async with open_device(name, timeout) as client:
        console.print(f"[green]Connected[/green] (MTU: {client.mtu_size})")
        console.print(
            f"[yellow]>> sending {len(data)} bytes to slot {slot}...[/yellow]"
        )

        acks = await send_data(client, CMD_PNG_DATA, data, slot=slot, timeout=30.0)

        if all(acks):
            console.print(f"[green]Static text sent ({len(acks)} window(s)).[/green]")
        else:
            console.print("[yellow]Some windows did not ACK.[/yellow]")


async def _send_scroll(
    name: str,
    text: str,
    slot: int,
    timeout: float,
    fg: tuple[int, int, int],
    bg: tuple[int, int, int],
    height: int,
    speed: int,
    width: int,
) -> None:
    data = _render_scroll_gif(text, width, height, fg, bg, speed)
    console.print(
        f"[dim]Scrolling text '{text}' -> GIF ({len(data)} bytes, {speed}% speed)[/dim]"
    )

    async with open_device(name, timeout) as client:
        console.print(f"[green]Connected[/green] (MTU: {client.mtu_size})")
        console.print(
            f"[yellow]>> sending {len(data)} bytes to slot {slot}...[/yellow]"
        )

        acks = await send_data(client, CMD_GIF_DATA, data, slot=slot, timeout=30.0)

        for i, ack in enumerate(acks):
            if ack:
                console.print(
                    f"[cyan]<< {ack.hex(' ')}[/cyan]  (ACK window {i + 1}/{len(acks)})"
                )
            else:
                console.print(f"[yellow]Window {i + 1}/{len(acks)}: no ACK[/yellow]")

        if all(acks):
            console.print(
                f"[green]Scrolling text sent ({len(acks)} window(s)).[/green]"
            )
        else:
            console.print("[yellow]Some windows did not ACK.[/yellow]")


def main(
    text: Annotated[
        str,
        typer.Argument(help="Text to display on the LED cap."),
    ],
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="BLE device name."),
    ] = None,
    scroll: Annotated[
        bool,
        typer.Option(
            "--scroll/--static",
            help="Use scrolling GIF animation or static PNG.",
        ),
    ] = False,
    slot: Annotated[
        int,
        typer.Option("--slot", "-s", help="Display buffer slot (1-9)."),
    ] = 1,
    timeout: Annotated[
        float,
        typer.Option("--timeout", "-t", help="Scan timeout in seconds."),
    ] = 10.0,
    color: Annotated[
        str,
        typer.Option("--color", "-c", help="Text color (hex or R,G,B)."),
    ] = "ffffff",
    bg: Annotated[
        str,
        typer.Option("--bg", help="Background color (hex or R,G,B)."),
    ] = "000000",
    speed: Annotated[
        int,
        typer.Option("--speed", help="Scroll speed 0-100 (scroll only)."),
    ] = 50,
    width: Annotated[
        int,
        typer.Option("--width", "-W", help="Display width in pixels."),
    ] = DISPLAY_WIDTH,
    height: Annotated[
        int,
        typer.Option("--height", "-H", help="Display height in pixels."),
    ] = DISPLAY_HEIGHT,
) -> None:
    """Display text on the LED cap (static or scrolling)."""
    try:
        fg_rgb = _parse_color(color)
        bg_rgb = _parse_color(bg)
    except ValueError as exc:
        console.print(f"[red]Invalid color: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    device_name = resolve_device_name(name, console)
    if is_dry_run():
        typer.echo(f"[DRY RUN] Would display '{text}' on '{device_name}'")
        return
    console.print(f"[dim]Connecting to '{device_name}'...[/dim]")

    if scroll:
        asyncio.run(
            _send_scroll(
                device_name,
                text,
                slot,
                timeout,
                fg_rgb,
                bg_rgb,
                height,
                speed,
                width,
            )
        )
    else:
        asyncio.run(
            _send_static(
                device_name,
                text,
                slot,
                timeout,
                fg_rgb,
                bg_rgb,
                width,
                height,
            )
        )
