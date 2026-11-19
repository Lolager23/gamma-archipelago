from dataclasses import replace

import pytest

from gamma_archipelago.configuration import encode_configuration
from gamma_archipelago.scouting import ScoutedReward, decode_requests, encode_scouted

from .assertions import assert_lua_error
from .test_game_adapter import saved_state
from .test_loadout import CONFIG_PATH, configured_game
from .test_tracker import KEY, state_for

EPOCH = "c" * 16
REQUEST_PATH = "D:/AnomalyAP/appdata/archipelago\\scout_requests.txt"
INFO_PATH = "D:/AnomalyAP/appdata/archipelago\\scouted_items.txt"
REWARD = ScoutedReward(28052001, 2, 1, "Friend", "Toolkit")


def packet(state, sequence=1, rewards=(REWARD,), epoch=EPOCH):
    return encode_scouted(KEY, state.configuration_key, epoch, sequence, rewards)


def ready_state(lua, **options):
    state = state_for(lua, **options)
    state.configuration_key = state.configuration.digest
    return state


def test_request_roundtrip_limits_and_legacy_save_copy(lua):
    module = lua.globals().gamma_ap_scouting
    codec = lua.globals().gamma_ap_scout_protocol
    state = ready_state(lua, scouting_mode=1)
    assert module.request(state, 28052001)[0] is True
    assert module.request(state, 999)[0] is False
    assert decode_requests(
        codec.requests(state), KEY, state.configuration_key, frozenset(state.enabled_checks.keys())
    ) == {28052001}
    copied = lua.globals().gamma_ap_state.copy_state(state)
    assert copied.scout_requests[28052001]
    assert lua.globals().gamma_ap_save_validation.validate(copied) is True
    copied.scout_requests = None
    assert lua.globals().gamma_ap_save_validation.validate(copied) is True
    assert not list(lua.globals().gamma_ap_state.copy_state(copied).scout_requests.keys())
    copied.scout_requests = "bad"
    assert lua.globals().gamma_ap_save_validation.validate(copied)[0] is False
    copied.scout_requests = lua.table_from({999: True})
    assert lua.globals().gamma_ap_save_validation.validate(copied)[0] is False
    state.scout_requests = lua.table_from({index: True for index in range(1, 514)})
    assert_lua_error(codec.requests(state))
    assert module.request(state, 28052002)[0] is False
    state.scout_requests[28052001] = True
    assert module.request(state, 28052001)[0] is True
    assert module.request(ready_state(lua), 28052001)[0] is False


def test_information_roundtrips_unicode_and_cannot_complete_checks_or_receipts(lua):
    state = ready_state(lua)
    codec = lua.globals().gamma_ap_scout_protocol
    frame = codec.parse(
        packet(state, rewards=(replace(REWARD, player="Оуэн"),)),
        KEY,
        state.configuration_key,
        state.enabled_checks,
    )
    assert frame.rewards[28052001].player == "Оуэн"
    assert state.received_count == 0 and not list(state.checks.items())


@pytest.mark.parametrize(
    "mutation",
    [
        lambda text: text[:-1],
        lambda text: "x" * 1048577,
        lambda text: text.replace("SCOUTED|1", "SCOUTED|2"),
        lambda text: text.replace("session|" + KEY, "session|" + "d" * 64),
        lambda text: text.replace("configuration|", "wrong|"),
        lambda text: text.replace(EPOCH, "bad"),
        lambda text: text.replace("|1\nitem", "|01\nitem"),
        lambda text: text.replace("end|1", "end|2"),
        lambda text: text.replace("end|1", "end|513"),
        lambda text: text.replace("item|28052001", "item|999"),
        lambda text: text.replace("|2|1|", "|0|1|"),
        lambda text: text.replace("|2|1|", "|2|8|"),
        lambda text: text.replace("467269656e64", "f"),
        lambda text: text.replace("467269656e64", "25"),
        lambda text: text.replace("467269656e64", "61" * 385),
        lambda text: text.replace("end|1", text.splitlines()[4] + "\nend|2"),
    ],
)
def test_malformed_or_cross_session_metadata_is_refused(lua, mutation):
    state = ready_state(lua)
    assert_lua_error(
        lua.globals().gamma_ap_scout_protocol.parse(
            mutation(packet(state)), KEY, state.configuration_key, state.enabled_checks
        )
    )


def test_cached_information_requires_an_advancing_heartbeat_and_expires(lua):
    game, engine, configuration = configured_game(lua, scouting_mode=1)
    engine.files[CONFIG_PATH] = encode_configuration(KEY, configuration, expanded=True)
    game.actor_on_update()
    state = saved_state(lua, game).gamma_archipelago_v1
    engine.files[INFO_PATH] = packet(state, 1)
    assert "Cached" in game.tracker_view().connection_status
    engine.files[INFO_PATH] = packet(state, 2)
    assert "active" in game.tracker_view().connection_status
    engine.now = 0
    assert "Cached" in game.tracker_view().connection_status
    engine.now = 1000
    engine.now += 5001
    assert "Cached" in game.tracker_view().connection_status
    engine.files[INFO_PATH] = packet(state, 1)
    assert "Outdated" in game.tracker_view().connection_status
    engine.files[INFO_PATH] = packet(state, 1, epoch="e" * 16)
    assert "Cached" in game.tracker_view().connection_status
    engine.files[INFO_PATH] = "broken\n"
    assert "mismatch" in game.tracker_view().connection_status.lower()
    engine.fail_close = True
    assert "close failed" in game.tracker_view().connection_status
    engine.fail_close = False
    engine.root = "D:/Anomaly/appdata/"
    assert "isolated" in game.tracker_view().connection_status
    assert game.request_scout(28052002)[0] is False


def test_requests_are_written_immediately_and_errors_never_create_rewards(lua):
    game, engine, configuration = configured_game(lua, scouting_mode=1)
    engine.files[CONFIG_PATH] = encode_configuration(KEY, configuration, expanded=True)
    game.actor_on_update()
    assert game.request_scout(999)[0] is False
    assert game.request_scout(28052002)[0] is True
    assert "request|28052002" in engine.files[REQUEST_PATH]
    before = len(engine.created)
    for failure in ("fail_open", "fail_write", "fail_close"):
        engine[failure] = True
        assert game.request_scout(28052002)[0] is False
        engine[failure] = False
    assert len(engine.created) == before
    state = saved_state(lua, game).gamma_archipelago_v1
    state.scout_requests = lua.table_from({index: True for index in range(1, 514)})
    assert lua.globals().gamma_ap_scouting.write_requests(state)[0] is False


def test_next_side_task_and_faction_previews_advance_from_real_completed_checks(lua):
    module = lua.globals().gamma_ap_scouting
    state = ready_state(
        lua, checks_side_task_milestones=1, checks_faction_standing=1, reward_previews=1
    )
    previews = list(module.previews(state).values())
    assert len(previews) == 2
    previous = [row.id for row in previews]
    for identity in previous:
        state.checks[identity] = True
    assert all(
        row.id > old for row, old in zip(module.previews(state).values(), previous, strict=True)
    )
    for identity in state.enabled_checks:
        state.checks[identity] = True
    assert not list(module.previews(state).values())


def test_optional_scout_file_failure_does_not_block_normal_reward_application(lua):
    game, engine, configuration = configured_game(lua, scouting_mode=1)
    engine.files[CONFIG_PATH] = encode_configuration(KEY, configuration, expanded=True)
    lua.execute("gamma_ap_scouting.io={open=function() return nil end}")
    game.actor_on_update()
    assert saved_state(lua, game).gamma_archipelago_v1.received_count == 1
    assert "scouting requests" in list(engine.logs.values())[-1]


def test_older_save_can_open_tracker_before_the_first_new_configuration_poll(lua):
    game, engine, _ = configured_game(lua)
    game.actor_on_update()
    data = saved_state(lua, game)
    data.gamma_archipelago_v1.configuration.options.scouting_mode = None
    game.load_state(data)
    assert game.tracker_view().scouting_enabled is False
    assert game.request_scout(28052002)[0] is False
