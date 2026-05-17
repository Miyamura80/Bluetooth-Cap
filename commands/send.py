"""Send raw bytes to the LED cap for protocol reverse engineering."""

import asyncio
from typing import Annotated

import typer
from rich.console import Console

from commands._resolve import resolve_device_name
from src.cli.state import is_dry_run
from src.protocol.commands import NOTIFY_UUID, WRITE_UUID
from src.protocol.connection import open_device

console = Console()


def _parse_hex_args(hex_args: list[str]) -> bytes:
    """Parse hex arguments like 'AA BB CC' or '0xAA 0xBB' or 'AABBCC' into bytes."""
    joined = "".join(hex_args)
    cleaned = joined.replace("0x", "").replace("0X", "").replace(" ", "")
    if len(cleaned) % 2 != 0:
        console.print("[red]Hex string must have even number of characters.[/red]")
        raise typer.Exit(code=1)
    try:
        return bytes.fromhex(cleaned)
    except ValueError as exc:
        console.print(f"[red]Invalid hex: {exc}[/red]")
        raise typer.Exit(code=1) from exc


async def _send(
    name: str,
    data: bytes,
    char_uuid: str,
    timeout: float,
    listen: bool,
    listen_duration: float,
) -> None:
    async with open_device(name, timeout) as client:
        console.print(f"[green]Connected[/green] (MTU: {client.mtu_size})")

        notifications: list[bytes] = []

        if listen:

            def on_notify(_char: object, recv: bytearray) -> None:
                notifications.append(bytes(recv))
                console.print(f"[cyan]<< {recv.hex(' ')}[/cyan]")

            await client.start_notify(NOTIFY_UUID, on_notify)

        try:
            console.print(f"[yellow]>> {data.hex(' ')}[/yellow]  ({len(data)} bytes)")
            await client.write_gatt_char(char_uuid, data)

            if listen:
                console.print(
                    f"[dim]Listening for responses ({listen_duration}s)...[/dim]"
                )
                await asyncio.sleep(listen_duration)
                if not notifications:
                    console.print("[dim]No notifications received.[/dim]")
                else:
                    console.print(
                        f"[dim]Received {len(notifications)} notification(s).[/dim]"
                    )
        finally:
            if listen:
                await client.stop_notify(NOTIFY_UUID)


def main(
    hex_bytes: Annotated[
        list[str],
        typer.Argument(help="Hex bytes to send (e.g. 05 00 07 01 01)."),
    ],
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="BLE device name."),
    ] = None,
    char: Annotated[
        str,
        typer.Option("--char", "-c", help="Write characteristic UUID."),
    ] = WRITE_UUID,
    timeout: Annotated[
        float,
        typer.Option("--timeout", "-t", help="Scan timeout in seconds."),
    ] = 10.0,
    listen: Annotated[
        bool,
        typer.Option("--listen", "-l", help="Listen for notifications after sending."),
    ] = True,
    listen_duration: Annotated[
        float,
        typer.Option(
            "--listen-for", help="How long to listen for responses (seconds)."
        ),
    ] = 3.0,
) -> None:
    """Send raw hex bytes to the cap (for protocol reverse engineering).

    Examples:
        bluecap send 05 00 07 01 01          # power on
        bluecap send 05 00 04 80 32          # brightness 50%
        bluecap send 08 00 01 80 0E 1E 00 00 # device info query
    """
    data = _parse_hex_args(hex_bytes)
    device_name = resolve_device_name(name, console)
    if is_dry_run():
        typer.echo(f"[DRY RUN] Would send {data.hex(' ')} to '{device_name}'")
        return
    console.print(f"[dim]Connecting to '{device_name}'...[/dim]")
    asyncio.run(_send(device_name, data, char, timeout, listen, listen_duration))
