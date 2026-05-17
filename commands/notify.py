"""Subscribe to BLE notifications from a characteristic."""

import asyncio
from typing import Annotated

import typer
from rich.console import Console

from commands._resolve import resolve_device_name
from src.cli.state import is_dry_run
from src.protocol.connection import open_device

console = Console()


async def _listen(name: str, char_uuid: str, timeout: float) -> None:
    async with open_device(name, timeout) as client:
        console.print(f"[green]Connected.[/green] Subscribing to {char_uuid}...")

        count = 0

        def callback(_char: object, data: bytearray) -> None:
            nonlocal count
            console.print(f"[cyan]<< {data.hex(' ')}[/cyan]")
            count += 1

        await client.start_notify(char_uuid, callback)
        console.print("[dim]Listening for notifications (Ctrl+C to stop)...[/dim]")
        try:
            while True:
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        finally:
            await client.stop_notify(char_uuid)
            console.print(f"[dim]Received {count} notification(s).[/dim]")


def main(
    char: Annotated[
        str,
        typer.Argument(help="Characteristic UUID to subscribe to."),
    ],
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="BLE device name (e.g. LED_BLE_62F7C880)."),
    ] = None,
    timeout: Annotated[
        float,
        typer.Option("--timeout", "-t", help="Scan timeout in seconds."),
    ] = 10.0,
) -> None:
    """Subscribe to BLE notifications from a characteristic."""
    device_name = resolve_device_name(name, console)
    if is_dry_run():
        typer.echo(f"[DRY RUN] Would subscribe to {char} on '{device_name}'")
        return
    console.print(f"[dim]Connecting to '{device_name}'...[/dim]")
    asyncio.run(_listen(device_name, char, timeout))
