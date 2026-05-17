"""Tests for iPIXEL device type parsing."""

from src.protocol.device_types import LED_DIMENSIONS, parse_device_info
from tests.test_template import TestTemplate


class TestParseDeviceInfo(TestTemplate):
    def test_short_response_returns_raw(self):
        data = bytes([0x01, 0x02, 0x03])
        result = parse_device_info(data)
        assert "raw" in result
        assert "device_byte" not in result

    def test_known_device_type(self):
        data = bytes([0x08, 0x00, 0x01, 0x80, 132, 0x02, 0x03, 0x01, 0x00, 0x00, 0xFF])
        result = parse_device_info(data)
        assert result["device_byte"] == 132
        assert result["type_id"] == 1
        assert result["dimensions"] == (96, 16)
        assert result["has_password"] is False

    def test_unknown_device_type(self):
        data = bytes([0x08, 0x00, 0x01, 0x80, 200, 0x02, 0x03, 0x01, 0x00, 0x00, 0x01])
        result = parse_device_info(data)
        assert result["device_byte"] == 200
        assert result["type_id"] is None
        assert result["dimensions"] is None
        assert result["has_password"] is True

    def test_password_protected(self):
        data = bytes([0x08, 0x00, 0x01, 0x80, 128, 0x01, 0x00, 0x01, 0x00, 0x00, 42])
        result = parse_device_info(data)
        assert result["has_password"] is True

    def test_all_dimensions_defined(self):
        for _type_id, dims in LED_DIMENSIONS.items():
            assert len(dims) == 2
            assert dims[0] > 0
            assert dims[1] > 0
