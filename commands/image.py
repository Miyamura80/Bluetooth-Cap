"""Display an image or GIF animation on the LED cap."""

import asyncio
import io
from pathlib import Path
from typing import Annotated

import typer
from PIL import Image
from rich.console import Console

from commands._resolve import resolve_device_name
from src.cli.state import is_dry_run
from src.protocol.commands import CMD_GIF_DATA, CMD_PNG_DATA
from src.protocol.connection import open_device
from src.protocol.transport import send_data

console = Console()

DISPLAY_WIDTH = 32
DISPLAY_HEIGHT = 16


def _is_gif(path: Path) -> bool:
    return path.suffix.lower() == ".gif"


def _prepare_png(path: Path, width: int, height: int) -> bytes:
    """Load, resize, and encode an image as PNG bytes."""
    img = Image.open(path).convert("RGB")
    img = img.resize((width, height), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _prepare_gif(path: Path, width: int, height: int) -> bytes:
    """Load a GIF, resize all frames, and re-encode as GIF bytes."""
    img = Image.open(path)
    frames: list[Image.Image] = []
    durations: list[int] = []

    try:
        while True:
            frame = img.copy().convert("RGBA")
            frame = frame.resize((width, height), Image.Resampling.LANCZOS)
            frames.append(frame)
            durations.append(img.info.get("duration", 100))
            img.seek(img.tell() + 1)
    except EOFError:
        pass

    if not frames:
        console.print("[red]GIF has no frames.[/red]")
        raise typer.Exit(code=1)

    buf = io.BytesIO()
    frames[0].save(
        buf,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        disposal=2,
        optimize=False,
    )
    return buf.getvalue()


async def _send_image(
    name: str,
    path: Path,
    slot: int,
    timeout: float,
    width: int,
    height: int,
) -> None:
    is_animated = _is_gif(path)

    if is_animated:
        data = _prepare_gif(path, width, height)
        cmd = CMD_GIF_DATA
        fmt_label = "GIF"
    else:
        data = _prepare_png(path, width, height)
        cmd = CMD_PNG_DATA
        fmt_label = "PNG"

    console.print(
        f"[dim]Image: {path.name} -> {width}x{height} ({len(data)} bytes {fmt_label})[/dim]"
    )

    async with open_device(name, timeout) as client:
        console.print(f"[green]Connected[/green] (MTU: {client.mtu_size})")
        console.print(
            f"[yellow]>> sending {len(data)} bytes to slot {slot}...[/yellow]"
        )

        acks = await send_data(client, cmd, data, slot=slot, timeout=30.0)

        for i, ack in enumerate(acks):
            if ack:
                console.print(
                    f"[cyan]<< {ack.hex(' ')}[/cyan]  (ACK window {i + 1}/{len(acks)})"
                )
            else:
                console.print(f"[yellow]Window {i + 1}/{len(acks)}: no ACK[/yellow]")

        if all(acks):
            console.print(f"[green]{fmt_label} sent ({len(acks)} window(s)).[/green]")
        else:
            console.print("[yellow]Some windows did not ACK.[/yellow]")


def main(
    path: Annotated[
        Path,
        typer.Argument(help="Path to image file (PNG, JPEG, BMP, GIF)."),
    ],
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="BLE device name."),
    ] = None,
    slot: Annotated[
        int,
        typer.Option("--slot", "-s", help="Display buffer slot (1-9)."),
    ] = 1,
    timeout: Annotated[
        float,
        typer.Option("--timeout", "-t", help="Scan timeout in seconds."),
    ] = 10.0,
    width: Annotated[
        int,
        typer.Option("--width", "-W", help="Target width in pixels."),
    ] = DISPLAY_WIDTH,
    height: Annotated[
        int,
        typer.Option("--height", "-H", help="Target height in pixels."),
    ] = DISPLAY_HEIGHT,
) -> None:
    """Display an image or GIF animation on the LED cap."""
    if not path.exists():
        console.print(f"[red]File not found: {path}[/red]")
        raise typer.Exit(code=1)
    device_name = resolve_device_name(name, console)
    if is_dry_run():
        typer.echo(f"[DRY RUN] Would send '{path}' to '{device_name}' slot {slot}")
        return
    console.print(f"[dim]Connecting to '{device_name}'...[/dim]")
    asyncio.run(_send_image(device_name, path, slot, timeout, width, height))
