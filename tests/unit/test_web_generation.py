import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from gamma_archipelago import web_generation
from gamma_archipelago.web_generation import GenerationBusy, SeedGenerator


@pytest.fixture
def generator(tmp_path, monkeypatch):
    source, runtime = tmp_path / "source", tmp_path / "runtime"
    for path in ("apworld/gamma/world.py", "src/gamma_archipelago/catalog.json"):
        file = source / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("source")
    (runtime / "worlds/gamma").mkdir(parents=True)
    for path in ("Generate.py", "worlds/gamma/world.py", "worlds/gamma/catalog.json"):
        (runtime / path).write_text("source")

    def run(command, **kwargs):
        output = Path(command[command.index("--outputpath") + 1])
        output.mkdir()
        (output / "AP_123.zip").write_bytes(b"archive")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(web_generation.subprocess, "run", run)
    return SeedGenerator(source, runtime, tmp_path / "sessions")


def test_generation_uses_isolated_paths_bounded_subprocess_and_fixed_yaml(generator):
    assert generator.generate({"name": "Owen"}, "0") == ("AP_123.zip", b"archive")
    yaml = next(generator.storage.glob("*/players/gamma.yaml"))
    assert '"Owen"' in yaml.read_text()
    assert not generator.lock.locked()


@pytest.mark.parametrize("seed", [None, 12, "-1", "1;calc", "", "１", "0" * 21, str(2**64)])
def test_invalid_seed_never_runs(generator, seed):
    with pytest.raises(ValueError, match="Seed"):
        generator.generate({}, seed)
    assert not generator.storage.exists()


def test_concurrent_generation_is_refused(generator):
    with generator.lock, pytest.raises(GenerationBusy):
        generator.generate({}, "1")


@pytest.mark.parametrize("failure", ["timeout", "exit", "empty", "many", "large"])
def test_generation_failures_are_visible_and_always_release_lock(generator, monkeypatch, failure):
    def run(command, **kwargs):
        if failure == "timeout":
            raise subprocess.TimeoutExpired(command, 180)
        output = Path(command[command.index("--outputpath") + 1])
        output.mkdir()
        if failure in {"many", "large"}:
            archive = output / "AP_1.zip"
            with archive.open("wb") as stream:
                stream.truncate(16 * 1024 * 1024 + 1 if failure == "large" else 1)
        if failure == "many":
            (output / "AP_2.zip").write_bytes(b"extra")
        return SimpleNamespace(returncode=1 if failure == "exit" else 0)

    monkeypatch.setattr(web_generation.subprocess, "run", run)
    with pytest.raises(ValueError):
        generator.generate({}, "1")
    assert not generator.lock.locked()


@pytest.mark.parametrize(
    "mismatch", ["Generate.py", "worlds/gamma/world.py", "worlds/gamma/catalog.json"]
)
def test_missing_or_mismatched_runtime_is_refused(generator, mismatch):
    path = generator.runtime / mismatch
    path.write_text("different")
    if mismatch == "Generate.py":
        path.unlink()
    with pytest.raises(ValueError, match="runtime|catalogue"):
        generator.generate({}, "1")
    assert not generator.storage.exists()
