"""Display a clock on the LED cap."""

import asyncio
from datetime import datetime
from typing import Annotated

import typer
from rich.console import Console

from commands._resolve import resolve_device_name
from src.cli.state import is_dry_run
from src.protocol import commands as proto
from src.protocol.connection import open_device, write_command

console = Console()


async def _set_clock(
    name: str,
    style: int,
    is_24h: bool,
    show_date: bool,
    timeout: float,
) -> None:
    now = datetime.now()  # noqa: DTZ005 - local time is correct here, the cap has no timezone

    async with open_device(name, timeout) as client:
        time_payload = proto.make_payload(
            proto.CMD_SET_TIME,
            bytes([now.hour, now.minute, now.second, 0x00]),
        )
        console.print(
            f"[yellow]>> {time_payload.hex(' ')}[/yellow]  (sync time {now.strftime('%H:%M:%S')})"
        )
        await write_command(client, time_payload)

        clock_payload = proto.clock_mode(
            style=style,
            is_24h=is_24h,
            show_date=show_date,
            year=now.year % 100,
            month=now.month,
            day=now.day,
            weekday=now.isoweekday() % 7,
        )
        console.print(
            f"[yellow]>> {clock_payload.hex(' ')}[/yellow]  (clock style {style})"
        )
        await write_command(client, clock_payload)
        console.print(
            f"[green]Clock mode set (style {style}, {'24h' if is_24h else '12h'}).[/green]"
        )


def main(
    style: Annotated[
        int,
        typer.Option("--style", "-s", help="Clock style (0-7)."),
    ] = 0,
    is_24h: Annotated[
        bool,
        typer.Option("--24h/--12h", help="24-hour or 12-hour format."),
    ] = True,
    show_date: Annotated[
        bool,
        typer.Option("--date/--no-date", help="Show date alongside time."),
    ] = False,
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="BLE device name."),
    ] = None,
    timeout: Annotated[
        float,
        typer.Option("--timeout", "-t", help="Scan timeout in seconds."),
    ] = 10.0,
) -> None:
    """Display a clock on the LED cap."""
    if style < 0 or style > 7:
        console.print("[red]Style must be between 0 and 7.[/red]")
        raise typer.Exit(code=1)
    device_name = resolve_device_name(name, console)
    if is_dry_run():
        typer.echo(f"[DRY RUN] Would set clock style {style} on '{device_name}'")
        return
    console.print(f"[dim]Connecting to '{device_name}'...[/dim]")
    asyncio.run(_set_clock(device_name, style, is_24h, show_date, timeout))
