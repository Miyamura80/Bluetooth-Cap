"""BLE connection management for iPIXEL devices."""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from bleak import BleakClient, BleakGATTCharacteristic, BleakScanner

from src.protocol.commands import NOTIFY_UUID, WRITE_UUID


class DeviceNotFoundError(Exception):
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Device '{name}' not found")


@asynccontextmanager
async def open_device(
    name: str, timeout: float = 10.0
) -> AsyncGenerator[BleakClient, None]:
    """Find and connect to a named BLE device."""
    device = await BleakScanner.find_device_by_name(name, timeout=timeout)
    if device is None:
        raise DeviceNotFoundError(name)

    async with BleakClient(device) as client:
        yield client


async def write_command(client: BleakClient, payload: bytes) -> None:
    """Write a command payload to the iPIXEL write characteristic."""
    await client.write_gatt_char(WRITE_UUID, payload)


async def send_and_receive(
    client: BleakClient,
    payload: bytes,
    timeout: float = 5.0,
) -> bytes | None:
    """Write a command and wait for a single notification response."""
    response: asyncio.Future[bytes] = asyncio.get_event_loop().create_future()

    def on_notify(_char: BleakGATTCharacteristic, data: bytearray) -> None:
        if not response.done():
            response.set_result(bytes(data))

    await client.start_notify(NOTIFY_UUID, on_notify)
    try:
        await client.write_gatt_char(WRITE_UUID, payload)
        return await asyncio.wait_for(response, timeout=timeout)
    except TimeoutError:
        return None
    finally:
        await client.stop_notify(NOTIFY_UUID)


async def send_chunked(
    client: BleakClient,
    payload: bytes,
    timeout: float = 10.0,
) -> bytes | None:
    """Send a large payload in MTU-sized chunks and wait for ACK."""
    chunk_size = min(client.mtu_size - 3, 512)

    ack: asyncio.Future[bytes] = asyncio.get_event_loop().create_future()

    def on_ack(_char: BleakGATTCharacteristic, data: bytearray) -> None:
        if not ack.done():
            ack.set_result(bytes(data))

    await client.start_notify(NOTIFY_UUID, on_ack)
    try:
        for i in range(0, len(payload), chunk_size):
            await client.write_gatt_char(WRITE_UUID, payload[i : i + chunk_size])
        return await asyncio.wait_for(ack, timeout=timeout)
    except TimeoutError:
        return None
    finally:
        await client.stop_notify(NOTIFY_UUID)
