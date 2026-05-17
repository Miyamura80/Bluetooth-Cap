"""iPIXEL device type detection and LED dimension mapping."""

DEVICE_TYPE_TO_ID: dict[int, int] = {
    128: 0,
    129: 2,
    130: 4,
    131: 3,
    132: 1,
    133: 5,
    134: 6,
    135: 7,
    136: 8,
    137: 9,
    138: 10,
    139: 11,
    140: 12,
    141: 13,
    142: 14,
    143: 15,
    144: 16,
    145: 17,
    146: 18,
    147: 19,
}

LED_DIMENSIONS: dict[int, tuple[int, int]] = {
    0: (64, 64),
    1: (96, 16),
    2: (32, 32),
    3: (64, 16),
    4: (32, 16),
    5: (64, 20),
    6: (128, 32),
    7: (144, 16),
    8: (192, 16),
    9: (48, 24),
    10: (64, 32),
    11: (96, 32),
    12: (128, 32),
    13: (96, 32),
    14: (160, 32),
    15: (192, 32),
    16: (256, 32),
    17: (320, 32),
    18: (384, 32),
    19: (448, 32),
}


def parse_device_info(data: bytes) -> dict:
    """Parse a device info response from the fa03 notify characteristic.

    Returns a dict with parsed fields and always includes the raw hex.
    """
    result: dict = {"raw": data.hex(" "), "length": len(data)}

    if len(data) < 5:
        return result

    device_byte = data[4]
    type_id = DEVICE_TYPE_TO_ID.get(device_byte)
    dimensions = LED_DIMENSIONS.get(type_id) if type_id is not None else None

    result["device_byte"] = device_byte
    result["type_id"] = type_id
    result["dimensions"] = dimensions

    if len(data) >= 8:
        result["mcu_version"] = f"{data[4]}.{data[5]}"
        result["ble_version"] = f"{data[6]}.{data[7]}"

    if len(data) >= 11:
        result["password_flag"] = data[10]
        result["has_password"] = data[10] != 255

    return result
