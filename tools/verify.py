"""Run affected regressions by default, or the complete release verifier."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*arguments: str) -> None:
    subprocess.run([sys.executable, *arguments], cwd=ROOT, check=True)


def check_coverage(path: Path, modules: tuple[str, ...] = ()) -> None:
    report = json.loads(path.read_text(encoding="utf-8"))
    expected = {module.replace(".", "/") + ".py" for module in modules}
    matched = set()
    for name, data in report["files"].items():
        normal = name.replace("\\", "/")
        selected = {module for module in expected if normal.endswith(module)}
        if expected and not selected:
            continue
        matched.update(selected)
        summary = data["summary"]
        required = 100 if Path(normal).stem in {"protocol", "session"} else 95
        for covered, total in (
            ("covered_lines", "num_statements"),
            ("covered_branches", "num_branches"),
        ):
            percentage = 100 * summary[covered] / max(1, summary[total]) if summary[total] else 100
            if percentage < required:
                raise SystemExit(f"{name}: {covered} {percentage:.2f}% < required {required}%")
    if expected - matched:
        raise SystemExit(f"Changed modules missing from coverage: {sorted(expected - matched)}")
    print("Independent per-module Python line and branch coverage gates passed.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ap-source", default="D:/GAMMAAPTools/Archipelago")
    parser.add_argument("--ap-root", default="D:/GAMMAAPTools/ap-runtime")
    parser.add_argument("--base", default="origin/main", help="Compare changes with this Git ref")
    parser.add_argument("--full", action="store_true", help="Complete release verification")
    parser.add_argument(
        "--plan", action="store_true", help="Print affected selection without running"
    )
    arguments = parser.parse_args()
    if not arguments.full:
        from verify_changed import verify

        verify(arguments)
        return
    if arguments.plan:
        parser.error("--plan describes affected verification; omit --full")
    os.environ["AP_RUNTIME_ROOT"] = str(Path(arguments.ap_root).resolve())
    run("-m", "ruff", "check", "src", "apworld", "tools", "tests")
    run("-m", "ruff", "format", "--check", "src", "apworld", "tools", "tests")
    run("-m", "mypy", "src/gamma_archipelago")
    for filename in ("app.js", "ui.js", "form_state.js", "reward_controls.js"):
        subprocess.run(["node", "--check", str(ROOT / "web/generator" / filename)], check=True)
    subprocess.run(["node", "--test", str(ROOT / "tests/web/test_form_state.mjs")], check=True)
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
