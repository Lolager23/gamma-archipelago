"""Explicit component boundaries for normal development verification."""

from dataclasses import dataclass
from pathlib import Path

NETWORK_TESTS = {
    "test_client.py",
    "test_causal_client.py",
    "test_presence_client.py",
    "test_scouting_client.py",
    "test_live_server.py",
    "test_expanded_server.py",
    "test_goal_release.py",
}
SERVER_TESTS = {"test_live_server.py", "test_expanded_server.py", "test_goal_release.py"}
RELEASE_ONLY_TESTS = {
    "test_expansion_two_matrix.py",
    "test_preview_archive.py",
    "test_web_generation.py",
}
TOOL_TESTS = {
    "test_cli_source.py",
    "test_git_identity.py",
    "test_lua_coverage.py",
    "test_package_sources.py",
    "test_probe_cli_checkout.py",
    "test_probe_sources.py",
    "test_probe_tools.py",
    "test_probe_report.py",
    "test_release_candidate.py",
    "test_shop_icon.py",
    "test_stash_icon.py",
    "test_verification_scope.py",
    "test_verification_runner.py",
}


@dataclass(frozen=True)
class Scope:
    areas: tuple[str, ...]
    tests: tuple[str, ...]
    coverage: tuple[str, ...]
    bootstrap: bool
    build: bool
    web: bool


def area(path: str) -> str | None:
    """Unknown executable inputs require an explicit mapping, never a silent skip."""
    if path in {"pyproject.toml", "requirements-ap.txt", "tests/conftest.py"}:
        return "shared"
    if path.startswith("src/gamma_archipelago/"):
        if Path(path).name == "catalog.json":
            return "shared"
        if Path(path).name == "presets.py":
            return "world"
        return "web" if Path(path).name.startswith("web_") else "python"
    if path.startswith("apworld/gamma/"):
        return (
            "client"
            if Path(path).stem in {"client", "notices", "scouting", "presence"}
            else "world"
        )
    if path.startswith(("mod/", "probes/")):
        return "game"
    if path.startswith("web/"):
        return "web"
    if path.startswith(("tools/", ".github/workflows/")):
        return "tooling"
    if path.startswith("presets/"):
        return "world"
    if path.startswith("tests/"):
        return "game" if path.startswith("tests/lua/") else None
    if path.startswith(("docs/", ".githooks/", ".codex/")) or path.endswith((".md", ".txt")):
        return None
    if path in {".gitignore", ".gitattributes", ".editorconfig"}:
        return None
    raise ValueError(f"Unmapped verification input: {path}; add its affected component")


def coverage_module(path: str) -> str | None:
    if not path.endswith(".py"):
        return None
    if path.startswith("src/gamma_archipelago/"):
        return path.removeprefix("src/").removesuffix(".py").replace("/", ".")
    if path.startswith("apworld/gamma/"):
        return path.replace("apworld/", "worlds/", 1).removesuffix(".py").replace("/", ".")
    if path in {"tools/verify.py", "tools/verify_changed.py", "tools/verification_scope.py"}:
        return Path(path).stem
    return None


def plan(root: Path, changed: list[str]) -> Scope:
    areas = {selected for path in changed if (selected := area(path))}
    if "shared" in areas:
        areas.update({"python", "world", "client", "game", "web", "tooling"})
    if "python" in areas:
        areas.update({"world", "client"})
    files = {p.relative_to(root).as_posix() for p in (root / "tests").rglob("test_*.py")}
    tests = {path for path in changed if path in files}
    tool_tests = TOOL_TESTS | {
        f"test_{Path(path).stem}.py" for path in changed if path.startswith("tools/")
    }
    for path in files:
        name = Path(path).name
        if "python" in areas and path.startswith("tests/unit/"):
            tests.add(path)
        if "world" in areas and path.startswith("tests/integration/") and name not in NETWORK_TESTS:
            tests.add(path)
        if "world" in areas and name in {"test_presets.py", "test_web_planner.py"}:
            tests.add(path)
        if "client" in areas and (path.startswith("tests/unit/") or name in NETWORK_TESTS):
            tests.add(path)
        if "game" in areas and path.startswith("tests/lua/"):
            tests.add(path)
        if "web" in areas and name.startswith(("test_web_", "test_presets")):
            tests.add(path)
        if "tooling" in areas and name in tool_tests:
            tests.add(path)
    if any(path in changed for path in ("tools/build.py", "tools/bootstrap_ap.py")):
        tests.add("tests/integration/test_packages.py")
    # The shared Lua fixture loads all native modules and gates their coverage.
    # Keep that small adapter suite intact instead of weakening its collector.
    if any(path.startswith("tests/lua/") for path in tests):
        tests.update(path for path in files if path.startswith("tests/lua/"))
    existing = [path for path in changed if (root / path).is_file()]
    coverage = tuple(sorted({module for path in existing if (module := coverage_module(path))}))
    # This native tracker test compares PDA availability with real APWorld rules.
    bootstrap = "tests/lua/test_activity.py" in tests or any(
        path.startswith("tests/integration/") for path in tests
    )
    build = bootstrap or bool(areas & {"game", "world", "shared"})
    return Scope(
        tuple(sorted(areas)),
        tuple(sorted(tests)),
        coverage,
        bootstrap,
        build,
        "web" in areas or any(path.startswith("tests/web/") for path in changed),
    )
