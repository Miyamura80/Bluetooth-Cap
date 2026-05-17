"""Windowed BLE data transfer for large payloads (images, GIFs, text).

The iPIXEL protocol splits payloads larger than 12KB into windows.
Each window gets its own header with an option byte (0x00 first, 0x02
subsequent) and the total data size/CRC. The device ACKs each window
before the next is sent.
"""

import asyncio
from zlib import crc32

from bleak import BleakClient, BleakGATTCharacteristic

from src.protocol.commands import NOTIFY_UUID, WRITE_UUID, make_payload

WINDOW_SIZE = 12288


async def send_data(
    client: BleakClient,
    cmd: int,
    raw_data: bytes,
    slot: int = 1,
    timeout: float = 30.0,
) -> list[bytes]:
    """Send data with automatic windowing for large payloads.

    Builds per-window payloads (option + total_size + total_crc + slot + chunk),
    sends each in MTU-sized BLE writes, and waits for ACK after each window.

    Returns a list of ACK responses (one per window).
    """
    total_size = len(raw_data)
    total_crc = crc32(raw_data) & 0xFFFFFFFF

    windows = []
    for i in range(0, total_size, WINDOW_SIZE):
        windows.append(raw_data[i : i + WINDOW_SIZE])

    if not windows:
        windows = [b""]

    chunk_size = min(client.mtu_size - 3, 512)
    acks: list[bytes] = []

    for i, window_data in enumerate(windows):
        option = 0x00 if i == 0 else 0x02
        header = (
            bytes([option])
            + total_size.to_bytes(4, "little")
            + total_crc.to_bytes(4, "little")
            + bytes([0x00, slot])
        )
        payload = make_payload(cmd, header + window_data)

        ack_future: asyncio.Future[bytes] = asyncio.get_event_loop().create_future()

        def _on_ack(
            _char: BleakGATTCharacteristic,
            data: bytearray,
            fut: asyncio.Future[bytes] = ack_future,
        ) -> None:
            if not fut.done():
                fut.set_result(bytes(data))

        await client.start_notify(NOTIFY_UUID, _on_ack)
        try:
            for j in range(0, len(payload), chunk_size):
                await client.write_gatt_char(WRITE_UUID, payload[j : j + chunk_size])
            ack = await asyncio.wait_for(ack_future, timeout=timeout)
            acks.append(ack)
        except TimeoutError:
            acks.append(b"")
            break
        finally:
            await client.stop_notify(NOTIFY_UUID)

    return acks
