"""Recipe permissions belong to the first three real paced reward waves."""

import pytest
from BaseClasses import LocationProgressType
from Fill import distribute_items_restrictive
from Options import OptionError
from test.general import setup_multiworld
from test_pacing import started_world
from worlds.gamma import GammaWorld
from worlds.gamma.analysis import analyse, early_checks
from worlds.gamma.early_recipes import place_recipes

from gamma_archipelago.presets import presets
from gamma_archipelago.web_planner import catalogue

RECIPES = {"Recipe Access: " + group for group in ("General", "Medical", "Ammunition", "Artefacts")}


@pytest.mark.parametrize("seed", range(10))
@pytest.mark.parametrize("starting", [0, 1, 2])
def test_all_recipes_are_received_by_paced_step_three(seed, starting):
    multi = setup_multiworld(
        GammaWorld,
        options=presets()["full_story"] | {"starting_location": starting},
        seed=seed,
    )
    distribute_items_restrictive(multi)
    report = analyse(multi.worlds[1], True, True)
    recipes = {
        row["item"]: step["step"]
        for step in report["steps"]
        for row in step["available_checks"]
        if row["item"].startswith("Recipe Access:")
    }
    assert len(recipes) == 4
    assert max(recipes.values()) <= 3, recipes
    assert report["goal_reachable"] and report["unreachable_checks"] == 0


@pytest.mark.parametrize(
    "change", [{"playability_logic": 0}, {"regional_progression": 0}, {"rewards_recipe_access": 0}]
)
def test_disabled_recipe_pacing_leaves_ordinary_fill_unchanged(change):
    multi = setup_multiworld(GammaWorld, options={"rewards_recipe_access": 1} | change)
    assert not multi.worlds[1].opening_placements
    assert not any(row.item.name in RECIPES for row in multi.get_filled_locations())
    distribute_items_restrictive(multi)
    assert multi.can_beat_game()


@pytest.mark.parametrize("all_recipes", [False, True])
def test_starting_recipe_gifts_are_not_duplicated(all_recipes):
    gifts = tuple(sorted(RECIPES)) if all_recipes else ("Recipe Access: General",)
    multi, world = started_world({"rewards_recipe_access": 1}, gifts)
    world.pre_fill()
    for name in gifts:
        assert not any(row["item"] == name for row in world.opening_placements)
        assert not any(item.name == name for item in multi.itempool)
        assert not any(row.item.name == name for row in multi.get_filled_locations())
    assert len(world.opening_placements) == 4 - len(gifts)
    distribute_items_restrictive(multi)
    assert multi.can_beat_game()


def test_start_inventory_from_pool_depletes_the_recipe_once():
    name = "Recipe Access: General"
    multi, world = started_world(
        {"rewards_recipe_access": 1, "start_inventory_from_pool": {name: 1}},
        (name,),
    )
    multi.itempool.remove(next(item for item in multi.itempool if item.name == name))
    multi.itempool.append(world.create_filler())
    world.pre_fill()
    assert len(world.opening_placements) == 3
    assert all(row["item"] != name for row in world.opening_placements)
    distribute_items_restrictive(multi)
    assert multi.can_beat_game()


@pytest.mark.parametrize("late", [False, True])
def test_planned_recipe_is_preserved_and_a_late_conflict_fails_before_mutation(late):
    multi, world = started_world({"rewards_recipe_access": 1})
    world.opening_placements = []
    location = multi.get_location("Cordon: First Arrival", 1)
    item = next(item for item in multi.itempool if item.name == "Recipe Access: Medical")
    multi.itempool.remove(item)
    location.place_locked_item(item)
    before = multi.itempool[:]
    if late:
        location.access_rule = lambda state: False
        with pytest.raises(OptionError, match="Placed recipe access"):
            place_recipes(world, catalogue())
        assert multi.itempool == before
        assert world.opening_placements == []
        assert [row for row in multi.get_filled_locations() if row.address is not None] == [
            location
        ]
    else:
        place_recipes(world, catalogue())
        assert len(world.opening_placements) == 3
        assert all(row["item"] != item.name for row in world.opening_placements)
    assert location.item is item


def test_insufficient_opening_capacity_does_not_partially_place_recipes():
    multi, world = started_world({"rewards_recipe_access": 1})
    world.opening_placements = []
    for location in multi.get_locations():
        location.item_rule = lambda item: False
    for location in list(multi.get_locations(1))[:3]:
        location.item_rule = lambda item: True
    before = multi.itempool[:]
    with pytest.raises(OptionError, match="first three paced steps"):
        place_recipes(world, catalogue())
    assert multi.itempool == before
    assert world.opening_placements == []
    assert not any(row.address is not None for row in multi.get_filled_locations())


def test_excluded_names_flags_and_item_rules_are_respected():
    gifts = tuple(sorted(RECIPES - {"Recipe Access: Medical"}))
    multi, world = started_world({"rewards_recipe_access": 1}, gifts)
    world.opening_placements = []
    allowed = {"Cordon: First Arrival", "Garbage: First Arrival", "Rostok: First Arrival"}
    for location in multi.get_locations():
        location.item_rule = lambda item, valid=location.name in allowed: valid
    world.options.exclude_locations.value = {"Cordon: First Arrival"}
    multi.get_location("Garbage: First Arrival", 1).progress_type = LocationProgressType.EXCLUDED
    place_recipes(world, catalogue())
    assert world.opening_placements == [
        {"location": "Rostok: First Arrival", "item": "Recipe Access: Medical", "finder": "1"}
    ]


@pytest.mark.parametrize("locality", ["local_items", "non_local_items"])
def test_two_slots_respect_explicit_recipe_locality_and_receive_them_early(locality):
    multi = setup_multiworld(
        [GammaWorld, GammaWorld], options={"rewards_recipe_access": 1, locality: RECIPES}, seed=35
    )
    distribute_items_restrictive(multi)
    for player in (1, 2):
        recipes = [
            row
            for row in multi.get_filled_locations()
            if row.item.player == player and row.item.name in RECIPES
        ]
        assert len(recipes) == 4
        assert all((row.player == player) == (locality == "local_items") for row in recipes)
        assert all(early_checks(multi.worlds[player])[row] <= 3 for row in recipes)
    assert multi.can_beat_game()


def test_nonlocal_recipe_in_a_solo_world_reports_the_conflict():
    with pytest.raises(OptionError, match="relax locality/plando"):
        setup_multiworld(
            GammaWorld, options={"rewards_recipe_access": 1, "non_local_items": RECIPES}
        )


def test_partial_analysis_uses_plans_without_mutating_the_world_and_defers_tiers():
    multi, world = started_world({})
    names = ("Cordon: First Arrival", "Garbage: First Arrival", "Rostok: First Arrival")
    plan = {
        multi.get_location(name, 1): world.create_item("Progressive Firearm Class")
        for name in names
    }
    later = multi.get_location("Darkscape: First Arrival", 1)
    later.access_rule = lambda state: state.count("Progressive Firearm Class", 1) >= 3
    assert later not in early_checks(world, placements=plan)
    assert early_checks(world, steps=4, placements=plan)[later] == 4
    assert early_checks(world, steps=0) == {}
    assert all(location.item is None and item.location is None for location, item in plan.items())
    assert multi.state.count("Progressive Firearm Class", 1) == 0


def test_recipe_sampling_can_choose_step_three_but_not_a_later_task(monkeypatch):
    remaining = "Recipe Access: Artefacts"
    multi, world = started_world(
        {
            "checks_maps": 0,
            "checks_side_task_milestones": 1,
            "side_task_milestones": [1, 2, 3, 4],
            "rewards_recipe_access": 1,
        },
        tuple(sorted(RECIPES - {remaining})),
    )
    world.opening_placements = []
    monkeypatch.setattr(
        world.random, "choice", lambda candidates: max(candidates, key=lambda row: row.address)
    )
    place_recipes(world, catalogue())
    assert multi.get_location("Complete 3 Side Tasks", 1).item.name == remaining
    assert multi.get_location("Complete 4 Side Tasks", 1).item is None
    assert len(world.opening_placements) == 1
