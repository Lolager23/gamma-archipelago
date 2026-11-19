import pytest

from gamma_archipelago.catalog import ITEM_SECTIONS, LOCATION_IDS, MAX_ITEMS
from gamma_archipelago.protocol import ProtocolError, decode_outgoing, encode_incoming

KEY = "a" * 64
ITEM = next(iter(ITEM_SECTIONS))
LOCATION = min(LOCATION_IDS)


def outgoing(*, key=KEY, received=0, checks=(), goal=0):
    return "\n".join(
        ["GAMMA_AP_OUT|1", f"session|{key}", f"received|{received}"]
        + [f"check|{value}" for value in checks]
        + [f"goal|{goal}", f"end|{len(checks)}", ""]
    )


def test_round_trip_game_observation():
    state = decode_outgoing(outgoing(received=1, checks=[LOCATION]), KEY)
    assert state.received_count == 1
    assert state.checked_locations == {LOCATION}
    assert not state.goal_complete


def test_empty_and_complete_snapshots():
    assert not decode_outgoing(outgoing(), KEY).checked_locations
    assert decode_outgoing(outgoing(checks=sorted(LOCATION_IDS), goal=1), KEY).goal_complete


def test_incoming_history_has_stable_zero_based_indexes():
    assert encode_incoming(KEY, (ITEM, ITEM)) == (
        f"GAMMA_AP_IN|1\nsession|{KEY}\nitem|0|{ITEM}\nitem|1|{ITEM}\nend|2\n"
    )
    assert encode_incoming(KEY, ()).endswith("end|0\n")


@pytest.mark.parametrize("key", ["", "a" * 63, "A" * 64, "x" * 64, "a" * 65, "a\n" * 32])
def test_rejects_invalid_session_key(key):
    with pytest.raises(ProtocolError):
        encode_incoming(key, ())
    with pytest.raises(ProtocolError):
        decode_outgoing(outgoing(), key)


@pytest.mark.parametrize("items", [(123,), (ITEM,) * (MAX_ITEMS + 1)])
def test_rejects_unsupported_or_unbounded_incoming_history(items):
    with pytest.raises(ProtocolError):
        encode_incoming(KEY, items)


@pytest.mark.parametrize(
    "content",
    [
        "",
        outgoing()[:-1],
        "x" * 131073 + "\n",
        outgoing().replace("GAMMA_AP_OUT|1", "GAMMA_AP_OUT|2"),
        outgoing(key="b" * 64),
        outgoing().replace("received|0", "receipt|0"),
        outgoing().replace("goal|0", "goal|2"),
        outgoing().replace("end|0", "end|1"),
        outgoing().replace("goal|0", "unknown|42\ngoal|0"),
        outgoing(checks=[LOCATION, LOCATION]),
        outgoing(checks=[42]),
        outgoing(checks=[LOCATION], goal=1),
        outgoing(received=4001),
    ],
)
def test_rejects_malformed_and_wrong_session_snapshots(content):
    with pytest.raises(ProtocolError):
        decode_outgoing(content, KEY)


@pytest.mark.parametrize("number", ["-1", "+1", "01", "1.0", "", "12345678901", "1|2"])
def test_received_count_is_a_canonical_integer(number):
    with pytest.raises(ProtocolError):
        decode_outgoing(outgoing(received=number), KEY)


def test_crlf_snapshot_is_readable():
    assert decode_outgoing(outgoing().replace("\n", "\r\n"), KEY).received_count == 0


def test_alternate_goal_wire_is_bound_to_its_selected_goal_instead_of_pilot_checks(tmp_path):
    from gamma_archipelago.bridge import FileBridge

    content = outgoing(checks=[LOCATION], goal=1).replace("GAMMA_AP_OUT|1", "GAMMA_AP_OUT|2")
    assert decode_outgoing(content, KEY, pilot_goal=False).goal_complete
    with pytest.raises(ProtocolError, match="Unsupported"):
        decode_outgoing(content, KEY)
    with pytest.raises(ProtocolError, match="Unsupported"):
        decode_outgoing(outgoing(), KEY, pilot_goal=False)
    bridge = FileBridge(tmp_path, allowed_root=tmp_path)
    bridge.pilot_goal = False
    (bridge.directory / "outgoing.txt").write_text(content)
    assert bridge.read_game(KEY).goal_complete


@pytest.mark.parametrize("pilot_goal", [True, False])
def test_configured_snapshots_bind_the_digest_before_accepting_checks_or_goals(pilot_goal):
    digest = "b" * 64
    content = (
        outgoing(checks=LOCATION_IDS, goal=1)
        .replace("GAMMA_AP_OUT|1", "GAMMA_AP_OUT|3")
        .replace(f"session|{KEY}\n", f"session|{KEY}\nconfiguration|{digest}\n")
    )
    snapshot = decode_outgoing(content, KEY, configuration_key=digest, pilot_goal=pilot_goal)
    assert snapshot.checked_locations == LOCATION_IDS and snapshot.goal_complete
    for invalid in (
        content.replace(digest, "c" * 64),
        content.replace(f"configuration|{digest}\n", ""),
        content.replace("configuration|", "settings|"),
        content.replace("received|0", f"configuration|{digest}\nreceived|0"),
        outgoing(),
    ):
        with pytest.raises(ProtocolError):
            decode_outgoing(invalid, KEY, configuration_key=digest, pilot_goal=pilot_goal)
    with pytest.raises(ProtocolError):
        decode_outgoing(content, KEY)


@pytest.mark.parametrize("digest", ["", "x" * 64, "A" * 64])
def test_configured_snapshot_expected_digest_is_validated(digest):
    with pytest.raises(ProtocolError):
        decode_outgoing(outgoing(), KEY, configuration_key=digest)
