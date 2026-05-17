"""Scan for nearby BLE LED cap devices."""

import asyncio
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from src.cli.state import is_dry_run, is_quiet

console = Console()

DEFAULT_DEVICE_PREFIX = "LED_BLE"


def _build_results_table(
    devices: list[dict], prefix: str
) -> tuple[list[dict], list[dict]]:
    matched = []
    other = []
    for d in devices:
        name = d.get("name") or "(unknown)"
        if name.startswith(prefix):
            matched.append(d)
        else:
            other.append(d)
    matched.sort(key=lambda d: d["rssi"], reverse=True)
    other.sort(key=lambda d: d["rssi"], reverse=True)
    return matched, other


async def _scan_ble(timeout: float, prefix: str, show_all: bool) -> None:
    from bleak import BleakScanner

    quiet = is_quiet()

    if not quiet:
        console.print(f"[dim]Scanning for BLE devices ({timeout}s)...[/dim]")
    devices = await BleakScanner.discover(timeout=timeout, return_adv=True)

    results = []
    for _addr, (device, adv_data) in devices.items():
        results.append(
            {
                "address": device.address,
                "name": device.name or "(unknown)",
                "rssi": adv_data.rssi,
            }
        )

    matched, other = _build_results_table(results, prefix)

    if quiet:
        emit = matched + other if show_all else matched
        for d in emit:
            typer.echo(d["name"])
        return

    if not matched:
        console.print(f"[yellow]No devices matching '{prefix}*' found.[/yellow]")
        if not show_all:
            console.print("[dim]Use --all to see all nearby BLE devices.[/dim]")
    else:
        table = Table(title=f"LED Cap Devices ({len(matched)} found)")
        table.add_column("Name", style="cyan bold")
        table.add_column("Address", style="dim")
        table.add_column("RSSI", justify="right")
        for d in matched:
            rssi = d["rssi"]
            rssi_style = "green" if rssi > -60 else "yellow" if rssi > -80 else "red"
            table.add_row(d["name"], d["address"], f"[{rssi_style}]{rssi}[/]")
        console.print(table)

    if show_all and other:
        table = Table(title=f"Other BLE Devices ({len(other)} found)")
        table.add_column("Name", style="white")
        table.add_column("Address", style="dim")
        table.add_column("RSSI", justify="right")
        for d in other:
            table.add_row(d["name"], d["address"], str(d["rssi"]))
        console.print(table)


def main(
    timeout: Annotated[
        float,
        typer.Option("--timeout", "-t", help="Scan duration in seconds."),
    ] = 10.0,
    prefix: Annotated[
        str,
        typer.Option("--prefix", "-p", help="Device name prefix to filter."),
    ] = DEFAULT_DEVICE_PREFIX,
    show_all: Annotated[
        bool,
        typer.Option("--all", "-a", help="Show all BLE devices, not just LED caps."),
    ] = False,
) -> None:
    """Scan for nearby BLE LED cap devices."""
    if is_dry_run():
        typer.echo(f"[DRY RUN] Would scan for BLE devices with prefix '{prefix}'")
        return

    asyncio.run(_scan_ble(timeout, prefix, show_all))
