import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("name", ["deploy_mod.py", "inspect_probe_sources.py", "report_probes.py"])
def test_cli_uses_its_own_checkout_before_an_unrelated_editable_package(tmp_path, name):
    trap = tmp_path / "gamma_archipelago"
    trap.mkdir()
    (trap / "__init__.py").write_text("raise RuntimeError('Unrelated source was imported')\n")
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / name), "--help"],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout
