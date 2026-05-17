"""Set individual pixels on the LED cap via DIY mode."""

import asyncio
from typing import Annotated

import typer
from rich.console import Console

from commands._resolve import resolve_device_name
from src.cli.state import is_dry_run
from src.protocol import commands as proto
from src.protocol.connection import open_device, write_command

console = Console()


def _parse_color_arg(color: str) -> tuple[int, int, int]:
    """Parse hex color like 'ff0000' or 'FF0000' into (R, G, B)."""
    cleaned = color.lstrip("#").replace("0x", "")
    if len(cleaned) != 6:
        console.print("[red]Color must be 6 hex characters (e.g. ff0000).[/red]")
        raise typer.Exit(code=1)
    try:
        return (int(cleaned[0:2], 16), int(cleaned[2:4], 16), int(cleaned[4:6], 16))
    except ValueError as exc:
        console.print(f"[red]Invalid hex color: {exc}[/red]")
        raise typer.Exit(code=1) from exc


async def _set_pixel(
    name: str,
    x: int,
    y: int,
    r: int,
    g: int,
    b: int,
    timeout: float,
) -> None:
    async with open_device(name, timeout) as client:
        enter = proto.diy_mode(enable=True)
        console.print(f"[yellow]>> {enter.hex(' ')}[/yellow]  (enter DIY mode)")
        await write_command(client, enter)

        try:
            pixel = proto.set_pixel(x, y, r, g, b)
            console.print(
                f"[yellow]>> {pixel.hex(' ')}[/yellow]  (pixel ({x},{y}) = #{r:02x}{g:02x}{b:02x})"
            )
            await write_command(client, pixel)
        finally:
            exit_cmd = proto.diy_mode(enable=False)
            console.print(f"[yellow]>> {exit_cmd.hex(' ')}[/yellow]  (exit DIY mode)")
            await write_command(client, exit_cmd)

        console.print(f"[green]Pixel set at ({x},{y}).[/green]")


def main(
    x: Annotated[int, typer.Argument(help="X coordinate.")],
    y: Annotated[int, typer.Argument(help="Y coordinate.")],
    color: Annotated[
        str,
        typer.Option("--color", "-c", help="Pixel color as hex (e.g. ff0000)."),
    ] = "ffffff",
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="BLE device name."),
    ] = None,
    timeout: Annotated[
        float,
        typer.Option("--timeout", "-t", help="Scan timeout in seconds."),
    ] = 10.0,
) -> None:
    """Set a single pixel on the LED cap (enters and exits DIY mode)."""
    r, g, b = _parse_color_arg(color)
    device_name = resolve_device_name(name, console)
    if is_dry_run():
        typer.echo(f"[DRY RUN] Would set pixel ({x},{y}) on '{device_name}'")
        return
    console.print(f"[dim]Connecting to '{device_name}'...[/dim]")
    asyncio.run(_set_pixel(device_name, x, y, r, g, b, timeout))
