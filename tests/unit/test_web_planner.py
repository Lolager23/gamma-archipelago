import pytest

from gamma_archipelago.configuration import build_configuration, defaults
from gamma_archipelago.content_progression import configured_item_ids
from gamma_archipelago.discovery import configured_location_ids
from gamma_archipelago.presets import presets
from gamma_archipelago.web_estimates import ASSUMPTIONS, estimate_playtime
from gamma_archipelago.web_planner import metadata, player_document, preview


def test_metadata_and_all_presets_match_authoritative_catalogues():
    data = metadata()
    assert len(data["checks"]) == 21 and len(data["rewards"]) == 18
    assert len(data["gear"]) == 9 and len(data["quantities"]) == 4
    assert len(data["goals"]) == 9 and len(data["levels"]) == 33
    for values in presets().values():
        configuration = build_configuration(values)
        result = preview(values, {})
        assert {row["id"] for row in result["checks"]} == configured_location_ids(configuration)
        assert {row["id"] for row in result["rewards"]} == configured_item_ids(configuration)
        assert result["reward_slots"] == result["network_checks"]
        assert result["digest"] == configuration.digest
    full = preview(presets()["full_story"], {})
    assert (full["network_checks"], full["reward_types"]) == (253, 101)


def test_quick_pilot_estimates_goal_separately_from_optional_map_completion():
    result = preview(presets()["pilot"], {})
    assert result["estimates"]["breakdown_hours"]["goal_baseline"] == 0.1
    assert result["estimates"]["goal_hours"][1] < 1
    assert result["estimates"]["completion_hours"][0] > 1


def test_new_seed_exports_require_ap_start_and_random_preview_does_not_roll():
    values = {**defaults(), "starting_location": 3}
    result = preview(values, {})
    document = player_document("NewStart", values)
    configuration = build_configuration(document["S.T.A.L.K.E.R. GAMMA"])
    assert result["configuration"]["ap_start"] == 1
    assert result["configuration"]["starting_location"] == 3
    assert result["digest"] == configuration.digest
    assert any("Random native preset" in note for note in result["notes"])
    assert values["ap_start"] == 0


def test_custom_totals_and_insufficient_progression_slots():
    values = {**defaults(), "checks_kill_milestones": 1, "kill_milestones": [1, 500, 10000]}
    result = preview(values, {})
    assert result["check_counts"]["checks_kill_milestones"] == 3
    assert any(row["id"] == 28110000 for row in result["checks"])
    values.update(checks_maps=0, kill_milestones=[1], rewards_quest_keys=1)
    with pytest.raises(ValueError, match="cannot hold"):
        preview(values, {})


@pytest.mark.parametrize("name", [None, "", "   ", "../escape", "a" * 17, "name\nInjected", 123])
def test_player_names_cannot_be_invalid_or_inject_yaml(name):
    with pytest.raises(ValueError, match="name"):
        player_document(name, defaults())


def test_player_document_normalizes_starting_gear_without_mutating_inputs():
    values = {**defaults(), "no_starting_weapons": 1}
    result = player_document("Owen-AP_1", values)
    assert result["name"] == "Owen-AP_1"
    assert result[result["game"]]["starting_firearms"] == 1
    assert values["starting_firearms"] == 0


@pytest.mark.parametrize("name", ["Archipelago", "archipelago", " Archipelago "])
def test_reserved_server_name_is_rejected_before_upstream_generation(name):
    with pytest.raises(ValueError, match="reserved"):
        player_document(name, defaults())


def test_exported_name_matches_the_trimmed_upstream_slot_name():
    assert player_document(" Owen ", defaults())["name"] == "Owen"


@pytest.mark.parametrize("name", ASSUMPTIONS)
def test_playtime_assumptions_reject_invalid_types_and_bounds(name):
    configuration = build_configuration(defaults())
    for value in (True, "5", float("nan"), ASSUMPTIONS[name][1] - 1, ASSUMPTIONS[name][2] + 1):
        with pytest.raises(ValueError, match=name):
            estimate_playtime(configuration, {}, {name: value})


def test_estimates_are_scenarios_sensitive_to_goal_pace_totals_and_wait():
    values = presets()["full_story"]
    basic = preview(defaults(), {})["estimates"]
    full = preview(values, {})["estimates"]
    slower = preview(values, {"pace_percent": 200, "multiworld_wait_minutes": 120})["estimates"]
    assert basic["goal_hours"][0] < full["goal_hours"][0] < slower["goal_hours"][0]
    assert full["completion_hours"][0] >= full["goal_hours"][0]
    assert "not measured" in full["confidence"]
    assert full["breakdown_hours"]["rank_floor"] == 60
    totals = {**defaults(), "checks_side_task_milestones": 1, "side_task_milestones": [1000]}
    assert preview(totals, {})["estimates"]["breakdown_hours"]["tasks"] > 300
    with pytest.raises(ValueError, match="Unknown"):
        estimate_playtime(build_configuration(values), {}, {"invented": 1})
