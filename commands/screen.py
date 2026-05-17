"""Select which display buffer to show on the LED cap."""

import asyncio
from typing import Annotated

import typer
from rich.console import Console

from commands._resolve import resolve_device_name
from src.cli.state import is_dry_run
from src.protocol import commands as proto
from src.protocol.connection import open_device, write_command

console = Console()


async def _select(name: str, slot: int, timeout: float) -> None:
    async with open_device(name, timeout) as client:
        payload = proto.select_screen(slot)
        console.print(f"[yellow]>> {payload.hex(' ')}[/yellow]  (select screen {slot})")
        await write_command(client, payload)
        console.print(f"[green]Screen {slot} selected.[/green]")


def main(
    slot: Annotated[
        int,
        typer.Argument(help="Display buffer slot to show (1-9)."),
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
    """Select which display buffer slot to show (1-9)."""
    if slot < 1 or slot > 9:
        console.print("[red]Slot must be between 1 and 9.[/red]")
        raise typer.Exit(code=1)
    device_name = resolve_device_name(name, console)
    if is_dry_run():
        typer.echo(f"[DRY RUN] Would select screen {slot} on '{device_name}'")
        return
    console.print(f"[dim]Connecting to '{device_name}'...[/dim]")
    asyncio.run(_select(device_name, slot, timeout))
