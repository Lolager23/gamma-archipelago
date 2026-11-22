"""The fast path must select dependencies without silently losing regressions."""

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
scope = importlib.import_module("verification_scope")


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("docs/coding-standard.md", None),
        ("AGENTS.md", None),
        (".gitignore", None),
        (".codex/local.json", None),
        ("tests/unit/test_session.py", None),
        ("src/gamma_archipelago/catalog.json", "shared"),
        ("pyproject.toml", "shared"),
        ("requirements-ap.txt", "shared"),
        ("tests/conftest.py", "shared"),
        ("src/gamma_archipelago/session.py", "python"),
        ("src/gamma_archipelago/presets.py", "world"),
        ("src/gamma_archipelago/web_server.py", "web"),
        ("apworld/gamma/client.py", "client"),
        ("apworld/gamma/analysis.py", "world"),
        ("mod/gamedata/scripts/gamma_ap_state.script", "game"),
        ("probes/gamedata/scripts/gamma_ap_probe.script", "game"),
        ("web/generator/app.js", "web"),
        ("tools/verify.py", "tooling"),
        (".github/workflows/verify.yml", "tooling"),
        ("presets/full-story.yaml", "world"),
        ("tests/lua/test_tasks.py", "game"),
    ],
)
def test_explicit_component_boundaries(path, expected):
    assert scope.area(path) == expected


def test_unmapped_executable_input_is_actionable():
    with pytest.raises(ValueError, match="Unmapped verification input"):
        scope.area("new-runtime/worker.py")


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("src/gamma_archipelago/session.py", "gamma_archipelago.session"),
        ("apworld/gamma/analysis.py", "worlds.gamma.analysis"),
        ("apworld/gamma/__init__.py", "worlds.gamma.__init__"),
        ("tools/build.py", None),
        ("tools/verify.py", "verify"),
        ("tools/verification_scope.py", "verification_scope"),
        ("src/gamma_archipelago/catalog.json", None),
    ],
)
def test_coverage_targets_only_changed_runtime_modules(path, expected):
    assert scope.coverage_module(path) == expected


@pytest.fixture
def tree(tmp_path):
    names = [
        "tests/unit/test_session.py",
        "tests/unit/test_web_server.py",
        "tests/unit/test_git_identity.py",
        "tests/unit/test_verification_scope.py",
        "tests/integration/test_world.py",
        "tests/integration/test_client.py",
        "tests/integration/test_live_server.py",
        "tests/integration/test_web_generation.py",
        "tests/integration/test_packages.py",
        "tests/lua/test_state.py",
        "tests/lua/test_tasks.py",
        "src/gamma_archipelago/session.py",
        "apworld/gamma/analysis.py",
    ]
    for name in names:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()
    return tmp_path


def test_world_scope_excludes_native_and_network_components(tree):
    result = scope.plan(tree, ["apworld/gamma/analysis.py"])
    assert "tests/integration/test_world.py" in result.tests
    assert not any(path.startswith(("tests/unit/", "tests/lua/")) for path in result.tests)
    assert "tests/integration/test_client.py" not in result.tests
    assert result.coverage == ("worlds.gamma.analysis",)
    assert result.bootstrap and result.build and not result.web


def test_preset_change_selects_world_and_planner_consumers_without_network(tree):
    for name in ("test_presets.py", "test_web_planner.py"):
        (tree / "tests/unit" / name).touch()
    result = scope.plan(tree, ["src/gamma_archipelago/presets.py"])
    assert result.areas == ("world",)
    assert {"tests/unit/test_presets.py", "tests/unit/test_web_planner.py"} <= set(result.tests)
    assert "tests/unit/test_session.py" not in result.tests
    assert "tests/integration/test_client.py" not in result.tests


def test_python_change_includes_world_and_network_dependents(tree):
    result = scope.plan(tree, ["src/gamma_archipelago/session.py"])
    assert set(result.areas) == {"python", "world", "client"}
    assert "tests/unit/test_session.py" in result.tests
    assert "tests/integration/test_client.py" in result.tests
    assert not any(path.startswith("tests/lua/") for path in result.tests)


def test_shared_catalogue_covers_all_consuming_components(tree):
    result = scope.plan(tree, ["src/gamma_archipelago/catalog.json"])
    assert set(result.areas) == {"shared", "python", "world", "client", "game", "web", "tooling"}
    assert "tests/lua/test_state.py" in result.tests and result.web


def test_tooling_change_does_not_run_game_or_world(tree):
    result = scope.plan(tree, ["tools/verify.py"])
    assert set(result.tests) == {
        "tests/unit/test_git_identity.py",
        "tests/unit/test_verification_scope.py",
    }
    assert not result.bootstrap and not result.build and not result.web


def test_build_change_retains_real_package_loader(tree):
    result = scope.plan(tree, ["tools/build.py"])
    assert "tests/integration/test_packages.py" in result.tests
    assert result.bootstrap and result.build


def test_web_and_test_only_scopes(tree):
    result = scope.plan(tree, ["web/generator/ui.js"])
    assert result.web and "tests/unit/test_web_server.py" in result.tests
    assert "tests/unit/test_session.py" not in result.tests
    result = scope.plan(tree, ["tests/unit/test_session.py"])
    assert result.tests == ("tests/unit/test_session.py",)
    assert result.coverage == () and not result.bootstrap


def test_lua_fixture_keeps_its_existing_complete_line_gate(tree):
    result = scope.plan(tree, ["tests/lua/test_tasks.py"])
    assert set(result.tests) == {"tests/lua/test_tasks.py", "tests/lua/test_state.py"}


def test_docs_deleted_modules_and_empty_change_set(tree):
    assert scope.plan(tree, ["docs/testing.md"]).tests == ()
    assert scope.plan(tree, []).tests == ()
    result = scope.plan(tree, ["src/gamma_archipelago/deleted.py"])
    assert result.coverage == () and "tests/unit/test_session.py" in result.tests
