from dataclasses import replace

import pytest

from gamma_archipelago.bridge import FileBridge
from gamma_archipelago.protocol import ProtocolError
from gamma_archipelago.scouting import (
    MAX_SCOUT_BYTES,
    MAX_SCOUTS,
    ScoutedReward,
    decode_requests,
    encode_scouted,
)

KEY, CONFIG, EPOCH = "a" * 64, "b" * 64, "c" * 16
ALLOWED = frozenset({28052001, 28052002})
REWARD = ScoutedReward(28052001, 2, 1, "Friend", "Toolkit")


def requests(*ids, key=KEY, configuration=CONFIG):
    return "\n".join(
        [
            "GAMMA_AP_SCOUTS|1",
            f"session|{key}",
            f"configuration|{configuration}",
            *(f"request|{identity}" for identity in ids),
            f"end|{len(ids)}",
            "",
        ]
    )


@pytest.mark.parametrize(
    "content",
    [
        "bad",
        "x" * (MAX_SCOUT_BYTES + 1),
        requests(28052001)[:-1],
        "é\n",
        requests(key="d" * 64),
        requests(configuration="d" * 64),
        requests(28052001, 28052001),
        requests(999),
        requests(28052001).replace("request|28052001", "request|028052001"),
        requests().replace("end|0", "end|00"),
        requests(*range(1, MAX_SCOUTS + 2)),
    ],
)
def test_malformed_stale_or_disabled_scouts_are_refused(content):
    with pytest.raises(ProtocolError):
        decode_requests(content, KEY, CONFIG, ALLOWED)


def test_requests_are_bounded_and_bind_both_session_and_configuration():
    assert decode_requests(requests(), KEY, CONFIG, ALLOWED) == frozenset()
    assert decode_requests(requests(28052001, 28052002), KEY, CONFIG, ALLOWED) == ALLOWED
    with pytest.raises(ProtocolError):
        decode_requests(requests(), "bad", CONFIG, ALLOWED)


@pytest.mark.parametrize(
    ("epoch", "sequence"), [("bad", 0), (EPOCH, True), (EPOCH, -1), (EPOCH, 10**10), (EPOCH, 1.2)]
)
def test_invalid_heartbeat_is_rejected(epoch, sequence):
    with pytest.raises(ProtocolError):
        encode_scouted(KEY, CONFIG, epoch, sequence, ())


@pytest.mark.parametrize(
    "reward",
    [
        replace(REWARD, location=0),
        replace(REWARD, recipient=0),
        replace(REWARD, flags=8),
        replace(REWARD, flags=True),
        replace(REWARD, player=""),
        replace(REWARD, item="%c[red]"),
        replace(REWARD, item="x" * 97),
        replace(REWARD, player=1),
    ],
)
def test_bad_ids_flags_and_labels_never_cross_the_display_bridge(reward):
    with pytest.raises(ProtocolError):
        encode_scouted(KEY, CONFIG, EPOCH, 0, (reward,))


def test_metadata_preserves_safe_unicode_opaque_labels_and_does_not_encode_receipts():
    content = encode_scouted(
        KEY, CONFIG, EPOCH, 3, (replace(REWARD, player="Оуэн", item="{player} Toolkit"),)
    )
    assert "Оуэн".encode().hex() in content and "heartbeat|" + EPOCH + "|3" in content
    assert "received|" not in content and "check|" not in content
    for invalid in ((REWARD, REWARD), (REWARD,) * (MAX_SCOUTS + 1)):
        with pytest.raises(ProtocolError):
            encode_scouted(KEY, CONFIG, EPOCH, 1, invalid)
    maximum = tuple(
        replace(REWARD, location=index + 1, player="🦊" * 96, item="🦊" * 96)
        for index in range(MAX_SCOUTS)
    )
    assert len(encode_scouted(KEY, CONFIG, EPOCH, 1, maximum)) < MAX_SCOUT_BYTES


def test_file_bridge_reads_only_the_owned_snapshot_and_publishes_atomically(tmp_path):
    bridge = FileBridge(tmp_path, allowed_root=tmp_path)
    assert bridge.read_scout_requests(KEY, CONFIG, ALLOWED) == frozenset()
    source = bridge.directory / "scout_requests.txt"
    source.write_text(requests(28052001), encoding="ascii")
    assert bridge.read_scout_requests(KEY, CONFIG, ALLOWED) == {28052001}
    source.write_bytes(b"\xff")
    with pytest.raises(ProtocolError, match="ASCII"):
        bridge.read_scout_requests(KEY, CONFIG, ALLOWED)
    bridge.write_scouted(KEY, CONFIG, EPOCH, 1, (REWARD,))
    assert (bridge.directory / "scouted_items.txt").read_text() == encode_scouted(
        KEY, CONFIG, EPOCH, 1, (REWARD,)
    )
    assert not (bridge.directory / "scouted_items.tmp").exists()
