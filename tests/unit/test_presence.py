import pytest

from gamma_archipelago.bridge import FileBridge
from gamma_archipelago.presence import encode_presence
from gamma_archipelago.protocol import ProtocolError

KEY, CONFIG, EPOCH = "a" * 64, "b" * 64, "c" * 16


def test_presence_is_bounded_data_and_atomic_without_check_or_receipt_fields(tmp_path):
    bridge = FileBridge(tmp_path, allowed_root=tmp_path)
    bridge.write_presence(KEY, None, EPOCH, 1, "Оуэн {player}")
    target = bridge.directory / "presence.txt"
    assert target.read_text() == encode_presence(KEY, None, EPOCH, 1, "Оуэн {player}")
    assert "configuration|-\n" in target.read_text()
    assert not (bridge.directory / "presence.tmp").exists()
    original = target.read_bytes()
    with pytest.raises(ProtocolError):
        bridge.write_presence(KEY, CONFIG, EPOCH, 2, "%c[red]")
    assert target.read_bytes() == original
    assert "configuration|" + CONFIG in encode_presence(KEY, CONFIG, EPOCH, 9999999999, "Player")


@pytest.mark.parametrize(
    "changes",
    [
        {"key": "bad"},
        {"configuration": "bad"},
        {"epoch": "bad"},
        {"epoch": None},
        {"sequence": True},
        {"sequence": -1},
        {"sequence": 10**10},
        {"sequence": 1.5},
        {"player": None},
        {"player": ""},
        {"player": "A" * 97},
        {"player": "Name\n"},
    ],
)
def test_invalid_presence_fields_are_rejected_before_publication(changes):
    fields = dict(key=KEY, configuration=CONFIG, epoch=EPOCH, sequence=0, player="Player")
    fields.update(changes)
    with pytest.raises(ProtocolError):
        encode_presence(**fields)
