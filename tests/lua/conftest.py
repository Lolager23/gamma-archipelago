import sys
from pathlib import Path

import pytest
from lupa.luajit21 import LuaRuntime

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import lua_coverage  # noqa: E402


@pytest.fixture
def lua():
    runtime = LuaRuntime(unpack_returned_tuples=True)
    runtime.execute("jit.off(); jit.flush()")
    runtime.execute(lua_coverage.TRACE_SETUP)
    loader = runtime.globals().load_ap_module
    for name in (
        "catalog",
        "paths",
        "protocol",
        "configuration",
        "start",
        "start_menu",
        "loadout_menu",
        "equipment",
        "equipment_classes",
        "tool_permissions",
        "tool_use",
        "loadout",
        "starting_supplies",
        "convenience",
        "deliveries",
        "upgrade_tools",
        "workshop",
        "discovery",
        "activity",
        "mutant_diversity",
        "progression_readiness",
        "quest_routes",
        "playability",
        "weather",
        "stamina",
        "combat",
        "collection",
        "tasks",
        "equipment_checks",
        "rank",
        "reputation",
        "skills",
        "quest_keys",
        "gear_locks",
        "equipment_use",
        "purchase_guard",
        "zone_recovery",
        "transition_geometry",
        "zone_keys",
        "travel",
        "goals",
        "goodwill_migration",
        "save_validation",
        "stashes",
        "stash_loot",
        "shop",
        "shop_ui",
        "state",
        "settlements",
        "settlement_access",
        "notice_text",
        "readiness",
        "notifications",
        "communication",
        "hints",
        "room",
        "tracker",
        "scout_protocol",
        "scouting",
        "services",
    ):
        path = ROOT / "mod/gamedata/scripts" / f"gamma_ap_{name}.script"
        runtime.globals()[f"gamma_ap_{name}"] = loader(str(path))
    yield runtime
    lua_coverage.collect(runtime)


def pytest_sessionfinish(session, exitstatus):
    if lua_coverage.EXPECTED and not lua_coverage.report():
        session.exitstatus = 1
