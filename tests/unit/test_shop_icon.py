import hashlib
import struct
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

import pytest

from .test_package_sources import build

ROOT = Path(__file__).resolve().parents[2]


def test_official_archipelago_asset_is_pinned_credited_and_converted_reproducibly(tmp_path):
    data = (ROOT / "assets/archipelago/icon.png").read_bytes()
    assert (
        hashlib.sha256(data).hexdigest()
        == "55b8e964106cde2f52839e9bb5cdcceb95e427dce00a71892b116c91118e9273"
    )
    texture = build.shop_icon()
    assert texture == (ROOT / "mod" / build.SHOP_TEXTURE_PATH).read_bytes()
    assert texture == build.shop_icon()
    header = struct.unpack("<31I", texture[4:128])
    assert texture[:4] == b"DDS " and header[2:4] == (64, 64)
    assert len(texture) == 16512
    pixels = [tuple(texture[index : index + 4]) for index in range(128, len(texture), 4)]
    assert pixels[0][3] == 0 and any(0 < pixel[3] < 255 for pixel in pixels)
    assert len({pixel for pixel in pixels if pixel[3] == 255}) >= 6
    credit = (ROOT / "mod/ARCHIPELAGO-ICON-LICENSE.txt").read_text()
    assert "Krista Corkos and Christopher Wilson" in credit
    assert "creativecommons.org/licenses/by-nc/4.0" in credit
    descriptor = ElementTree.parse(
        ROOT / "mod/gamedata/configs/ui/textures_descr/ui_gamma_ap_shop.xml"
    )
    assert descriptor.find("file/texture").get("id") == "gamma_ap_shop_icon"
    build.generate_shop_icon(tmp_path)
    build.package(tmp_path, tmp_path.parent / "icon.zip")
    with ZipFile(tmp_path.parent / "icon.zip") as archive:
        assert archive.read(build.SHOP_TEXTURE_PATH) == texture


def test_corrupt_or_foreign_shop_textures_are_still_rejected(tmp_path):
    (tmp_path / "gamma_ap_shop.dds").write_bytes(b"DDS foreign")
    with pytest.raises(ValueError, match="Unexpected package source"):
        build.package(tmp_path, tmp_path.parent / "invalid.zip")
