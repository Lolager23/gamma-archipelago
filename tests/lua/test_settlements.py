import pytest

from gamma_archipelago.catalog import MAP_LOCATION_IDS, enabled_location_ids
from gamma_archipelago.configuration import encode_configuration
from gamma_archipelago.protocol import ProtocolError, decode_outgoing, encode_confirmed

from .assertions import assert_lua_error
from .test_game_adapter import saved_state
from .test_loadout import CONFIG_PATH, KEY, configured_game


def configured_settlements(lua, *, maps=0):
    game, engine, configuration = configured_game(lua, checks_maps=maps, checks_settlements=1)
    engine.files[CONFIG_PATH] = encode_configuration(KEY, configuration, expanded=True)
    game.actor_on_update()
    return game, engine, configuration


def smart(lua, name, *, online=True, distance=50):
    return lua.table(
        name=lua.eval(f"function() return '{name}' end"),
        online=online,
        dist_to_actor=distance,
    )


def test_every_named_hub_and_alias_is_finite_deduplicated_and_saved(lua):
    game, engine, configuration = configured_settlements(lua)
    for name, definition in lua.globals().gamma_ap_catalog.settlements.items():
        engine.level = definition.level
        for _ in range(2):
            game.actor_on_interaction("smarts", smart(lua, name), name)
    state = saved_state(lua, game).gamma_archipelago_v1
    expected = enabled_location_ids(configuration.checks)
    assert set(state.checks.keys()) == expected
    assert len(expected) == 18
    game.load_state(lua.table(gamma_archipelago_v1=state))
    assert set(saved_state(lua, game).gamma_archipelago_v1.checks.keys()) == expected
    assert set(state.enabled_checks.keys()) == expected


@pytest.mark.parametrize("distance", [-1, 50.001, float("inf"), float("nan"), "50", None])
def test_callback_requires_actual_bounded_entry_distance(lua, distance):
    game, _, _ = configured_settlements(lua)
    name = "esc_smart_terrain_2_12"
    game.actor_on_interaction("smarts", smart(lua, name, distance=distance), name)
    assert not list(saved_state(lua, game).gamma_archipelago_v1.checks.keys())


def test_wrong_level_object_type_name_and_dead_actor_cannot_trigger_hub(lua):
    game, engine, _ = configured_settlements(lua)
    name = "esc_smart_terrain_2_12"
    object_ = smart(lua, name)
    game.actor_on_interaction("notes", object_, name)
    game.actor_on_interaction("smarts", object_, "unknown")
    game.actor_on_interaction("smarts", None, name)
    game.actor_on_interaction("smarts", smart(lua, name, online=False), name)
    game.actor_on_interaction("smarts", smart(lua, "wrong"), name)
    engine.level = "l05_bar"
    game.actor_on_interaction("smarts", object_, name)
    engine.level = "l01_escape"
    engine.alive = False
    game.actor_on_interaction("smarts", object_, name)
    lua.globals().db.actor = None
    game.actor_on_interaction("smarts", object_, name)
    assert not list(saved_state(lua, game).gamma_archipelago_v1.checks.keys())


def test_disabled_category_legacy_and_unbound_state_do_not_record_settlements(lua):
    module = lua.globals().gamma_ap_settlements
    state = lua.globals().gamma_ap_state.new_state()
    name = "esc_smart_terrain_2_12"
    object_ = smart(lua, name)
    module.observe(state, "smarts", object_, name, "l01_escape")
    state.session_key = KEY
    module.observe(state, "smarts", object_, name, "l01_escape")
    state.expanded = True
    module.observe(state, "smarts", object_, name, "l01_escape")
    assert not list(state.checks.keys())


def test_goal_observation_is_independent_of_map_checks_and_disabled_confirmations_fail(lua):
    game, engine, configuration = configured_settlements(lua)
    for level_name in ("l01_escape", "l02_garbage", "l05_bar"):
        engine.now += 1000
        engine.level = level_name
        game.actor_on_update()
    allowed = enabled_location_ids(configuration.checks)
    outgoing = engine.files["D:/AnomalyAP/appdata/archipelago\\outgoing.txt"]
    snapshot = decode_outgoing(outgoing, KEY, allowed, configuration_key=configuration.digest)
    assert snapshot.goal_complete and not snapshot.checked_locations
    state = saved_state(lua, game).gamma_archipelago_v1
    assert set(state.visited_maps.keys()) >= {28052001, 28052002, 28052003}
    with pytest.raises(ProtocolError):
        decode_outgoing(
            outgoing.replace("goal|1", "check|28052001\ngoal|1"),
            KEY,
            allowed,
            configuration_key=configuration.digest,
        )
    assert_lua_error(
        lua.globals().gamma_ap_protocol.parse_confirmed(
            encode_confirmed(KEY, MAP_LOCATION_IDS), KEY, state.enabled_checks
        )
    )
    assert allowed.isdisjoint(MAP_LOCATION_IDS) and len(allowed) == 18
