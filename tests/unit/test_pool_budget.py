import pytest

from gamma_archipelago.catalog import MAP_LOCATION_IDS
from gamma_archipelago.configuration import build_configuration, defaults
from gamma_archipelago.discovery import configured_location_ids
from gamma_archipelago.pool_budget import CARRY, budget_pool
from gamma_archipelago.presets import presets
from gamma_archipelago.settings_ui import advanced_options
from gamma_archipelago.web_planner import metadata, preview


def configuration(**values):
    return build_configuration({**defaults(), "reward_quantities": 0, **values})


def test_budget_accounts_for_progressive_copies_gifts_and_pool_depletion_before_filler():
    config = configuration(
        rewards_progressive_tools=1, rewards_convenience=1, content_progression=0
    )
    plan = budget_pool(config, MAP_LOCATION_IDS, starting={"Progressive Tools": 2, CARRY: 1})
    assert plan.required == ("Progressive Tools",) and plan.convenience == (CARRY,) * 2
    assert plan.filler_slots == 30
    assert plan.report()["required_copies"] == 1
    pool = budget_pool(
        config,
        MAP_LOCATION_IDS,
        starting={"Progressive Tools": 2},
        from_pool={"Progressive Tools": 2},
    )
    assert len(pool.required) == 3 and pool.report()["starting_from_pool"] == {
        "Progressive Tools": 2
    }
    complete = budget_pool(config, MAP_LOCATION_IDS, starting={"Progressive Tools": 3, CARRY: 3})
    assert not complete.required and not complete.convenience and complete.filler_slots == 33
    assert complete.starting == ((CARRY, 3), ("Progressive Tools", 3))


@pytest.mark.parametrize(
    "values",
    [
        {"unknown": 1},
        {"Progressive Tools": 1},
        {"Medkit": True},
        {"Medkit": -1},
        {"Medkit": 4001},
        {"Medkit": 4000},
    ],
)
def test_invalid_disabled_or_oversized_starting_inventory_is_refused(values):
    with pytest.raises(ValueError):
        budget_pool(configuration(), MAP_LOCATION_IDS, starting=values)


def test_zero_counts_and_impossible_depletion_requests_are_explicit():
    assert budget_pool(configuration(), MAP_LOCATION_IDS, starting={"Medkit": 0}).starting == ()
    with pytest.raises(ValueError, match="precollected"):
        budget_pool(configuration(), MAP_LOCATION_IDS, from_pool={"Medkit": 1})
    with pytest.raises(ValueError, match="guaranteed"):
        budget_pool(
            configuration(), MAP_LOCATION_IDS, starting={"Medkit": 1}, from_pool={"Medkit": 1}
        )


@pytest.mark.parametrize(
    "ids,excluded",
    [
        (frozenset(), frozenset()),
        (frozenset({123}), frozenset()),
        (MAP_LOCATION_IDS, frozenset({123})),
    ],
)
def test_budget_refuses_unknown_empty_or_unowned_check_manifests(ids, excluded):
    with pytest.raises(ValueError, match="manifest"):
        budget_pool(configuration(), ids, excluded)


def test_missable_checks_cannot_hold_progression_or_capped_useful_rewards():
    config = configuration(checks_maps=0, checks_shops=1, rewards_progressive_tools=1)
    with pytest.raises(ValueError, match="reliable"):
        budget_pool(config, configured_location_ids(config))
    config = configuration(checks_maps=0, checks_shops=1, rewards_convenience=1)
    with pytest.raises(ValueError, match="reliable"):
        budget_pool(config, configured_location_ids(config))
    allowed = configuration(**{**config.to_values(), "optional_check_policy": 2})
    assert len(budget_pool(allowed, configured_location_ids(allowed)).convenience) == 3
    no_slots = configuration(rewards_zone_keys=1, rewards_progressive_tools=1)
    with pytest.raises(ValueError, match="cannot hold"):
        budget_pool(no_slots, MAP_LOCATION_IDS)


def test_protected_opening_reports_local_permissions_and_refuses_overloaded_cordon():
    options = {
        **defaults(),
        "opening_policy": 1,
        "reward_quantities": 0,
        "starting_pda": 2,
        "rewards_starting_gear_unlocks": 1,
        "rewards_zone_keys": 1,
        "checks_settlements": 1,
    }
    result = preview(options, {})
    assert result["opening_permissions"] == ["Equipment Unlock: PDA"]
    assert result["preview_kind"] == "settings_only"
    with pytest.raises(ValueError, match="Cordon"):
        preview({**options, "checks_settlements": 0}, {})
    config = build_configuration({**options, "checks_settlements": 0})
    assert budget_pool(
        config, configured_location_ids(config), starting={"Equipment Unlock: PDA": 1}
    )
    for name in ("short", "standard", "extended"):
        result = preview(presets()[name], {})
        assert result["configuration"]["opening_policy"] == 1
        assert result["required_rewards"] == result["pool_budget"]["required_copies"]


def test_settings_metadata_covers_every_bounded_option_and_roster():
    data = metadata()
    assert len(data["discovery_types"]) == 104
    assert data["advanced"] == advanced_options()
    for row in data["advanced"]:
        if row["choices"] is not None:
            assert len(row["choices"]) == row["maximum"] + 1
        else:
            assert row["key"].endswith(("_discovery_count", "_filler_tail", "_ceiling"))


@pytest.mark.parametrize(
    "profile,kills,tasks",
    [
        (1, (5, 15, 30), (1, 3, 6)),
        (2, (10, 25, 50, 100), (5, 10, 20, 40)),
        (3, (25, 75, 150, 250), (10, 25, 50, 75)),
    ],
)
def test_grind_profiles_resolve_both_threshold_lists_deterministically(profile, kills, tasks):
    config = configuration(grind_profile=profile)
    assert config.kill_milestones == kills and config.side_task_milestones == tasks
    assert build_configuration(config.to_values()).digest == config.digest
