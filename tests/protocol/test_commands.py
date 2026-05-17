"""Tests for iPIXEL protocol command encoding."""

from src.protocol.commands import (
    brightness,
    clock_mode,
    default_mode,
    diy_mode,
    erase_buffers,
    make_payload,
    png_data,
    power,
    query_device_info,
    select_screen,
    set_pixel,
    upside_down,
)
from tests.test_template import TestTemplate


class TestMakePayload(TestTemplate):
    def test_empty_data(self):
        result = make_payload(0x8003)
        assert result == bytes([0x04, 0x00, 0x03, 0x80])

    def test_with_data(self):
        result = make_payload(0x0107, bytes([0x01]))
        assert result == bytes([0x05, 0x00, 0x07, 0x01, 0x01])

    def test_length_is_little_endian(self):
        result = make_payload(0x0002, b"\x00" * 300)
        assert result[0] == (304 & 0xFF)
        assert result[1] == (304 >> 8) & 0xFF

    def test_command_is_little_endian(self):
        result = make_payload(0x8004, bytes([0x32]))
        assert result[2] == 0x04
        assert result[3] == 0x80


class TestPowerCommand(TestTemplate):
    def test_power_on(self):
        result = power(on=True)
        assert result == bytes([0x05, 0x00, 0x07, 0x01, 0x01])

    def test_power_off(self):
        result = power(on=False)
        assert result == bytes([0x05, 0x00, 0x07, 0x01, 0x00])


class TestBrightnessCommand(TestTemplate):
    def test_brightness_50(self):
        result = brightness(50)
        assert result == bytes([0x05, 0x00, 0x04, 0x80, 0x32])

    def test_brightness_100(self):
        result = brightness(100)
        assert result == bytes([0x05, 0x00, 0x04, 0x80, 0x64])

    def test_brightness_clamps_low(self):
        result = brightness(0)
        assert result[-1] == 1

    def test_brightness_clamps_high(self):
        result = brightness(200)
        assert result[-1] == 100


class TestDefaultMode(TestTemplate):
    def test_default_mode(self):
        result = default_mode()
        assert result == bytes([0x04, 0x00, 0x03, 0x80])


class TestUpsideDown(TestTemplate):
    def test_flip_on(self):
        result = upside_down(flip=True)
        assert result == bytes([0x05, 0x00, 0x06, 0x80, 0x01])

    def test_flip_off(self):
        result = upside_down(flip=False)
        assert result == bytes([0x05, 0x00, 0x06, 0x80, 0x00])


class TestSelectScreen(TestTemplate):
    def test_screen_3(self):
        result = select_screen(3)
        assert result == bytes([0x05, 0x00, 0x07, 0x80, 0x03])


class TestDiyMode(TestTemplate):
    def test_enable(self):
        result = diy_mode(enable=True)
        assert result == bytes([0x05, 0x00, 0x04, 0x01, 0x01])

    def test_disable(self):
        result = diy_mode(enable=False)
        assert result == bytes([0x05, 0x00, 0x04, 0x01, 0x00])


class TestSetPixel(TestTemplate):
    def test_red_pixel_at_10_20(self):
        result = set_pixel(x=10, y=20, r=0xFF, g=0x00, b=0x00)
        assert result == bytes(
            [0x0A, 0x00, 0x05, 0x01, 0xFF, 0x00, 0x00, 0xFF, 0x0A, 0x14]
        )


class TestClockMode(TestTemplate):
    def test_clock_style_1(self):
        result = clock_mode(
            style=1,
            is_24h=True,
            show_date=True,
            year=26,
            month=5,
            day=17,
            weekday=6,
        )
        assert result == bytes(
            [
                0x0B,
                0x00,
                0x06,
                0x01,
                0x01,
                0x01,
                0x01,
                0x1A,
                0x05,
                0x11,
                0x06,
            ]
        )


class TestQueryDeviceInfo(TestTemplate):
    def test_returns_8_bytes(self):
        result = query_device_info()
        assert len(result) == 8
        assert result[2:4] == bytes([0x01, 0x80])


class TestPngData(TestTemplate):
    def test_structure(self):
        fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
        result = png_data(fake_png, buffer_number=2)
        assert result[2:4] == bytes([0x02, 0x00])
        assert result[4] == 0x00
        assert result[13] == 0x00
        assert result[14] == 2


class TestEraseBuffers(TestTemplate):
    def test_erase_two_buffers(self):
        result = erase_buffers([1, 3])
        assert result[2:4] == bytes([0x02, 0x01])
        assert result[6] == 1
        assert result[7] == 3
