import hashlib
import importlib
import json
import sys
from pathlib import Path
from zipfile import ZipFile

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
release = importlib.import_module("prepare_release")


def candidate_source(tmp_path, monkeypatch):
    monkeypatch.setattr(release, "ROOT", tmp_path)
    (tmp_path / "dist").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "presets").mkdir()
    (tmp_path / "pyproject.toml").write_text('[project]\nversion="1.0.0rc1"\n')
    for name in (
        "README.md",
        "NOTICE.md",
        "CHANGELOG.md",
        "docs/acceptance.md",
        "presets/mvp.yaml",
    ):
        (tmp_path / name).write_text("candidate\n")

    def build(*args, **kwargs):
        for name in release.PACKAGES:
            (tmp_path / "dist" / name).write_bytes(b"owned candidate payload")

    def git(arguments, **kwargs):
        return "" if arguments[1] == "status" else "a" * 40 + "\n"

    monkeypatch.setattr(release.subprocess, "run", build)
    monkeypatch.setattr(release.subprocess, "check_output", git)


def test_candidate_is_reproducible_traceable_and_explicitly_unaccepted(tmp_path, monkeypatch):
    candidate_source(tmp_path, monkeypatch)
    first = release.prepare()
    original = first.read_bytes()
    assert release.prepare().read_bytes() == original
    with ZipFile(first) as archive:
        manifest = json.loads(archive.read("release-manifest.json"))
        assert manifest["source_commit"] == "a" * 40
        assert manifest["publication_approved"] is False
        assert manifest["engine_acceptance"] == "not_run"
        assert manifest["owned_code_licence"] == "owner_decision_pending"
        for name, record in manifest["files"].items():
            data = archive.read(name)
            assert record == {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    checksum = first.with_suffix(".zip.sha256").read_text()
    assert checksum.startswith(hashlib.sha256(original).hexdigest())


def test_dirty_source_is_refused_before_build_or_packaging(tmp_path, monkeypatch):
    candidate_source(tmp_path, monkeypatch)
    monkeypatch.setattr(
        release.subprocess, "check_output", lambda *args, **kwargs: " M source.py\n"
    )
    with pytest.raises(SystemExit, match="source changes"):
        release.prepare()
    assert not list((tmp_path / "dist").glob("*.zip"))


@pytest.mark.parametrize("version", ['"../unsafe"', "123"])
def test_invalid_candidate_version_cannot_escape_output_directory(tmp_path, monkeypatch, version):
    candidate_source(tmp_path, monkeypatch)
    (tmp_path / "pyproject.toml").write_text(f"[project]\nversion={version}\n")
    with pytest.raises(SystemExit, match="filename-safe"):
        release.prepare()
