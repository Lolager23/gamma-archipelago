import pytest
from BaseClasses import CollectionState, LocationProgressType
from Fill import distribute_items_restrictive
from test.general import setup_multiworld
from worlds.gamma import GammaWorld

from gamma_archipelago.discovery import QUOTAS, protected_tail_ids
from gamma_archipelago.presets import presets


@pytest.mark.parametrize("seed", range(6))
def test_tail_fill_and_seeded_starting_permission_are_beatably_placed(seed):
    values = presets()["full_story"] | {
        "mutant_discovery_mode": 1,
        "mutant_discovery_count": 15,
        "mutant_filler_tail": 5,
        "artefact_discovery_mode": 1,
        "artefact_discovery_count": 30,
        "artefact_filler_tail": 10,
        "random_starting_unlock": 1,
    }
    multiworld = setup_multiworld(GammaWorld, seed=seed, options=values)
    world = multiworld.worlds[1]
    gifted = multiworld.precollected_items[1]
    assert len(gifted) == 1 and gifted[0].name in {
        "Equipment Unlock: PDA",
        "Equipment Unlock: Detector",
        "Equipment Unlock: Firearms",
    }
    assert gifted[0].name not in world.pool_budget.required
    assert (
        sum(
            name == gifted[0].name
            for name, count in world.pool_budget.starting
            for _ in range(count)
        )
        == 1
    )
    protected = protected_tail_ids(
        world.configuration, frozenset(world.fill_slot_data()["location_ids"])
    )
    assert protected == frozenset(QUOTAS["mutant"][10:15] + QUOTAS["artefact"][20:30])
    distribute_items_restrictive(multiworld)
    assert multiworld.can_beat_game()
    for location in multiworld.get_locations():
        if location.address in protected:
            assert location.progress_type == LocationProgressType.EXCLUDED
            assert location.item.classification == 0
    copy = setup_multiworld(GammaWorld, seed=seed, options=values)
    assert copy.precollected_items[1][0].name == gifted[0].name


@pytest.mark.parametrize("mode", [0, 1, 2])
def test_pda_detector_and_weapon_requirements_apply_to_typed_and_generic_checks(mode):
    values = dict(
        equipment_class_progression=0,
        checks_quest_types=1,
        checks_side_task_milestones=1,
        checks_story_milestones=1,
        checks_artefacts=1,
        checks_mutant_first_kills=1,
        checks_kill_milestones=1,
        starting_pda=mode,
        starting_detector=mode,
        starting_firearms=mode,
        starting_melee=mode,
        rewards_starting_gear_unlocks=int(mode == 2),
        mutant_discovery_mode=1,
        artefact_discovery_mode=1,
    )
    multiworld = setup_multiworld(
        GammaWorld,
        options=values,
        steps=("generate_early", "create_regions", "create_items", "set_rules"),
    )
    for address, permission in [
        (28052501, "PDA"),
        (28120005, "PDA"),
        (QUOTAS["artefact"][0], "Detector"),
    ]:
        state = CollectionState(multiworld)
        location = next(loc for loc in multiworld.get_locations() if loc.address == address)
        assert location.access_rule(state) == (mode != 2)
        state.collect(multiworld.worlds[1].create_item("Equipment Unlock: " + permission))
        assert location.access_rule(state)
    mutant = next(loc for loc in multiworld.get_locations() if loc.address == QUOTAS["mutant"][0])
    assert mutant.access_rule(state) == (mode != 2)
    state.collect(multiworld.worlds[1].create_item("Equipment Unlock: Melee"))
    assert mutant.access_rule(state)


def test_random_gift_never_duplicates_common_starting_permissions():
    names = ["Equipment Unlock: PDA", "Equipment Unlock: Firearms", "Equipment Unlock: Detector"]
    values = dict(
        starting_pda=2,
        starting_firearms=2,
        starting_detector=2,
        rewards_starting_gear_unlocks=1,
        random_starting_unlock=1,
    )
    world = setup_multiworld(
        GammaWorld, options=values | {"start_inventory": dict.fromkeys(names[:2], 1)}
    )
    assert [item.name for item in world.precollected_items[1]] == names[2:]
    full = setup_multiworld(
        GammaWorld,
        steps=("generate_early",),
        options=values | {"start_inventory_from_pool": dict.fromkeys(names, 1)},
    )
    assert not full.precollected_items[1]


@pytest.mark.generation
@pytest.mark.parametrize("start", range(3))
def test_thirty_full_story_seeds_per_start_with_generic_tails_and_random_gifts(start):
    from test_generation_matrix import assert_seed

    values = presets()["full_story"] | {
        "starting_location": start,
        "random_starting_unlock": 1,
        "mutant_discovery_mode": 1,
        "mutant_discovery_count": 15,
        "mutant_filler_tail": 5,
        "artefact_discovery_mode": 1,
        "artefact_discovery_count": 30,
        "artefact_filler_tail": 10,
    }
    for seed in range(30):
        assert_seed(values, seed)
