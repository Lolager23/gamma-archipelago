from collections import Counter

import pytest

from gamma_archipelago.configuration import build_configuration, defaults, encode_configuration
from gamma_archipelago.discovery import configured_location_ids
from gamma_archipelago.pool_budget import budget_pool
from gamma_archipelago.presets import presets
from gamma_archipelago.settlement_access import (
    NEUTRALITY_ITEMS,
    SETTLEMENT_RULES,
    protected_settlements,
    required_reputation,
    requirement,
)
from gamma_archipelago.web_planner import preview


def test_reviewed_hostile_bases_share_faction_quotas_and_use_the_exact_neutral_boundary():
    config = build_configuration(presets()["full_story"] | {"shared_faction_goodwill": 0})
    ids = configured_location_ids(config)
    assert set(SETTLEMENT_RULES) == {28052103, 28052106, 28052108, 28052112, 28052113, 28052114}
    assert protected_settlements(config) == {28052113, 28052114}
    requirements = required_reputation(config, ids)
    assert set(requirements) == NEUTRALITY_ITEMS
    assert set(requirements.values()) == {5}
    assert sum(requirements.values()) == 15  # Two Military bases share five rewards.
    for id in (28052103, 28052106, 28052108, 28052112):
        rule = requirement(config, id)
        assert rule.minimum == 1001 and rule.copies == 5 and rule.neutral == -999
        assert 4 * 250 < rule.minimum <= 5 * 250
    assert requirement(config, 28052113) is None
    assert requirement(config, None) is None


@pytest.mark.parametrize("enabled,rewards", [(0, 0), (0, 1), (1, 0), (1, 1)])
def test_disabled_and_unsupported_routes_never_require_unavailable_rewards(enabled, rewards):
    config = build_configuration(
        (presets()["full_story"] | {"shared_faction_goodwill": 0})
        | {"settlement_reputation_logic": enabled, "rewards_faction_reputation": rewards}
    )
    ids = configured_location_ids(config)
    assert bool(required_reputation(config, ids)) == bool(enabled and rewards)
    expected = ({28052113, 28052114} if rewards else set(SETTLEMENT_RULES)) if enabled else set()
    assert protected_settlements(config) == expected


def test_reputation_is_budgeted_before_optional_rewards_and_starting_copies_are_accounted_for():
    config = build_configuration(presets()["full_story"] | {"shared_faction_goodwill": 0})
    ids = configured_location_ids(config)
    plan = budget_pool(config, ids)
    assert Counter(plan.required)["Faction Goodwill: army"] == 5
    assert (
        budget_pool(config, ids, starting={"Faction Goodwill: army": 4}).required.count(
            "Faction Goodwill: army"
        )
        == 1
    )
    assert (
        budget_pool(config, ids, starting={"Faction Goodwill: army": 5}).required.count(
            "Faction Goodwill: army"
        )
        == 0
    )
    depleted = budget_pool(
        config, ids, starting={"Faction Goodwill: army": 5}, from_pool={"Faction Goodwill: army": 5}
    )
    assert dict(depleted.from_pool)["Faction Goodwill: army"] == 5
    assert plan.eligible_checks == 220  # All eight rank checks now accept filler only.
    data = preview(config.to_values(), {})
    for reward in data["rewards"]:
        if reward["name"] in NEUTRALITY_ITEMS:
            assert reward["classification"] == "progression"
    with pytest.raises(ValueError, match="cannot hold"):
        budget_pool(config, frozenset({28052103}))


def test_omitted_old_setting_keeps_legacy_identity_and_wire_compatibility():
    values = defaults()
    assert values["settlement_reputation_logic"] == 1
    values.pop("settlement_reputation_logic")
    old = build_configuration(values)
    explicit = build_configuration(values | {"settlement_reputation_logic": 0})
    assert old.digest == explicit.digest
    assert old.option("settlement_reputation_logic") == 0
    assert "settlement_reputation_logic" not in encode_configuration("a" * 64, old)
    assert not protected_settlements(old)
