"""Composite frame renderer: typewriter text + spectrum bars."""

import io
import threading
import time

import numpy as np
from PIL import Image, ImageDraw

from src.transcription.assets import (
    FONT,
    ICONS,
    LAYERED_ICONS,
    MACROS,
    PHRASE_MACROS,
    TEXT_MACROS,
    Color,
)

SPECTRUM_COLORS = [
    (0, 255, 0),
    (100, 255, 0),
    (200, 255, 0),
    (255, 200, 0),
    (255, 100, 0),
    (255, 0, 0),
]

_CHAR_GAP = 1


def _char_width(ch: str) -> int:
    entry = FONT.get(ch)
    return entry[0] if entry else 0


def _measure_word(word: str) -> int:
    total = 0
    for i, ch in enumerate(word):
        total += _char_width(ch)
        if i < len(word) - 1:
            total += _CHAR_GAP
    return total


def _word_width(word: str) -> int:
    icon_name = MACROS.get(word)
    if icon_name:
        if icon_name in ICONS:
            return ICONS[icon_name][0]
        if icon_name in LAYERED_ICONS:
            return LAYERED_ICONS[icon_name][0][0]
    return _measure_word(word)


class TextStrip:
    """Thread-safe two-row typewriter text display.

    Words fill left-to-right across two rows. When both rows are full,
    the screen wipes and text restarts from the top-left.
    """

    def __init__(
        self,
        text_height: int = 14,
        width: int = 32,
        fg: tuple[int, int, int] = (255, 255, 255),
        bg: tuple[int, int, int] = (0, 0, 0),
    ):
        self.width = width
        self.text_height = text_height
        self.fg = fg
        self.bg = bg
        self._row_height = text_height // 2
        self._text = ""
        self._lock = threading.Lock()

        self._lines: list[list[tuple[str, int]]] = [[], []]
        self._cursor_x = 0
        self._cursor_row = 0
        self._frame: Image.Image | None = None
        self._linger_until = 0.0
        self._pending_words: list[str] = []
        self._space_w = _char_width(" ")

    @property
    def text(self) -> str:
        with self._lock:
            return self._text

    @property
    def has_content(self) -> bool:
        with self._lock:
            return self._frame is not None

    def _wipe(self) -> None:
        self._lines = [[], []]
        self._cursor_row = 0
        self._cursor_x = 0

    def _would_overflow(self, word: str) -> bool:
        if self._cursor_row < 1:
            return False
        word_w = _word_width(word)
        space_w = self._space_w + _CHAR_GAP if self._cursor_x > 0 else 0
        return self._cursor_x + space_w + word_w > self.width

    def _place_word(self, word: str) -> None:
        word_w = _word_width(word)
        space_w = self._space_w + _CHAR_GAP if self._cursor_x > 0 else 0

        if (
            self._cursor_x > 0
            and self._cursor_x + space_w + word_w > self.width
            and self._cursor_row == 0
        ):
            self._cursor_row = 1
            self._cursor_x = 0
            space_w = 0

        if word_w <= self.width:
            self._cursor_x += space_w
            self._lines[self._cursor_row].append((word, self._cursor_x))
            self._cursor_x += word_w
            return

        idx = 0
        while idx < len(word) and self._cursor_row <= 1:
            sp = self._space_w + _CHAR_GAP if self._cursor_x > 0 else 0
            fit = 0
            w = sp
            for j in range(idx, len(word)):
                cw = _char_width(word[j])
                gap = _CHAR_GAP if fit > 0 else 0
                if self._cursor_x + w + gap + cw > self.width:
                    break
                w += gap + cw
                fit += 1
            if fit == 0:
                if self._cursor_row == 0:
                    self._cursor_row = 1
                    self._cursor_x = 0
                    continue
                break
            chunk = word[idx : idx + fit]
            self._cursor_x += sp
            self._lines[self._cursor_row].append((chunk, self._cursor_x))
            self._cursor_x += _measure_word(chunk)
            idx += fit
            if idx < len(word) and self._cursor_row == 0:
                self._cursor_row = 1
                self._cursor_x = 0

    @staticmethod
    def _preprocess_words(words: list[str]) -> list[str]:
        result: list[str] = []
        cleaned = [w.rstrip(".,!?;:") for w in words]
        i = 0
        while i < len(words):
            matched = False
            for phrase, abbrev in PHRASE_MACROS:
                end = i + len(phrase)
                if end <= len(cleaned) and cleaned[i:end] == phrase:
                    result.append(abbrev)
                    i = end
                    matched = True
                    break
            if not matched:
                w = cleaned[i]
                result.append(TEXT_MACROS.get(w, w))
                i += 1
        return result

    def append(self, new_text: str) -> None:
        with self._lock:
            self._text = (self._text + " " + new_text.upper()).strip()
            words = self._preprocess_words(new_text.upper().split())

            for word in words:
                if self._linger_until > 0:
                    self._pending_words.append(word)
                elif self._cursor_row == 1 and self._would_overflow(word):
                    self._linger_until = time.monotonic() + 1.0
                    self._pending_words.append(word)
                else:
                    self._place_word(word)
                    self._frame = self._render()

    def _draw_bitmap(
        self,
        pixels: list[list[Color | None]],
        bitmap: tuple[int, list[int]],
        x: int,
        y: int,
        color: Color = (255, 255, 255),
    ) -> None:
        w, rows = bitmap
        for row_i, bits in enumerate(rows):
            py = y + row_i
            if py < 0 or py >= self.text_height:
                continue
            for bit in range(w):
                px = x + (w - 1 - bit)
                if 0 <= px < self.width and bits & (1 << bit):
                    pixels[py][px] = color

    def _draw_word(
        self,
        pixels: list[list[Color | None]],
        word: str,
        wx: int,
        y: int,
    ) -> None:
        icon_name = MACROS.get(word)
        if icon_name and icon_name in ICONS:
            w, rows, color = ICONS[icon_name]
            self._draw_bitmap(pixels, (w, rows), wx, y, color)
        elif icon_name and icon_name in LAYERED_ICONS:
            for lw, lrows, lcolor in LAYERED_ICONS[icon_name]:
                self._draw_bitmap(pixels, (lw, lrows), wx, y, lcolor)
        else:
            cx = wx
            for i, ch in enumerate(word):
                entry = FONT.get(ch)
                if entry:
                    self._draw_bitmap(pixels, entry, cx, y, self.fg)
                cx += _char_width(ch)
                if i < len(word) - 1:
                    cx += _CHAR_GAP

    def _render(self) -> Image.Image:
        pixels: list[list[Color | None]] = [
            [None] * self.width for _ in range(self.text_height)
        ]

        for row_idx, line in enumerate(self._lines):
            y = row_idx * self._row_height
            for word, wx in line:
                self._draw_word(pixels, word, wx, y)

        frame = Image.new("RGB", (self.width, self.text_height), self.bg)
        for y in range(self.text_height):
            for x in range(self.width):
                px = pixels[y][x]
                if px is not None:
                    frame.putpixel((x, y), px)
        return frame

    def get_text_row(self) -> Image.Image | None:
        with self._lock:
            if self._linger_until > 0 and time.monotonic() >= self._linger_until:
                self._linger_until = 0.0
                self._wipe()
                pending = self._pending_words
                self._pending_words = []
                for i, word in enumerate(pending):
                    if self._cursor_row == 1 and self._would_overflow(word):
                        self._frame = self._render()
                        self._linger_until = time.monotonic() + 1.0
                        self._pending_words = pending[i:]
                        return self._frame
                    self._place_word(word)
                self._frame = self._render()
            return self._frame


def render_composite_frame(
    text_row: Image.Image | None,
    magnitudes: np.ndarray,
    width: int = 32,
    height: int = 16,
    spectrum_height: int = 1,
) -> bytes:
    """Combine typewriter text (top) with spectrum bars (bottom) into one PNG."""
    frame = Image.new("RGB", (width, height), (0, 0, 0))

    if text_row is not None:
        frame.paste(text_row, (0, 0))

    draw = ImageDraw.Draw(frame)
    num_bands = min(len(magnitudes), width)

    for i in range(num_bands):
        bar_h = int(magnitudes[i] * spectrum_height)
        bar_h = max(0, min(spectrum_height, bar_h))
        for j in range(bar_h):
            row_frac = j / max(1, spectrum_height - 1)
            idx = int(row_frac * (len(SPECTRUM_COLORS) - 1))
            idx = min(idx, len(SPECTRUM_COLORS) - 2)
            local_frac = row_frac * (len(SPECTRUM_COLORS) - 1) - idx
            c0 = SPECTRUM_COLORS[idx]
            c1 = SPECTRUM_COLORS[idx + 1]
            color = (
                int(c0[0] + (c1[0] - c0[0]) * local_frac),
                int(c0[1] + (c1[1] - c0[1]) * local_frac),
                int(c0[2] + (c1[2] - c0[2]) * local_frac),
            )
            py = height - 1 - j
            draw.point((i, py), fill=color)

    for x in range(width):
        draw.point((x, height - 1), fill=(0, 200, 0))

    buf = io.BytesIO()
    frame.save(buf, format="PNG")
    return buf.getvalue()
