"""Query the LED cap for device type and display dimensions."""

import asyncio
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from commands._resolve import resolve_device_name
from src.cli.state import is_dry_run
from src.protocol.commands import query_device_info
from src.protocol.connection import open_device, send_and_receive
from src.protocol.device_types import parse_device_info

console = Console()


async def _probe(name: str, timeout: float) -> None:
    async with open_device(name, timeout) as client:
        console.print(f"[green]Connected[/green] (MTU: {client.mtu_size})")

        payload = query_device_info()
        console.print(f"[yellow]>> {payload.hex(' ')}[/yellow]  (device info query)")

        response = await send_and_receive(client, payload, timeout=5.0)

        if response is None:
            console.print("[red]No response received (timed out).[/red]")
            console.print("[dim]The device may not support the iPIXEL protocol.[/dim]")
            raise typer.Exit(code=1)

        console.print(f"[cyan]<< {response.hex(' ')}[/cyan]")
        console.print()

        info = parse_device_info(response)

        table = Table(title="Device Info")
        table.add_column("Field", style="cyan")
        table.add_column("Value")

        table.add_row("Raw response", info["raw"])
        table.add_row("Response length", str(info["length"]))

        if "device_byte" in info:
            table.add_row("Device type byte", f"0x{info['device_byte']:02X}")

        if info.get("dimensions"):
            w, h = info["dimensions"]
            table.add_row("LED matrix size", f"{w} x {h}")
        elif info.get("type_id") is not None:
            table.add_row("Type ID", str(info["type_id"]))
        else:
            table.add_row("LED matrix size", "[dim]unknown[/dim]")

        if info.get("mcu_version"):
            table.add_row("MCU version", info["mcu_version"])
        if info.get("ble_version"):
            table.add_row("BLE version", info["ble_version"])
        if "has_password" in info:
            table.add_row(
                "Password protected",
                "yes" if info["has_password"] else "no",
            )

        console.print(table)


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
    """Query device type and LED matrix dimensions (iPIXEL protocol)."""
    device_name = resolve_device_name(name, console)
    if is_dry_run():
        typer.echo(f"[DRY RUN] Would probe '{device_name}'")
        return
    console.print(f"[dim]Connecting to '{device_name}'...[/dim]")
    asyncio.run(_probe(device_name, timeout))
