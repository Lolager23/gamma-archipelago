from .test_start_menu import menu
from .test_tracker import state_for
from .test_tracker import view as tracker_view


def test_native_quest_facts_require_both_shutdown_flags_and_fail_closed(lua):
    module = lua.globals().gamma_ap_quest_routes
    assert module.facts() is False
    lua.execute("""
        flags={}
        has_alife_info=function(flag) return flags[flag] == true end
    """)
    assert module.facts() is False
    lua.globals().flags.yan_labx16_switcher_primary_off = True
    assert module.facts() is False
    lua.globals().flags.bar_deactivate_radar_done = True
    assert module.facts() is True


def test_tracker_north_waits_for_native_quests_even_with_every_zone_key_and_psi(lua):
    state = state_for(lua, rewards_zone_keys=1)
    for permission in lua.globals().gamma_ap_catalog.zone_keys.values():
        state.unlocks[permission] = True
    routes = lua.globals().gamma_ap_quest_routes
    tracker = lua.globals().gamma_ap_tracker
    assert routes.allowed(None, "l13_generators", False)
    assert routes.allowed(state.configuration, "l10_radar", False)
    assert routes.reason(state, "l13_generators")
    assert tracker.reachable(state, True)["l13_generators"] is None
    result = tracker_view(lua, state)
    assert any("Miracle Machine" in row.reason for row in result.rows.values())
    lua.execute("has_alife_info=function() return true end")
    assert tracker.reachable(state, True)["l13_generators"] is True
    assert routes.reason(state, "l13_generators") is None
    state.configuration.options.quest_zone_logic = 0
    assert routes.allowed(state.configuration, "l13_generators", False)


def test_quest_restricted_starts_require_native_story_controls_even_for_pilot(lua):
    window, engine = menu(lua, quest_zone_logic=1)
    assert window.OnStartGame(window) == "started"
    assert engine.story is True
    window.ck_story = None
    assert window.OnStartGame(window) is False
    assert engine.warning == "gamma_ap_start_unsupported"
