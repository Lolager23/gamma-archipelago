"""One bounded local generation at a time; no game launch or deployment."""

import json
import os
import subprocess
import sys
import threading
import uuid
from pathlib import Path

from .paths import require_safe_child


class GenerationBusy(ValueError):
    """Another request already owns the generator."""


class SeedGenerator:
    def __init__(self, source: Path, runtime: Path, storage: Path) -> None:
        self.source, self.runtime, self.storage = source, runtime, storage
        self.lock = threading.Lock()

    def generate(self, document: dict[str, object], seed: object) -> tuple[str, bytes]:
        if not isinstance(seed, str) or not seed.isascii() or not seed.isdecimal():
            raise ValueError("Seed must contain 1–20 decimal digits")
        if not 1 <= len(seed) <= 20 or int(seed) > 2**64 - 1:
            raise ValueError("Seed must fit an unsigned 64-bit integer")
        if not self.lock.acquire(blocking=False):
            raise GenerationBusy("A seed is already generating; wait for it to finish")
        try:
            return self._run(document, seed)
        finally:
            self.lock.release()

    def _run(self, document: dict[str, object], seed: str) -> tuple[str, bytes]:
        self._check_runtime()
        self.storage.mkdir(parents=True, exist_ok=True)
        job = require_safe_child(self.storage, uuid.uuid4().hex)
        players = require_safe_child(job, "players")
        players.mkdir(parents=True)
        require_safe_child(players, "gamma.yaml").write_text(
            json.dumps(document, indent=2) + "\n", encoding="utf-8"
        )
        command = [
            sys.executable,
            str(self.source / "tools/run_ap.py"),
            "generate",
            "--ap-root",
            str(self.runtime),
            "--player_files_path",
            str(players),
            "--outputpath",
            str(job / "output"),
            "--seed",
            seed,
            "--spoiler",
            "1",
            "--log_level",
            "warning",
        ]
        with require_safe_child(job, "generation.log").open("wb") as log:
            try:
                result = subprocess.run(
                    command,
                    cwd=self.source,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=180,
                    env={**os.environ, "SKIP_REQUIREMENTS_UPDATE": "1"},
                )
            except subprocess.TimeoutExpired as error:
                raise ValueError(
                    "Generation timed out after 180 seconds; inspect the local log"
                ) from error
        if result.returncode:
            raise ValueError(
                "Archipelago rejected this seed; inspect generation.log in the session folder"
            )
        archives = list(require_safe_child(job, "output").glob("*.zip"))
        if len(archives) != 1:
            raise ValueError("Generation did not produce exactly one seed archive")
        archive = require_safe_child(job, archives[0].relative_to(job).as_posix())
        if archive.stat().st_size > 16 * 1024 * 1024:
            raise ValueError("Generated archive exceeds the 16 MiB download limit")
        return archive.name, archive.read_bytes()

    def _check_runtime(self) -> None:
        if not require_safe_child(self.runtime, "Generate.py").is_file():
            raise ValueError("Prepare the separate AP runtime with tools/bootstrap_ap.py first")
        for path in (self.source / "apworld/gamma").glob("*.py"):
            installed = require_safe_child(self.runtime, "worlds/gamma/" + path.name)
            if not installed.is_file() or installed.read_bytes() != path.read_bytes():
                raise ValueError(
                    "AP runtime world differs from source; bootstrap its matching revision"
                )
        source_catalogue = self.source / "src/gamma_archipelago/catalog.json"
        if (
            require_safe_child(self.runtime, "worlds/gamma/catalog.json").read_bytes()
            != source_catalogue.read_bytes()
        ):
            raise ValueError(
                "AP runtime catalogue differs from source; bootstrap its matching revision"
            )
