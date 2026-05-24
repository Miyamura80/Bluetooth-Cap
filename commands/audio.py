"""Audio-reactive LED visualization on the cap."""

import asyncio
from typing import Annotated

import typer
from rich.console import Console

from commands._resolve import resolve_device_name
from src.cli.state import is_dry_run

console = Console()

DISPLAY_WIDTH = 32
DISPLAY_HEIGHT = 16


def main(
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="BLE device name."),
    ] = None,
    timeout: Annotated[
        float,
        typer.Option("--timeout", "-t", help="Scan timeout in seconds."),
    ] = 10.0,
    width: Annotated[
        int,
        typer.Option("--width", "-W", help="Display width in pixels."),
    ] = DISPLAY_WIDTH,
    height: Annotated[
        int,
        typer.Option("--height", "-H", help="Display height in pixels."),
    ] = DISPLAY_HEIGHT,
    slot: Annotated[
        int,
        typer.Option("--slot", "-s", help="Display buffer slot (1-9)."),
    ] = 1,
    sample_rate: Annotated[
        int,
        typer.Option("--sample-rate", help="Audio sample rate in Hz."),
    ] = 44100,
    block_size: Annotated[
        int,
        typer.Option("--block-size", help="FFT block size (power of 2)."),
    ] = 2048,
    min_interval: Annotated[
        float,
        typer.Option(
            "--min-interval",
            help="Minimum seconds between frames (0 = as fast as BLE allows).",
        ),
    ] = 0.0,
    audio_device: Annotated[
        int | None,
        typer.Option(
            "--audio-device",
            "-d",
            help="Audio input device index (see --list-devices).",
        ),
    ] = None,
    list_devices: Annotated[
        bool,
        typer.Option("--list-devices", help="List audio input devices and exit."),
    ] = False,
) -> None:
    """Stream live audio-reactive spectrum visualization to the LED cap."""
    if list_devices:
        import sounddevice as sd

        for i, d in enumerate(sd.query_devices()):
            if d["max_input_channels"] > 0:
                marker = " *" if d == sd.query_devices(kind="input") else ""
                console.print(
                    f"  [{i}] {d['name']} ({d['max_input_channels']}ch){marker}"
                )
        return

    device_name = resolve_device_name(name, console)
    if is_dry_run():
        typer.echo(f"[DRY RUN] Would stream audio visualization to '{device_name}'")
        return

    from src.audio_reactive.engine import run_audio_reactive

    asyncio.run(
        run_audio_reactive(
            device_name=device_name,
            timeout=timeout,
            width=width,
            height=height,
            slot=slot,
            sample_rate=sample_rate,
            block_size=block_size,
            min_interval=min_interval,
            audio_device=audio_device,
        )
    )
