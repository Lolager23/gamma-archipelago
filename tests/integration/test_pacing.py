import json

import pytest
from BaseClasses import CollectionState
from Fill import distribute_items_restrictive
from Options import OptionError
from test.general import setup_multiworld
from test_generation_matrix import assert_seed
from worlds.AutoWorld import call_all
from worlds.gamma import GammaWorld
from worlds.gamma.opening import place_opening

from gamma_archipelago.presets import presets
from gamma_archipelago.web_planner import catalogue

CATALOG = catalogue()


def started_world(options, starting=(), seed=35):
    multiworld = setup_multiworld(
        GammaWorld, steps=("generate_early", "create_regions"), options=options, seed=seed
    )
    world = multiworld.worlds[1]
    for name in starting:
        multiworld.push_precollected(world.create_item(name))
    for step in ("create_items", "set_rules", "connect_entrances", "generate_basic"):
        call_all(multiworld, step)
    return multiworld, world


def test_protected_opening_places_local_pda_before_zone_route_and_preserves_all_counts():
    world = setup_multiworld(GammaWorld, options=presets()["standard"], seed=1)
    gamma = world.worlds[1]
    placement = gamma.opening_placements[0]
    assert placement["item"] == "Equipment Unlock: PDA"
    check = world.get_location(placement["location"], 1)
    assert check.parent_region.name == "l01_escape" and check.item.player == 1
    assert check.can_reach(CollectionState(world))
    distribute_items_restrictive(world)
    assert world.can_beat_game()
    assert all(row.item for row in world.get_locations())


def test_nonlocal_permissions_and_protected_opening_plando_conflicts_are_explicit():
    with pytest.raises(OptionError, match="local"):
        setup_multiworld(
            GammaWorld,
            options={**presets()["standard"], "non_local_items": ["Equipment Unlock: PDA"]},
        )
    multiworld, world = started_world(presets()["standard"])
    item = next(item for item in multiworld.itempool if item.name == "Equipment Unlock: PDA")
    multiworld.itempool.remove(item)
    with pytest.raises(OptionError, match="conflicts"):
        world.pre_fill()


def test_gifted_permissions_reduce_pool_and_precollected_zone_keys_do_not_break_route():
    options = {
        "rewards_zone_keys": 1,
        "checks_settlements": 1,
        "opening_policy": 1,
        "starting_pda": 2,
        "rewards_starting_gear_unlocks": 1,
    }
    multiworld, world = started_world(options, ("Equipment Unlock: PDA", "Zone Key: Garbage"))
    assert "Equipment Unlock: PDA" not in world.pool_budget.required
    assert "Zone Key: Garbage" not in world.pool_budget.required
    world.pre_fill()
    distribute_items_restrictive(multiworld)
    assert multiworld.can_beat_game()
    assert len([item for item in multiworld.itempool if item.name == "Zone Key: Garbage"]) == 0


def test_upstream_from_pool_depletion_is_counted_once_before_filler_replacement():
    options = {
        "rewards_progressive_tools": 1,
        "content_progression": 0,
        "checks_gear_upgrades": 1,
        "start_inventory_from_pool": {"Progressive Tools": 2},
    }
    multiworld, world = started_world(options, ("Progressive Tools",) * 2)
    assert len(world.pool_budget.required) == 3
    assert world.pool_budget.report()["remaining_progression_copies"] == 1
    for _ in range(2):
        item = next(item for item in multiworld.itempool if item.name == "Progressive Tools")
        multiworld.itempool.remove(item)
        multiworld.itempool.append(world.create_filler())
    world.pre_fill()
    distribute_items_restrictive(multiworld)
    assert multiworld.can_beat_game()


def test_opening_rejects_a_permission_check_that_cannot_accept_its_item():
    multiworld, world = started_world(presets()["standard"])
    check = multiworld.get_location("Rookie Village: First Entry", 1)
    check.item_rule = lambda item: False
    with pytest.raises(OptionError, match="own requirements"):
        place_opening(world, CATALOG)


@pytest.mark.parametrize("supply", [None, "Bandage"])
def test_opening_supplies_are_optional_and_bandages_are_a_valid_fallback(supply):
    multiworld, world = started_world(presets()["standard"])
    multiworld.itempool[:] = [
        item
        for item in multiworld.itempool
        if item.name not in {"Medkit", "Bandage"} or item.name == supply
    ]
    if supply:
        multiworld.itempool.append(world.create_item(supply))
    place_opening(world, CATALOG)
    names = [row["item"] for row in world.opening_placements]
    assert names == ["Equipment Unlock: PDA"] + ([supply] if supply else [])


def test_opening_does_not_reserve_a_supply_without_a_spare_check():
    multiworld, world = started_world(
        {
            "opening_policy": 1,
            "starting_pda": 2,
            "rewards_starting_gear_unlocks": 1,
        }
    )
    place_opening(world, CATALOG)
    assert len(world.opening_placements) == 1


@pytest.mark.parametrize("restriction", ["nonlocal_medkit", "nonlocal_both", "item_rule"])
def test_optional_opening_supplies_respect_common_locality_and_location_rules(restriction):
    multiworld, world = started_world(presets()["standard"])
    if restriction.startswith("nonlocal"):
        world.options.non_local_items.value = {"Medkit"}
        if restriction == "nonlocal_both":
            world.options.non_local_items.value.add("Bandage")
    else:
        for check in multiworld.get_locations(1):
            check.item_rule = lambda item: item.name != "Medkit"
    place_opening(world, CATALOG)
    expected = ["Equipment Unlock: PDA"]
    if restriction != "nonlocal_both":
        expected.append("Bandage")
    assert [row["item"] for row in world.opening_placements] == expected


def test_zone_route_uses_another_reachable_map_after_a_reservation():
    multiworld, world = started_world({"rewards_zone_keys": 1}, ("Zone Key: Garbage",))
    multiworld.get_location("Cordon: First Arrival", 1).place_locked_item(
        world.create_item("Bandage")
    )
    world.pre_fill()
    assert multiworld.get_location("Garbage: First Arrival", 1).item is not None


def test_zone_route_refuses_when_all_reachable_map_checks_are_reserved():
    multiworld, world = started_world({"rewards_zone_keys": 1})
    multiworld.get_location("Cordon: First Arrival", 1).place_locked_item(
        world.create_item("Bandage")
    )
    with pytest.raises(OptionError, match="unreserved reachable"):
        world.pre_fill()


@pytest.mark.parametrize("precollected", [False, True])
def test_zone_route_refuses_nonlocal_keys_only_when_they_remain_in_the_pool(precollected):
    starting = ("Zone Key: Garbage",) if precollected else ()
    _, world = started_world({"rewards_zone_keys": 1}, starting)
    world.options.non_local_items.value = {"Zone Key: Garbage"}
    if precollected:
        world.pre_fill()
    else:
        with pytest.raises(OptionError, match="must remain local"):
            world.pre_fill()


@pytest.mark.parametrize("mode", [0, 1, 2])
def test_actual_seed_reports_are_optional_and_spoilers_require_explicit_choice(tmp_path, mode):
    multiworld = setup_multiworld(
        GammaWorld, options={**presets()["standard"], "generation_preview": mode}
    )
    world = multiworld.worlds[1]
    multiworld.seed_name = "preview"
    if mode:
        with pytest.raises(ValueError, match="fill"):
            world.generate_output(str(tmp_path))
    distribute_items_restrictive(multiworld)
    world.generate_output(str(tmp_path))
    files = list(tmp_path.glob("*_gamma_preview.json"))
    assert len(files) == int(mode > 0)
    if not mode:
        return
    data = json.loads(files[0].read_text())
    assert (
        data["kind"] == "actual_generated_seed"
        and data["configuration_key"] == world.configuration.digest
    )
    assert data["budget"]["network_checks"] == len(world.fill_slot_data()["location_ids"])
    assert bool(data.get("spoiler_placements")) == (mode == 2)
    assert data["native_verification"] == "not run"


@pytest.mark.generation
@pytest.mark.parametrize("key", ["Zone Key: Radar", "Zone Key: Lab X16", "Zone Key: Lab X19"])
def test_precollected_psi_zone_keys_never_replace_psi_protection_in_the_route(key):
    for seed in range(50):
        multiworld, world = started_world(presets()["standard"], (key,), seed)
        world.pre_fill()
        distribute_items_restrictive(multiworld)
        assert multiworld.can_beat_game(), (key, seed)


@pytest.mark.generation
def test_independent_pacing_combinations_generate_without_unlock_cycles():
    for combat in range(3):
        for access in range(2):
            for grind in range(1, 4):
                for seed in range(5):
                    assert_seed(
                        {
                            **presets()["standard"],
                            "combat_logic": combat,
                            "access_pacing": access,
                            "grind_profile": grind,
                        },
                        seed,
                    )
