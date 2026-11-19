"""Read only the isolated saved MO2 profile and its loose script candidates."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gamma_archipelago.paths import DEFAULT_GAME_ROOT, DEFAULT_MO2_ROOT, require_isolated_root  # noqa: E402
from gamma_archipelago.probe_sources import inspect_sources  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="Archipelago DEV")
    arguments = parser.parse_args()
    game_root = require_isolated_root(DEFAULT_GAME_ROOT, DEFAULT_GAME_ROOT)
    mo2_root = require_isolated_root(DEFAULT_MO2_ROOT, DEFAULT_MO2_ROOT)
    print(json.dumps(inspect_sources(game_root, mo2_root, arguments.profile), indent=2))


if __name__ == "__main__":
    main()
