import pytest

from gamma_archipelago.bridge import FileBridge
from gamma_archipelago.catalog import LOCATION_IDS
from gamma_archipelago.protocol import ProtocolError, encode_confirmed
from gamma_archipelago.session import SessionCoordinator

KEY = "a" * 64


def test_known_milestone_universe_is_not_an_unbounded_seed_snapshot():
    from gamma_archipelago.catalog import ALL_LOCATION_IDS

    with pytest.raises(ProtocolError):
        encode_confirmed(KEY, ALL_LOCATION_IDS)


def test_confirmed_checks_are_canonical_and_only_accept_known_locations(tmp_path):
    encoded = encode_confirmed(KEY, LOCATION_IDS)
    assert encoded == (
        f"GAMMA_AP_CONFIRMED|1\nsession|{KEY}\n"
        "check|28052001\ncheck|28052002\ncheck|28052003\nend|3\n"
    )
    bridge = FileBridge(tmp_path, allowed_root=tmp_path)
    bridge.write_confirmed(KEY, LOCATION_IDS)
    assert (bridge.directory / "confirmed_checks.txt").read_text() == encoded
    assert not (bridge.directory / "confirmed_checks.tmp").exists()
    session = SessionCoordinator(KEY)
    session.accept_confirmed(LOCATION_IDS)
    session.accept_confirmed(frozenset())
    assert session.checked_locations == LOCATION_IDS
    for operation in [
        lambda: encode_confirmed(KEY, frozenset({99})),
        lambda: session.accept_confirmed(frozenset({99})),
    ]:
        with pytest.raises(ProtocolError):
            operation()
