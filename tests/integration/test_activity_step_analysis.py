"""Paced activity totals advance in finite, ordered batches."""

import pytest
from BaseClasses import CollectionState, Location
from Fill import distribute_items_restrictive
from test.general import setup_multiworld
from worlds.gamma import GammaWorld
from worlds.gamma.analysis import _reachable, analyse

from gamma_archipelago.catalog import MAX_SIDE_TASK_MILESTONE, SIDE_TASK_MILESTONE_BASE
from gamma_archipelago.content_progression import TOOL_CLAIMS
from gamma_archipelago.discovery import QUOTAS, SOURCES
from gamma_archipelago.tool_permissions import TOOL_CAPABILITIES


@pytest.mark.parametrize("totals", [[5, 10, 20, 40], [3, 7, 11], [1, MAX_SIDE_TASK_MILESTONE]])
def test_task_totals_advance_one_configured_milestone_per_step(totals):
    multi = setup_multiworld(
        GammaWorld,
        options={
            "checks_maps": 0,
            "checks_side_task_milestones": 1,
            "side_task_milestones": totals,
            "grind_profile": 0,
        },
        seed=35,
    )
    distribute_items_restrictive(multi)
    world = multi.worlds[1]
    logical = analyse(world, False, True)
    paced = analyse(world, True, True)
    names = [row["location"] for row in logical["steps"][0]["available_checks"]]
    assert len(names) == len(totals)
    assert [[row["location"] for row in wave["available_checks"]] for wave in paced["steps"]] == [
        [name] for name in names
    ]
    assert paced["goal_reachable"] and paced["unreachable_checks"] == 0


@pytest.mark.parametrize("count", [1, 5, 6, 12, 20])
def test_generic_artefacts_advance_in_batches_of_five(count):
    multi = setup_multiworld(
        GammaWorld,
        options={
            "checks_maps": 0,
            "checks_artefacts": 1,
            "artefact_discovery_mode": 1,
            "artefact_discovery_count": count,
        },
        seed=35,
    )
    distribute_items_restrictive(multi)
    world = multi.worlds[1]
    logical = analyse(world, False, True)
    names = [row["location"] for row in logical["steps"][0]["available_checks"]]
    assert len(names) == count
    paced = analyse(world, True, True)
    assert [[row["location"] for row in wave["available_checks"]] for wave in paced["steps"]] == [
        names[index : index + 5] for index in range(0, count, 5)
    ]
    assert paced["goal_reachable"] and paced["unreachable_checks"] == 0


def test_artefacts_cannot_skip_an_incomplete_batch():
    multi = setup_multiworld(
        GammaWorld,
        options={
            "checks_artefacts": 1,
            "artefact_discovery_mode": 1,
            "artefact_discovery_count": 10,
        },
        seed=35,
    )
    rows = {row for row in multi.get_locations(1) if row.address in QUOTAS["artefact"][:10]}
    blocked = next(row for row in rows if row.address == QUOTAS["artefact"][2])
    blocked.access_rule = lambda state: False
    state = CollectionState(multi)
    first = set(_reachable(multi.worlds[1], state, rows, True))
    assert {row.address for row in first} == set(QUOTAS["artefact"][:5]) - {blocked.address}
    assert _reachable(multi.worlds[1], state, rows - first, True) == []
    blocked.access_rule = lambda state: True
    assert _reachable(multi.worlds[1], state, rows - first, True) == [blocked]
    assert {
        row.address for row in _reachable(multi.worlds[1], state, rows - first - {blocked}, True)
    } == set(QUOTAS["artefact"][5:10])


def test_named_artefacts_keep_their_independent_access_rules():
    multi = setup_multiworld(
        GammaWorld,
        options={"checks_artefacts": 1, "artefact_discovery_mode": 0},
        seed=35,
    )
    rows = {row for row in multi.get_locations(1) if row.address in SOURCES["artefact"].values()}
    assert rows
    state = CollectionState(multi)
    assert set(_reachable(multi.worlds[1], state, rows, True)) == set(
        _reachable(multi.worlds[1], state, rows, False)
    )


def test_each_gamma_slot_has_independent_task_and_artefact_batches():
    multi = setup_multiworld(
        [GammaWorld, GammaWorld],
        options={
            "checks_maps": 0,
            "checks_artefacts": 1,
            "artefact_discovery_mode": 1,
            "artefact_discovery_count": 10,
            "checks_side_task_milestones": 1,
            "side_task_milestones": [5, 10],
        },
        seed=35,
    )
    rows = {row for row in multi.get_locations() if row.address is not None}
    state = CollectionState(multi)
    for offset in (0, 5):
        wave = set(_reachable(multi.worlds[1], state, rows, True))
        expected = {
            SIDE_TASK_MILESTONE_BASE + (5 if offset == 0 else 10),
            *QUOTAS["artefact"][offset : offset + 5],
        }
        assert {(row.player, row.address) for row in wave} == {
            (player, address) for player in (1, 2) for address in expected
        }
        rows -= wave
    assert not rows


def test_foreign_games_do_not_inherit_task_or_artefact_pacing():
    from worlds.apquest.world import APQuestWorld

    multi = setup_multiworld([GammaWorld, APQuestWorld], seed=35)
    parent = multi.get_region(multi.worlds[2].origin_region_name, 2)
    rows = {
        Location(2, f"Synthetic {address}", address, parent)
        for address in (
            *QUOTAS["artefact"][:10],
            SIDE_TASK_MILESTONE_BASE + 5,
            SIDE_TASK_MILESTONE_BASE + 10,
        )
    }
    assert set(_reachable(multi.worlds[1], CollectionState(multi), rows, True)) == rows


def test_non_batch_chains_still_select_only_one_head_when_orders_tie():
    multi = setup_multiworld(GammaWorld, seed=35)
    parent = multi.get_region("Menu", 1)
    rows = {Location(1, name, None, parent) for name in (TOOL_CLAIMS[0], TOOL_CAPABILITIES[0])}
    assert len(_reachable(multi.worlds[1], CollectionState(multi), rows, True)) == 1
