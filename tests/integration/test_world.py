import json
from pathlib import Path

import pytest
from BaseClasses import ItemClassification
from Fill import distribute_items_restrictive
from Options import OptionError
from test.general import setup_multiworld
from worlds.apquest.world import APQuestWorld
from worlds.gamma import GammaWorld

from gamma_archipelago.catalog import GAME, ITEM_NAMES, ITEM_SECTIONS, LOCATION_NAMES

pytestmark = pytest.mark.integration
ROOT = Path(__file__).resolve().parents[2]


def generate(seed, *, mixed=False):
    worlds = [GammaWorld, APQuestWorld] if mixed else [GammaWorld]
    multiworld = setup_multiworld(worlds, seed=seed)
    distribute_items_restrictive(multiworld)
    return multiworld


def test_world_uses_real_upstream_types_and_catalogue():
    world = generate(123).worlds[1]
    assert world.game == GAME
    assert world.item_name_to_id == ITEM_NAMES
    assert world.location_name_to_id == LOCATION_NAMES
    assert world.create_item("Basic Toolkit").classification == ItemClassification.useful
    assert world.create_item("Medkit").classification == ItemClassification.filler
    assert world.get_filler_item_name() == "Bandage"
    slot_data = world.fill_slot_data()
    assert slot_data["schema_version"] == 3 and slot_data["pilot"] is False
    assert slot_data["goal"] == "visit_all_pilot_regions"
    assert slot_data["configuration"] == world.configuration.to_values()
    assert slot_data["configuration_key"] == world.configuration.digest
    source = ROOT / "src/gamma_archipelago/catalog.json"
    assert json.loads(source.read_text()) == json.loads(
        (ROOT / "apworld/gamma/catalog.json").read_text()
    )


def test_world_generation_rejects_invalid_options_instead_of_ignoring_them():
    world = generate(123).worlds[1]
    world.options.kill_milestones.value = [10, 10]
    with pytest.raises(OptionError, match="strictly increasing"):
        world.generate_early()


def test_one_thousand_pilot_seeds_are_fully_filled_and_beatable():
    for seed in range(1000):
        multiworld = generate(seed)
        locations = multiworld.get_locations(1)
        assert len(locations) == 33
        assert {location.item.name for location in locations} == {
            name for name, identity in ITEM_NAMES.items() if identity in ITEM_SECTIONS
        }
        assert multiworld.can_beat_game()
        assert all(multiworld.state.can_reach(location) for location in locations)


def test_deterministic_generation_and_mixed_game_multiworld():
    def placements(multiworld):
        return [
            (location.name, location.item.name, location.item.player)
            for location in multiworld.get_locations()
        ]

    assert placements(generate(1234)) == placements(generate(1234))
    multiworld = generate(1234, mixed=True)
    assert multiworld.can_beat_game()
    assert all(location.item is not None for location in multiworld.get_locations())


@pytest.mark.parametrize("maps,settlements,count", [(1, 0, 33), (0, 1, 18), (1, 1, 51)])
def test_category_manifests_pools_and_reachability(maps, settlements, count):
    from gamma_archipelago.catalog import enabled_location_ids

    multiworld = setup_multiworld(
        GammaWorld, seed=88, options={"checks_maps": maps, "checks_settlements": settlements}
    )
    distribute_items_restrictive(multiworld)
    world = multiworld.worlds[1]
    expected = enabled_location_ids(world.configuration.checks)
    assert len(multiworld.get_locations(1)) == len(expected) == count
    assert set(world.fill_slot_data()["location_ids"]) == expected
    assert all(location.item is not None for location in multiworld.get_locations(1))
    assert multiworld.can_beat_game()


@pytest.mark.parametrize(
    "category,count",
    [
        ("checks_mutant_first_kills", 25),
        ("checks_faction_first_kills", 13),
        ("checks_kill_milestones", 3),
        ("checks_artefacts", 66),
    ],
)
def test_combat_categories_and_custom_milestones_generate_exactly(category, count):
    from gamma_archipelago.catalog import enabled_location_ids

    multiworld = setup_multiworld(
        GammaWorld,
        seed=51,
        options={
            "checks_maps": 0,
            category: 1,
            "kill_milestones": [1, 9, 10000],
        },
    )
    distribute_items_restrictive(multiworld)
    world = multiworld.worlds[1]
    assert len(multiworld.get_locations(1)) == count
    assert set(world.fill_slot_data()["location_ids"]) == enabled_location_ids(
        world.configuration.checks, world.configuration.kill_milestones
    )
    assert all(location.item for location in multiworld.get_locations())
    assert multiworld.can_beat_game()


def test_single_threshold_seed_has_one_reward_without_pool_overflow():
    multiworld = setup_multiworld(
        GammaWorld,
        options={
            "checks_maps": 0,
            "checks_kill_milestones": 1,
            "kill_milestones": [1],
        },
    )
    distribute_items_restrictive(multiworld)
    assert len(multiworld.get_locations()) == 1
    assert next(iter(multiworld.get_locations())).item is not None


@pytest.mark.parametrize(
    "category,count",
    [
        ("checks_quest_types", 13),
        ("checks_story_milestones", 53),
        ("checks_side_task_milestones", 3),
    ],
)
def test_task_categories_generate_independently_with_stable_custom_thresholds(category, count):
    from gamma_archipelago.catalog import enabled_location_ids

    multiworld = setup_multiworld(
        GammaWorld,
        seed=91,
        options={
            "checks_maps": 0,
            category: 1,
            "side_task_milestones": [1, 3, 10000],
        },
    )
    distribute_items_restrictive(multiworld)
    world = multiworld.worlds[1]
    assert len(multiworld.get_locations(1)) == count
    assert set(world.fill_slot_data()["location_ids"]) == enabled_location_ids(
        world.configuration.checks,
        world.configuration.kill_milestones,
        world.configuration.side_task_milestones,
    )
    assert all(location.item for location in multiworld.get_locations())
    assert multiworld.can_beat_game()


@pytest.mark.parametrize(
    "category,count",
    [
        ("checks_gear_upgrades", 6),
        ("checks_armour_tiers", 4),
        ("checks_weapon_tiers", 6),
        ("checks_knife_tiers", 4),
    ],
)
def test_equipment_categories_generate_independently(category, count):
    multiworld = setup_multiworld(GammaWorld, seed=12, options={"checks_maps": 0, category: 1})
    distribute_items_restrictive(multiworld)
    assert len(multiworld.get_locations()) == count
    assert all(location.item for location in multiworld.get_locations())
    assert multiworld.can_beat_game()


def test_rank_category_generates_exactly_the_eight_supported_ranks():
    multiworld = setup_multiworld(
        GammaWorld, seed=13, options={"checks_maps": 0, "checks_rank_milestones": 1}
    )
    distribute_items_restrictive(multiworld)
    assert len(multiworld.get_locations()) == 8
    assert all(location.item for location in multiworld.get_locations())
    assert multiworld.can_beat_game()


def test_loot_stash_pool_is_optional_seeded_and_fits_even_one_check():
    from gamma_archipelago.catalog import ITEM_IDS, enabled_item_ids

    placements = []
    for seed in (1, 1, 2):
        multiworld = setup_multiworld(GammaWorld, seed=seed, options={"rewards_loot_stashes": 1})
        distribute_items_restrictive(multiworld)
        world = multiworld.worlds[1]
        names = [location.item.name for location in multiworld.get_locations()]
        assert any("Loot Stash:" in name for name in names)
        assert "Basic Toolkit" in names
        assert set(world.fill_slot_data()["item_ids"]) == ITEM_IDS - {
            28051201,
            *range(28051301, 28051309),
            *range(28051401, 28051405),
            *range(28051501, 28051504),
        }
        assert enabled_item_ids(world.configuration.rewards) == ITEM_IDS - {
            28051201,
            *range(28051301, 28051309),
            *range(28051401, 28051405),
            *range(28051501, 28051504),
        }
        assert multiworld.can_beat_game()
        placements.append(names)
    assert placements[0] == placements[1] and placements[0] != placements[2]
    single = setup_multiworld(
        GammaWorld,
        options={
            "checks_maps": 0,
            "checks_kill_milestones": 1,
            "kill_milestones": [1],
            "rewards_loot_stashes": 1,
        },
    )
    distribute_items_restrictive(single)
    assert "Loot Stash:" in next(iter(single.get_locations())).item.name


def test_orange_stash_is_required_and_its_local_claim_is_a_separate_event():
    from BaseClasses import CollectionState

    multiworld = setup_multiworld(GammaWorld, seed=15, options={"rewards_progression_stashes": 1})
    world = multiworld.worlds[1]
    claim = multiworld.get_location("Claim Cordon Psi Stash", 1)
    state = CollectionState(multiworld)
    assert not claim.can_reach(state)
    state.collect(world.create_item("Progression Stash: Calibrated Psi Helmet"))
    assert claim.can_reach(state)
    assert claim.address is None and claim.item.code is None
    assert claim.item.name == "Calibrated Psi Protection"
    distribute_items_restrictive(multiworld)
    assert len(world.fill_slot_data()["location_ids"]) == 33
    assert 28051201 in world.fill_slot_data()["item_ids"]
    assert (
        len(
            [
                loc
                for loc in multiworld.get_locations()
                if loc.item.name == "Progression Stash: Calibrated Psi Helmet"
            ]
        )
        == 1
    )
    assert multiworld.can_beat_game()
    for location in list(multiworld.get_locations()):
        if location.address is not None:
            location.item = None
            location.locked = False
            location.parent_region.locations.remove(location)
    with pytest.raises(OptionError, match="cannot hold"):
        world.create_items()


def test_quest_permissions_are_required_items_and_gate_their_story_checks():
    from BaseClasses import CollectionState

    multiworld = setup_multiworld(
        GammaWorld, options={"checks_story_milestones": 1, "rewards_quest_keys": 1}
    )
    world = multiworld.worlds[1]
    location = next(loc for loc in multiworld.get_locations() if loc.address == 28052601)
    state = CollectionState(multiworld)
    assert not location.can_reach(state)
    state.collect(world.create_item("Quest Key: Living Legend"))
    assert location.can_reach(state)
    distribute_items_restrictive(multiworld)
    assert multiworld.can_beat_game()
    assert all(
        any(loc.item.name == name for loc in multiworld.get_locations())
        for name in (
            "Quest Key: Living Legend",
            "Quest Key: Mortal Sin",
            "Quest Key: Operation Afterglow",
        )
    )
