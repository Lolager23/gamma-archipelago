from gamma_archipelago.configuration import build_configuration
from gamma_archipelago.presets import presets


def test_presets_are_independent_valid_configurations_with_safe_supply_defaults():
    first, second = presets(), presets()
    assert len(first) == 9
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
