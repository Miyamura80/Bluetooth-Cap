"""Main loop: audio capture -> visualization -> BLE send."""

import asyncio
import time

from bleak import BleakClient
from rich.console import Console
from rich.live import Live
from rich.table import Table

from extensions.audio_reactive.capture import AudioCapture
from extensions.audio_reactive.visualizer import image_to_png_bytes, spectrum_to_image
from src.protocol.commands import CMD_PNG_DATA
from src.protocol.connection import open_device
from src.protocol.transport import send_data

console = Console()


def _stats_table(
    frame_num: int,
    fps: float,
    send_ms: float,
    png_bytes: int,
    peak_mag: float,
) -> Table:
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column(style="dim")
    table.add_column(style="bold")
    table.add_row("Frame", str(frame_num))
    table.add_row("FPS", f"{fps:.1f}")
    table.add_row("Send", f"{send_ms:.0f}ms")
    table.add_row("PNG", f"{png_bytes}B")
    table.add_row("Peak", f"{peak_mag:.2f}")
    return table


async def _send_frame(client: BleakClient, png_bytes: bytes, slot: int) -> float:
    t0 = time.monotonic()
    await send_data(client, CMD_PNG_DATA, png_bytes, slot=slot, timeout=10.0)
    return (time.monotonic() - t0) * 1000


async def run_audio_reactive(
    device_name: str,
    timeout: float = 10.0,
    width: int = 32,
    height: int = 16,
    slot: int = 1,
    sample_rate: int = 44100,
    block_size: int = 2048,
    min_interval: float = 0.0,
    audio_device: int | None = None,
) -> None:
    num_bands = width

    capture = AudioCapture(
        sample_rate=sample_rate,
        block_size=block_size,
        num_bands=num_bands,
        device=audio_device,
    )

    console.print(f"[dim]Connecting to '{device_name}'...[/dim]")

    async with open_device(device_name, timeout) as client:
        console.print(f"[green]Connected[/green] (MTU: {client.mtu_size})")
        console.print("[dim]Starting audio capture... Press Ctrl+C to stop.[/dim]")

        capture.start()
        frame_num = 0
        fps = 0.0
        last_send_ms = 0.0
        last_png_bytes = 0

        try:
            with Live(console=console, refresh_per_second=10) as live:
                t_prev = time.monotonic()
                while True:
                    mags = capture.magnitudes

                    img = spectrum_to_image(mags, width, height)
                    png_bytes = image_to_png_bytes(img)

                    last_send_ms = await _send_frame(client, png_bytes, slot)
                    last_png_bytes = len(png_bytes)

                    frame_num += 1
                    t_now = time.monotonic()
                    dt = t_now - t_prev
                    t_prev = t_now

                    if dt > 0:
                        fps = 1.0 / dt

                    live.update(
                        _stats_table(
                            frame_num,
                            fps,
                            last_send_ms,
                            last_png_bytes,
                            float(mags.max()),
                        )
                    )

                    if min_interval > 0:
                        elapsed = time.monotonic() - t_now
                        if elapsed < min_interval:
                            await asyncio.sleep(min_interval - elapsed)

        except KeyboardInterrupt:
            console.print("\n[yellow]Stopped.[/yellow]")
        finally:
            capture.stop()

        console.print(
            f"[green]Done.[/green] {frame_num} frames sent, last FPS: {fps:.1f}"
        )
