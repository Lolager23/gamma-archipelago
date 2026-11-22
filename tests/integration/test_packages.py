"""Test the distributed archive through upstream's actual APWorld loader."""

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

import pytest

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.integration


def test_packages_are_reproducible_and_load_from_apworld(tmp_path):
    subprocess.run([sys.executable, "tools/build.py"], cwd=ROOT, check=True)
    outputs = [
        ROOT / "dist" / name
        for name in (
            "gamma.apworld",
            "gamma-archipelago-mo2.zip",
            "gamma-archipelago-probes.zip",
            "gamma-archipelago-client.zip",
        )
    ]
    first = [hashlib.sha256(path.read_bytes()).digest() for path in outputs]
    subprocess.run([sys.executable, "tools/build.py"], cwd=ROOT, check=True)
    assert [hashlib.sha256(path.read_bytes()).digest() for path in outputs] == first
    with ZipFile(outputs[1]) as archive:
        assert set(archive.namelist()) == {
            f"gamedata/scripts/gamma_ap_{name}.script"
            for name in (
                "catalog",
                "paths",
                "protocol",
                "state",
                "game",
                "actions",
                "mcm",
                "notice_text",
                "readiness",
                "tracker",
                "pda",
                "scout_protocol",
                "scouting",
                "services",
                "discovery",
                "activity",
                "playability",
                "weather",
                "stamina",
                "workshop",
                "deliveries",
                "convenience",
                "notifications",
                "presence",
                "configuration",
                "equipment",
                "loadout",
                "settlements",
                "settlement_access",
                "combat",
                "collection",
                "tasks",
                "equipment_checks",
                "rank",
                "reputation",
                "skills",
                "quest_keys",
                "gear_locks",
                "equipment_use",
                "purchase_guard",
                "start",
                "start_menu",
                "transition_geometry",
                "zone_keys",
                "zone_recovery",
                "travel",
                "goals",
                "save_validation",
                "stashes",
                "shop",
                "shop_ui",
            )
        } | {
            "gamedata/configs/text/eng/st_gamma_archipelago.xml",
            "gamedata/configs/text/eng/st_gamma_ap_notices.xml",
            "gamedata/configs/text/eng/st_gamma_ap_pda.xml",
            "gamedata/configs/ui/gamma_ap_pda.xml",
            "gamedata/scripts/modxml_gamma_ap_pda.script",
            "gamedata/scripts/modxml_gamma_ap_stashes.script",
            "gamedata/configs/ui/textures_descr/ui_gamma_ap_stash.xml",
            "gamedata/textures/ui/gamma_ap_stash.dds",
            "ARCHIPELAGO-ICON-LICENSE.txt",
            "gamedata/configs/text/eng/st_gamma_ap_shop.xml",
            "gamedata/configs/text/eng/st_gamma_ap_guards.xml",
            "gamedata/configs/ui/gamma_ap_shop.xml",
            "gamedata/configs/ui/textures_descr/ui_gamma_ap_shop.xml",
            "gamedata/textures/ui/gamma_ap_shop.dds",
        }
    with ZipFile(outputs[2]) as archive:
        assert set(archive.namelist()) == {
            f"gamedata/scripts/gamma_ap_probe_{name}.script" for name in ("capture", "game")
        } | {"gamedata/scripts/gamma_ap_paths.script"}
    runtime = Path(os.environ.get("AP_RUNTIME_ROOT", "D:/GAMMAAPTools/ap-runtime"))
    isolated = tmp_path / "runtime"
    shutil.copytree(
        runtime,
        isolated,
        ignore=shutil.ignore_patterns("gamma", "gamma_archipelago", "user", "cache", "__pycache__"),
    )
    with ZipFile(outputs[3]) as archive:
        archive.extractall(isolated)
    shutil.copy2(outputs[0], isolated / "worlds/gamma.apworld")
    code = """
import sys
sys.path.insert(0, sys.argv[1])
import Utils
Utils.user_path.cached_path = sys.argv[1] + '/user'
Utils.cache_path.cached_path = sys.argv[1] + '/cache'
import worlds
from worlds.gamma import GammaWorld
from worlds.Files import APWorldContainer
assert not worlds.failed_world_loads, worlds.failed_world_loads
assert str(GammaWorld.zip_path).endswith('gamma.apworld'), GammaWorld.zip_path
container = APWorldContainer(str(GammaWorld.zip_path))
container.read()
assert container.world_version == Utils.Version(1, 0, 0)
assert len(GammaWorld.location_name_to_id) == 20375
import worlds.gamma.client
import gamma_archipelago
assert str(gamma_archipelago.__file__).startswith(sys.argv[1]), gamma_archipelago.__file__
"""
    subprocess.run(
        [sys.executable, "-c", code, str(isolated)],
        check=True,
        env={
            **os.environ,
            "SKIP_REQUIREMENTS_UPDATE": "1",
            "PYTHONPATH": "",
        },
        timeout=30,
    )
    help_result = subprocess.run(
        [sys.executable, str(isolated / "GammaArchipelagoClient.py"), "--help"],
        cwd=isolated,
        env={**os.environ, "PYTHONPATH": ""},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert help_result.returncode == 0, help_result.stderr
    assert "--name" in help_result.stdout
