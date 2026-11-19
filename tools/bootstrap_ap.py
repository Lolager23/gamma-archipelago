"""Build a small isolated runtime from a pinned upstream checkout, without editing it."""

import argparse
import shutil
import subprocess
from pathlib import Path

from build import ROOT, generate_catalogues

AP_COMMIT = "54803be064fc7e80c4628777ed0b46a9390f255f"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("D:/GAMMAAPTools/Archipelago"))
    parser.add_argument("--destination", type=Path, default=Path("D:/GAMMAAPTools/ap-runtime"))
    arguments = parser.parse_args()
    revision = subprocess.check_output(
        ["git", "-C", str(arguments.source), "rev-parse", "HEAD"], text=True
    ).strip()
    if revision != AP_COMMIT:
        raise SystemExit(f"Expected pinned AP commit {AP_COMMIT}; found {revision}")
    destination = arguments.destination.resolve()
    source = arguments.source.resolve()
    if any(
        destination == protected
        or destination.is_relative_to(protected)
        or protected.is_relative_to(destination)
        for protected in (
            source,
            ROOT,
            Path("D:/Anomaly").resolve(),
            Path("D:/GAMMA").resolve(),
            Path("D:/AnomalyAP").resolve(),
            Path("D:/GAMMAAP").resolve(),
        )
    ):
        raise SystemExit("Runtime destination must be separate from upstream and project source")
    destination.mkdir(parents=True, exist_ok=True)
    for name in ("apmw", "rule_builder", "data", "test"):
        shutil.copytree(arguments.source / name, destination / name, dirs_exist_ok=True)
    for path in arguments.source.glob("*.py"):
        shutil.copy2(path, destination / path.name)
    worlds = destination / "worlds"
    worlds.mkdir(exist_ok=True)
    for path in (arguments.source / "worlds").glob("*.py"):
        shutil.copy2(path, worlds / path.name)
    for name in ("generic", "apquest"):
        shutil.copytree(arguments.source / "worlds" / name, worlds / name, dirs_exist_ok=True)
    generate_catalogues()
    shutil.copytree(ROOT / "apworld/gamma", worlds / "gamma", dirs_exist_ok=True)
    shutil.copytree(
        ROOT / "src/gamma_archipelago", destination / "gamma_archipelago", dirs_exist_ok=True
    )
    (destination / "user").mkdir(exist_ok=True)
    print(f"Pinned Archipelago runtime prepared at {destination}")


if __name__ == "__main__":
    main()
