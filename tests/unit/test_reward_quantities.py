from collections import Counter

import pytest

from gamma_archipelago.artefact_capacity import resolve_capacity
from gamma_archipelago.configuration import build_configuration, defaults, legacy_defaults
from gamma_archipelago.discovery import QUOTAS, configured_location_ids
from gamma_archipelago.pool_budget import budget_pool
from gamma_archipelago.presets import presets
from gamma_archipelago.reward_quantities import requested, useful_count
from gamma_archipelago.web_planner import preview


def config(**values):
    return build_configuration({**defaults(), **values})


def test_explicit_counts_are_deterministic_and_disabled_categories_add_nothing():
    assert not requested(config())
    assert requested(config(basic_toolkits=2)) == Counter({"Basic Toolkit": 2})
    c = config(rewards_supply_medical=1, medical_packages=72, rewards_loot_stashes=1)
    counts = requested(c)
    assert counts["Medical Supply Package"] == 72
    assert counts.total() == 84
    assert useful_count(counts) == 76
    assert not requested(config(rewards_supply_medical=1, reward_quantities=0))
    assert not requested(config(rewards_supply_medical=1, medical_packages=0))


def test_quantities_preserve_permissions_and_count_starting_gifts_once():
    c = config(rewards_supply_medical=1, medical_packages=20)
    ids = configured_location_ids(c)
    plan = budget_pool(c, ids, starting={"Medical Supply Package": 3})
    assert Counter(plan.convenience)["Medical Supply Package"] == 17
    assert plan.filler_slots == 16
    with pytest.raises(ValueError, match="quantities"):
        budget_pool(config(rewards_supply_medical=1, medical_packages=40), ids)
    with pytest.raises(ValueError):
        config(medical_packages=4001)
    assert config(medical_packages=4000).option("medical_packages") == 4000
    assert build_configuration(legacy_defaults()).option("reward_quantities") == 0


def test_conditional_artefacts_add_only_the_required_nonfiller_capacity():
    base = presets()["full_story"]
    original = build_configuration(base)
    assert resolve_capacity(original) == original
    before = budget_pool(original, configured_location_ids(original))
    # Each extra medical package is useful. Demand one more than base eligibility.
    desired = (
        before.eligible_checks
        - len(before.required)
        - useful_count(Counter(before.convenience))
        + 5
    )
    c = build_configuration({**base, "medical_packages": 4 + desired})
    resolved = resolve_capacity(c)
    assert resolved.option("artefact_overflow_count") == 5
    assert QUOTAS["artefact"][44] in configured_location_ids(resolved)
    assert QUOTAS["artefact"][45] not in configured_location_ids(resolved)
    assert (
        budget_pool(resolved, configured_location_ids(resolved)).network_checks
        == before.network_checks + 5
    )
    gift = resolve_capacity(c, starting={"Medical Supply Package": 5})
    assert gift.option("artefact_overflow_count") == 0
    excluded = frozenset({next(iter(configured_location_ids(original)))})
    assert resolve_capacity(c, excluded).option("artefact_overflow_count") in (5, 6)
    capped = resolve_capacity(build_configuration({**c.to_values(), "artefact_extra_ceiling": 42}))
    assert capped.option("artefact_overflow_count") == 2
    with pytest.raises(ValueError, match="quantities"):
        budget_pool(capped, configured_location_ids(capped))
    filler = resolve_capacity(build_configuration({**base, "basic_loot_stashes": 300}))
    assert filler.option("artefact_overflow_count") == 0
    with pytest.raises(ValueError, match="quantities"):
        budget_pool(filler, configured_location_ids(filler))
    assert resolve_capacity(config()).option("artefact_overflow_count") == 0
    assert preview(c.to_values(), {})["configuration"]["artefact_overflow_count"] == 5


@pytest.mark.parametrize(
    "values",
    [
        {"artefact_overflow_count": 1},
        {
            "checks_artefacts": 1,
            "artefact_overflow_count": 1,
            "rewards_artefact_melter": 1,
            "artefact_extra_ceiling": 40,
        },
        {
            "checks_artefacts": 1,
            "artefact_overflow_count": 1,
            "rewards_artefact_melter": 1,
            "artefact_discovery_count": 20,
        },
    ],
)
def test_invalid_derived_capacity_is_refused(values):
    with pytest.raises(ValueError, match="Extra artefacts"):
        config(**values)
