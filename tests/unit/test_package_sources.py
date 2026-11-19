import importlib.util
import os
from pathlib import Path
from zipfile import ZipFile

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("package_build", ROOT / "tools/build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


def test_packaging_refuses_accidental_saves_before_writing_an_archive(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "owned.script").write_text("-- owned\n")
    (source / "private.sav").write_bytes(b"not distributable")
    output = tmp_path / "output.zip"
    with pytest.raises(ValueError, match="Unexpected package source"):
        build.package(source, output)
    assert not output.exists()


def test_packaging_refuses_hardlinked_payloads_and_extras(tmp_path):
    original = tmp_path / "outside.py"
    original.write_text("print('owned')\n")
    source = tmp_path / "source"
    source.mkdir()
    linked = source / "linked.py"
    os.link(original, linked)
    with pytest.raises(ValueError, match="links"):
        build.package(source, tmp_path / "output.zip")
    linked.unlink()
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValueError, match="links"):
        os.link(original, linked)
        build.package(empty, tmp_path / "output.zip", extras={"entry.py": linked})


def test_packaging_refuses_symbolic_links_when_supported(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    target = tmp_path / "target.py"
    target.write_text("pass\n")
    try:
        (source / "linked.py").symlink_to(target)
    except OSError:
        pytest.skip("Creating symlinks is unavailable for this Windows account")
    with pytest.raises(ValueError, match="links"):
        build.package(source, tmp_path / "output.zip")
    linked_root = tmp_path / "linked-root"
    linked_root.symlink_to(source, target_is_directory=True)
    with pytest.raises(ValueError, match="links"):
        build.package(linked_root, tmp_path / "output.zip")


def test_missing_package_source_is_an_error_instead_of_an_empty_archive(tmp_path):
    with pytest.raises(ValueError, match="missing"):
        build.package(tmp_path / "missing", tmp_path / "output.zip")


def test_text_line_endings_and_zip_platform_metadata_are_reproducible(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    payload = source / "owned.py"
    payload.write_bytes(b"one\r\ntwo\r\n")
    first, second = tmp_path / "first.zip", tmp_path / "second.zip"
    build.package(source, first)
    payload.write_bytes(b"one\ntwo\n")
    build.package(source, second)
    assert first.read_bytes() == second.read_bytes()
    with ZipFile(first) as archive:
        assert archive.getinfo("owned.py").create_system == 3
        assert archive.read("owned.py") == b"one\ntwo\n"
