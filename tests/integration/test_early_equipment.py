import pytest
from BaseClasses import CollectionState
from Fill import distribute_items_restrictive
from Options import OptionError
from test.general import setup_multiworld
from worlds.gamma import GammaWorld
from worlds.gamma.early_equipment import place_equipment

from gamma_archipelago.presets import presets
from gamma_archipelago.web_planner import catalogue


@pytest.mark.parametrize("seed", range(30))
def test_all_local_equipment_arrives_in_three_low_grind_spheres_without_zone_keys(seed):
    multi = setup_multiworld(GammaWorld, options=presets()["full_story"], seed=seed)
    selected = [
        row
        for row in multi.get_filled_locations(1)
        if row.item.name.startswith("Equipment Unlock:")
    ]
    assert len(selected) == 9
    state = CollectionState(multi)
    for _ in range(3):
        accessible = [row for row in selected if row.can_reach(state)]
        for row in accessible:
            state.collect(row.item, True)
            selected.remove(row)
    assert not selected
    assert not any(
        name.startswith("Zone Key:") and count for name, count in state.prog_items[1].items()
    )
    distribute_items_restrictive(multi)
    assert multi.can_beat_game()


def test_explicit_nonlocal_equipment_uses_upstream_early_requests():
    names = {"Equipment Unlock: PDA", "Equipment Unlock: Firearms", "Equipment Unlock: Detector"}
    multi = setup_multiworld(
        GammaWorld, options=presets()["full_story"] | {"non_local_items": names}
    )
    assert names <= multi.early_items[1].keys()
    assert not any(row.item.name in names for row in multi.get_filled_locations(1))


def test_insufficient_early_checks_refuse_instead_of_hiding_gear_behind_late_routes():
    from gamma_archipelago.configuration import GEAR_OPTIONS, defaults

    options = {
        **defaults(),
        **dict.fromkeys(GEAR_OPTIONS, 2),
        "rewards_starting_gear_unlocks": 1,
        "ap_start": 1,
        "checks_rank_milestones": 1,
    }
    multi = setup_multiworld(
        GammaWorld,
        options=options,
        steps=("generate_early", "create_regions", "create_items", "set_rules"),
    )
    world = multi.worlds[1]
    world.opening_placements = []
    with pytest.raises(OptionError, match="Early equipment"):
        place_equipment(world, catalogue())
    assert world.opening_placements == []
