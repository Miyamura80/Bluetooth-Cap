"""Flip the LED cap display orientation."""

import asyncio
from typing import Annotated

import typer
from rich.console import Console

from commands._resolve import resolve_device_name
from src.cli.state import is_dry_run
from src.protocol import commands as proto
from src.protocol.connection import open_device, write_command

console = Console()


async def _flip(name: str, on: bool, timeout: float) -> None:
    async with open_device(name, timeout) as client:
        payload = proto.upside_down(on)
        label = "flipped" if on else "normal"
        console.print(f"[yellow]>> {payload.hex(' ')}[/yellow]  (orientation: {label})")
        await write_command(client, payload)
        console.print(f"[green]Display {label}.[/green]")


def main(
    on: Annotated[
        bool,
        typer.Option("--on/--off", help="Flip on (upside down) or off (normal)."),
    ] = True,
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="BLE device name."),
    ] = None,
    timeout: Annotated[
        float,
        typer.Option("--timeout", "-t", help="Scan timeout in seconds."),
    ] = 10.0,
) -> None:
    """Flip the display upside down (or back to normal)."""
    device_name = resolve_device_name(name, console)
    if is_dry_run():
        typer.echo(f"[DRY RUN] Would flip {'on' if on else 'off'} '{device_name}'")
        return
    console.print(f"[dim]Connecting to '{device_name}'...[/dim]")
    asyncio.run(_flip(device_name, on, timeout))
