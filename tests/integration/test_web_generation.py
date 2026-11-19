import io
from pathlib import Path
from zipfile import ZipFile

import pytest

from gamma_archipelago.presets import presets
from gamma_archipelago.web_generation import SeedGenerator
from gamma_archipelago.web_planner import player_document

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.generation
def test_web_backend_generates_a_real_downloadable_seed(tmp_path):
    import os

    generator = SeedGenerator(ROOT, Path(os.environ["AP_RUNTIME_ROOT"]), tmp_path / "sessions")
    document = player_document("WebAcceptance", presets()["mvp"])
    name, data = generator.generate(document, "20261119")
    assert name.startswith("AP_") and name.endswith(".zip")
    with ZipFile(io.BytesIO(data)) as archive:
        assert archive.testzip() is None
        assert any(path.endswith(".archipelago") for path in archive.namelist())
        assert any("Spoiler" in path for path in archive.namelist())
