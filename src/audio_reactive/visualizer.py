"""Render audio spectrum data as PIL images for the LED matrix."""

import io

import numpy as np
from PIL import Image, ImageDraw

PALETTE = [
    (0, 255, 0),
    (50, 255, 0),
    (100, 255, 0),
    (150, 255, 0),
    (200, 255, 0),
    (255, 255, 0),
    (255, 200, 0),
    (255, 150, 0),
    (255, 100, 0),
    (255, 50, 0),
    (255, 0, 0),
    (255, 0, 0),
    (255, 0, 50),
    (255, 0, 100),
    (255, 0, 150),
    (255, 0, 200),
]


def _lerp_color(
    frac: float, low: tuple[int, int, int], high: tuple[int, int, int]
) -> tuple[int, int, int]:
    return (
        int(low[0] + (high[0] - low[0]) * frac),
        int(low[1] + (high[1] - low[1]) * frac),
        int(low[2] + (high[2] - low[2]) * frac),
    )


def spectrum_to_image(
    magnitudes: np.ndarray,
    width: int = 32,
    height: int = 16,
) -> Image.Image:
    """Render spectrum bars onto a PIL Image."""
    img = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    num_bands = len(magnitudes)
    bar_width = max(1, width // num_bands)

    for i in range(min(num_bands, width // bar_width)):
        bar_height = int(magnitudes[i] * height)
        bar_height = max(0, min(height, bar_height))

        x0 = i * bar_width
        x1 = x0 + bar_width - 1

        for y in range(bar_height):
            row_frac = y / max(1, height - 1)
            idx = int(row_frac * (len(PALETTE) - 1))
            idx = min(idx, len(PALETTE) - 2)
            local_frac = row_frac * (len(PALETTE) - 1) - idx
            color = _lerp_color(local_frac, PALETTE[idx], PALETTE[idx + 1])

            py = height - 1 - y
            draw.line([(x0, py), (x1, py)], fill=color)

    return img


def image_to_png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
