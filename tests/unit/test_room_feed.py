import pytest

from gamma_archipelago.bridge import FileBridge
from gamma_archipelago.protocol import ProtocolError
from gamma_archipelago.room_feed import RoomMessage, encode_feed, safe_text

KEY = "a" * 64


def test_feed_is_bounded_sanitized_and_written_to_the_isolated_bridge(tmp_path):
    root = tmp_path / "game"
    root.mkdir()
    bridge = FileBridge(root, allowed_root=root)
    message = RoomMessage(1, 'Dave gave "Sword" to Dave.')
    bridge.write_room_feed(KEY, None, "b" * 16, 1, (message,))
    text = (bridge.directory / "room_feed.txt").read_text(encoding="ascii")
    assert text == encode_feed(KEY, None, "b" * 16, 1, (message,))
    assert "configuration|-" in text and text.endswith("end|1\n")
    assert "configuration|" + KEY in encode_feed(KEY, KEY, "b" * 16, 2, ())
    assert safe_text(" a\n[%c]<>| b ") == "a c b"
    assert len(safe_text("é" * 2048).encode("utf-8")) == 2048


@pytest.mark.parametrize(
    "change",
    [
        {"key": "bad"},
        {"configuration": "bad"},
        {"epoch": "x"},
        {"heartbeat": True},
        {"heartbeat": 0},
        {"heartbeat": 10**9},
        {"messages": tuple(RoomMessage(i + 1, "x") for i in range(65))},
        {"messages": (RoomMessage(True, "x"),)},
        {"messages": (RoomMessage(0, "x"),)},
        {"messages": (RoomMessage(2, "x"), RoomMessage(1, "x"))},
        {"messages": (RoomMessage(1, ""),)},
        {"messages": (RoomMessage(1, "<markup>"),)},
        {"messages": (RoomMessage(1, "x" * 2049),)},
    ],
)
def test_invalid_feed_is_refused(change):
    fields = dict(key=KEY, configuration=None, epoch="b" * 16, heartbeat=1, messages=())
    with pytest.raises(ProtocolError):
        encode_feed(**(fields | change))
