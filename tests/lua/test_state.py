import pytest

from gamma_archipelago.catalog import ITEM_SECTIONS, LOCATION_IDS
from gamma_archipelago.protocol import decode_outgoing, encode_incoming

KEY = "a" * 64
ITEMS = tuple(ITEM_SECTIONS)


def incoming(lua, ids=ITEMS, key=KEY):
    return lua.globals().gamma_ap_protocol.parse_incoming(encode_incoming(key, ids))


def test_lua_python_protocol_interoperability_and_duplicate_delivery(lua):
    module = lua.globals().gamma_ap_state
    state = module.new_state()
    sections = []

    def reward(section):
        sections.append(section)
        return True

    packet = incoming(lua)
    for _ in range(5):
        assert module.apply_pending(state, packet, reward) is True
    assert sections == [ITEM_SECTIONS[item] for item in ITEMS]
    assert state.received_count == 3
    module.check_level(state, "unknown-level")
    for name in ("l01_escape", "l02_garbage", "l05_bar", "l05_bar"):
        module.check_level(state, name)
    snapshot = decode_outgoing(lua.globals().gamma_ap_protocol.encode_outgoing(state), KEY)
    assert snapshot.checked_locations == LOCATION_IDS
    assert snapshot.goal_complete


def test_failed_creation_does_not_acknowledge_and_can_be_retried(lua):
    module = lua.globals().gamma_ap_state
    state = module.new_state()
    assert module.apply_pending(state, incoming(lua), lambda _: False)[0] is False
    assert state.received_count == 0
    assert module.apply_pending(state, incoming(lua), lambda _: True) is True
    assert state.received_count == 1


def test_save_snapshot_is_deep_copied_and_old_save_replays_only_missing_items(lua):
    module = lua.globals().gamma_ap_state
    state = module.new_state()
    assert module.apply_pending(state, incoming(lua), lambda _: True) is True
    module.check_level(state, "l01_escape")
    saved = module.copy_state(state)
    module.apply_pending(state, incoming(lua), lambda _: True)
    module.check_level(state, "l02_garbage")
    assert saved.received_count == 1
    assert saved.checks[min(LOCATION_IDS)] is True
    assert saved.checks[sorted(LOCATION_IDS)[1]] is None
    assert saved.applied_items[2] is None
    received = []
    assert module.apply_pending(
        saved, incoming(lua), lambda section: received.append(section) or True
    )
    assert received == [ITEM_SECTIONS[ITEMS[1]]]


def test_other_session_short_history_and_conflicting_receipts_are_rejected(lua):
    module = lua.globals().gamma_ap_state
    state = module.new_state()
    module.apply_pending(state, incoming(lua), lambda _: True)
    invalid = [incoming(lua, key="b" * 64), incoming(lua, ids=()), incoming(lua, ids=ITEMS[::-1])]
    for packet in invalid:
        assert (
            module.apply_pending(state, packet, lambda _: pytest.fail("No reward expected"))[0]
            is False
        )
        assert state.received_count == 1


def test_unrecognised_item_is_not_delivered_even_if_parser_is_bypassed(lua):
    state_module = lua.globals().gamma_ap_state
    packet = incoming(lua)
    packet["items"][1] = 42
    state = state_module.new_state()
    assert (
        state_module.apply_pending(state, packet, lambda _: pytest.fail("Not deliverable"))[0]
        is False
    )


@pytest.mark.parametrize(
    "content",
    [
        None,
        "",
        "x" * 131073 + "\n",
        "GAMMA_AP_IN|1\n",
        "GAMMA_AP_IN|2\nend|0\n",
        "GAMMA_AP_IN|1\nsession|bad\nend|0\n",
        "GAMMA_AP_IN|1\nsession|" + "A" * 64 + "\nend|0\n",
        encode_incoming(KEY, ()).replace("end|0", "end|1"),
        encode_incoming(KEY, ()).replace("end|0", "end|4001"),
        encode_incoming(KEY, ()).replace("end|0", "end|01"),
        encode_incoming(KEY, ITEMS[:1]).replace("item|0", "item|1"),
        encode_incoming(KEY, ITEMS[:1]).replace(str(ITEMS[0]), "42"),
        encode_incoming(KEY, ITEMS[:1]).replace("item|0", "item|00"),
        encode_incoming(KEY, ITEMS[:1]).replace("item|0", "item|12345678901"),
        encode_incoming(KEY, ITEMS[:1]).replace("item|0", "surprise|0"),
    ],
)
def test_lua_parser_rejects_incompatible_and_incomplete_data(lua, content):
    result = lua.globals().gamma_ap_protocol.parse_incoming(content)
    assert result[0] is None
    assert result[1]


def test_empty_crlf_history_binds_without_rewards(lua):
    packet = lua.globals().gamma_ap_protocol.parse_incoming(
        encode_incoming(KEY, ()).replace("\n", "\r\n")
    )
    state = lua.globals().gamma_ap_state.new_state()
    assert lua.globals().gamma_ap_state.apply_pending(state, packet, lambda _: pytest.fail("Empty"))
    assert not decode_outgoing(
        lua.globals().gamma_ap_protocol.encode_outgoing(state), KEY
    ).goal_complete
