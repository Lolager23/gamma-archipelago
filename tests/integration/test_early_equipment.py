import pytest
from BaseClasses import CollectionState
from Fill import distribute_items_restrictive
from Options import OptionError
from test.general import setup_multiworld
from worlds.gamma import GammaWorld
from worlds.gamma.early_equipment import place_equipment

from gamma_archipelago.presets import presets
from gamma_archipelago.web_planner import catalogue


@pytest.mark.parametrize("seed", range(10))
@pytest.mark.parametrize("starting", [0, 1, 2])
def test_equipment_and_workshops_arrive_in_three_low_grind_spheres_without_zone_keys(
    seed, starting
):
    multi = setup_multiworld(
        GammaWorld, options=presets()["full_story"] | {"starting_location": starting}, seed=seed
    )
    selected = [
        row
        for row in multi.get_filled_locations(1)
        if row.item.name.startswith(("Equipment Unlock:", "Workshop Access:"))
    ]
    assert len(selected) == 12
    assert not any(row.name.startswith("Reach Stalker Rank:") for row in selected)
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
    names = {
        "Equipment Unlock: PDA",
        "Equipment Unlock: Firearms",
        "Equipment Unlock: Detector",
        "Workshop Access: Repair",
        "Workshop Access: Upgrades",
        "Workshop Access: Crafting",
    }
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
        "checks_gear_upgrades": 1,
        "exclude_locations": [
            region + ": First Arrival"
            for region in (
                "Garbage",
                "Great Swamps",
                "Darkscape",
                "Meadow",
                "Agroprom",
                "Dark Valley",
                "Rostok",
                "Truck Cemetery",
                "Wild Territory",
                "Army Warehouses",
                "Yantar",
            )
        ],
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


def test_gifts_and_existing_plando_equipment_are_not_duplicated_or_moved():
    from test_pacing import started_world

    gifts = ("Equipment Unlock: PDA", "Workshop Access: Repair")
    multi, world = started_world(presets()["full_story"], gifts)
    plans = []
    for name, location in (
        ("Equipment Unlock: Helmet", "Darkscape: First Arrival"),
        ("Workshop Access: Upgrades", "Meadow: First Arrival"),
    ):
        item = next(row for row in multi.itempool if row.name == name)
        multi.itempool.remove(item)
        planned = multi.get_location(location, 1)
        planned.place_locked_item(item)
        plans.append((planned, item))
    world.pre_fill()
    assert all(planned.item is item for planned, item in plans)
    assert not any(
        row["item"] in {*gifts, "Equipment Unlock: Helmet", "Workshop Access: Upgrades"}
        for row in world.opening_placements
    )
    distribute_items_restrictive(multi)
    assert multi.can_beat_game()


@pytest.mark.parametrize(
    "change", [{"rewards_workshop_access": 0}, {"playability_logic": 0}, {"content_progression": 0}]
)
def test_disabled_workshops_and_legacy_placement_do_not_gain_reservations(change):
    multi = setup_multiworld(GammaWorld, options=presets()["full_story"] | change)
    assert not any(
        row.item.name.startswith("Workshop Access:") for row in multi.get_filled_locations(1)
    )


def test_workshop_only_activity_pool_uses_starting_access_without_gear_locks():
    multi = setup_multiworld(
        GammaWorld, options={"rewards_workshop_access": 1, "checks_gear_upgrades": 1}
    )
    workshops = [
        row for row in multi.get_filled_locations(1) if row.item.name.startswith("Workshop Access:")
    ]
    assert len(workshops) == 3
    assert all(row.can_reach(CollectionState(multi)) for row in workshops)


def test_unlocked_nearby_maps_keep_small_custom_equipment_pools_supported():
    multi = setup_multiworld(
        GammaWorld,
        options={
            "checks_gear_upgrades": 1,
            "starting_outfit": 2,
            "starting_helmet": 2,
            "rewards_starting_gear_unlocks": 1,
        },
    )
    world = multi.worlds[1]
    assert len(world.opening_placements) == 2
    assert any(row["location"] == "Cordon: First Arrival" for row in world.opening_placements)
    distribute_items_restrictive(multi)
    assert multi.can_beat_game()


def test_filler_only_rank_checks_preserve_the_sparse_exploration_fallback():
    multi = setup_multiworld(
        GammaWorld,
        options={
            "quest_zone_logic": 0,
            "checks_rank_milestones": 1,
            "rewards_zone_keys": 1,
            "rewards_starting_gear_unlocks": 1,
            "starting_pda": 2,
        },
        seed=42,
    )
    assert not multi.worlds[1].opening_placements
    distribute_items_restrictive(multi)
    ranks = [loc for loc in multi.get_locations(1) if loc.name.startswith("Reach Stalker Rank:")]
    assert len(ranks) == 8
    assert all(not loc.item.advancement and not loc.item.useful for loc in ranks)
    assert multi.can_beat_game()
