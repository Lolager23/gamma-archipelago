"""Run the same fail-fast checks locally and in CI."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*arguments: str) -> None:
    subprocess.run([sys.executable, *arguments], cwd=ROOT, check=True)


def check_coverage(path: Path) -> None:
    report = json.loads(path.read_text(encoding="utf-8"))
    for name, data in report["files"].items():
        summary = data["summary"]
        required = 100 if Path(name).stem in {"protocol", "session"} else 95
        for covered, total in (
            ("covered_lines", "num_statements"),
            ("covered_branches", "num_branches"),
        ):
            percentage = 100 * summary[covered] / max(1, summary[total]) if summary[total] else 100
            if percentage < required:
                raise SystemExit(f"{name}: {covered} {percentage:.2f}% < required {required}%")
    print("Independent per-module Python line and branch coverage gates passed.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ap-source", default="D:/GAMMAAPTools/Archipelago")
    parser.add_argument("--ap-root", default="D:/GAMMAAPTools/ap-runtime")
    arguments = parser.parse_args()
    os.environ["AP_RUNTIME_ROOT"] = str(Path(arguments.ap_root).resolve())
    run("-m", "ruff", "check", "src", "apworld", "tools", "tests")
    run("-m", "ruff", "format", "--check", "src", "apworld", "tools", "tests")
    run("-m", "mypy", "src/gamma_archipelago")
    for filename in ("app.js", "ui.js"):
        subprocess.run(["node", "--check", str(ROOT / "web/generator" / filename)], check=True)
    run("tools/build.py")
    run(
        "tools/bootstrap_ap.py", "--source", arguments.ap_source, "--destination", arguments.ap_root
    )
    run(
        "-m",
        "pytest",
        "-q",
        "-m",
        "not server and not generation",
        "--cov=gamma_archipelago",
        "--cov=worlds.gamma",
        "--cov-branch",
        "--cov-report=term-missing",
        "--cov-report=json:coverage.json",
    )
    check_coverage(ROOT / "coverage.json")
    # On this Python 3.12.3 installation, tracing upstream's C-backed YAML loader
    # yields invalid None tags. Exercise the real generator/server without tracing;
    # the same owned client/world code is covered by the preceding regression suite.
    # Keep the complete large seed matrix, without tracing every repeated graph
    # traversal. The covered regression pass exercises these same world branches.
    run("-m", "pytest", "-q", "-m", "server or generation")


if __name__ == "__main__":
    main()
