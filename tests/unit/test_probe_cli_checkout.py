"""Diagnostic commands remain usable alongside another editable checkout."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("tool", ["report_probes.py", "inspect_probe_sources.py"])
def test_probe_cli_uses_its_own_checkout_before_an_unrelated_install(tmp_path, tool):
    package = tmp_path / "gamma_archipelago"
    package.mkdir()
    (package / "__init__.py").write_text("raise RuntimeError('wrong checkout loaded')\n")
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / tool), "--help"],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(tmp_path)},
        capture_output=True,
        text=True,
        check=True,
    )
    assert "usage:" in result.stdout
