"""Read only a development engine log; print a data-only diagnostic summary."""

import argparse
import json
from pathlib import Path

from gamma_archipelago.paths import DEFAULT_GAME_ROOT, require_isolated_root, require_safe_child
from gamma_archipelago.probe_report import summarize


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("log_name", help="Filename under D:/AnomalyAP/appdata/logs")
    arguments = parser.parse_args()
    if (
        Path(arguments.log_name).name != arguments.log_name
        or any(character in arguments.log_name for character in "/\\:")
        or not arguments.log_name.endswith(".log")
    ):
        parser.error("Supply a .log filename without directories")
    root = require_isolated_root(DEFAULT_GAME_ROOT, DEFAULT_GAME_ROOT)
    path = require_safe_child(root, f"appdata/logs/{arguments.log_name}")
    with path.open(encoding="utf-8", errors="replace") as source:
        print(json.dumps(summarize(source), indent=2))


if __name__ == "__main__":
    main()
