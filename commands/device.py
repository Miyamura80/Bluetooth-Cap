"""Connect to a LED cap and inspect its BLE services."""

import asyncio
from typing import Annotated

import typer
from rich.console import Console
from rich.tree import Tree

from src.cli.state import is_dry_run

app = typer.Typer()
console = Console()


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

        count = 0

        def callback(sender, data):
            nonlocal count
            hex_str = data.hex(" ")
            console.print(f"[cyan]<< {hex_str}[/cyan]")
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


def _resolve_device_name(name: str | None) -> str:
    if name:
        return name
    try:
        from common import global_config

        ble_cfg = getattr(global_config, "ble", None)
        if isinstance(ble_cfg, dict) and ble_cfg.get("device_name"):
            return ble_cfg["device_name"]
    except (ImportError, AttributeError, KeyError, TypeError):
        pass
    console.print("[red]No device name specified.[/red]")
    console.print("[dim]Use --name or set ble.device_name in global_config.yaml[/dim]")
    console.print("[dim]Example: bluecap device info --name LED_BLE_62F7C880[/dim]")
    raise typer.Exit(code=1)


@app.command()
def info(
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="BLE device name (e.g. LED_BLE_62F7C880)."),
    ] = None,
    timeout: Annotated[
        float,
        typer.Option("--timeout", "-t", help="Scan timeout in seconds."),
    ] = 10.0,
) -> None:
    """Connect to a LED cap and show its BLE service tree."""
    device_name = _resolve_device_name(name)
    if is_dry_run():
        typer.echo(f"[DRY RUN] Would connect to '{device_name}'")
        return
    asyncio.run(_connect_and_inspect(device_name, timeout))


@app.command()
def notify(
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
    device_name = _resolve_device_name(name)
    if is_dry_run():
        typer.echo(f"[DRY RUN] Would subscribe to {char} on '{device_name}'")
        return
    asyncio.run(_read_notify(device_name, char, timeout))
