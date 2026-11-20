"""Draw our original rainbow backpack as a deterministic, uncompressed RGBA DDS.

The small UI texture needs no external renderer, copied game art or build dependency.
Coordinates describe a 64px icon; four samples per axis soften its silhouette.
"""

import struct
from pathlib import Path

from gamma_archipelago.paths import require_safe_child

SIZE = 64
TEXTURE_PATH = "gamedata/textures/ui/gamma_ap_stash.dds"
RAINBOW = (
    (244, 70, 78),
    (255, 155, 48),
    (255, 222, 65),
    (70, 205, 117),
    (67, 171, 248),
    (161, 109, 248),
)
OUTLINE = (18, 23, 31)
EDGE = (239, 242, 248)


def rounded(x: float, y: float, bounds: tuple[int, int, int, int], radius: int) -> bool:
    left, top, right, bottom = bounds
    if not left <= x <= right or not top <= y <= bottom:
        return False
    nearest_x = min(max(x, left + radius), right - radius)
    nearest_y = min(max(y, top + radius), bottom - radius)
    return (x - nearest_x) ** 2 + (y - nearest_y) ** 2 <= radius**2


def sample(x: float, y: float) -> tuple[int, int, int] | None:
    colour = None
    # Light outside rim and dark outline keep the pack readable over any PDA map.
    for bounds, radius, fill in (
        ((21, 3, 43, 19), 6, EDGE),
        ((23, 5, 41, 18), 4, OUTLINE),
        ((27, 9, 37, 17), 1, None),
        ((9, 12, 55, 61), 10, EDGE),
        ((11, 14, 53, 59), 8, OUTLINE),
    ):
        if rounded(x, y, bounds, radius):
            colour = fill
    if rounded(x, y, (15, 18, 49, 55), 5):
        colour = RAINBOW[min(int((y - 18) / 6.2), len(RAINBOW) - 1)]
    # Pocket seam, central buckle and zip pull suggest a stash rather than a flag.
    if rounded(x, y, (18, 36, 46, 51), 3) and not rounded(x, y, (20, 39, 44, 49), 1):
        colour = OUTLINE
    if rounded(x, y, (28, 17, 36, 27), 1):
        colour = OUTLINE
    if rounded(x, y, (30, 19, 34, 23), 0) or rounded(x, y, (41, 39, 43, 43), 0):
        colour = EDGE
    return colour


def stash_icon() -> bytes:
    pixels = bytearray()
    for y in range(SIZE):
        for x in range(SIZE):
            colours = [
                colour
                for row in range(4)
                for column in range(4)
                if (colour := sample(x + (column + 0.5) / 4, y + (row + 0.5) / 4)) is not None
            ]
            rgb = (
                tuple(round(sum(c[i] for c in colours) / len(colours)) for i in range(3))
                if colours
                else (0, 0, 0)
            )
            pixels.extend((*rgb[::-1], round(255 * len(colours) / 16)))
    # DDS_HEADER, DDS_PIXELFORMAT: DDPF_RGB | DDPF_ALPHAPIXELS, D3DFMT_A8R8G8B8.
    header = [124, 0x100F, SIZE, SIZE, SIZE * 4, 0, 0, *([0] * 11)]
    header += [32, 0x41, 0, 32, 0xFF0000, 0xFF00, 0xFF, 0xFF000000]
    header += [0x1000, 0, 0, 0, 0]
    return b"DDS " + struct.pack("<31I", *header) + pixels


def generate_stash_icon(mod_root: Path) -> None:
    destination = require_safe_child(mod_root, TEXTURE_PATH)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(stash_icon())
