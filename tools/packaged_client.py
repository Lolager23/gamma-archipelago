"""Entry point distributed beside a separate pinned Archipelago runtime."""

import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))
os.environ["SKIP_REQUIREMENTS_UPDATE"] = "1"
import Utils  # noqa: E402

Utils.user_path.cached_path = str(root / "user")
Utils.cache_path.cached_path = str(root / "cache")
Path(Utils.user_path()).mkdir(parents=True, exist_ok=True)
from worlds.gamma.client import launch  # noqa: E402

launch(*sys.argv[1:])
