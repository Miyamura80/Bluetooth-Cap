"""Control LED cap brightness."""

import asyncio
from typing import Annotated

import typer
from rich.console import Console

from commands._resolve import resolve_device_name
from src.cli.state import is_dry_run
from src.protocol import commands as proto
from src.protocol.connection import open_device, write_command

console = Console()


async def _set_brightness(name: str, level: int, timeout: float) -> None:
    async with open_device(name, timeout) as client:
        payload = proto.brightness(level)
        console.print(f"[yellow]>> {payload.hex(' ')}[/yellow]  (brightness {level}%)")
        await write_command(client, payload)
        console.print(f"[green]Brightness set to {level}%.[/green]")


def main(
    level: Annotated[
        int,
        typer.Argument(help="Brightness level (1-100)."),
    ],
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="BLE device name."),
    ] = None,
    timeout: Annotated[
        float,
        typer.Option("--timeout", "-t", help="Scan timeout in seconds."),
    ] = 10.0,
) -> None:
    """Set LED cap brightness (1-100)."""
    if level < 1 or level > 100:
        console.print("[red]Brightness must be between 1 and 100.[/red]")
        raise typer.Exit(code=1)
    device_name = resolve_device_name(name, console)
    if is_dry_run():
        typer.echo(f"[DRY RUN] Would set brightness to {level} on '{device_name}'")
        return
    console.print(f"[dim]Connecting to '{device_name}'...[/dim]")
    asyncio.run(_set_brightness(device_name, level, timeout))
