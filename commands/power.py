"""Control LED cap power state."""

import asyncio
from enum import StrEnum
from typing import Annotated

import typer
from rich.console import Console

from commands._resolve import resolve_device_name
from src.cli.state import is_dry_run
from src.protocol import commands as proto
from src.protocol.connection import open_device, write_command

console = Console()


class PowerState(StrEnum):
    on = "on"
    off = "off"


async def _set_power(name: str, state: PowerState, timeout: float) -> None:
    async with open_device(name, timeout) as client:
        payload = proto.power(state == PowerState.on)
        console.print(f"[yellow]>> {payload.hex(' ')}[/yellow]  (power {state})")
        await write_command(client, payload)
        console.print(f"[green]Power {state}.[/green]")


def main(
    state: Annotated[
        PowerState,
        typer.Argument(help="Power state: on or off."),
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
    """Turn the LED cap on or off."""
    device_name = resolve_device_name(name, console)
    if is_dry_run():
        typer.echo(f"[DRY RUN] Would power {state} '{device_name}'")
        return
    console.print(f"[dim]Connecting to '{device_name}'...[/dim]")
    asyncio.run(_set_power(device_name, state, timeout))
