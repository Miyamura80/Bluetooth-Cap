"""Main loop: streaming capture -> AssemblyAI realtime -> composite frames."""

import time
from dataclasses import dataclass

from bleak import BleakClient
from rich.console import Console
from rich.live import Live
from rich.table import Table

from extensions.transcription.capture import UnifiedCapture
from extensions.transcription.renderer import TextStrip, render_composite_frame
from extensions.transcription.transcriber import Transcriber
from src.protocol.commands import CMD_PNG_DATA
from src.protocol.connection import open_device
from src.protocol.transport import send_data

console = Console()


@dataclass
class _Stats:
    segments: int = 0
    send_ms: float = 0.0
    fps: float = 0.0
    latest_text: str = ""


def _stats_table(s: _Stats, transcript: str) -> Table:
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column(style="dim", width=10)
    table.add_column(style="bold")
    table.add_row("Segments", str(s.segments))
    table.add_row("Send", f"{s.send_ms:.0f}ms")
    table.add_row("FPS", f"{s.fps:.1f}")
    table.add_row("Latest", s.latest_text)
    display = transcript
    if len(display) > 120:
        display = "..." + display[-117:]
    table.add_row("Transcript", display)
    return table


async def _frame_loop(
    client: BleakClient,
    capture: UnifiedCapture,
    strip: TextStrip,
    stats: _Stats,
    transcriber: Transcriber,
    width: int,
    height: int,
    slot: int,
    spectrum_height: int,
) -> None:
    with Live(console=console, refresh_per_second=10) as live:
        t_prev = time.monotonic()
        while True:
            err = transcriber.get_error()
            if err:
                stats.latest_text = f"[ERR] {err}"

            mags = capture.magnitudes
            text_row = strip.get_text_row()

            png = render_composite_frame(text_row, mags, width, height, spectrum_height)

            t1 = time.monotonic()
            await send_data(client, CMD_PNG_DATA, png, slot=slot, timeout=10.0)
            stats.send_ms = (time.monotonic() - t1) * 1000

            t_now = time.monotonic()
            dt = t_now - t_prev
            t_prev = t_now
            if dt > 0:
                stats.fps = 1.0 / dt

            live.update(_stats_table(stats, strip.text))


async def run_transcription(
    device_name: str,
    timeout: float = 10.0,
    width: int = 32,
    height: int = 16,
    slot: int = 1,
    sample_rate: int = 16000,
    audio_device: int | None = None,
    spectrum_height: int = 1,
) -> None:
    text_height = max(1, height - spectrum_height)

    capture = UnifiedCapture(
        sample_rate=sample_rate,
        block_size=1024,
        num_bands=width,
        device=audio_device,
    )
    transcriber = Transcriber()
    strip = TextStrip(text_height=text_height, width=width)
    stats = _Stats()

    def on_text(text: str) -> None:
        stats.segments += 1
        stats.latest_text = text
        strip.append(text)

    console.print(f"[dim]Connecting to '{device_name}'...[/dim]")

    async with open_device(device_name, timeout) as client:
        console.print(f"[green]Connected[/green] (MTU: {client.mtu_size})")
        console.print("[dim]Starting realtime transcription...[/dim]")

        transcriber.start(on_text=on_text, sample_rate=sample_rate)
        capture.start(on_audio=transcriber.send_audio)

        console.print("[dim]Listening... Press Ctrl+C to stop.[/dim]")

        try:
            await _frame_loop(
                client,
                capture,
                strip,
                stats,
                transcriber,
                width,
                height,
                slot,
                spectrum_height,
            )
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopped.[/yellow]")
        finally:
            capture.stop()
            transcriber.stop()

        if strip.text:
            console.print(f"\n[bold]Full transcript:[/bold]\n{strip.text}")
