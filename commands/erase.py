"""Erase display buffers on the LED cap."""

import asyncio
from typing import Annotated

import typer
from rich.console import Console

from commands._resolve import resolve_device_name
from src.cli.state import is_dry_run
from src.protocol import commands as proto
from src.protocol.connection import open_device, write_command

console = Console()


async def _erase(name: str, slots: list[int], timeout: float) -> None:
    async with open_device(name, timeout) as client:
        payload = proto.erase_buffers(slots)
        label = ", ".join(str(s) for s in slots)
        console.print(f"[yellow]>> {payload.hex(' ')}[/yellow]  (erase slots: {label})")
        await write_command(client, payload)
        console.print(f"[green]Erased slot(s): {label}.[/green]")


def main(
    slots: Annotated[
        list[int],
        typer.Argument(help="Buffer slot(s) to erase (e.g. 1 2 3)."),
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
    """Erase one or more display buffer slots."""
    device_name = resolve_device_name(name, console)
    if is_dry_run():
        typer.echo(f"[DRY RUN] Would erase slots {slots} on '{device_name}'")
        return
    console.print(f"[dim]Connecting to '{device_name}'...[/dim]")
    asyncio.run(_erase(device_name, slots, timeout))
