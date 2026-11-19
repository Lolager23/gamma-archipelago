"""Run upstream generation or hosting with private tooling state."""

import argparse
import asyncio
import os
import sys
from pathlib import Path

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("action", choices=("generate", "host"))
parser.add_argument("--ap-root", type=Path, default=Path("D:/GAMMAAPTools/ap-runtime"))
arguments, upstream_arguments = parser.parse_known_args()
runtime = arguments.ap_root.resolve()
os.environ["SKIP_REQUIREMENTS_UPDATE"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(runtime))
import Utils  # noqa: E402

Utils.user_path.cached_path = str(runtime / "user")
Utils.cache_path.cached_path = str(runtime / "cache")
Path(Utils.user_path()).mkdir(parents=True, exist_ok=True)
if arguments.action == "generate":
    import Generate
    import Main

    generation, seed = Generate.main(Generate.mystery_argparse(upstream_arguments))
    Main.main(generation, seed)
else:
    import MultiServer

    sys.argv = [sys.argv[0], *upstream_arguments]
    asyncio.run(MultiServer.main(MultiServer.parse_args()))
