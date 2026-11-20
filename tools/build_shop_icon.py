"""Convert the pinned, credited Archipelago icon to a small native UI texture.

This deliberately accepts one known RGBA PNG, not arbitrary image input. The
standard-library decoder keeps reproducible Windows/Linux builds dependency-free.
"""

import hashlib
import struct
import zlib
from pathlib import Path

from gamma_archipelago.paths import require_safe_child

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA256 = "55b8e964106cde2f52839e9bb5cdcceb95e427dce00a71892b116c91118e9273"
SHOP_TEXTURE_PATH = "gamedata/textures/ui/gamma_ap_shop.dds"


def decode_icon(data: bytes) -> list[bytearray]:
    if hashlib.sha256(data).hexdigest() != SOURCE_SHA256:
        raise ValueError("Archipelago icon differs from its pinned, credited source")
    if struct.unpack(">IIBBBBB", data[16:29]) != (512, 512, 8, 6, 0, 0, 0):
        raise ValueError("Unsupported Archipelago icon PNG format")
    compressed, offset = bytearray(), 8
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        if data[offset + 4 : offset + 8] == b"IDAT":
            compressed.extend(data[offset + 8 : offset + 8 + length])
        offset += length + 12
    filtered = zlib.decompress(compressed)
    rows, previous = [], bytearray(2048)
    for y in range(512):
        mode = filtered[y * 2049]
        row = bytearray(filtered[y * 2049 + 1 : (y + 1) * 2049])
        for x in range(2048):
            left, above = row[x - 4] if x >= 4 else 0, previous[x]
            corner = previous[x - 4] if x >= 4 else 0
            prediction = left + above - corner
            paeth = min((left, above, corner), key=lambda v: abs(prediction - v))
            row[x] = (row[x] + (0, left, above, (left + above) // 2, paeth)[mode]) % 256
        rows.append(row)
        previous = row
    return rows


def shop_icon() -> bytes:
    source = require_safe_child(ROOT, "assets/archipelago/icon.png")
    rows = decode_icon(source.read_bytes())
    pixels = bytearray()
    for y in range(64):
        for x in range(64):
            samples = [
                rows[yy][xx * 4 : xx * 4 + 4]
                for yy in range(y * 8, y * 8 + 8)
                for xx in range(x * 8, x * 8 + 8)
            ]
            alpha = sum(pixel[3] for pixel in samples)
            rgb = [
                round(sum(pixel[i] * pixel[3] for pixel in samples) / alpha) if alpha else 0
                for i in range(3)
            ]
            pixels.extend((*rgb[::-1], round(alpha / 64)))
    header = [124, 0x100F, 64, 64, 256, 0, 0, *([0] * 11)]
    header += [32, 0x41, 0, 32, 0xFF0000, 0xFF00, 0xFF, 0xFF000000]
    header += [0x1000, 0, 0, 0, 0]
    return b"DDS " + struct.pack("<31I", *header) + pixels


def generate_shop_icon(mod_root: Path) -> None:
    destination = require_safe_child(mod_root, SHOP_TEXTURE_PATH)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(shop_icon())
