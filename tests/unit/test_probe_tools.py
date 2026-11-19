import json
import sys

import pytest

from tools import deploy_mod, inspect_probe_sources, report_probes


@pytest.mark.parametrize("component,count", [("pilot", 37), ("probes", 3)])
def test_deployer_copies_each_component_to_a_separate_mod(tmp_path, monkeypatch, component, count):
    monkeypatch.setattr(deploy_mod, "DEFAULT_MO2_ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["deploy_mod.py", "--component", component])
    deploy_mod.main()
    installed = list((tmp_path / "mods").rglob("*.script"))
    assert len(installed) == count
    source_root = deploy_mod.ROOT / ("mod" if component == "pilot" else "probes")
    for target in installed:
        original = source_root / "gamedata/scripts" / target.name
        if target.name == "gamma_ap_paths.script":
            original = deploy_mod.ROOT / "mod/gamedata/scripts" / target.name
        assert target.read_bytes() == original.read_bytes()
        assert target.stat().st_nlink == 1 and target.stat().st_ino != original.stat().st_ino
    if component == "probes":
        assert all(
            "gamma_ap_probe_" in path.name or path.name == "gamma_ap_paths.script"
            for path in installed
        )
    else:
        assert all("gamma_ap_probe_" not in path.name for path in installed)


@pytest.mark.parametrize("name", ["../normal.log", "D:\\normal.log", "normal\\x.log", "data.txt"])
def test_log_cli_rejects_paths_before_reading(tmp_path, monkeypatch, name):
    monkeypatch.setattr(report_probes, "DEFAULT_GAME_ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["report_probes.py", name])
    with pytest.raises(SystemExit) as error:
        report_probes.main()
    assert error.value.code == 2
    assert not list(tmp_path.iterdir())


def test_log_cli_reads_only_the_development_log(tmp_path, monkeypatch, capsys):
    folder = tmp_path / "appdata/logs"
    folder.mkdir(parents=True)
    (folder / "engine.log").write_text("GAMMA_AP_PROBE|1|1|0|started|-|-|-|-\n")
    monkeypatch.setattr(report_probes, "DEFAULT_GAME_ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["report_probes.py", "engine.log"])
    report_probes.main()
    assert json.loads(capsys.readouterr().out)["counts"] == {"started": 1}


def test_source_cli_reads_the_explicit_saved_profile(tmp_path, monkeypatch, capsys):
    profile = tmp_path / "mo2/profiles/DEV"
    profile.mkdir(parents=True)
    (profile / "modlist.txt").write_text("")
    monkeypatch.setattr(inspect_probe_sources, "DEFAULT_GAME_ROOT", tmp_path / "game")
    monkeypatch.setattr(inspect_probe_sources, "DEFAULT_MO2_ROOT", tmp_path / "mo2")
    monkeypatch.setattr(sys, "argv", ["inspect_probe_sources.py", "--profile", "DEV"])
    inspect_probe_sources.main()
    assert json.loads(capsys.readouterr().out)["enabled_mods"] == 0
