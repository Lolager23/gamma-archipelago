from gamma_archipelago.configuration import build_configuration
from gamma_archipelago.presets import presets


def test_presets_are_independent_valid_configurations_with_safe_supply_defaults():
    first, second = presets(), presets()
    assert len(first) == 10
    for name, values in first.items():
        assert build_configuration(values).to_values() == values
        assert values["starting_food"] == 100
        assert second[name] == values
    first["mvp"]["goal"] = 5
    assert presets()["mvp"]["goal"] == 2


def test_mutating_one_presets_threshold_list_does_not_change_another():
    values = presets()
    values["full_story"]["kill_milestones"].append(500)
    assert values["full_labs"]["kill_milestones"] == [10, 25, 50, 100]


def test_pilot_uses_quick_dialogue_goal_without_changing_legacy_defaults():
    from gamma_archipelago.configuration import defaults

    assert build_configuration(presets()["pilot"]).goal == "talk_sidorovich"
    assert build_configuration(defaults()).goal == "pilot_tour"


def test_all_fresh_presets_default_to_generic_mutant_faction_and_artefact_checks():
    from gamma_archipelago.discovery import GROUPS
    from gamma_archipelago.web_planner import metadata

    for values in metadata()["presets"].values():
        assert all(values[f"{group}_discovery_mode"] == 1 for group in GROUPS)


def test_story_tiers_have_distinct_endings_and_optional_chains():
    from gamma_archipelago.discovery import configured_location_ids
    from gamma_archipelago.web_planner import catalogue, metadata, player_document

    data = catalogue()
    living, full = (
        build_configuration(presets()[name]) for name in ("living_legend", "full_story")
    )
    assert living.goal == "living_legend" and full.goal == "operation_afterglow"
    assert "checks_story_milestones" in living.checks & full.checks
    for arc in ("living_legend", "mortal_sin", "operation_afterglow"):
        ids = {row["id"] for row in data["locations"] if row.get("story_arc") == arc}
        assert ids and ids <= configured_location_ids(full)
        if arc == "living_legend":
            assert ids <= configured_location_ids(living)
        else:
            assert not ids & configured_location_ids(living)
    for name in ("living_legend", "full_story"):
        values = presets()[name]
        assert metadata()["presets"][name] == values
        assert player_document("StoryTier", values)[data["game"]] == values
    values = presets()["living_legend"]
    values["checks_mortal_sin"] = 1
    values["checks_operation_afterglow"] = 1
    assert build_configuration(values).goal == "living_legend"
    assert presets()["living_legend"]["checks_mortal_sin"] == 0
    # A saved/exported former Full Story configuration keeps its original ending.
    old = presets()["full_story"] | {"goal": 4}
    assert build_configuration(old).goal == "living_legend"
    assert old["checks_mortal_sin"] == old["checks_operation_afterglow"] == 1
