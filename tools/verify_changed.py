"""Run affected component regressions; exhaustive sweeps belong to releases."""

import argparse
import json
import os
import subprocess
from dataclasses import asdict
from pathlib import Path

from verification_scope import RELEASE_ONLY_TESTS, SERVER_TESTS, plan

ROOT = Path(__file__).resolve().parents[1]


def changed_paths(base: str) -> list[str]:
    commit = subprocess.check_output(
        ["git", "rev-parse", "--verify", "--end-of-options", f"{base}^{{commit}}"],
        cwd=ROOT,
        text=True,
    ).strip()
    arguments = ["git", "diff", "--name-only", "--no-renames", "-z"]
    committed = subprocess.check_output([*arguments, f"{commit}...HEAD"], cwd=ROOT)
    working = subprocess.check_output(arguments, cwd=ROOT)
    staged = subprocess.check_output([*arguments, "--cached"], cwd=ROOT)
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=ROOT
    )
    return sorted(
        set((committed + working + staged + untracked).decode("utf-8").split("\0")) - {""}
    )


def verify(arguments: argparse.Namespace) -> None:
    from verify import check_coverage, run

    changed = changed_paths(arguments.base)
    scope = plan(ROOT, changed)
    covered_tests = [
        p for p in scope.tests if Path(p).name not in SERVER_TESTS | RELEASE_ONLY_TESTS
    ]
    server_tests = [p for p in scope.tests if Path(p).name in SERVER_TESTS]
    output = ROOT / "artifacts"
    output.mkdir(exist_ok=True)
    record = {
        "mode": "affected",
        "base": arguments.base,
        "changed": changed,
        **asdict(scope),
        "covered_tests": covered_tests,
        "server_tests": server_tests,
    }
    (output / "verification-scope.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(record, indent=2), flush=True)
    if arguments.plan:
        return
    os.environ["AP_RUNTIME_ROOT"] = str(Path(arguments.ap_root).resolve())
    run("-m", "ruff", "check", "src", "apworld", "tools", "tests")
    run("-m", "ruff", "format", "--check", "src", "apworld", "tools", "tests")
    if any(path.startswith("src/") for path in changed):
        run("-m", "mypy", "src/gamma_archipelago")
    if scope.web:
        for name in ("app.js", "ui.js", "form_state.js"):
            subprocess.run(["node", "--check", str(ROOT / "web/generator" / name)], check=True)
        subprocess.run(["node", "--test", str(ROOT / "tests/web/test_form_state.mjs")], check=True)
    if scope.build:
        run("tools/build.py")
    if scope.bootstrap:
        run(
            "tools/bootstrap_ap.py",
            "--source",
            arguments.ap_source,
            "--destination",
            arguments.ap_root,
        )
    if not scope.tests:
        print("No Python regressions selected; applicable static/Node checks passed.")
        return
    coverage = [f"--cov={module.removesuffix('.__init__')}" for module in scope.coverage]
    if coverage:
        # Package __init__ targets also trace unchanged children. The exact changed
        # modules retain their 95%/100% gates below; unrelated totals are not a gate.
        coverage.extend(
            [
                "--cov-branch",
                "--cov-report=term-missing",
                "--cov-report=json:coverage.json",
                "--cov-fail-under=0",
            ]
        )
    if covered_tests:
        run("-m", "pytest", "-q", *covered_tests, "-m", "not server and not generation", *coverage)
    elif coverage:
        raise SystemExit("Changed runtime modules need covered regression tests")
    if coverage:
        check_coverage(ROOT / "coverage.json", scope.coverage)
    # Include newly changed boundary tests even when the client source is unchanged.
    if server_tests:
        run("-m", "pytest", "-q", *server_tests, "-m", "server and not generation")
