"""Serve the local APWorld workbench without starting GAMMA or MultiServer."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gamma_archipelago.paths import require_safe_child  # noqa: E402
from gamma_archipelago.web_generation import SeedGenerator  # noqa: E402
from gamma_archipelago.web_server import serve  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=38290)
    arguments = parser.parse_args()
    tooling = Path("D:/GAMMAAPTools")
    runtime = require_safe_child(tooling, "generator-runtime")
    storage = require_safe_child(tooling, "generator-sessions")
    generator = SeedGenerator(ROOT, runtime, storage)
    with serve(ROOT / "web/generator", generator, arguments.port) as server:
        print(f"GAMMA seed workbench: http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("Workbench stopped.")


if __name__ == "__main__":
    main()
