from pathlib import Path

import pytest
from worlds.gamma.client import configured_bridge

from gamma_archipelago.installation import enroll, inspect_installation


def test_legacy_default_is_unchanged_and_appdata_requires_an_explicit_game():
    assert configured_bridge(None, None) is None
    with pytest.raises(ValueError, match="requires"):
        configured_bridge(None, Path("unused"))


def test_cli_refuses_unregistered_roots_then_reads_the_selected_game_and_custom_data(tmp_path):
    game = tmp_path / "Mini Anomaly"
    game.mkdir()
    (game / "fsgame.ltx").write_text("$app_data_root$=true|false|$fs_root$|appdata\\\n")
    (game / "appdata").mkdir()
    with pytest.raises(ValueError, match="Configure"):
        configured_bridge(game, None)
    data = tmp_path / "Profile data"
    data.mkdir()
    enrollment = inspect_installation(game, appdata_root=data)
    enroll(enrollment)
    bridge = configured_bridge(game, data)
    assert bridge.game_root == game and bridge.directory == data / "archipelago"
    assert not (game / "appdata/archipelago").exists()
