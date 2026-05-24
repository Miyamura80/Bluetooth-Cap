"""Live voice transcription streamed to the LED cap."""

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
    ] = 16000,
    audio_device: Annotated[
        int | None,
        typer.Option(
            "--audio-device",
            "-d",
            help="Audio input device index (see 'bluecap audio --list-devices').",
        ),
    ] = None,
    spectrum_height: Annotated[
        int,
        typer.Option("--spectrum-height", help="Height of spectrum bar area."),
    ] = 1,
    list_devices: Annotated[
        bool,
        typer.Option("--list-devices", help="List audio input devices and exit."),
    ] = False,
) -> None:
    """Stream live voice transcription to the LED cap via AssemblyAI."""
    if list_devices:
        import sounddevice as sd

        for i, d in enumerate(sd.query_devices()):
            if d["max_input_channels"] > 0:
                marker = " *" if d == sd.query_devices(kind="input") else ""
                console.print(
                    f"  [{i}] {d['name']} ({d['max_input_channels']}ch){marker}"
                )
        return

    import os

    if not os.environ.get("ASSEMBLY_AI_API_KEY"):
        console.print(
            "[red]ASSEMBLY_AI_API_KEY not set.[/red] "
            "Export it before running: export ASSEMBLY_AI_API_KEY=..."
        )
        raise typer.Exit(code=1)

    device_name = resolve_device_name(name, console)
    if is_dry_run():
        typer.echo(f"[DRY RUN] Would stream transcription to '{device_name}'")
        return

    from src.transcription.engine import run_transcription

    asyncio.run(
        run_transcription(
            device_name=device_name,
            timeout=timeout,
            width=width,
            height=height,
            slot=slot,
            sample_rate=sample_rate,
            audio_device=audio_device,
            spectrum_height=spectrum_height,
        )
    )
