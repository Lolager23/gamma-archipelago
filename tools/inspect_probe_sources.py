"""Read only the isolated saved MO2 profile and its loose script candidates."""

import argparse
import json

from gamma_archipelago.paths import DEFAULT_GAME_ROOT, DEFAULT_MO2_ROOT, require_isolated_root
from gamma_archipelago.probe_sources import inspect_sources


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="Archipelago DEV")
    arguments = parser.parse_args()
    game_root = require_isolated_root(DEFAULT_GAME_ROOT, DEFAULT_GAME_ROOT)
    mo2_root = require_isolated_root(DEFAULT_MO2_ROOT, DEFAULT_MO2_ROOT)
    print(json.dumps(inspect_sources(game_root, mo2_root, arguments.profile), indent=2))


if __name__ == "__main__":
    main()
