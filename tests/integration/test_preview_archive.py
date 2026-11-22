"""Exercise actual upstream generation, not an emulation of precollected-item order."""

import io
import json
import os
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

import pytest
from MultiServer import Context

from gamma_archipelago.presets import presets
from gamma_archipelago.web_generation import SeedGenerator
from gamma_archipelago.web_planner import player_document

ROOT = Path(__file__).resolve().parents[2]
GAME = "S.T.A.L.K.E.R. GAMMA"


@pytest.mark.generation
@pytest.mark.parametrize("mode", [0, 1, 2])
def test_actual_archives_bind_starting_items_deplete_once_and_control_preview_spoilers(
    tmp_path, mode
):
    options = {**presets()["standard"], "generation_preview": mode, "content_progression": 0}
    document = player_document("StartingItems", options)
    document[GAME].update(
        start_inventory={"Equipment Unlock: PDA": 1, "Zone Key: Garbage": 1},
        start_inventory_from_pool={"Progressive Tools": 2},
    )
    generator = SeedGenerator(ROOT, Path(os.environ["AP_RUNTIME_ROOT"]), tmp_path / "sessions")
    _, data = generator.generate(document, "20261119")
    with ZipFile(io.BytesIO(data)) as archive:
        name = next(name for name in archive.namelist() if name.endswith(".archipelago"))
        multidata = Context.decompress(archive.read(name))
        precollected = Counter(multidata["precollected_items"][1])
        assert precollected[28051801] == 2
        placed = Counter(row[0] for row in multidata["locations"][1].values())
        assert placed[28051801] == 1
        assert multidata["slot_data"][1]["schema_version"] == 4
        assert len(multidata["slot_data"][1]["generation_identity"]) == 64
        reports = [name for name in archive.namelist() if name.endswith("_gamma_preview.json")]
        assert len(reports) == int(mode > 0)
        if not mode:
            return
        report = json.loads(archive.read(reports[0]))
        assert report["kind"] == "actual_generated_seed"
        assert report["budget"]["starting_from_pool"] == {"Progressive Tools": 2}
        assert report["budget"]["starting_items"]["Equipment Unlock: PDA"] == 1
        assert report["budget"]["required_progression"]["Progressive Tools"] == 3
        assert "Equipment Unlock: PDA" not in report["budget"]["required_progression"]
        assert "Zone Key: Garbage" not in report["budget"]["required_progression"]
        assert "Garbage: First Arrival" in report["initial_reachable_checks"]
        assert bool(report.get("spoiler_placements")) == (mode == 2)
        if mode == 2:
            assert len(report["spoiler_placements"]) == len(multidata["locations"][1])
        assert report["native_verification"] == "not run"
