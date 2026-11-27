import json
from importlib.resources import files

import pytest
from BaseClasses import CollectionState, LocationProgressType
from Fill import distribute_items_restrictive
from test.general import setup_multiworld
from worlds.gamma import GammaWorld

from gamma_archipelago.activity_requirements import unreliable_check_ids
from gamma_archipelago.presets import presets


def legacy_full():
    return presets()["full_story"] | {
        "equipment_class_progression": 0,
        "regional_progression": 0,
        "starting_melee": 2,
        "starting_tools": 2,
    }


CATALOG = json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text())
CATEGORIES = {row["id"]: row["category"] for row in CATALOG["locations"]}


def collect(world, state, *names):
    for name in names:
        state.collect(world.create_item(name), True)


def test_cordon_kills_artefacts_and_tasks_require_their_equipment_not_every_key():
    # Named-source access is still selectable after generic discoveries become default.
    options = legacy_full() | {"mutant_discovery_mode": 0, "artefact_discovery_mode": 0}
    multi = setup_multiworld(GammaWorld, options=options, seed=1)
    world = multi.worlds[1]
    state = CollectionState(multi)
    ids = {row.address: row for row in multi.get_locations() if row.address}
    boar, artefact, fetch, assault = (ids[id] for id in (28052202, 28052445, 28052501, 28052510))
    assert not any(loc.can_reach(state) for loc in (boar, artefact, fetch, assault))
    collect(world, state, "Equipment Unlock: Melee")
    assert boar.can_reach(state) and not assault.can_reach(state)
    collect(world, state, "Equipment Unlock: Detector")
    assert artefact.can_reach(state) and not fetch.can_reach(state)
    collect(world, state, "Equipment Unlock: PDA")
    assert fetch.can_reach(state) and assault.can_reach(state)
    assert ids[28120005].can_reach(state) and ids[28100010].can_reach(state)
    assert not ids[28052601].can_reach(state)
    collect(world, state, "Zone Key: Great Swamps", "Quest Key: Living Legend")
    assert ids[28052601].can_reach(state)
    assert not ids[28052602].can_reach(state)


def test_progression_excludes_uncertain_sources_and_keeps_the_native_check_manifest():
    multi = setup_multiworld(GammaWorld, options=legacy_full())
    unsafe = unreliable_check_ids(multi.worlds[1].configuration)
    locations = [row for row in multi.get_locations() if row.address]
    assert len(locations) == 252
    assert all(
        row.progress_type == LocationProgressType.EXCLUDED
        for row in locations
        if row.address in unsafe
    )
    distribute_items_restrictive(multi)
    assert all(
        not row.item.advancement and not row.item.useful
        for row in locations
        if row.address in unsafe
    )
    assert multi.can_beat_game()


@pytest.mark.generation
def test_regional_fill_reaches_all_checks_and_places_keys_outside_exploration():
    categories = set()
    for seed in range(40):
        multi = setup_multiworld(GammaWorld, options=legacy_full(), seed=seed)
        distribute_items_restrictive(multi)
        assert multi.can_beat_game()
        seen = set()
        for sphere in multi.get_spheres():
            assert sphere
            for loc in sphere:
                seen.add(loc)
                if (
                    loc.item.name.startswith("Zone Key:")
                    and loc.address
                    and not loc.name.endswith("First Arrival")
                ):
                    categories.add(
                        CATEGORIES.get(
                            loc.address,
                            "checks_kill_milestones"
                            if loc.address < 28120000
                            else "checks_side_task_milestones",
                        )
                    )
        assert len(seen) == len(multi.get_locations())
    assert categories & {"checks_artefacts", "checks_mutant_first_kills", "checks_quest_types"}


def test_reliable_global_checks_use_general_fill_without_sparse_map_reservations():
    multi = setup_multiworld(
        GammaWorld, options={"rewards_zone_keys": 1, "checks_mutant_first_kills": 1}
    )
    assert all(
        item.location is None for item in multi.itempool if item.name.startswith("Zone Key:")
    )
    distribute_items_restrictive(multi)
    assert multi.can_beat_game()


def test_rank_has_a_viable_quest_or_combat_path_and_upgrades_respect_tool_use_permission():
    multi = setup_multiworld(GammaWorld, options=legacy_full(), seed=11)
    world = multi.worlds[1]
    state = CollectionState(multi)
    rank = next(loc for loc in multi.get_locations() if loc.address == 28052802)
    upgrade = next(loc for loc in multi.get_locations() if loc.address == 28052731)
    assert not rank.can_reach(state)
    assert next(loc for loc in multi.get_locations() if loc.address == 28052801).can_reach(state)
    collect(world, state, "Equipment Unlock: PDA")
    assert not rank.can_reach(state)
    collect(world, state, "Faction Goodwill: stalker")
    assert rank.can_reach(state)
    other = CollectionState(multi)
    collect(world, other, "Equipment Unlock: Melee", "Faction Goodwill: stalker")
    assert not rank.can_reach(other)
    collect(world, other, "Equipment Unlock: PDA")
    assert rank.can_reach(other)
    collect(
        world,
        state,
        "Progressive Tools",
        "Progressive Tools",
        "Progressive Tools",
        "Workshop Access: Upgrades",
    )
    assert not upgrade.can_reach(state)
    collect(world, state, "Equipment Unlock: Tools")
    assert upgrade.can_reach(state)


def test_later_story_checks_and_local_victory_retain_earlier_mandatory_combat():
    multi = setup_multiworld(
        GammaWorld,
        options=legacy_full(),
        seed=20,
        steps=("generate_early", "create_regions", "create_items", "set_rules"),
    )
    world = multi.worlds[1]
    state = CollectionState(multi)
    for item in multi.itempool:
        if item.name not in {"Equipment Unlock: Firearms", "Equipment Unlock: Melee"}:
            state.collect(item, True)
    state.sweep_for_advancements()
    checks = {loc.address: loc for loc in multi.get_locations() if loc.address}
    assert checks[28052601].can_reach(state)
    for id in (28052606, 28052611, 28052621, 28052622, 28052644):
        assert not checks[id].can_reach(state)
    assert not multi.get_location("Conclude Strelok's First Conversation", 1).can_reach(state)
    assert not multi.get_location("Return After Living Legend", 1).can_reach(state)
    assert not multi.can_beat_game(state)
    collect(world, state, "Equipment Unlock: Melee")
    state.sweep_for_advancements()
    assert all(
        checks[id].can_reach(state) for id in (28052606, 28052611, 28052621, 28052622, 28052644)
    )
    assert multi.can_beat_game(state)


@pytest.mark.parametrize("local", [False, True])
def test_activity_opener_uses_upstream_early_requests_and_preserves_user_requests(local):
    from worlds.gamma.opening import request_activity_opener

    multi = setup_multiworld(
        GammaWorld,
        options=legacy_full()
        | {"starting_money": 0, "checks_emissions": 0, "checks_psi_storms": 0, "checks_shops": 0},
        seed=740,
        steps=("generate_early", "create_regions", "create_items", "set_rules"),
    )
    requests = multi.local_early_items[1] if local else multi.early_items[1]
    requests["Equipment Unlock: PDA"] = 2
    request_activity_opener(multi.worlds[1], CATALOG)
    assert requests["Equipment Unlock: PDA"] == 2
    assert not any(
        count for name, count in multi.early_items[1].items() if name != "Equipment Unlock: PDA"
    )


@pytest.mark.parametrize("seed,start", [(740, 0), (66, 2), (99, 3)])
def test_dependent_tools_cannot_clog_the_fully_locked_opening(seed, start):
    multi = setup_multiworld(
        GammaWorld, options={**legacy_full(), "starting_location": start}, seed=seed
    )
    assert sum(multi.early_items[1].values()) == 0  # Paid shop provides an opening.
    assert all(
        item.location is None for item in multi.itempool if item.name.startswith("Zone Key:")
    )
    distribute_items_restrictive(multi)
    assert multi.can_beat_game()
    state = CollectionState(multi)
    state.sweep_for_advancements()
    assert all(loc.can_reach(state) for loc in multi.get_locations())


def test_activity_opener_requests_a_capability_when_no_paid_start_is_affordable():
    from worlds.gamma.opening import request_activity_opener

    multi = setup_multiworld(
        GammaWorld,
        options=legacy_full()
        | {"starting_money": 0, "checks_emissions": 0, "checks_psi_storms": 0, "checks_shops": 0},
        steps=("generate_early", "create_regions", "create_items", "set_rules"),
    )
    request_activity_opener(multi.worlds[1], CATALOG)
    assert sum(multi.early_items[1].values()) == 1
    assert next(iter(multi.early_items[1])).startswith("Equipment Unlock:")
