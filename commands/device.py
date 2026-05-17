"""Connect to a LED cap and inspect its BLE services."""

import asyncio
from typing import Annotated

import typer
from rich.console import Console
from rich.tree import Tree

from src.cli.state import is_dry_run

app = typer.Typer()
console = Console()

DEFAULT_DEVICE_NAME = "LED_BLE_62F7C880"


async def _find_device(name: str, timeout: float):
    from bleak import BleakScanner

    console.print(f"[dim]Searching for '{name}' ({timeout}s)...[/dim]")
    device = await BleakScanner.find_device_by_name(name, timeout=timeout)
    return device


async def _connect_and_inspect(name: str, timeout: float) -> None:
    from bleak import BleakClient

    device = await _find_device(name, timeout)
    if not device:
        console.print(f"[red]Device '{name}' not found.[/red]")
        console.print("[dim]Run 'bluecap scan' to find nearby devices.[/dim]")
        raise typer.Exit(code=1)

    console.print(f"[green]Found:[/green] {device.name} @ {device.address}")
    console.print("[dim]Connecting...[/dim]")

    async with BleakClient(device) as client:
        console.print(f"[green]Connected[/green] (MTU: {client.mtu_size})")
        console.print()

        tree = Tree(f"[bold cyan]{device.name}[/bold cyan]")
        for service in client.services:
            svc_label = f"[yellow]Service[/yellow] {service.uuid}"
            if service.description and service.description != "Vendor specific":
                svc_label += f"  [dim]{service.description}[/dim]"
            svc_node = tree.add(svc_label)
            for char in service.characteristics:
                props = ", ".join(char.properties)
                char_label = f"[cyan]Char[/cyan] {char.uuid}  [dim][{props}][/dim]"
                char_node = svc_node.add(char_label)
                for desc in char.descriptors:
                    char_node.add(f"[dim]Desc {desc.uuid}  {desc.description}[/dim]")

        console.print(tree)


async def _read_notify(name: str, char_uuid: str, timeout: float) -> None:
    from bleak import BleakClient

    device = await _find_device(name, timeout)
    if not device:
        console.print(f"[red]Device '{name}' not found.[/red]")
        raise typer.Exit(code=1)

    console.print(f"[dim]Connecting to {device.name}...[/dim]")

    async with BleakClient(device) as client:
        console.print(f"[green]Connected.[/green] Subscribing to {char_uuid}...")

        received = []

        def callback(sender, data):
            hex_str = data.hex(" ")
            console.print(f"[cyan]<< {hex_str}[/cyan]")
            received.append(data)

        await client.start_notify(char_uuid, callback)
        console.print("[dim]Listening for notifications (Ctrl+C to stop)...[/dim]")
        try:
            while True:
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        finally:
            await client.stop_notify(char_uuid)
            console.print(f"[dim]Received {len(received)} notification(s).[/dim]")


@app.command()
def info(
    name: Annotated[
        str,
        typer.Option("--name", "-n", help="BLE device name to connect to."),
    ] = DEFAULT_DEVICE_NAME,
    timeout: Annotated[
        float,
        typer.Option("--timeout", "-t", help="Scan timeout in seconds."),
    ] = 10.0,
) -> None:
    """Connect to a LED cap and show its BLE service tree."""
    if is_dry_run():
        typer.echo(f"[DRY RUN] Would connect to '{name}'")
        return
    asyncio.run(_connect_and_inspect(name, timeout))


@app.command()
def notify(
    char: Annotated[
        str,
        typer.Argument(help="Characteristic UUID to subscribe to."),
    ],
    name: Annotated[
        str,
        typer.Option("--name", "-n", help="BLE device name."),
    ] = DEFAULT_DEVICE_NAME,
    timeout: Annotated[
        float,
        typer.Option("--timeout", "-t", help="Scan timeout in seconds."),
    ] = 10.0,
) -> None:
    """Subscribe to BLE notifications from a characteristic."""
    if is_dry_run():
        typer.echo(f"[DRY RUN] Would subscribe to {char} on '{name}'")
        return
    asyncio.run(_read_notify(name, char, timeout))
