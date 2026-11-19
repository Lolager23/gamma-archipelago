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
        for name in ("gamma.apworld", "gamma-archipelago-mo2.zip", "gamma-archipelago-probes.zip")
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
                "notifications",
                "configuration",
                "equipment",
                "loadout",
                "settlements",
                "combat",
                "collection",
                "tasks",
            )
        } | {"gamedata/configs/text/eng/st_gamma_archipelago.xml"}
    with ZipFile(outputs[2]) as archive:
        assert set(archive.namelist()) == {
            f"gamedata/scripts/gamma_ap_probe_{name}.script" for name in ("capture", "game")
        } | {"gamedata/scripts/gamma_ap_paths.script"}
    runtime = Path(os.environ.get("AP_RUNTIME_ROOT", "D:/GAMMAAPTools/ap-runtime"))
    isolated = tmp_path / "runtime"
    shutil.copytree(
        runtime, isolated, ignore=shutil.ignore_patterns("gamma", "user", "cache", "__pycache__")
    )
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
assert container.world_version == Utils.Version(0, 1, 0)
assert len(GammaWorld.location_name_to_id) == 20221
import worlds.gamma.client
"""
    subprocess.run(
        [sys.executable, "-c", code, str(isolated)],
        check=True,
        env={
            **os.environ,
            "SKIP_REQUIREMENTS_UPDATE": "1",
            "PYTHONPATH": str(ROOT / "src"),
        },
        timeout=30,
    )
