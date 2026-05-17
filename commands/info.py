"""Connect to a LED cap and inspect its BLE services."""

import asyncio
from typing import Annotated

import typer
from rich.console import Console
from rich.tree import Tree

from commands._resolve import resolve_device_name
from src.cli.state import is_dry_run
from src.protocol.connection import open_device

console = Console()


async def _inspect(name: str, timeout: float) -> None:
    async with open_device(name, timeout) as client:
        console.print(f"[green]Connected[/green] (MTU: {client.mtu_size})")
        console.print()

        tree = Tree(f"[bold cyan]{name}[/bold cyan]")
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


def main(
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
    device_name = resolve_device_name(name, console)
    if is_dry_run():
        typer.echo(f"[DRY RUN] Would connect to '{device_name}'")
        return
    console.print(f"[dim]Connecting to '{device_name}' ({timeout}s)...[/dim]")
    asyncio.run(_inspect(device_name, timeout))
