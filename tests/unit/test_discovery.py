import pytest

from gamma_archipelago.configuration import ConfigurationError, build_configuration, defaults
from gamma_archipelago.discovery import (
    GROUPS,
    MISSABLE_IDS,
    QUOTAS,
    SOURCES,
    TOKENS,
    configured_location_ids,
    normalize_exclusions,
)
from gamma_archipelago.web_planner import preview


@pytest.mark.parametrize("group", GROUPS)
def test_quota_selects_fixed_milestones_and_exclusions_reduce_roster(group):
    token, source = next(iter(SOURCES[group].items()))
    values = {
        **defaults(),
        "checks_maps": 0,
        GROUPS[group]: 1,
        f"{group}_discovery_mode": 1,
        f"{group}_discovery_count": 3,
        "discovery_exclusions": [token],
    }
    configuration = build_configuration(values)
    assert configured_location_ids(configuration) == frozenset(QUOTAS[group][:3])
    assert {row["id"] for row in preview(values, {})["checks"]} == set(QUOTAS[group][:3])
    all_types = build_configuration({**values, f"{group}_discovery_count": 0})
    assert len(configured_location_ids(all_types)) == len(SOURCES[group]) - 1
    per_type = build_configuration({**values, f"{group}_discovery_mode": 0})
    assert source not in configured_location_ids(per_type)
    assert len(configured_location_ids(per_type)) == len(SOURCES[group]) - 1
    with pytest.raises(ConfigurationError, match="roster"):
        build_configuration({**values, f"{group}_discovery_count": len(SOURCES[group])})


@pytest.mark.parametrize(
    "value", [None, 0, "mutant:dog", ["unknown"], [True], ["mutant:dog", "mutant:dog"], ["x"] * 105]
)
def test_invalid_exclusion_lists_refuse_before_mutation(value):
    with pytest.raises(ConfigurationError, match="exclusion"):
        build_configuration({**defaults(), "discovery_exclusions": value})


def test_empty_roster_and_omitted_only_pool_refuse():
    with pytest.raises(ConfigurationError, match="no checks"):
        build_configuration(
            {**defaults(), "checks_maps": 0, "checks_shops": 1, "optional_check_policy": 1}
        )
    with pytest.raises(ConfigurationError, match="roster"):
        build_configuration(
            {
                **defaults(),
                "checks_mutant_first_kills": 1,
                "mutant_discovery_mode": 1,
                "discovery_exclusions": list(SOURCES["mutant"]),
            }
        )


def test_optional_policy_exclusion_normalization_and_legacy_identity():
    values = defaults()
    legacy = {
        key: value
        for key, value in values.items()
        if not key.endswith(("_discovery_mode", "_discovery_count"))
        and key not in {"discovery_exclusions", "optional_check_policy"}
    }
    assert build_configuration(values).digest == build_configuration(legacy).digest
    assert normalize_exclusions(frozenset(TOKENS)) == tuple(sorted(TOKENS))
    assert normalize_exclusions(set()) == ()
    included = build_configuration(
        {**values, "checks_shops": 1, "checks_shop_purchases": 1, "checks_faction_standing": 1}
    )
    assert configured_location_ids(included) >= MISSABLE_IDS
    omitted = build_configuration({**included.to_values(), "optional_check_policy": 1})
    assert not MISSABLE_IDS & configured_location_ids(omitted)
