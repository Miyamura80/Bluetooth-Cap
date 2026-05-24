"""Composite frame renderer: typewriter text + spectrum bars."""

import io
import threading
import time

import numpy as np
from PIL import Image, ImageDraw

SPECTRUM_COLORS = [
    (0, 255, 0),
    (100, 255, 0),
    (200, 255, 0),
    (255, 200, 0),
    (255, 100, 0),
    (255, 0, 0),
]

# 4x7 bitmap font (M/W are 5 wide). MSB = leftmost pixel.
_FONT: dict[str, tuple[int, list[int]]] = {
    " ": (2, [0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]),
    "A": (4, [0x6, 0x9, 0x9, 0xF, 0x9, 0x9, 0x9]),
    "B": (4, [0xE, 0x9, 0x9, 0xE, 0x9, 0x9, 0xE]),
    "C": (4, [0x6, 0x9, 0x8, 0x8, 0x8, 0x9, 0x6]),
    "D": (4, [0xE, 0x9, 0x9, 0x9, 0x9, 0x9, 0xE]),
    "E": (4, [0xF, 0x8, 0x8, 0xE, 0x8, 0x8, 0xF]),
    "F": (4, [0xF, 0x8, 0x8, 0xE, 0x8, 0x8, 0x8]),
    "G": (4, [0x6, 0x9, 0x8, 0xB, 0x9, 0x9, 0x6]),
    "H": (4, [0x9, 0x9, 0x9, 0xF, 0x9, 0x9, 0x9]),
    "I": (3, [0x7, 0x2, 0x2, 0x2, 0x2, 0x2, 0x7]),
    "J": (4, [0x3, 0x1, 0x1, 0x1, 0x9, 0x9, 0x6]),
    "K": (4, [0x9, 0xA, 0xC, 0xC, 0xA, 0x9, 0x9]),
    "L": (4, [0x8, 0x8, 0x8, 0x8, 0x8, 0x8, 0xF]),
    "M": (5, [0x11, 0x1B, 0x15, 0x11, 0x11, 0x11, 0x11]),
    "N": (4, [0x9, 0xD, 0xF, 0xB, 0x9, 0x9, 0x9]),
    "O": (4, [0x6, 0x9, 0x9, 0x9, 0x9, 0x9, 0x6]),
    "P": (4, [0xE, 0x9, 0x9, 0xE, 0x8, 0x8, 0x8]),
    "Q": (4, [0x6, 0x9, 0x9, 0x9, 0xA, 0x6, 0x1]),
    "R": (4, [0xE, 0x9, 0x9, 0xE, 0xA, 0x9, 0x9]),
    "S": (4, [0x6, 0x9, 0x8, 0x6, 0x1, 0x9, 0x6]),
    "T": (3, [0x7, 0x2, 0x2, 0x2, 0x2, 0x2, 0x2]),
    "U": (4, [0x9, 0x9, 0x9, 0x9, 0x9, 0x9, 0x6]),
    "V": (4, [0x9, 0x9, 0x9, 0x9, 0x9, 0x6, 0x6]),
    "W": (5, [0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11]),
    "X": (4, [0x9, 0x9, 0x6, 0x6, 0x6, 0x9, 0x9]),
    "Y": (4, [0x9, 0x9, 0x6, 0x2, 0x2, 0x2, 0x2]),
    "Z": (4, [0xF, 0x1, 0x2, 0x4, 0x8, 0x8, 0xF]),
    "0": (4, [0x6, 0x9, 0x9, 0x9, 0x9, 0x9, 0x6]),
    "1": (3, [0x2, 0x6, 0x2, 0x2, 0x2, 0x2, 0x7]),
    "2": (4, [0x6, 0x9, 0x1, 0x2, 0x4, 0x8, 0xF]),
    "3": (4, [0xE, 0x1, 0x1, 0x6, 0x1, 0x1, 0xE]),
    "4": (4, [0x1, 0x3, 0x5, 0x9, 0xF, 0x1, 0x1]),
    "5": (4, [0xF, 0x8, 0xE, 0x1, 0x1, 0x9, 0x6]),
    "6": (4, [0x6, 0x8, 0x8, 0xE, 0x9, 0x9, 0x6]),
    "7": (4, [0xF, 0x1, 0x2, 0x2, 0x4, 0x4, 0x4]),
    "8": (4, [0x6, 0x9, 0x9, 0x6, 0x9, 0x9, 0x6]),
    "9": (4, [0x6, 0x9, 0x9, 0x7, 0x1, 0x2, 0x4]),
    ".": (1, [0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x1]),
    ",": (2, [0x0, 0x0, 0x0, 0x0, 0x0, 0x1, 0x2]),
    "!": (1, [0x1, 0x1, 0x1, 0x1, 0x1, 0x0, 0x1]),
    "?": (4, [0x6, 0x9, 0x1, 0x2, 0x2, 0x0, 0x2]),
    "'": (1, [0x1, 0x1, 0x0, 0x0, 0x0, 0x0, 0x0]),
    "-": (3, [0x0, 0x0, 0x0, 0x7, 0x0, 0x0, 0x0]),
    ":": (1, [0x0, 0x0, 0x1, 0x0, 0x1, 0x0, 0x0]),
    "/": (3, [0x1, 0x1, 0x2, 0x2, 0x2, 0x4, 0x4]),
    "&": (5, [0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D]),
}

_Color = tuple[int, int, int]

# 7x7 bitmap icons for word macros - (width, rows, color)
_ICONS: dict[str, tuple[int, list[int], _Color]] = {
    #  .......  .##.##.  #######  #######  .#####.  ..###..  ...#...
    "heart": (7, [0x00, 0x36, 0x7F, 0x7F, 0x3E, 0x1C, 0x08], (255, 0, 40)),
    #  .#...#.  ###.###  .#...#.  ..#.#..  ..#.#..  ...#...  ...#...
    "wheat": (7, [0x22, 0x77, 0x22, 0x14, 0x14, 0x08, 0x08], (255, 200, 0)),
    #  ...#...  ..###..  #######  .#####.  .#.#.#.  #..#..#  .......
    "star": (7, [0x08, 0x1C, 0x7F, 0x3E, 0x2A, 0x49, 0x00], (255, 255, 0)),
    #  .......  .##.##.  .##.##.  .......  #.#.#.#  .#...#.  ..###..
    "smile": (7, [0x00, 0x36, 0x36, 0x00, 0x55, 0x22, 0x1C], (255, 255, 0)),
    #  #..#..#  .#.#.#.  ..###..  #######  ..###..  .#.#.#.  #..#..#
    "sun": (7, [0x49, 0x2A, 0x1C, 0x7F, 0x1C, 0x2A, 0x49], (255, 160, 0)),
    #  .......  .##.##.  .......  .......  .#####.  #.....#  .......
    "sad": (7, [0x00, 0x36, 0x00, 0x00, 0x3E, 0x41, 0x00], (100, 140, 255)),
    #  ..#.#..  ...#...  #.###.#  .##.##.  #.###.#  ...#...  ..#.#..
    "snow": (7, [0x14, 0x08, 0x5D, 0x36, 0x5D, 0x08, 0x14], (150, 220, 255)),
    #  ...#...  ..###..  .#####.  .#####.  .##.##.  ..###..  ...#...
    "flame": (7, [0x08, 0x1C, 0x3E, 0x3E, 0x36, 0x1C, 0x08], (255, 80, 0)),
    #  .#####.  .#...#.  .#...#.  .#...#.  ##..##.  ##..##.  .......
    "music": (7, [0x3E, 0x22, 0x22, 0x22, 0x66, 0x66, 0x00], (180, 100, 255)),
    #  ..###..  .#.#.#.  .#.#...  ..###..  ...#.#.  .#.#.#.  ..###..
    "dollar": (7, [0x1C, 0x2A, 0x28, 0x1C, 0x0A, 0x2A, 0x1C], (0, 200, 80)),
    #  ..###..  ..##...  .###...  ######.  ...###.  ...##..  ..##...
    "bolt": (7, [0x1C, 0x18, 0x38, 0x7E, 0x0E, 0x0C, 0x18], (255, 255, 100)),
    #  .#.#.#.  .......  #.#.#..  .......  .#.#.#.  .......  #.#.#..
    "rain": (7, [0x2A, 0x00, 0x54, 0x00, 0x2A, 0x00, 0x54], (0, 140, 255)),
    "text": (7, [0x3E, 0x7F, 0x7F, 0x7F, 0x3E, 0x10, 0x20], (0, 200, 80)),
    "c_red": (5, [0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F], (255, 0, 0)),
    "c_blue": (5, [0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F], (0, 0, 255)),
    "c_green": (5, [0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F], (0, 255, 0)),
    "c_yellow": (5, [0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F], (255, 255, 0)),
    "c_orange": (5, [0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F], (255, 165, 0)),
    "c_purple": (5, [0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F], (128, 0, 255)),
    "c_pink": (5, [0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F], (255, 100, 200)),
    "c_white": (5, [0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F], (255, 255, 255)),
    "c_cyan": (5, [0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F], (0, 255, 255)),
}

_LAYERED_ICONS: dict[str, list[tuple[int, list[int], _Color]]] = {
    "robot": [
        (5, [0x00, 0x00, 0x1F, 0x15, 0x1F, 0x11, 0x0E], (184, 188, 194)),
        (5, [0x00, 0x04, 0x00, 0x00, 0x00, 0x00, 0x11], (110, 116, 128)),
        (5, [0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], (217, 74, 74)),
        (5, [0x00, 0x00, 0x00, 0x0A, 0x00, 0x00, 0x00], (255, 255, 0)),
    ],
    "email": [
        (7, [0x7F, 0x63, 0x55, 0x49, 0x41, 0x41, 0x7F], (70, 130, 220)),
    ],
    "sickle": [
        (5, [0x0F, 0x11, 0x01, 0x00, 0x00, 0x00, 0x00], (154, 160, 166)),
        (5, [0x00, 0x00, 0x00, 0x01, 0x01, 0x01, 0x01], (139, 90, 43)),
    ],
    "plug": [
        (5, [0x0E, 0x0A, 0x0E, 0x04, 0x0E, 0x0A, 0x0E], (112, 112, 112)),
        (5, [0x0C, 0x08, 0x00, 0x04, 0x0C, 0x08, 0x00], (192, 192, 192)),
        (5, [0x08, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00], (232, 232, 232)),
    ],
    "tree": [
        (5, [0x04, 0x0E, 0x1F, 0x0E, 0x1F, 0x00, 0x00], (34, 180, 34)),
        (5, [0x00, 0x00, 0x00, 0x00, 0x00, 0x04, 0x04], (139, 90, 43)),
    ],
    "wrench": [
        (5, [0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], (74, 74, 74)),
        (5, [0x0F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], (184, 184, 184)),
        (5, [0x00, 0x1F, 0x00, 0x00, 0x00, 0x00, 0x00], (138, 138, 138)),
        (5, [0x00, 0x00, 0x04, 0x04, 0x04, 0x04, 0x04], (184, 115, 51)),
    ],
    "search": [
        #  ..###..  .#####.  #######  .#####.  ..###..  .......  .......
        (7, [0x1C, 0x3E, 0x7F, 0x3E, 0x1C, 0x00, 0x00], (80, 140, 220)),
        #  .......  ...#...  ..###..  ...#...  .......  .......  .......
        (7, [0x00, 0x08, 0x1C, 0x08, 0x00, 0x00, 0x00], (170, 215, 255)),
        #  ..###..  .#...#.  #.....#  .#...#.  ..###..  ....#..  .....#.
        (7, [0x1C, 0x22, 0x41, 0x22, 0x1C, 0x04, 0x02], (220, 180, 80)),
    ],
    "arrow_up": [
        (7, [0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F], (40, 80, 200)),
        (7, [0x08, 0x1C, 0x3E, 0x08, 0x08, 0x08, 0x00], (255, 255, 255)),
    ],
    "arrow_down": [
        (7, [0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F], (40, 80, 200)),
        (7, [0x00, 0x08, 0x08, 0x08, 0x3E, 0x1C, 0x08], (255, 255, 255)),
    ],
    "arrow_left": [
        (7, [0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F], (40, 80, 200)),
        (7, [0x00, 0x10, 0x20, 0x3E, 0x20, 0x10, 0x00], (255, 255, 255)),
    ],
    "arrow_right": [
        (7, [0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F], (40, 80, 200)),
        (7, [0x00, 0x04, 0x02, 0x3E, 0x02, 0x04, 0x00], (255, 255, 255)),
    ],
    "rainbow": [
        (7, [0x40, 0x40, 0x40, 0x40, 0x40, 0x40, 0x40], (255, 0, 0)),
        (7, [0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20], (255, 127, 0)),
        (7, [0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10], (255, 255, 0)),
        (7, [0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08], (0, 255, 0)),
        (7, [0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04], (0, 100, 255)),
        (7, [0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02], (75, 0, 130)),
        (7, [0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01], (148, 0, 211)),
    ],
    "flag_jp": [
        (7, [0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F], (240, 240, 240)),
        (7, [0x00, 0x08, 0x1C, 0x1C, 0x1C, 0x08, 0x00], (188, 0, 45)),
    ],
    "flag_ua": [
        (7, [0x7F, 0x7F, 0x7F, 0x7F, 0x00, 0x00, 0x00], (0, 87, 183)),
        (7, [0x00, 0x00, 0x00, 0x00, 0x7F, 0x7F, 0x7F], (255, 215, 0)),
    ],
    "flag_ru": [
        (7, [0x7F, 0x7F, 0x00, 0x00, 0x00, 0x00, 0x00], (240, 240, 240)),
        (7, [0x00, 0x00, 0x7F, 0x7F, 0x7F, 0x00, 0x00], (0, 57, 166)),
        (7, [0x00, 0x00, 0x00, 0x00, 0x00, 0x7F, 0x7F], (213, 43, 30)),
    ],
    "flag_bg": [
        (7, [0x7F, 0x7F, 0x00, 0x00, 0x00, 0x00, 0x00], (240, 240, 240)),
        (7, [0x00, 0x00, 0x7F, 0x7F, 0x7F, 0x00, 0x00], (0, 150, 68)),
        (7, [0x00, 0x00, 0x00, 0x00, 0x00, 0x7F, 0x7F], (214, 38, 18)),
    ],
    "flag_gr": [
        (7, [0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F], (13, 94, 175)),
        (7, [0x20, 0x7F, 0x20, 0x7F, 0x00, 0x7F, 0x00], (240, 240, 240)),
    ],
    "flag_gb": [
        (7, [0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F], (0, 36, 125)),
        (7, [0x41, 0x22, 0x14, 0x08, 0x14, 0x22, 0x41], (240, 240, 240)),
        (7, [0x08, 0x08, 0x08, 0x7F, 0x08, 0x08, 0x08], (200, 16, 46)),
    ],
    "flag_us": [
        (7, [0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F], (178, 34, 52)),
        (7, [0x00, 0x7F, 0x00, 0x7F, 0x00, 0x7F, 0x00], (240, 240, 240)),
        (7, [0x78, 0x78, 0x78, 0x78, 0x00, 0x00, 0x00], (0, 56, 130)),
        (7, [0x50, 0x28, 0x50, 0x28, 0x00, 0x00, 0x00], (240, 240, 240)),
    ],
    "flag_ro": [
        (7, [0x60, 0x60, 0x60, 0x60, 0x60, 0x60, 0x60], (0, 43, 127)),
        (7, [0x1C, 0x1C, 0x1C, 0x1C, 0x1C, 0x1C, 0x1C], (252, 209, 22)),
        (7, [0x03, 0x03, 0x03, 0x03, 0x03, 0x03, 0x03], (206, 17, 38)),
    ],
    "flag_it": [
        (7, [0x60, 0x60, 0x60, 0x60, 0x60, 0x60, 0x60], (0, 146, 70)),
        (7, [0x1C, 0x1C, 0x1C, 0x1C, 0x1C, 0x1C, 0x1C], (240, 240, 240)),
        (7, [0x03, 0x03, 0x03, 0x03, 0x03, 0x03, 0x03], (206, 43, 55)),
    ],
    "flag_fr": [
        (7, [0x60, 0x60, 0x60, 0x60, 0x60, 0x60, 0x60], (0, 35, 149)),
        (7, [0x1C, 0x1C, 0x1C, 0x1C, 0x1C, 0x1C, 0x1C], (240, 240, 240)),
        (7, [0x03, 0x03, 0x03, 0x03, 0x03, 0x03, 0x03], (237, 41, 57)),
    ],
    "flag_es": [
        (7, [0x7F, 0x7F, 0x00, 0x00, 0x00, 0x7F, 0x7F], (170, 21, 27)),
        (7, [0x00, 0x00, 0x7F, 0x7F, 0x7F, 0x00, 0x00], (241, 191, 0)),
    ],
    "flag_cn": [
        (7, [0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F], (222, 41, 16)),
        (7, [0x08, 0x24, 0x70, 0x24, 0x08, 0x00, 0x00], (255, 222, 0)),
    ],
}

_MACROS: dict[str, str] = {
    "LOVE": "heart",
    "LOVES": "heart",
    "HEART": "heart",
    "HEARTS": "heart",
    "WHEAT": "wheat",
    "STAR": "star",
    "STARS": "star",
    "SMILE": "smile",
    "SMILES": "smile",
    "HAPPY": "smile",
    "SUN": "sun",
    "SUNNY": "sun",
    "SAD": "sad",
    "MEH": "sad",
    "SNOW": "snow",
    "SNOWY": "snow",
    "SNOWING": "snow",
    "FROZEN": "snow",
    "COLD": "snow",
    "ICE": "snow",
    "HOT": "flame",
    "FIRE": "flame",
    "FLAMES": "flame",
    "LIT": "flame",
    "MUSIC": "music",
    "SONG": "music",
    "SONGS": "music",
    "MONEY": "dollar",
    "CASH": "dollar",
    "DOLLAR": "dollar",
    "DOLLARS": "dollar",
    "LIGHTNING": "bolt",
    "THUNDER": "bolt",
    "RAIN": "rain",
    "RAINING": "rain",
    "RAINY": "rain",
    "TOOL": "wrench",
    "TOOLS": "wrench",
    "WRENCH": "wrench",
    "BUILD": "wrench",
    "EMAIL": "email",
    "EMAILS": "email",
    "MAIL": "email",
    "TEXT": "text",
    "TEXTS": "text",
    "TEXTING": "text",
    "MESSAGE": "text",
    "MESSAGES": "text",
    "SMS": "text",
    "HARVEST": "sickle",
    "SICKLE": "sickle",
    "REAP": "sickle",
    "CONNECT": "plug",
    "CONNECTED": "plug",
    "PLUG": "plug",
    "LINK": "plug",
    "AI": "robot",
    "ROBOT": "robot",
    "ROBOTS": "robot",
    "AGENT": "robot",
    "AGENTS": "robot",
    "INVESTIGATE": "search",
    "FIND": "search",
    "SEARCH": "search",
    "LOOKING": "search",
    "RED": "c_red",
    "BLUE": "c_blue",
    "GREEN": "c_green",
    "YELLOW": "c_yellow",
    "ORANGE": "c_orange",
    "PURPLE": "c_purple",
    "PINK": "c_pink",
    "WHITE": "c_white",
    "CYAN": "c_cyan",
    "RAINBOW": "rainbow",
    "RAINBOWS": "rainbow",
    "TREE": "tree",
    "TREES": "tree",
    "FOREST": "tree",
    "UP": "arrow_up",
    "DOWN": "arrow_down",
    "LEFT": "arrow_left",
    "RIGHT": "arrow_right",
    "JAPAN": "flag_jp",
    "JAPANESE": "flag_jp",
    "UKRAINE": "flag_ua",
    "UKRAINIAN": "flag_ua",
    "RUSSIA": "flag_ru",
    "RUSSIAN": "flag_ru",
    "BULGARIA": "flag_bg",
    "BULGARIAN": "flag_bg",
    "GREECE": "flag_gr",
    "GREEK": "flag_gr",
    "BRITAIN": "flag_gb",
    "BRITISH": "flag_gb",
    "ENGLISH": "flag_gb",
    "ENGLAND": "flag_gb",
    "AMERICA": "flag_us",
    "AMERICAN": "flag_us",
    "ROMANIA": "flag_ro",
    "ROMANIAN": "flag_ro",
    "ITALY": "flag_it",
    "ITALIAN": "flag_it",
    "FRANCE": "flag_fr",
    "FRENCH": "flag_fr",
    "SPAIN": "flag_es",
    "SPANISH": "flag_es",
    "CHINA": "flag_cn",
    "CHINESE": "flag_cn",
}

_TEXT_MACROS: dict[str, str] = {
    "PROBABLY": "PROB",
    "DEFINITELY": "DEF",
    "ESPECIALLY": "ESP",
    "THANKS": "THX",
    "PEOPLE": "PPL",
    "TOMORROW": "TMR",
    "AND": "&",
    "WITHOUT": "W/O",
    "INFORMATION": "INFO",
}

_PHRASE_MACROS: list[tuple[list[str], str]] = [
    (["BY", "THE", "WAY"], "BTW"),
    (["IN", "MY", "OPINION"], "IMO"),
    (["TO", "BE", "HONEST"], "TBH"),
    (["I", "DON'T", "KNOW"], "IDK"),
    (["RIGHT", "NOW"], "RN"),
    (["THANK", "YOU"], "THX"),
]

_CHAR_GAP = 1


def _char_width(ch: str) -> int:
    entry = _FONT.get(ch)
    return entry[0] if entry else 0


def _measure_word(word: str) -> int:
    total = 0
    for i, ch in enumerate(word):
        total += _char_width(ch)
        if i < len(word) - 1:
            total += _CHAR_GAP
    return total


def _word_width(word: str) -> int:
    icon_name = _MACROS.get(word)
    if icon_name:
        if icon_name in _ICONS:
            return _ICONS[icon_name][0]
        if icon_name in _LAYERED_ICONS:
            return _LAYERED_ICONS[icon_name][0][0]
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
            for phrase, abbrev in _PHRASE_MACROS:
                end = i + len(phrase)
                if end <= len(cleaned) and cleaned[i:end] == phrase:
                    result.append(abbrev)
                    i = end
                    matched = True
                    break
            if not matched:
                w = cleaned[i]
                result.append(_TEXT_MACROS.get(w, w))
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
        pixels: list[list[_Color | None]],
        bitmap: tuple[int, list[int]],
        x: int,
        y: int,
        color: _Color = (255, 255, 255),
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
        pixels: list[list[_Color | None]],
        word: str,
        wx: int,
        y: int,
    ) -> None:
        icon_name = _MACROS.get(word)
        if icon_name and icon_name in _ICONS:
            w, rows, color = _ICONS[icon_name]
            self._draw_bitmap(pixels, (w, rows), wx, y, color)
        elif icon_name and icon_name in _LAYERED_ICONS:
            for lw, lrows, lcolor in _LAYERED_ICONS[icon_name]:
                self._draw_bitmap(pixels, (lw, lrows), wx, y, lcolor)
        else:
            cx = wx
            for i, ch in enumerate(word):
                entry = _FONT.get(ch)
                if entry:
                    self._draw_bitmap(pixels, entry, cx, y, self.fg)
                cx += _char_width(ch)
                if i < len(word) - 1:
                    cx += _CHAR_GAP

    def _render(self) -> Image.Image:
        pixels: list[list[_Color | None]] = [
            [None] * self.width for _ in range(self.text_height)
        ]

        for row_idx, line in enumerate(self._lines):
            y = row_idx * (self._row_height + 1)
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
                for word in pending:
                    if self._cursor_row == 1 and self._would_overflow(word):
                        self._frame = self._render()
                        self._linger_until = time.monotonic() + 1.0
                        self._pending_words = pending[pending.index(word) :]
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
