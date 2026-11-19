"""Copy only our add-on into the explicit development MO2 instance."""

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gamma_archipelago.paths import DEFAULT_MO2_ROOT, require_isolated_root, require_safe_child  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--component", choices=("pilot", "probes"), default="pilot")
    arguments = parser.parse_args()
    root = require_isolated_root(DEFAULT_MO2_ROOT, DEFAULT_MO2_ROOT)
    name = (
        "GAMMA Archipelago DEV"
        if arguments.component == "pilot"
        else "GAMMA Archipelago Callback Probes DEV"
    )
    source_root = ROOT / ("mod" if arguments.component == "pilot" else "probes")
    destination = require_safe_child(root, f"mods/{name}")
    sources = [
        (source, source.relative_to(source_root))
        for source in source_root.rglob("*")
        if source.is_file()
    ]
    if arguments.component == "probes":
        relative = Path("gamedata/scripts/gamma_ap_paths.script")
        sources.append((ROOT / "mod" / relative, relative))
    for source, relative in sources:
        target = require_safe_child(root, str(destination.relative_to(root) / relative))
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    print(f"Deployed copied files to {destination}; enable only in Archipelago DEV profile.")


if __name__ == "__main__":
    main()
