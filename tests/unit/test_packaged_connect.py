import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "packaged_connect", ROOT / "tools/packaged_connect.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def installation(tmp_path):
    game = tmp_path / "Game with spaces"
    game.mkdir()
    (game / "fsgame.ltx").write_text("$app_data_root$=true|false|$fs_root$|appdata\\\n")
    (game / "appdata").mkdir()
    return game


def settings(tmp_path, **values):
    path = tmp_path / "connection.json"
    path.write_text(
        json.dumps(
            {"slot": "Mini", "port": 4444, "server": "127.0.0.1", "password": "test-only", **values}
        )
    )
    return path


def answers(monkeypatch, values):
    sequence = iter(values)
    monkeypatch.setattr("builtins.input", lambda _: next(sequence))


def test_first_configuration_registers_real_selected_directory_and_can_be_reused(
    tmp_path, monkeypatch
):
    game = installation(tmp_path)
    path = settings(tmp_path)
    answers(monkeypatch, [str(game), "ENABLE"])
    selected = module.selected_installation(path, False, [])
    assert selected.game_root == game
    assert (game / "appdata/archipelago/installation.txt").is_file()
    assert module.selected_installation(path, False, []) == selected
    assert "password" not in (tmp_path / "installation.json").read_text()


def test_cancelled_selection_does_not_create_a_marker_or_local_configuration(tmp_path, monkeypatch):
    game = installation(tmp_path)
    answers(monkeypatch, [str(game), "NO"])
    with pytest.raises(ValueError, match="Cancelled"):
        module.selected_installation(settings(tmp_path), True, [])
    assert not (game / "appdata/archipelago").exists()
    assert not (tmp_path / "installation.json").exists()


def test_custom_alias_can_be_selected_explicitly(tmp_path, monkeypatch):
    game = installation(tmp_path)
    (game / "fsgame.ltx").write_text("$app_data_root$=true|false|$custom$|saves")
    data = tmp_path / "Profile saves"
    data.mkdir()
    answers(monkeypatch, [str(game), str(data), "ENABLE"])
    selected = module.selected_installation(settings(tmp_path), True, [])
    assert selected.appdata_root == data


def test_an_unrelated_folder_is_not_registered(tmp_path, monkeypatch):
    answers(monkeypatch, [str(tmp_path)])
    with pytest.raises(ValueError, match="fsgame"):
        module.selected_installation(settings(tmp_path), True, [])
    assert not (tmp_path / "installation.json").exists()


@pytest.mark.parametrize(
    "rows",
    [
        [{"CommandLine": "python GammaArchipelagoClient.py"}],
        [{"CommandLine": "python run_client.py"}],
    ],
)
def test_existing_companion_is_not_overlapped(rows):
    with pytest.raises(ValueError, match="existing"):
        module.ensure_stopped(rows)


def test_running_game_is_refused_before_enrollment_but_unrelated_games_are_ignored(tmp_path):
    from gamma_archipelago.installation import inspect_installation

    game = installation(tmp_path)
    selected = inspect_installation(game)
    for executable in (None, str(game / "bin/AnomalyDX11.exe")):
        with pytest.raises(ValueError, match="Close the selected game"):
            module.ensure_stopped(
                [{"Name": "AnomalyDX11.exe", "ExecutablePath": executable}], selected
            )
    module.ensure_stopped(
        [{"Name": "AnomalyDX11.exe", "ExecutablePath": str(tmp_path / "other/bin/game.exe")}],
        selected,
    )


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("", []),
        ('{"Name":"python.exe"}', [{"Name": "python.exe"}]),
        ('[{"Name":"python.exe"}]', [{"Name": "python.exe"}]),
    ],
)
def test_process_boundary_normalizes_empty_single_and_multiple_results(monkeypatch, raw, expected):
    monkeypatch.setattr(module.subprocess, "check_output", lambda *args, **kwargs: raw)
    assert module.processes() == expected


@pytest.mark.parametrize("payload", ["[]", "x" * 65537])
def test_invalid_settings_are_bounded(tmp_path, payload):
    path = tmp_path / "settings.json"
    path.write_text(payload)
    with pytest.raises(ValueError):
        module.document(path)


def test_connection_passes_selected_installation_to_the_matching_companion(tmp_path, monkeypatch):
    game = installation(tmp_path)
    answers(monkeypatch, [str(game), "ENABLE"])
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "processes", lambda: [])
    calls = []
    monkeypatch.setattr(module.subprocess, "run", lambda args, **kwargs: calls.append(args))
    module.connect(settings(tmp_path))
    args = calls[0]
    assert args[args.index("--game-root") + 1] == str(game)
    assert args[args.index("--appdata-root") + 1] == str(game / "appdata")
    assert args[args.index("--connect") + 1] == "127.0.0.1:4444"
    assert args[args.index("--name") + 1] == "Mini"


def test_configuration_only_never_starts_networking(tmp_path, monkeypatch):
    game = installation(tmp_path)
    answers(monkeypatch, [str(game), "ENABLE"])
    monkeypatch.setattr(module, "processes", lambda: [])
    module.connect(settings(tmp_path), configure=True)
    assert (tmp_path / "installation.json").is_file()


@pytest.mark.parametrize("fields", [{"port": True}, {"port": 0}, {"slot": ""}, {"slot": 1}])
def test_invalid_connection_identity_is_refused_before_installation_writes(tmp_path, fields):
    with pytest.raises(ValueError):
        module.connect(settings(tmp_path, **fields))
    assert not (tmp_path / "installation.json").exists()


@pytest.mark.parametrize("address", ["bad host", "http://host", 1, "x" * 257])
def test_invalid_server_is_not_executed(tmp_path, monkeypatch, address):
    monkeypatch.setattr(module, "processes", lambda: [])
    monkeypatch.setattr(module, "selected_installation", lambda *args: None)
    with pytest.raises(ValueError, match="host"):
        module.connect(settings(tmp_path, server=address))


@pytest.mark.parametrize(
    "error",
    [
        ValueError("bad config"),
        subprocess.CalledProcessError(1, ["client", "--password", "not-to-log"]),
    ],
)
def test_cli_reports_errors_without_leaking_child_password_arguments(
    tmp_path, monkeypatch, capsys, error
):
    monkeypatch.setattr(
        module.sys, "argv", ["connect", "--settings", str(tmp_path / "connection.json")]
    )

    def failed(*args, **kwargs):
        raise error

    monkeypatch.setattr(module, "connect", failed)
    with pytest.raises(SystemExit):
        module.main()
    assert "not-to-log" not in capsys.readouterr().err
