import os
from pathlib import Path

import pytest

from gamma_archipelago.bridge import FileBridge
from gamma_archipelago.catalog import ITEM_SECTIONS
from gamma_archipelago.paths import require_isolated_root, require_safe_child
from gamma_archipelago.protocol import ProtocolError

from .test_protocol import KEY, outgoing


def test_bridge_writes_complete_snapshot_atomically_and_reads_game(tmp_path):
    bridge = FileBridge(tmp_path, allowed_root=tmp_path)
    assert bridge.read_game(KEY) is None
    bridge.write_history(KEY, tuple(ITEM_SECTIONS))
    assert (bridge.directory / "incoming.txt").read_text().endswith("end|3\n")
    assert not (bridge.directory / "incoming.tmp").exists()
    (bridge.directory / "outgoing.txt").write_text(outgoing(), encoding="ascii")
    assert bridge.read_game(KEY).session_key == KEY
    bridge.write_history(KEY, ())
    assert (bridge.directory / "incoming.txt").read_text().endswith("end|0\n")


def test_invalid_history_does_not_replace_existing_snapshot(tmp_path):
    bridge = FileBridge(tmp_path, allowed_root=tmp_path)
    bridge.write_history(KEY, ())
    original = (bridge.directory / "incoming.txt").read_bytes()
    with pytest.raises(ProtocolError):
        bridge.write_history(KEY, (42,))
    assert (bridge.directory / "incoming.txt").read_bytes() == original


def test_non_ascii_and_partial_game_writes_are_rejected(tmp_path):
    bridge = FileBridge(tmp_path, allowed_root=tmp_path)
    source = bridge.directory / "outgoing.txt"
    source.write_bytes(b"\xff")
    with pytest.raises(ProtocolError, match="ASCII"):
        bridge.read_game(KEY)
    source.write_text(outgoing()[:-1], encoding="ascii")
    with pytest.raises(ProtocolError):
        bridge.read_game(KEY)


def test_forbidden_original_root_is_rejected_before_creation(tmp_path):
    wrong = tmp_path / "normal-game"
    with pytest.raises(ValueError, match="isolated"):
        FileBridge(wrong, allowed_root=tmp_path / "development")
    assert not wrong.exists()


def test_path_traversal_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="escapes"):
        require_safe_child(tmp_path, "../normal-game/saves")
    with pytest.raises(ValueError, match="escapes"):
        require_safe_child(
            tmp_path, str(tmp_path.parent / "other" / ".." / tmp_path.name / "state")
        )
    assert require_safe_child(tmp_path, "appdata/incoming.txt") == tmp_path / "appdata/incoming.txt"
    assert require_safe_child(tmp_path, ".") == tmp_path


def test_hardlinked_bridge_file_is_rejected(tmp_path):
    original = tmp_path / "original"
    original.write_text("private")
    os.link(original, tmp_path / "incoming.txt")
    with pytest.raises(ValueError, match="hardlinked"):
        require_safe_child(tmp_path, "incoming.txt")


def test_symlinked_child_and_root_are_rejected(tmp_path, monkeypatch):
    # Simulate a link without requiring Windows' CreateSymbolicLink privilege.
    linked = tmp_path / "appdata"
    monkeypatch.setattr(Path, "is_symlink", lambda path: path == linked)
    with pytest.raises(ValueError, match="Linked"):
        require_safe_child(tmp_path, "appdata/archipelago")
    with pytest.raises(ValueError, match="links"):
        require_isolated_root(linked, linked)


def test_junction_and_changed_resolution_are_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "is_junction", lambda path: path == tmp_path)
    with pytest.raises(ValueError, match="links"):
        require_isolated_root(tmp_path, tmp_path)
    monkeypatch.setattr(Path, "is_junction", lambda path: False)
    monkeypatch.setattr(Path, "resolve", lambda path: path / "redirected")
    with pytest.raises(ValueError, match="resolves"):
        require_isolated_root(tmp_path, tmp_path)
