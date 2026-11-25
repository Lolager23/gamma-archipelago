import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from gamma_archipelago import installation as module
from gamma_archipelago.bridge import FileBridge
from gamma_archipelago.protocol import encode_incoming


def game_at(root):
    root.mkdir(parents=True)
    (root / "fsgame.ltx").write_text(
        "$app_data_root$ = true | false | $fs_root$ | appdata\\\n", encoding="utf-8"
    )
    (root / "appdata").mkdir()
    return root


def test_arbitrary_installation_with_spaces_is_enrolled_and_uses_its_own_bridge(tmp_path):
    game = game_at(tmp_path / "Robert Cook" / "Anomaly Game")
    paths = module.inspect_installation(game)
    assert paths == module.Installation(game, game / "appdata")
    with pytest.raises(ValueError, match="Configure"):
        module.require_enrolled(paths)
    module.enroll(paths)
    module.require_enrolled(paths)
    marker = game / "appdata/archipelago/installation.txt"
    before = marker.stat().st_mtime_ns
    module.enroll(paths)
    assert marker.read_bytes() == module.MARKER.encode("ascii")
    assert marker.stat().st_mtime_ns == before
    bridge = FileBridge(game, allowed_root=game, appdata_root=paths.appdata_root)
    bridge.write_history("a" * 64, ())
    assert (paths.appdata_root / "archipelago/incoming.txt").read_text() == encode_incoming(
        "a" * 64, ()
    )


@pytest.mark.parametrize("byte_array", [True, False])
def test_mo2_folder_resolves_registered_game_path(tmp_path, byte_array):
    game = game_at(tmp_path / "Anomaly Game")
    mo2 = tmp_path / "GAMMA MO2"
    mo2.mkdir()
    value = str(game).replace("\\", "\\\\")
    if byte_array:
        value = "@ByteArray(" + value + ")"
    (mo2 / "ModOrganizer.ini").write_text(
        "[General]\ngamePath=" + value + "\n", encoding="utf-8-sig"
    )
    assert module.inspect_installation(mo2).game_root == game


def test_explicit_custom_appdata_directory_is_used_without_relocating_saves(tmp_path):
    game = game_at(tmp_path / "Game")
    custom = tmp_path / "Selected Profile Data"
    custom.mkdir()
    paths = module.inspect_installation(game, appdata_root=custom)
    module.enroll(paths)
    bridge = FileBridge(game, allowed_root=game, appdata_root=custom)
    bridge.write_confirmed("b" * 64, frozenset())
    assert (custom / "archipelago/confirmed_checks.txt").is_file()
    assert not (game / "appdata/archipelago").exists()


@pytest.mark.parametrize("relative", ["../outside", "/absolute", "C:/absolute", ""])
def test_unsafe_fsgame_aliases_are_refused_before_writes(tmp_path, relative):
    game = game_at(tmp_path / "Game")
    (game / "fsgame.ltx").write_text("$app_data_root$=true|false|$fs_root$|" + relative + "\n")
    with pytest.raises(ValueError):
        module.inspect_installation(game)
    assert not (game / "appdata/archipelago").exists()


@pytest.mark.parametrize(
    "text",
    [
        "",
        "$app_data_root$=true|false|$unknown$|appdata",
        "$app_data_root$=true|false|$fs_root$|appdata\n$app_data_root$=true|false|$fs_root$|other",
    ],
)
def test_unsupported_or_ambiguous_aliases_need_explicit_selection(tmp_path, text):
    game = game_at(tmp_path / "Game")
    (game / "fsgame.ltx").write_text(text)
    with pytest.raises(ValueError, match="appdata"):
        module.inspect_installation(game)


def test_relative_missing_and_drive_root_selections_are_refused(tmp_path):
    for path in (Path("relative"), tmp_path / "missing", Path(tmp_path.anchor)):
        with pytest.raises(ValueError):
            module.game_directory(path)
    empty = tmp_path / "not a game"
    empty.mkdir()
    with pytest.raises(ValueError, match="fsgame"):
        module.game_directory(empty)


@pytest.mark.parametrize("text", ["", "gamePath=one\ngamePath=two", "gamePath=relative"])
def test_unresolved_mo2_game_directory_is_refused(tmp_path, text):
    (tmp_path / "ModOrganizer.ini").write_text(text)
    with pytest.raises(ValueError):
        module.game_directory(tmp_path)


def test_mo2_target_must_be_a_real_anomaly_installation(tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    (tmp_path / "ModOrganizer.ini").write_text("gamePath=" + str(other))
    with pytest.raises(ValueError, match="fsgame"):
        module.game_directory(tmp_path)


@pytest.mark.parametrize("data", [b"x" * (module.MAX_CONFIG_BYTES + 1), b"\xff"])
def test_configuration_size_and_encoding_are_bounded(tmp_path, data):
    (tmp_path / "ModOrganizer.ini").write_bytes(data)
    with pytest.raises(ValueError):
        module.game_directory(tmp_path)


def test_protected_installations_are_never_enrolled(tmp_path):
    game = game_at(tmp_path / "normal")
    with pytest.raises(ValueError, match="protected"):
        module.inspect_installation(game, protected=(game,))
    with pytest.raises(ValueError, match="protected"):
        module.inspect_installation(game, protected=(tmp_path,))
    assert not (game / "appdata/archipelago").exists()


def test_links_and_hardlinked_markers_are_refused(tmp_path, monkeypatch):
    game = game_at(tmp_path / "Game")
    paths = module.inspect_installation(game)
    module.enroll(paths)
    marker = paths.appdata_root / "archipelago/installation.txt"
    os.link(marker, tmp_path / "other marker")
    with pytest.raises(ValueError, match="hardlinked"):
        module.require_enrolled(paths)
    monkeypatch.setattr(Path, "is_junction", lambda path: path == game)
    with pytest.raises(ValueError, match="links"):
        module.inspect_installation(game)


def test_a_bridge_root_replaced_by_a_link_after_configuration_is_refused(tmp_path, monkeypatch):
    game = game_at(tmp_path / "Game")
    data = tmp_path / "Profile data"
    data.mkdir()
    bridge = FileBridge(game, allowed_root=game, appdata_root=data)
    monkeypatch.setattr(Path, "is_junction", lambda path: path == data)
    with pytest.raises(ValueError, match="links"):
        bridge.write_history("a" * 64, ())
    assert not (data / "archipelago/incoming.txt").exists()


def test_windows_network_directories_are_not_claimed_as_supported(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(
        module, "require_isolated_root", lambda *args: SimpleNamespace(drive="\\\\server\\share")
    )
    with pytest.raises(ValueError, match="local drive"):
        module.game_directory(tmp_path)


@pytest.mark.parametrize(
    "data", [b"", b"wrong\n", module.MARKER.encode() + b"extra", b"x" * 100000]
)
def test_malformed_markers_are_refused_without_overwriting_existing_state(tmp_path, data):
    game = game_at(tmp_path / "Game")
    paths = module.inspect_installation(game)
    directory = game / "appdata/archipelago"
    directory.mkdir()
    marker = directory / module.MARKER_NAME
    marker.write_bytes(data)
    with pytest.raises(ValueError):
        module.require_enrolled(paths)
    with pytest.raises(ValueError):
        module.enroll(paths)
    assert marker.read_bytes() == data
