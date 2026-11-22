from collections import Counter

import pytest

from gamma_archipelago.configuration import build_configuration, defaults, legacy_defaults
from gamma_archipelago.content_progression import configured_item_ids
from gamma_archipelago.discovery import configured_location_ids
from gamma_archipelago.pool_budget import budget_pool
from gamma_archipelago.reward_quantities import requested
from gamma_archipelago.web_planner import catalogue


def test_physical_reward_roster_uses_sixty_supported_nonquest_types_and_safe_variants():
    data = catalogue()
    roster = {
        r["name"].split(": ", 1)[1]: r
        for r in data["locations"]
        if r["category"] == "checks_artefacts" and "quota_group" not in r and r["logic"]["reliable"]
    }
    rewards = [r for r in data["items"] if r.get("category") == "rewards_artefacts"]
    assert len(rewards) == len(roster) == 60
    for reward in rewards:
        source = roster[reward["name"].split(": ", 1)[1]]
        (section,) = reward["supplies"]
        assert section in source["aliases"]
        contained = [alias for alias in source["aliases"] if alias.endswith("_lead_box")]
        assert not contained or section in contained
        assert reward["classification"] == "useful" and reward["effect"] == "artefact_reward"


def test_category_and_quantities_control_artefact_rewards_without_changing_old_manifests():
    config = build_configuration(defaults() | {"rewards_artefacts": 1})
    counts = requested(config)
    assert counts.total() == 4
    assert len(configured_item_ids(config) & set(range(28053101, 28053161))) == 60
    assert not configured_item_ids(build_configuration(legacy_defaults())) & set(
        range(28053101, 28053161)
    )
    assert not requested(build_configuration(defaults()))
    zero = build_configuration(config.to_values() | {"artefact_rewards": 0})
    assert not requested(zero)
    sixty = build_configuration(config.to_values() | {"artefact_rewards": 60})
    assert set(requested(sixty).values()) == {1}
    assert (
        requested(build_configuration(config.to_values() | {"artefact_rewards": 61}))[
            "Artefact: Ball"
        ]
        == 2
    )
    with pytest.raises(ValueError, match="quantities"):
        budget_pool(sixty, configured_location_ids(sixty))
    assert Counter(budget_pool(config, configured_location_ids(config)).convenience) == counts
