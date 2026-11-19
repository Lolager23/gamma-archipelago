import pytest

from gamma_archipelago.catalog import ITEM_SECTIONS, LOCATION_IDS, MAX_ITEMS
from gamma_archipelago.protocol import GameSnapshot, ProtocolError
from gamma_archipelago.session import SessionCoordinator, make_session_key

ITEMS = tuple(ITEM_SECTIONS)
KEY = make_session_key("test-seed", 0, 1)


def test_session_identity_is_deterministic_and_unambiguous():
    assert make_session_key("test-seed", 0, 1) == KEY
    assert len(KEY) == 64
    assert len({make_session_key("test-seed", 0, 2), make_session_key("other", 0, 1), KEY}) == 3
    assert make_session_key("é", 0, 1)


@pytest.mark.parametrize(
    "values", [("", 0, 1), ("x", -1, 1), ("x", 0, 0), ("x", True, 1), ("x", 0, 1.1)]
)
def test_invalid_identity(values):
    with pytest.raises(ProtocolError):
        make_session_key(*values)


def test_history_can_only_extend_with_unchanged_prefix():
    session = SessionCoordinator(KEY)
    session.accept_history(ITEMS[:1])
    session.accept_history(ITEMS[:1])
    session.accept_history(ITEMS)
    assert session.item_ids == ITEMS
    for invalid in ((), (ITEMS[1],)):
        with pytest.raises(ProtocolError):
            session.accept_history(invalid)
        assert session.item_ids == ITEMS


@pytest.mark.parametrize("history", [(1234,), (ITEMS[0],) * (MAX_ITEMS + 1)])
def test_unknown_or_oversized_history(history):
    with pytest.raises(ProtocolError):
        SessionCoordinator(KEY).accept_history(history)


def test_checks_remain_monotonic_across_older_save_observations():
    session = SessionCoordinator(KEY)
    session.accept_history(ITEMS)
    first, second = sorted(LOCATION_IDS)[:2]
    assert session.observe_game(GameSnapshot(KEY, 3, frozenset({first}), False)) == (first,)
    assert session.observe_game(GameSnapshot(KEY, 0, frozenset({second}), False)) == (first, second)
    assert session.observe_game(GameSnapshot(KEY, 0, frozenset(), False)) == (first, second)


def test_wrong_seed_and_impossible_receipt_count_leave_state_unchanged():
    session = SessionCoordinator(KEY)
    for snapshot in [
        GameSnapshot("b" * 64, 0, LOCATION_IDS, False),
        GameSnapshot(KEY, 1, LOCATION_IDS, False),
    ]:
        with pytest.raises(ProtocolError):
            session.observe_game(snapshot)
        assert not session.checked_locations


def test_seed_manifest_is_bound_and_rejects_disabled_or_changed_checks():
    from gamma_archipelago.catalog import ALL_LOCATION_IDS

    session = SessionCoordinator(KEY)
    disabled = next(iter(ALL_LOCATION_IDS - LOCATION_IDS))
    with pytest.raises(ProtocolError, match="disabled"):
        session.observe_game(GameSnapshot(KEY, 0, frozenset({disabled}), False))
    for invalid in (frozenset(), frozenset({42})):
        with pytest.raises(ProtocolError, match="Unsupported"):
            session.bind_locations(invalid)
    session.bind_locations(ALL_LOCATION_IDS)
    session.bind_locations(ALL_LOCATION_IDS)
    session.accept_confirmed(ALL_LOCATION_IDS)
    with pytest.raises(ProtocolError, match="changed"):
        session.bind_locations(LOCATION_IDS)
