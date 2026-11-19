import http.client
import io
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from zipfile import ZipFile

import pytest
from MultiServer import Context

from gamma_archipelago.presets import presets
from gamma_archipelago.web_generation import SeedGenerator
from gamma_archipelago.web_planner import player_document, preview
from gamma_archipelago.web_server import serve

ROOT = Path(__file__).resolve().parents[2]


def load_multidata(data):
    with ZipFile(io.BytesIO(data)) as archive:
        assert archive.testzip() is None
        name = next(path for path in archive.namelist() if path.endswith(".archipelago"))
        assert any("Spoiler" in path for path in archive.namelist())
        return Context.decompress(archive.read(name))


@pytest.mark.generation
@pytest.mark.parametrize("preset", presets())
@pytest.mark.parametrize("seed", ["0", str(2**64 - 1)])
def test_each_web_preset_generates_exact_preview_ids_at_seed_boundaries(tmp_path, preset, seed):
    generator = SeedGenerator(ROOT, Path(os.environ["AP_RUNTIME_ROOT"]), tmp_path / "sessions")
    options = presets()[preset]
    if preset.startswith("full"):
        options.update(kill_milestones=[1, 10000], side_task_milestones=[1, 10000])
    document = player_document(" Test Player_1 ", options)
    name, data = generator.generate(document, seed)
    assert name.startswith("AP_") and name.endswith(".zip")
    multidata = load_multidata(data)
    expected = preview(options, {})
    assert multidata["slot_info"][1].name == "Test Player_1"
    assert set(multidata["locations"][1]) == {row["id"] for row in expected["checks"]}
    assert set(multidata["slot_data"][1]["item_ids"]) == {row["id"] for row in expected["rewards"]}
    assert (
        json.loads(json.dumps(multidata["slot_data"][1]["configuration"]))
        == expected["configuration"]
    )
    assert len(multidata["locations"][1]) == expected["reward_slots"]


@pytest.mark.generation
@pytest.mark.parametrize("seed", ["0", "20261119", str(2**64 - 1)])
def test_repeated_web_seed_reproduces_placements_and_settings(tmp_path, seed):
    generator = SeedGenerator(ROOT, Path(os.environ["AP_RUNTIME_ROOT"]), tmp_path / "sessions")
    document = player_document("Repeatable", presets()["full_story"])
    first_name, first = generator.generate(document, seed)
    second_name, second = generator.generate(document, seed)
    assert first_name == second_name
    first_data, second_data = load_multidata(first), load_multidata(second)
    for field in ("seed_name", "locations", "slot_data", "slot_info"):
        assert first_data[field] == second_data[field]


@pytest.mark.generation
def test_two_real_http_generations_refuse_overlap_then_recover(tmp_path):
    generator = SeedGenerator(ROOT, Path(os.environ["AP_RUNTIME_ROOT"]), tmp_path / "sessions")
    server = serve(ROOT / "web/generator", generator, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    barrier = threading.Barrier(2)
    payload = json.dumps(dict(name="Concurrent", seed="0", options=presets()["mvp"]))

    def request(overlap=True):
        if overlap:
            barrier.wait(timeout=10)
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=30)
        connection.request(
            "POST",
            "/api/generate",
            payload,
            {
                "Content-Type": "application/json",
                "Origin": f"http://127.0.0.1:{server.server_port}",
            },
        )
        response = connection.getresponse()
        result = response.status, response.read()
        connection.close()
        return result

    try:
        with ThreadPoolExecutor(max_workers=2) as clients:
            results = list(clients.map(lambda _: request(), range(2)))
        assert sorted(status for status, _ in results) == [200, 409]
        for status, data in results:
            if status == 200:
                assert len(load_multidata(data)["locations"][1]) == 33
            else:
                assert "already generating" in json.loads(data)["error"]
        status, data = request(overlap=False)
        assert status == 200 and len(load_multidata(data)["locations"][1]) == 33
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
