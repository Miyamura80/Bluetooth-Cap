"""Return the LED cap to its default display mode."""

import asyncio
from typing import Annotated

import typer
from rich.console import Console

from commands._resolve import resolve_device_name
from src.cli.state import is_dry_run
from src.protocol import commands as proto
from src.protocol.connection import open_device, write_command

console = Console()


async def _default(name: str, timeout: float) -> None:
    async with open_device(name, timeout) as client:
        payload = proto.default_mode()
        console.print(f"[yellow]>> {payload.hex(' ')}[/yellow]  (default mode)")
        await write_command(client, payload)
        console.print("[green]Default mode set.[/green]")


def main(
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="BLE device name."),
    ] = None,
    timeout: Annotated[
        float,
        typer.Option("--timeout", "-t", help="Scan timeout in seconds."),
    ] = 10.0,
) -> None:
    """Return to the default display mode."""
    device_name = resolve_device_name(name, console)
    if is_dry_run():
        typer.echo(f"[DRY RUN] Would set default mode on '{device_name}'")
        return
    console.print(f"[dim]Connecting to '{device_name}'...[/dim]")
    asyncio.run(_default(device_name, timeout))
