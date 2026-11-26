import pytest

from gamma_archipelago.bridge import FileBridge
from gamma_archipelago.game_commands import decode_requests, encode_status
from gamma_archipelago.protocol import ProtocolError

KEY, EPOCH, GAME = "a" * 64, "b" * 16, "c" * 16


def request(sequence=1, kind="loaded", text="", configuration=None):
    return (
        f"GAMMA_AP_COMMANDS|1\nsession|{KEY}\nconfiguration|{configuration or '-'}\n"
        f"game|{GAME}\ntarget|{EPOCH}\nrequest|{sequence}|{kind}|{text.encode().hex()}\nend|1\n"
    )


def status(**changes):
    fields = dict(
        key=KEY,
        configuration=None,
        epoch=EPOCH,
        heartbeat=1,
        connected=True,
        address="localhost:4444",
        game_epoch=None,
        acknowledged=0,
        confirmed=3,
        hint_points=4,
        hint_cost=10,
        total=100,
    )
    return encode_status(**(fields | changes))


def test_requests_and_status_roundtrip_and_bridge_io(tmp_path):
    root = tmp_path / "dev"
    root.mkdir()
    bridge = FileBridge(root, allowed_root=root)
    assert bridge.read_commands(KEY, EPOCH) is None
    source = bridge.directory / "game_requests.txt"
    source.write_text(request(), encoding="ascii")
    game, commands = bridge.read_commands(KEY, EPOCH)
    assert game == GAME and commands[0].kind == "loaded"
    assert bridge.read_commands(KEY, "d" * 16) is None
    assert (
        decode_requests(request(2, "say", "!hint PDA", KEY), KEY, KEY, EPOCH)[1][0].text
        == "!hint PDA"
    )
    bridge.write_connection_status(
        KEY,
        EPOCH,
        1,
        connected=True,
        address="host",
        game_epoch=GAME,
        acknowledged=1,
        confirmed=3,
        hint_points=4,
        hint_cost=10,
        total=100,
    )
    assert (bridge.directory / "connection_status.txt").read_text().endswith("end|1\n")
    assert "connection|1|" in status(configuration=KEY, game_epoch=GAME)
    source.write_bytes(b"\xff")
    with pytest.raises(ProtocolError, match="ASCII"):
        bridge.read_commands(KEY, EPOCH)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda s: s[:-1],
        lambda s: "x" * 40001,
        lambda s: "\n",
        lambda s: s.replace("COMMANDS|1", "COMMANDS|2"),
        lambda s: s.replace("game|", "other|"),
        lambda s: s.replace(GAME, "x" * 16),
        lambda s: s.replace("end|1", "end|0"),
        lambda s: s.replace("request|1|", "request|01|"),
        lambda s: s.replace("request|1|", "request|0|"),
        lambda s: s.replace("loaded", "exec"),
        lambda s: s.replace("request|1|loaded|", "request|1|say"),
        lambda s: s.replace("loaded|", "say|ff"),
        lambda s: s.replace("loaded|", "say|a"),
        lambda s: s.replace("loaded|", "say|00"),
        lambda s: s.replace("loaded|", "say|7f"),
        lambda s: s.replace("loaded|", "say|" + "61" * 513),
        lambda s: s.replace("loaded|", "loaded|61"),
        lambda s: s.replace("loaded|", "say|"),
        lambda s: s.replace("end|1", "request|1|loaded|\nend|2"),
        lambda s: s.replace("end|1", "request|2|loaded|\n" * 32 + "end|33"),
    ],
)
def test_request_validation_refuses_partial_unsafe_or_conflicting_data(mutate):
    with pytest.raises(ProtocolError):
        decode_requests(mutate(request()), KEY, None, EPOCH)


@pytest.mark.parametrize(
    "changes",
    [
        {"key": "bad"},
        {"configuration": "bad"},
        {"epoch": "bad"},
        {"game_epoch": "bad"},
        {"heartbeat": -1},
        {"heartbeat": True},
        {"acknowledged": 10**9},
        {"connected": 1},
        {"address": "<unsafe>"},
        {"address": ""},
    ],
)
def test_invalid_status_fields_are_refused(changes):
    with pytest.raises(ProtocolError):
        status(**changes)


@pytest.mark.parametrize(
    "text",
    ["  Hello  everyone  ", "100% [ready] <ok> | go", "!hint Progressive Tools", "Unicode: café"],
)
def test_chat_is_data_and_preserves_whitespace_punctuation_and_utf8(text):
    _, messages = decode_requests(request(2, "say", text), KEY, None, EPOCH)
    assert messages[0].text == text
