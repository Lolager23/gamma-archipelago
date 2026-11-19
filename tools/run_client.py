"""Run the installed CommonClient adapter without modifying a shared AP installation."""

import argparse
import os
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--ap-root", type=Path, default=Path("D:/GAMMAAPTools/ap-runtime"))
arguments, client_arguments = parser.parse_known_args()
os.environ["SKIP_REQUIREMENTS_UPDATE"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(arguments.ap_root.resolve()))
import Utils  # noqa: E402

Utils.user_path.cached_path = str(arguments.ap_root / "user")
Utils.cache_path.cached_path = str(arguments.ap_root / "cache")
Path(Utils.user_path()).mkdir(parents=True, exist_ok=True)
from worlds.gamma.client import launch  # noqa: E402

launch(*client_arguments)
