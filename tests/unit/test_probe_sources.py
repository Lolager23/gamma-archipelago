import hashlib
from pathlib import Path

import pytest

from gamma_archipelago.probe_sources import enabled_mods, inspect_sources


def write(root, relative, content):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_saved_modlist_keeps_highest_first_and_skips_disabled_entries():
    assert enabled_mods(["# generated", "", "+highest", "-disabled", "+lower"]) == (
        "highest",
        "lower",
    )


@pytest.mark.parametrize(
    "entry", ["+", "+.", "+..", "bad", "+../normal", "+D:normal", "+bad\\path"]
)
def test_invalid_mod_names_cannot_escape_or_fabricate_order(entry):
    with pytest.raises(ValueError, match="Invalid"):
        enabled_mods([entry])


def test_duplicate_entries_follow_mo2_first_occurrence_without_changing_priority():
    assert enabled_mods(["+vehicles", "+other", "+vehicles", "-OTHER", "*foreign"]) == (
        "vehicles",
        "other",
        "foreign",
    )
    assert enabled_mods(["-disabled", "+DISABLED"]) == ()


@pytest.mark.parametrize("profile", ["", ".", "..", "../GAMMA", "D:profile", "a\\b"])
def test_profile_cannot_select_another_installation(tmp_path, profile):
    with pytest.raises(ValueError, match="Profile"):
        inspect_sources(tmp_path / "game", tmp_path / "mo2", profile)


def test_candidate_order_hashes_missing_mods_and_unverified_runtime(tmp_path):
    game, mo2 = tmp_path / "game", tmp_path / "mo2"
    write(mo2, "profiles/DEV/modlist.txt", "\ufeff+high\n-low\n+missing\n+lower\n")
    write(mo2, "overwrite/gamedata/scripts/task_manager.script", "overwrite")
    write(mo2, "mods/high/gamedata/scripts/task_manager.script", "high")
    write(mo2, "mods/low/gamedata/scripts/task_manager.script", "disabled")
    write(mo2, "mods/lower/gamedata/scripts/task_manager.script", "lower")
    write(game, "gamedata/scripts/task_manager.script", "game")
    report = inspect_sources(game, mo2, "DEV")
    assert report["enabled_mods"] == 3
    assert report["missing_enabled_mods"] == ["missing"]
    result = report["files"]["task_manager.script"]
    assert [candidate["source"] for candidate in result["ordered_candidates"]] == [
        "overwrite",
        "high",
        "lower",
        "game loose files",
    ]
    assert result["ordered_candidates"][1]["sha256"] == hashlib.sha256(b"high").hexdigest()
    assert result["runtime_winner"] == "not verified"
    assert report["files"]["axr_main.script"]["ordered_candidates"] == []


def test_installation_changes_during_read_require_a_fresh_inventory(tmp_path, monkeypatch):
    mo2 = tmp_path / "mo2"
    modlist = write(mo2, "profiles/DEV/modlist.txt", "")
    original = Path.read_bytes
    reads = []

    def changing(path):
        reads.append(path)
        if len(reads) == 2:
            return b"changed"
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", changing)
    with pytest.raises(ValueError, match="changed"):
        inspect_sources(tmp_path / "game", mo2, "DEV")
    assert reads == [modlist, modlist]


def test_compatibility_inventory_exposes_enabled_consumers_with_disabled_providers(tmp_path):
    game, mo2 = tmp_path / "game", tmp_path / "mo2"
    write(mo2, "profiles/DEV/modlist.txt", "+compatibility\n-provider\n")
    pairs = (
        ("a_faction_prices.script", "faction_stocks.script"),
        ("mags_patches.script", "magazine_binder.script"),
        ("zz_ui_inventory_better_stats_bars.script", "better_stats_bars_mcm.script"),
    )
    for consumer, provider in pairs:
        write(mo2, "mods/compatibility/gamedata/scripts/" + consumer, "-- consumer")
        write(mo2, "mods/provider/gamedata/scripts/" + provider, "-- disabled provider")
    write(mo2, "mods/compatibility/gamedata/scripts/zzz_mspizza_godis_zoomcalc.script", "/*")
    report = inspect_sources(game, mo2, "DEV")
    for consumer, provider in pairs:
        assert report["files"][consumer]["ordered_candidates"][0]["source"] == "compatibility"
        assert report["files"][provider]["ordered_candidates"] == []
    assert report["files"]["zzz_mspizza_godis_zoomcalc.script"]["runtime_winner"] == "not verified"
