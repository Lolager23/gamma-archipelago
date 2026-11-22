"""Generation availability, not a substitute for engine playtesting or balance."""

import json
from itertools import combinations
from pathlib import Path

import pytest
from BaseClasses import CollectionState
from Fill import distribute_items_restrictive
from Options import OptionError
from test.general import setup_multiworld
from worlds.gamma import GammaWorld

from gamma_archipelago.configuration import CHECK_OPTIONS, GOALS, REWARD_OPTIONS
from gamma_archipelago.presets import presets

pytestmark = pytest.mark.integration
ROOT = Path(__file__).resolve().parents[2]


def assert_seed(options, seed):
    multiworld = setup_multiworld(GammaWorld, seed=seed, options=options)
    distribute_items_restrictive(multiworld)
    GammaWorld.stage_finalize_multiworld(multiworld)
    GammaWorld.stage_pre_output(multiworld)
    assert all(location.item is not None for location in multiworld.get_locations())
    assert multiworld.can_beat_game()
    state = CollectionState(multiworld)
    state.sweep_for_advancements()
    assert all(location.can_reach(state) for location in multiworld.get_locations())
    world = multiworld.worlds[1]
    assert len(world.fill_slot_data()["location_ids"]) == len(
        [location for location in multiworld.get_locations() if location.address is not None]
    )


@pytest.mark.parametrize("name,options", presets().items())
@pytest.mark.generation
def test_one_thousand_seeds_for_each_documented_preset(name, options):
    for seed in range(1000):
        assert_seed(options, seed)


@pytest.mark.generation
def test_each_category_and_every_pair_generate_without_implicit_dependency_changes():
    names = CHECK_OPTIONS + REWARD_OPTIONS
    for seed, selected in enumerate([(name,) for name in names] + list(combinations(names, 2))):
        options = {name: 1 for name in selected}
        if "rewards_zone_keys" in selected and {
            "rewards_progressive_tools",
            "rewards_workshop_access",
            "rewards_recipe_access",
        } & set(selected):
            with pytest.raises(OptionError, match="cannot hold"):
                setup_multiworld(GammaWorld, seed=seed, options=options)
            continue
        if "rewards_zone_keys" in selected and set(selected) & {
            "rewards_artefacts",
            "rewards_supply_medical",
            "rewards_supply_maintenance",
            "rewards_supply_ammunition",
            "rewards_supply_expedition",
            "rewards_loot_stashes",
            "rewards_stat_levels",
        }:
            # Explicit default counts exceed the maps-only pool after 32 keys.
            with pytest.raises(OptionError, match="quantities"):
                setup_multiworld(GammaWorld, seed=seed, options=options)
            continue
        if "rewards_starting_gear_unlocks" in selected:
            options["starting_pda"] = 2
            if "rewards_zone_keys" in selected:
                options["checks_quest_types"] = (
                    1  # Class rewards need reliable slots after 32 keys.
                )
                options["checks_settlements"] = 1
        if "rewards_zone_keys" in selected and any(
            name in selected for name in ("rewards_progression_stashes", "rewards_quest_keys")
        ):
            options["checks_settlements"] = 1
        # Zone keys intentionally need their map-check route; maps default on.
        assert_seed(options, seed)
    for goal in range(len(GOALS)):
        for seed in range(10):
            assert_seed({**presets()["full_story"], "goal": goal}, seed)


def test_impossible_pool_and_explicit_zone_location_exclusions_are_rejected():
    with pytest.raises(OptionError, match="cannot hold"):
        setup_multiworld(
            GammaWorld,
            options={
                "checks_maps": 0,
                "checks_kill_milestones": 1,
                "kill_milestones": [1],
                "rewards_quest_keys": 1,
            },
        )
    with pytest.raises(OptionError, match="exclude"):
        setup_multiworld(
            GammaWorld,
            options={"rewards_zone_keys": 1, "exclude_locations": ["Cordon: First Arrival"]},
        )


def test_preset_yaml_files_match_the_validated_python_definitions():
    import yaml

    for name, values in presets().items():
        content = yaml.safe_load((ROOT / "presets" / f"{name}.yaml").read_text())
        assert content[GammaWorld.game] == values
        assert content["game"] == GammaWorld.game
    report = {name: {"seeds": 1000, "options": values} for name, values in presets().items()}
    (ROOT / "artifacts").mkdir(exist_ok=True)
    (ROOT / "artifacts/generation-matrix.json").write_text(json.dumps(report, indent=2))
