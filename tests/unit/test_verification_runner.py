"""Regression coverage for release routing, selection and unchanged module gates."""

import argparse
import importlib
import json
import runpy
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
runner = importlib.import_module("verify_changed")
verifier = importlib.import_module("verify")
selection = importlib.import_module("verification_scope")


def test_diff_includes_committed_staged_working_deleted_and_untracked(monkeypatch):
    calls = []

    def output(args, **kwargs):
        calls.append(args)
        if args[1] == "rev-parse":
            return "a" * 40 + "\n"
        if args[1] == "ls-files":
            return b"tests/unit/new_test.py\0"
        if "--cached" in args:
            return b"staged.py\0"
        if any("...HEAD" in arg for arg in args):
            return b"deleted.py\0working.py\0"
        return b"working.py\0"

    monkeypatch.setattr(runner.subprocess, "check_output", output)
    assert runner.changed_paths("origin/main") == [
        "deleted.py",
        "staged.py",
        "tests/unit/new_test.py",
        "working.py",
    ]
    assert "--no-renames" in calls[1] and "a" * 40 + "...HEAD" in calls[1]


@pytest.mark.parametrize("field", ["covered_lines", "covered_branches"])
@pytest.mark.parametrize(
    ("module", "required"), [("session", 100), ("protocol", 100), ("catalog", 95)]
)
def test_changed_runtime_modules_keep_independent_thresholds(tmp_path, field, module, required):
    summary = dict(covered_lines=100, num_statements=100, covered_branches=100, num_branches=100)
    path = tmp_path / "coverage.json"
    summary[field] = required
    path.write_text(
        json.dumps({"files": {f"src/gamma_archipelago/{module}.py": {"summary": summary}}})
    )
    verifier.check_coverage(path, (f"gamma_archipelago.{module}",))
    summary[field] -= 1
    path.write_text(
        json.dumps({"files": {f"src/gamma_archipelago/{module}.py": {"summary": summary}}})
    )
    with pytest.raises(SystemExit, match="required"):
        verifier.check_coverage(path, (f"gamma_archipelago.{module}",))


def test_missing_module_fails_and_unchanged_modules_do_not_gate(tmp_path):
    path = tmp_path / "coverage.json"
    summary = dict(covered_lines=0, num_statements=0, covered_branches=0, num_branches=0)
    path.write_text(
        json.dumps(
            {
                "files": {
                    "C:\\runtime\\worlds\\gamma\\analysis.py": {"summary": summary},
                    "unchanged.py": {"summary": summary | {"num_statements": 50}},
                }
            }
        )
    )
    verifier.check_coverage(path, ("worlds.gamma.analysis",))
    with pytest.raises(SystemExit, match="missing from coverage"):
        verifier.check_coverage(path, ("gamma_archipelago.session",))
    with pytest.raises(SystemExit, match="required"):
        verifier.check_coverage(path)


@pytest.fixture
def harness(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "changed_paths", lambda base: ["docs/testing.md"])
    monkeypatch.setattr(verifier, "run", lambda *args: calls.append(args))
    monkeypatch.setattr(
        verifier, "check_coverage", lambda *args: calls.append(("coverage-gate", *args))
    )
    monkeypatch.setattr(subprocess, "run", lambda args, **kwargs: calls.append(tuple(args)))
    return calls, argparse.Namespace(
        base="base", ap_root=str(tmp_path / "runtime"), ap_source="upstream", plan=False
    )


def test_plan_and_docs_do_not_launch_tests(harness, monkeypatch):
    calls, args = harness
    args.plan = True
    runner.verify(args)
    assert calls == []
    args.plan = False
    runner.verify(args)
    assert len(calls) == 2 and all("ruff" in call for call in calls)


def test_affected_runner_separates_covered_regressions_and_real_server(harness, monkeypatch):
    calls, args = harness
    monkeypatch.setattr(runner, "changed_paths", lambda base: ["src/gamma_archipelago/session.py"])
    chosen = selection.Scope(
        ("client",),
        ("tests/unit/test_session.py", "tests/integration/test_live_server.py"),
        ("gamma_archipelago.session",),
        True,
        True,
        True,
    )
    monkeypatch.setattr(runner, "plan", lambda *args: chosen)
    runner.verify(args)
    covered = next(call for call in calls if "--cov=gamma_archipelago.session" in call)
    assert "not server and not generation" in covered and "--cov-fail-under=0" in covered
    assert any("server and not generation" in call for call in calls)
    assert any(call[0] == "coverage-gate" and call[-1] == chosen.coverage for call in calls)
    assert any("mypy" in call for call in calls)
    assert sum(call[0] == "node" for call in calls) == 4


def test_test_only_runner_has_no_coverage_or_server_sweep(harness, monkeypatch):
    calls, args = harness
    monkeypatch.setattr(
        runner,
        "plan",
        lambda *args: selection.Scope(
            ("client",), ("tests/unit/test_session.py",), (), False, False, False
        ),
    )
    runner.verify(args)
    tests = [call for call in calls if "pytest" in call]
    assert len(tests) == 1 and not any(arg.startswith("--cov") for arg in tests[0])


def test_default_full_and_plan_cli_routes(harness, monkeypatch):
    calls, args = harness
    monkeypatch.setattr(sys, "argv", ["verify.py", "--base", "previous"])
    monkeypatch.setattr(runner, "verify", lambda options: calls.append(("affected", options.base)))
    verifier.main()
    assert calls == [("affected", "previous")]
    calls.clear()
    monkeypatch.setattr(sys, "argv", ["verify.py", "--full"])
    verifier.main()
    assert any("server or generation" in call for call in calls)
    assert any("not server and not generation" in call for call in calls)
    monkeypatch.setattr(sys, "argv", ["verify.py", "--full", "--plan"])
    with pytest.raises(SystemExit):
        verifier.main()


def test_workflow_only_runs_full_for_release_or_explicit_release_preparation():
    workflow = yaml.load(
        (ROOT / ".github/workflows/verify.yml").read_text(), Loader=yaml.BaseLoader
    )
    events = workflow["on"]
    assert events["push"]["branches"] == ["main"] and "pull_request" in events
    assert events["release"]["types"] == ["published"]
    assert events["workflow_dispatch"]["inputs"]["verification"]["default"] == "affected"
    step = next(s for s in workflow["jobs"]["verify"]["steps"] if s.get("name") == "Verify")
    assert "github.event_name == 'release'" in step["env"]["VERIFICATION_FULL"]
    assert "inputs.verification == 'full'" in step["env"]["VERIFICATION_FULL"]
    assert "pull_request.base.sha" in step["env"]["VERIFICATION_BASE"]
    assert "os.environ['AP_TOOL_SOURCE']" in step["run"]
    assert "['--full']" in step["run"] and "['--base'," in step["run"]


def test_command_wrapper_and_script_entrypoint(harness, monkeypatch):
    calls, args = harness
    original_run = importlib.reload(verifier).run
    original_run("-m", "ruff", "check")
    assert calls[-1] == (sys.executable, "-m", "ruff", "check")
    monkeypatch.setattr(sys, "argv", ["verify.py", "--base", "parent"])
    monkeypatch.setattr(runner, "verify", lambda options: calls.append(("entry", options.base)))
    runpy.run_path(str(ROOT / "tools/verify.py"), run_name="__main__")
    assert calls[-1] == ("entry", "parent")


def test_boundary_only_and_release_only_edits_do_not_run_empty_covered_pass(harness, monkeypatch):
    calls, args = harness
    monkeypatch.setattr(
        runner,
        "plan",
        lambda *a: selection.Scope(
            (), ("tests/integration/test_live_server.py",), (), False, False, False
        ),
    )
    runner.verify(args)
    tests = [call for call in calls if "pytest" in call]
    assert len(tests) == 1 and "server and not generation" in tests[0]
    calls.clear()
    monkeypatch.setattr(
        runner,
        "plan",
        lambda *a: selection.Scope(
            (), ("tests/integration/test_expansion_two_matrix.py",), (), False, False, False
        ),
    )
    runner.verify(args)
    assert not any("pytest" in call for call in calls)
    calls.clear()
    monkeypatch.setattr(
        runner,
        "plan",
        lambda *a: selection.Scope(
            (),
            ("tests/integration/test_expansion_two_matrix.py",),
            ("gamma_archipelago.session",),
            False,
            False,
            False,
        ),
    )
    with pytest.raises(SystemExit, match="covered regression tests"):
        runner.verify(args)
