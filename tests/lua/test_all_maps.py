from gamma_archipelago.catalog import ALL_LOCATION_IDS, LOCATION_IDS, MAP_LOCATIONS
from gamma_archipelago.configuration import build_configuration, defaults, encode_configuration
from gamma_archipelago.protocol import decode_outgoing, encode_confirmed

from .test_game_adapter import saved_state
from .test_loadout import CONFIG_PATH, KEY, configured_game


def test_every_real_level_records_once_and_fake_or_unknown_levels_do_not(lua):
    module = lua.globals().gamma_ap_state
    state = module.new_state()
    state.session_key = KEY
    state.expanded = True
    for level in [*MAP_LOCATIONS, *MAP_LOCATIONS, "fake_start", "missing"]:
        module.check_level(state, level)
    snapshot = decode_outgoing(
        lua.globals().gamma_ap_protocol.encode_outgoing(state), KEY, ALL_LOCATION_IDS
    )
    assert snapshot.checked_locations == ALL_LOCATION_IDS
    assert snapshot.goal_complete
    copied = module.copy_state(state)
    assert copied.expanded is True
    assert len(list(copied.checks)) == 33
    state.checks[28052001] = None
    assert copied.checks[28052001] is True


def test_legacy_save_never_emits_new_map_ids_or_changes_its_three_map_goal(lua):
    module = lua.globals().gamma_ap_state
    state = module.new_state()
    state.session_key = KEY
    for level in MAP_LOCATIONS:
        module.check_level(state, level)
    # Even a stale extra saved check must not leak into a legacy snapshot.
    state.checks[28052004] = True
    snapshot = decode_outgoing(lua.globals().gamma_ap_protocol.encode_outgoing(state), KEY)
    assert snapshot.checked_locations == LOCATION_IDS and snapshot.goal_complete


def test_expanded_configuration_drives_live_adapter_and_survives_load(lua):
    game, engine, configuration = configured_game(lua)
    engine.files[CONFIG_PATH] = encode_configuration(KEY, configuration, expanded=True)
    engine.level = "k02_trucks_cemetery"
    game.actor_on_update()
    state = saved_state(lua, game).gamma_archipelago_v1
    assert state.expanded is True
    assert state.checks[MAP_LOCATIONS["k02_trucks_cemetery"]] is True
    game.load_state(lua.table(gamma_archipelago_v1=state))
    assert saved_state(lua, game).gamma_archipelago_v1.expanded is True
    parsed = lua.globals().gamma_ap_configuration.parse(
        encode_configuration(KEY, build_configuration(defaults()), expanded=True),
        KEY,
        configuration.digest,
    )
    assert parsed.expanded is True
    confirmed = lua.globals().gamma_ap_protocol.parse_confirmed(
        encode_confirmed(KEY, ALL_LOCATION_IDS), KEY
    )
    assert len(list(confirmed)) == 33
