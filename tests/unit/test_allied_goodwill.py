from collections import Counter

from gamma_archipelago.configuration import build_configuration
from gamma_archipelago.content_progression import configured_item_ids
from gamma_archipelago.discovery import configured_location_ids
from gamma_archipelago.goodwill import (
    ALLIED_ID,
    ALLIED_NAME,
    SHARED_ID,
    SHARED_NAME,
    copies,
    pool_name,
)
from gamma_archipelago.pool_budget import budget_pool
from gamma_archipelago.presets import presets
from gamma_archipelago.reward_quantities import requested
from gamma_archipelago.settlement_access import required_reputation


def test_allied_default_keeps_twelve_shared_and_fifteen_dedicated_hostile_rewards():
    config = build_configuration(presets()["living_legend"])
    assert config.option("shared_faction_goodwill") == 2
    ids = configured_item_ids(config)
    assert ALLIED_ID in ids and SHARED_ID not in ids
    checks = configured_location_ids(config)
    expected = {"Faction Goodwill: " + faction: 5 for faction in ("army", "bandit", "killer")}
    assert required_reputation(config, checks) == expected
    required = Counter(budget_pool(config, checks).required)
    assert {
        name: count for name, count in required.items() if name.startswith("Faction Goodwill:")
    } == {ALLIED_NAME: 12, **expected}
    assert (
        budget_pool(
            config, checks, starting={ALLIED_NAME: 2, "Faction Goodwill: army": 1}
        ).required.count(ALLIED_NAME)
        == 10
    )
    assert pool_name(config, "Faction Goodwill: army") == "Faction Goodwill: army"
    assert pool_name(config, "Faction Goodwill: dolg") == ALLIED_NAME
    counts = Counter(
        {ALLIED_NAME: 12, SHARED_NAME: 20, "Faction Goodwill: army": 1, "Faction Goodwill: dolg": 2}
    )
    assert copies(config, "Faction Goodwill: army", counts.__getitem__) == 1
    assert copies(config, "Faction Goodwill: dolg", counts.__getitem__) == 14
    assert copies(config, ALLIED_NAME, counts.__getitem__) == 12
    assert copies(config, SHARED_NAME, counts.__getitem__) == 0


def test_extra_shared_rewards_use_only_the_selected_version_and_disabled_has_no_global_items():
    values = presets()["living_legend"] | {"extra_faction_goodwill": 9}
    assert requested(build_configuration(values))[ALLIED_NAME] == 9
    legacy = build_configuration(values | {"shared_faction_goodwill": 1})
    assert requested(legacy)[SHARED_NAME] == 9 and requested(legacy)[ALLIED_NAME] == 0
    disabled = build_configuration(values | {"shared_faction_goodwill": 0})
    assert not ({SHARED_ID, ALLIED_ID} & configured_item_ids(disabled))
    assert not ({SHARED_NAME, ALLIED_NAME} & requested(disabled).keys())
