"""Copy only our add-on into the explicit development MO2 instance."""

import shutil
from pathlib import Path

from gamma_archipelago.paths import DEFAULT_MO2_ROOT, require_isolated_root, require_safe_child

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    root = require_isolated_root(DEFAULT_MO2_ROOT, DEFAULT_MO2_ROOT)
    destination = require_safe_child(root, "mods/GAMMA Archipelago DEV")
    for source in (ROOT / "mod").rglob("*"):
        if source.is_file():
            relative = source.relative_to(ROOT / "mod")
            target = require_safe_child(root, str(destination.relative_to(root) / relative))
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    print(f"Deployed copied files to {destination}; enable only in Archipelago DEV profile.")


if __name__ == "__main__":
    main()
