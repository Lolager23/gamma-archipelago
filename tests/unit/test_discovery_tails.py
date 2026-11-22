import pytest

from gamma_archipelago.configuration import build_configuration, defaults, encode_configuration
from gamma_archipelago.discovery import QUOTAS, configured_location_ids, protected_tail_ids
from gamma_archipelago.pool_budget import budget_pool
from gamma_archipelago.starting_unlock import preview_budget, unlock_candidates
from gamma_archipelago.web_planner import preview


@pytest.mark.parametrize(
    "group,category", [("mutant", "checks_mutant_first_kills"), ("artefact", "checks_artefacts")]
)
def test_last_x_generic_checks_are_filler_without_removing_checks(group, category):
    config = build_configuration(
        {
            **defaults(),
            category: 1,
            f"{group}_discovery_mode": 1,
            f"{group}_discovery_count": 10,
            f"{group}_filler_tail": 3,
        }
    )
    ids = configured_location_ids(config)
    assert protected_tail_ids(config, ids) == frozenset(QUOTAS[group][7:10])
    assert budget_pool(config, ids).eligible_checks == len(ids) - 3
    assert protected_tail_ids(config, frozenset({28052001})) == frozenset()
    assert budget_pool(config, frozenset({28052001})).eligible_checks == 1
    result = preview(config.to_values(), {})
    assert result["network_checks"] == len(ids)
    assert result["pool_budget"]["eligible_checks"] == len(ids) - 3
    for changes in ({category: 0}, {f"{group}_discovery_mode": 0}, {f"{group}_filler_tail": 11}):
        with pytest.raises(ValueError, match="filler tail"):
            build_configuration(config.to_values() | changes)


def test_tail_capacity_refuses_progression_instead_of_leaking_it_to_rare_checks():
    config = build_configuration(
        {
            **defaults(),
            "checks_maps": 0,
            "checks_mutant_first_kills": 1,
            "mutant_discovery_mode": 1,
            "mutant_discovery_count": 3,
            "mutant_filler_tail": 3,
            "rewards_progressive_tools": 1,
        }
    )
    with pytest.raises(ValueError, match="reliable"):
        budget_pool(config, configured_location_ids(config))


def test_new_zero_defaults_preserve_legacy_wire_and_random_unlock_requires_a_lock():
    values = defaults()
    old = {
        key: value
        for key, value in values.items()
        if key not in {"random_starting_unlock", "mutant_filler_tail", "artefact_filler_tail"}
    }
    assert encode_configuration("a" * 64, build_configuration(old)) == encode_configuration(
        "a" * 64, build_configuration(values)
    )
    assert "random_starting_unlock" not in encode_configuration(
        "a" * 64, build_configuration(values)
    )
    with pytest.raises(ValueError, match="Random starting unlock"):
        build_configuration(values | {"random_starting_unlock": 1})


def test_start_candidates_skip_unlocked_or_held_permissions_and_preview_does_not_roll():
    values = defaults() | {
        "equipment_class_progression": 0,
        "starting_pda": 2,
        "starting_detector": 2,
        "starting_firearms": 2,
        "rewards_starting_gear_unlocks": 1,
        "random_starting_unlock": 1,
    }
    config = build_configuration(values)
    names = unlock_candidates(config, {})
    assert names == (
        "Equipment Unlock: PDA",
        "Equipment Unlock: Firearms",
        "Equipment Unlock: Detector",
    )
    assert unlock_candidates(config, dict.fromkeys(names, 1)) == ()
    assert unlock_candidates(build_configuration(defaults()), {}) == ()
    ids = configured_location_ids(config)
    plan, report = preview_budget(config, ids)
    assert len(plan.required) == 2 and plan.filler_slots == len(ids) - 2
    assert set(report["random_starting_unlock_choices"]) == set(names)
    assert all(
        sum(row["starting_items"].values()) == 1
        for row in report["random_starting_unlock_choices"].values()
    )
    assert "required_progression" not in report
    assert preview(values, {})["configuration"]["random_starting_unlock"] == 1
    normal = build_configuration(defaults())
    assert preview_budget(normal, configured_location_ids(normal))[1]["starting_items"] == {}
