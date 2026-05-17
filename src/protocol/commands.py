"""iPIXEL Color protocol command encoding.

All commands are written to characteristic fa02.
Format: [LEN_LO][LEN_HI][CMD_LO][CMD_HI][DATA...]
All multi-byte fields are little-endian.
"""

import struct
from datetime import UTC, datetime
from zlib import crc32

WRITE_UUID = "0000fa02-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID = "0000fa03-0000-1000-8000-00805f9b34fb"

CMD_PNG_DATA = 0x0002
CMD_GIF_DATA = 0x0003
CMD_ERASE_DATA = 0x0102
CMD_DIY_MODE = 0x0104
CMD_SET_PIXEL = 0x0105
CMD_CLOCK_MODE = 0x0106
CMD_POWER = 0x0107
CMD_SET_TIME = 0x8001
CMD_DEFAULT_MODE = 0x8003
CMD_BRIGHTNESS = 0x8004
CMD_UPSIDE_DOWN = 0x8006
CMD_SELECT_SCREEN = 0x8007
CMD_PROGRAM_MODE = 0x8008


def make_payload(command: int, data: bytes = b"") -> bytes:
    """Encode an iPIXEL command into a BLE-ready byte sequence."""
    length = 4 + len(data)
    return struct.pack("<HH", length, command) + data


def power(on: bool) -> bytes:
    return make_payload(CMD_POWER, bytes([0x01 if on else 0x00]))


def brightness(level: int) -> bytes:
    return make_payload(CMD_BRIGHTNESS, bytes([max(1, min(100, level))]))


def query_device_info() -> bytes:
    """Send time sync which also triggers a device info response."""
    now = datetime.now(UTC)
    return make_payload(CMD_SET_TIME, bytes([now.hour, now.minute, now.second, 0x00]))


def default_mode() -> bytes:
    return make_payload(CMD_DEFAULT_MODE)


def upside_down(flip: bool) -> bytes:
    return make_payload(CMD_UPSIDE_DOWN, bytes([0x01 if flip else 0x00]))


def select_screen(screen: int) -> bytes:
    return make_payload(CMD_SELECT_SCREEN, bytes([screen]))


def diy_mode(enable: bool) -> bytes:
    return make_payload(CMD_DIY_MODE, bytes([0x01 if enable else 0x00]))


def set_pixel(x: int, y: int, r: int, g: int, b: int, a: int = 0xFF) -> bytes:
    return make_payload(CMD_SET_PIXEL, bytes([r, g, b, a, x, y]))


def clock_mode(
    style: int,
    is_24h: bool,
    show_date: bool,
    year: int,
    month: int,
    day: int,
    weekday: int,
) -> bytes:
    return make_payload(
        CMD_CLOCK_MODE,
        bytes(
            [
                style,
                0x01 if is_24h else 0x00,
                0x01 if show_date else 0x00,
                year,
                month,
                day,
                weekday,
            ]
        ),
    )


def png_data(png_bytes: bytes, buffer_number: int = 1) -> bytes:
    """Build payload for sending a PNG image to a display buffer."""
    data = (
        bytes([0x00])
        + len(png_bytes).to_bytes(4, "little")
        + crc32(png_bytes).to_bytes(4, "little")
        + bytes([0x00, buffer_number])
        + png_bytes
    )
    return make_payload(CMD_PNG_DATA, data)


def gif_data(gif_bytes: bytes, buffer_number: int = 1) -> bytes:
    """Build payload for sending a GIF animation to a display buffer."""
    data = (
        bytes([0x00])
        + len(gif_bytes).to_bytes(4, "little")
        + crc32(gif_bytes).to_bytes(4, "little")
        + bytes([0x00, buffer_number])
        + gif_bytes
    )
    return make_payload(CMD_GIF_DATA, data)


def erase_buffers(buffer_numbers: list[int]) -> bytes:
    count = len(buffer_numbers)
    data = count.to_bytes(2, "little") + bytes(buffer_numbers)
    return make_payload(CMD_ERASE_DATA, data)
