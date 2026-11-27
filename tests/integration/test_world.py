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


def network_locations(multiworld):
    return [loc for loc in multiworld.get_locations(1) if loc.address is not None]


def generate(seed, *, mixed=False):
    worlds = [GammaWorld, APQuestWorld] if mixed else [GammaWorld]
    multiworld = setup_multiworld(
        worlds,
        seed=seed,
        options={
            "reward_quantities": 0,
            "quest_zone_logic": 0,
            "regional_progression": 0,
            "varied_filler": 0,
        },
    )
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


@pytest.mark.generation
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
    assert len(network_locations(multiworld)) == len(expected) == count
    assert set(world.fill_slot_data()["location_ids"]) == expected
    assert all(location.item is not None for location in multiworld.get_locations(1))
    assert multiworld.can_beat_game()


@pytest.mark.parametrize(
    "category,count",
    [
        ("checks_mutant_first_kills", 25),
        ("checks_faction_first_kills", 13),
        ("checks_kill_milestones", 3),
        ("checks_artefacts", 40),
    ],
)
def test_combat_categories_and_custom_milestones_generate_exactly(category, count):
    from gamma_archipelago.discovery import configured_location_ids

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
    assert len(network_locations(multiworld)) == count
    assert set(world.fill_slot_data()["location_ids"]) == configured_location_ids(
        world.configuration
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
    assert len(network_locations(multiworld)) == 1
    assert next(iter(network_locations(multiworld))).item is not None


@pytest.mark.parametrize(
    "category,count",
    [
        ("checks_quest_types", 12),
        ("checks_story_milestones", 21),
        ("checks_side_task_milestones", 3),
    ],
)
def test_task_categories_generate_independently_with_stable_custom_thresholds(category, count):
    from gamma_archipelago.discovery import configured_location_ids

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
    assert len(network_locations(multiworld)) == count
    assert set(world.fill_slot_data()["location_ids"]) == configured_location_ids(
        world.configuration
    )
    assert all(location.item for location in multiworld.get_locations())
    assert multiworld.can_beat_game()


@pytest.mark.parametrize(
    "category,count",
    [
        ("checks_gear_upgrades", 6),
        ("checks_armour_tiers", 4),
        ("checks_weapon_tiers", 10),
        ("checks_knife_tiers", 4),
    ],
)
def test_equipment_categories_generate_independently(category, count):
    multiworld = setup_multiworld(GammaWorld, seed=12, options={"checks_maps": 0, category: 1})
    distribute_items_restrictive(multiworld)
    assert len([loc for loc in multiworld.get_locations() if loc.address]) == count
    assert all(location.item for location in multiworld.get_locations())
    assert multiworld.can_beat_game()


def test_rank_category_generates_exactly_the_eight_supported_ranks():
    multiworld = setup_multiworld(
        GammaWorld, seed=13, options={"checks_maps": 0, "checks_rank_milestones": 1}
    )
    distribute_items_restrictive(multiworld)
    assert len(network_locations(multiworld)) == 8
    assert all(location.item for location in multiworld.get_locations())
    assert multiworld.can_beat_game()


def test_loot_stash_pool_is_optional_seeded_and_fits_even_one_check():
    from gamma_archipelago.catalog import ITEM_IDS, enabled_item_ids

    placements = []
    for seed in (1, 1, 2):
        multiworld = setup_multiworld(
            GammaWorld, seed=seed, options={"rewards_loot_stashes": 1, "reward_quantities": 0}
        )
        distribute_items_restrictive(multiworld)
        world = multiworld.worlds[1]
        names = [location.item.name for location in multiworld.get_locations()]
        assert any("Loot Stash:" in name for name in names)
        assert "Basic Toolkit" in names
        assert set(world.fill_slot_data()["item_ids"]) == ITEM_IDS - {
            *range(28051801, 28052000),
            *range(28051201, 28051205),
            *range(28051301, 28051310),
            *range(28051401, 28051405),
            *range(28051501, 28051504),
            *range(28051601, 28051610),
            *range(28051701, 28051733),
            *range(28053001, 28053005),
            *range(28053101, 28053161),
        }
        assert enabled_item_ids(world.configuration.rewards) == ITEM_IDS - {
            *range(28051801, 28052000),
            *range(28051201, 28051205),
            *range(28051301, 28051310),
            *range(28051401, 28051405),
            *range(28051501, 28051504),
            *range(28051601, 28051610),
            *range(28051701, 28051733),
            *range(28053001, 28053005),
            *range(28053101, 28053161),
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
            "reward_quantities": 0,
        },
    )
    distribute_items_restrictive(single)
    assert "Loot Stash:" in next(iter(network_locations(single))).item.name


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


def test_restricted_start_places_selected_permissions_but_physical_stash_needs_no_pda():
    multiworld = setup_multiworld(
        GammaWorld,
        options={
            "starting_pda": 2,
            "starting_detector": 2,
            "rewards_starting_gear_unlocks": 1,
            "rewards_progression_stashes": 1,
        },
    )
    distribute_items_restrictive(multiworld)
    names = [loc.item.name for loc in multiworld.get_locations()]
    assert names.count("Equipment Unlock: PDA") == names.count("Equipment Unlock: Detector") == 1
    assert "Equipment Unlock: Firearms" not in names
    assert multiworld.can_beat_game()
    claim = multiworld.get_location("Claim Cordon Psi Stash", 1)
    from BaseClasses import CollectionState

    state = CollectionState(multiworld)
    world = multiworld.worlds[1]
    assert not claim.can_reach(state)
    state.collect(world.create_item("Progression Stash: Calibrated Psi Helmet"), prevent_sweep=True)
    assert claim.can_reach(state)
    state.collect(world.create_item("Equipment Unlock: PDA"), prevent_sweep=True)
    assert claim.can_reach(state)


def test_zone_keys_gate_all_entrances_and_conservative_global_activities():
    from BaseClasses import CollectionState

    from gamma_archipelago.configuration import CHECK_OPTIONS, GEAR_OPTIONS

    options = dict.fromkeys(CHECK_OPTIONS, 1)
    options.update(dict.fromkeys(GEAR_OPTIONS, 2))
    options.update(
        rewards_starting_gear_unlocks=1,
        rewards_zone_keys=1,
        rewards_progression_stashes=1,
        rewards_quest_keys=1,
    )
    multiworld = setup_multiworld(GammaWorld, seed=20, options=options)
    world = multiworld.worlds[1]
    state = CollectionState(multiworld)
    assert state.can_reach_region("l01_escape", 1)
    assert not state.can_reach_region("l02_garbage", 1)
    key = world.create_item("Zone Key: Garbage")
    state.collect(key, prevent_sweep=True)
    assert state.can_reach_region("l02_garbage", 1)
    assert not state.can_reach_region("l05_bar", 1)
    from gamma_archipelago.discovery import QUOTAS

    artefact = next(
        loc for loc in multiworld.get_locations() if loc.address == QUOTAS["artefact"][0]
    )
    assert not artefact.can_reach(state)
    for item in list(multiworld.itempool):
        state.collect(item, prevent_sweep=True)
    state.sweep_for_advancements()
    assert artefact.can_reach(state)
    distribute_items_restrictive(multiworld)
    assert multiworld.can_beat_game()
    assert len([name for name in world.item_name_to_id if name.startswith("Zone Key:")]) == 32


def test_zone_keys_require_map_checks_for_initial_reachable_slots():
    with pytest.raises(OptionError, match="require map checks"):
        setup_multiworld(
            GammaWorld, options={"checks_maps": 0, "checks_settlements": 1, "rewards_zone_keys": 1}
        )


def test_psi_goal_models_sakharov_acquisition_as_a_local_event_without_network_slot():
    multiworld = setup_multiworld(GammaWorld, seed=22, options={"goal": 1, "rewards_zone_keys": 1})
    distribute_items_restrictive(multiworld)
    world = multiworld.worlds[1]
    event = multiworld.get_location("Obtain Calibrated Helmet from Sakharov", 1)
    assert event.address is None and event.item.code is None
    assert len(world.fill_slot_data()["location_ids"]) == 33
    assert world.fill_slot_data()["goal"] == "psi_protection"
    assert multiworld.can_beat_game()


def test_sidorovich_goal_is_local_and_needs_no_psi_helmet_or_additional_check_slot():
    from BaseClasses import CollectionState

    multiworld = setup_multiworld(GammaWorld, options={"goal": 6, "rewards_zone_keys": 1})
    state = CollectionState(multiworld)
    assert not multiworld.completion_condition[1](state)
    event = multiworld.get_location("Talk to Sidorovich", 1)
    assert event.address is None and event.item.code is None
    assert event.parent_region.name == "l01_escape" and event.can_reach(state)
    assert not state.has("Calibrated Psi Protection", 1)
    state.collect(event.item, prevent_sweep=True)
    assert multiworld.completion_condition[1](state)
    assert multiworld.worlds[1].fill_slot_data()["goal"] == "talk_sidorovich"
    assert len(multiworld.worlds[1].fill_slot_data()["location_ids"]) == 33


def test_zone_chain_fills_previous_failure_seeds_and_keeps_yantar_before_psi_routes():
    from BaseClasses import CollectionState

    for seed in (1, 4, 5, 22):
        multiworld = setup_multiworld(
            GammaWorld, seed=seed, options={"goal": 1, "rewards_zone_keys": 1}
        )
        state = CollectionState(multiworld)
        state.sweep_for_advancements()
        assert all(
            state.can_reach_region(level, 1)
            for level in ("l08_yantar", "l10_radar", "l08u_brainlab", "l10u_bunker")
        )
        locked = [
            loc
            for loc in multiworld.get_locations()
            if loc.item and loc.item.name.startswith("Zone Key:")
        ]
        assert len(locked) == 32 and not any(loc.locked for loc in locked)
        distribute_items_restrictive(multiworld)
        assert multiworld.can_beat_game()


def test_scorcher_goal_requires_reaching_x19_with_psi_protection():
    multiworld = setup_multiworld(GammaWorld, seed=23, options={"goal": 2, "rewards_zone_keys": 1})
    distribute_items_restrictive(multiworld)
    event = multiworld.get_location("Shut Down Brain Scorcher", 1)
    assert event.address is None and event.parent_region.name == "l10u_bunker"
    assert multiworld.worlds[1].fill_slot_data()["goal"] == "brain_scorcher"
    assert multiworld.can_beat_game()


def test_meet_strelok_goal_respects_living_legend_permission_and_story_route():
    multiworld = setup_multiworld(
        GammaWorld,
        seed=24,
        options={
            "goal": 3,
            "checks_story_milestones": 1,
            "rewards_quest_keys": 1,
            "rewards_zone_keys": 1,
        },
    )
    distribute_items_restrictive(multiworld)
    event = multiworld.get_location("Conclude Strelok's First Conversation", 1)
    assert event.address is None and event.parent_region.name == "pripyat"
    assert multiworld.worlds[1].fill_slot_data()["goal"] == "meet_strelok"
    assert multiworld.can_beat_game()


def test_living_legend_goal_has_a_distinct_terminal_event_after_the_full_route():
    multiworld = setup_multiworld(
        GammaWorld,
        seed=25,
        options={
            "goal": 4,
            "checks_story_milestones": 1,
            "rewards_quest_keys": 1,
            "rewards_zone_keys": 1,
        },
    )
    distribute_items_restrictive(multiworld)
    event = multiworld.get_location("Return After Living Legend", 1)
    assert event.item.name == "Living Legend Complete"
    assert multiworld.worlds[1].fill_slot_data()["goal"] == "living_legend"
    assert multiworld.can_beat_game()


def test_all_labs_goal_has_a_frozen_roster_and_does_not_require_map_checks():
    for maps in (0, 1):
        options = {"goal": 5, "checks_maps": maps, "checks_settlements": 1}
        multiworld = setup_multiworld(GammaWorld, seed=26, options=options)
        distribute_items_restrictive(multiworld)
        assert multiworld.worlds[1].fill_slot_data()["goal"] == "all_x_labs"
        assert multiworld.can_beat_game()
    catalog = json.loads((ROOT / "src/gamma_archipelago/catalog.json").read_text())
    assert set(catalog["x_labs"]) == {
        "l04u_labx18",
        "l08u_brainlab",
        "l10u_bunker",
        "labx8",
        "l13u_warlab",
    }
    assert catalog["content_inventory"]["remaining_rosters"] == []


def test_disconnected_zone_catalogue_fails_clearly_before_placing_a_key():
    from test.general import gen_steps
    from worlds.gamma.zone_fill import place_zone_keys

    multiworld = setup_multiworld(
        GammaWorld, options={"rewards_zone_keys": 1}, steps=gen_steps[:-1]
    )
    catalog = json.loads((ROOT / "src/gamma_archipelago/catalog.json").read_text())
    catalog["connections"] = []
    with pytest.raises(OptionError, match="cannot reach"):
        place_zone_keys(multiworld.worlds[1], catalog)
