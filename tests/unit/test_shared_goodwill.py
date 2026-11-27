from collections import Counter

import pytest

from gamma_archipelago.configuration import build_configuration, defaults, encode_configuration
from gamma_archipelago.content_progression import configured_item_ids
from gamma_archipelago.discovery import configured_location_ids
from gamma_archipelago.goodwill import SHARED_ID, SHARED_NAME, copies, pool_name, shared
from gamma_archipelago.playability import allowed
from gamma_archipelago.pool_budget import budget_pool
from gamma_archipelago.presets import presets
from gamma_archipelago.reward_quantities import requested
from gamma_archipelago.settlement_access import required_reputation


def config(**values):
    return build_configuration(presets()["living_legend"] | values)


def test_twelve_shared_copies_cover_every_quota_without_redundant_faction_guarantees():
    cfg = config()
    checks = configured_location_ids(cfg)
    plan = budget_pool(cfg, checks)
    assert Counter(name for name in plan.required if name.startswith("Faction Goodwill:")) == {
        SHARED_NAME: 12
    }
    assert required_reputation(cfg, checks) == {SHARED_NAME: 5}
    assert budget_pool(cfg, checks, starting={SHARED_NAME: 3}).required.count(SHARED_NAME) == 9
    removed = budget_pool(cfg, checks, starting={SHARED_NAME: 3}, from_pool={SHARED_NAME: 3})
    assert removed.required.count(SHARED_NAME) == 12
    assert dict(removed.from_pool) == {SHARED_NAME: 3}
    assert SHARED_ID in configured_item_ids(cfg)


@pytest.mark.parametrize("mode,rewards,expected", [(0, 1, False), (1, 0, False), (1, 1, True)])
def test_shared_mode_is_explicit_and_extras_follow_the_selected_reward(mode, rewards, expected):
    cfg = config(
        shared_faction_goodwill=mode, rewards_faction_reputation=rewards, extra_faction_goodwill=9
    )
    assert shared(cfg) is expected
    assert (SHARED_ID in configured_item_ids(cfg)) is expected
    assert pool_name(cfg, "Faction Goodwill: army") == (
        SHARED_NAME if expected else "Faction Goodwill: army"
    )
    extras = requested(cfg)
    assert extras[SHARED_NAME] == (9 if expected else 0)
    counts = Counter({SHARED_NAME: 4, "Faction Goodwill: army": 1})
    assert copies(cfg, "Faction Goodwill: army", counts.__getitem__) == (5 if expected else 1)
    assert copies(cfg, SHARED_NAME, counts.__getitem__) == (4 if expected else 0)


def test_shared_and_named_copies_combine_per_faction_without_summing_unrelated_factions():
    cfg = config()
    row = dict(category="checks_faction_standing", minimum=3000)
    counts = Counter({SHARED_NAME: 10, "Faction Goodwill: dolg": 1, "Faction Goodwill: freedom": 1})
    assert not allowed(cfg, row, counts.__getitem__, lambda _: True)
    counts["Faction Goodwill: dolg"] += 1
    assert allowed(cfg, row, counts.__getitem__, lambda _: True)
    counts = Counter({SHARED_NAME: 12})
    assert allowed(cfg, row, counts.__getitem__, lambda _: True)


def test_omitted_mode_preserves_legacy_digest_wire_and_manifest():
    values = defaults()
    values.pop("shared_faction_goodwill")
    old = build_configuration(values)
    explicit = build_configuration(values | {"shared_faction_goodwill": 0})
    assert old.digest == explicit.digest
    assert encode_configuration("a" * 64, old, expanded=True) == encode_configuration(
        "a" * 64, explicit, expanded=True
    )
    assert "shared_faction_goodwill" not in encode_configuration("a" * 64, old, expanded=True)
    assert SHARED_ID not in configured_item_ids(old)
