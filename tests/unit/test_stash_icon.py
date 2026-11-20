import struct
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

import pytest

from .test_package_sources import build

ROOT = Path(__file__).resolve().parents[2]


def test_owned_icon_has_native_dds_header_six_colours_and_straight_alpha():
    data = build.stash_icon()
    assert data[:4] == b"DDS "
    header = struct.unpack("<31I", data[4:128])
    assert header[:7] == (124, 0x100F, 64, 64, 256, 0, 0)
    assert header[18:26] == (32, 0x41, 0, 32, 0xFF0000, 0xFF00, 0xFF, 0xFF000000)
    assert len(data) == 128 + 64 * 64 * 4
    pixels = [tuple(data[i : i + 4]) for i in range(128, len(data), 4)]
    assert pixels[0] == (0, 0, 0, 0)
    assert any(0 < pixel[3] < 255 for pixel in pixels)
    expected_colours = (
        (244, 70, 78),
        (255, 155, 48),
        (255, 222, 65),
        (70, 205, 117),
        (67, 171, 248),
        (161, 109, 248),
    )
    assert all((*colour[::-1], 255) in pixels for colour in expected_colours)


def test_map_texture_resource_resolves_to_the_owned_generated_asset():
    mod = ROOT / "mod"
    descriptor = ElementTree.parse(mod / "gamedata/configs/ui/textures_descr/ui_gamma_ap_stash.xml")
    resource = descriptor.find("file")
    assert resource.attrib["name"] == "ui\\gamma_ap_stash"
    assert resource.find("texture").attrib == {
        "id": "gamma_ap_stash_rainbow",
        "x": "0",
        "y": "0",
        "width": "64",
        "height": "64",
    }
    assert (mod / build.TEXTURE_PATH).read_bytes() == build.stash_icon()


def test_package_preserves_the_owned_binary_icon_without_text_decoding(tmp_path):
    source = tmp_path / "mod"
    source.mkdir()
    build.generate_stash_icon(source)
    output = tmp_path / "owned.zip"
    build.package(source, output)
    with ZipFile(output) as archive:
        assert archive.namelist() == [build.TEXTURE_PATH]
        assert archive.read(build.TEXTURE_PATH) == build.stash_icon()


@pytest.mark.parametrize("filename", ["gamma_ap_stash.dds", "game_asset.dds"])
def test_packager_still_refuses_foreign_or_corrupted_textures(tmp_path, filename):
    source = tmp_path / "mod"
    source.mkdir()
    (source / filename).write_bytes(b"DDS foreign or corrupted")
    with pytest.raises(ValueError, match="Unexpected package source"):
        build.package(source, tmp_path / "bad.zip")
