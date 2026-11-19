import pytest

from gamma_archipelago.catalog import ITEM_SECTIONS, LOCATION_IDS, enabled_item_ids
from gamma_archipelago.notifications import GAME, is_unlock
from gamma_archipelago.protocol import (
    GameSnapshot,
    ProtocolError,
    encode_confirmed,
    encode_incoming,
    validate_id_manifest,
    validate_session_key,
)
from gamma_archipelago.session import SessionCoordinator, make_session_key

KEY = "a" * 64
ITEM = min(ITEM_SECTIONS)
CHECK = min(LOCATION_IDS)


def test_known_ids_encoded_as_floats_are_not_silently_treated_as_integers():
    for operation in (
        lambda: encode_incoming(KEY, (float(ITEM),)),
        lambda: encode_confirmed(KEY, frozenset({float(CHECK)})),
        lambda: SessionCoordinator(KEY).bind_items(frozenset({float(ITEM)})),
        lambda: SessionCoordinator(KEY).bind_locations(frozenset({float(CHECK)})),
        lambda: SessionCoordinator(KEY).accept_history((float(ITEM),)),
        lambda: SessionCoordinator(KEY).accept_confirmed(frozenset({float(CHECK)})),
        lambda: SessionCoordinator(KEY).observe_game(
            GameSnapshot(KEY, 0, frozenset({float(CHECK)}), False)
        ),
    ):
        with pytest.raises(ProtocolError):
            operation()


@pytest.mark.parametrize(
    "count,goal", [(-1, False), (0.0, False), (True, False), (0, 1), (0, "true")]
)
def test_snapshot_scalar_types_are_validated_before_mutating_session(count, goal):
    session = SessionCoordinator(KEY)
    with pytest.raises(ProtocolError):
        session.observe_game(GameSnapshot(KEY, count, LOCATION_IDS, goal))
    assert not session.checked_locations


@pytest.mark.parametrize("manifest", [None, (), {}, [float(ITEM)], [True], [ITEM, ITEM], [42]])
def test_manifest_requires_a_canonical_integer_list(manifest):
    with pytest.raises(ProtocolError, match="manifest"):
        validate_id_manifest(manifest, frozenset({ITEM}), "item")
    validate_id_manifest([ITEM], frozenset({ITEM}), "item")


def test_identity_refuses_non_string_seed_and_session_values():
    with pytest.raises(ProtocolError):
        make_session_key(123, 0, 1)
    with pytest.raises(ProtocolError):
        validate_session_key(None)


def test_equipment_manifest_selects_only_locked_groups_and_retains_legacy_projection():
    rewards = frozenset({"rewards_starting_gear_unlocks"})
    selected = enabled_item_ids(rewards, (("starting_pda", 2), ("starting_detector", 1)))
    assert selected == set(ITEM_SECTIONS) | {28051602}
    assert len(enabled_item_ids(rewards)) == 12
    assert is_unlock(28051401, GAME) and not is_unlock(28051401, "APQuest")
