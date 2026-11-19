"""Match solver story-key dependencies to the native trilogy's chain order."""

import json
from pathlib import Path

import pytest
from BaseClasses import CollectionState
from test.general import setup_multiworld
from worlds.gamma import GammaWorld

pytestmark = pytest.mark.integration
ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "chain,missing",
    [
        ("living_legend", "Living Legend"),
        ("mortal_sin", "Living Legend"),
        ("mortal_sin", "Mortal Sin"),
        ("operation_afterglow", "Living Legend"),
        ("operation_afterglow", "Mortal Sin"),
        ("operation_afterglow", "Operation Afterglow"),
    ],
)
def test_quest_story_checks_require_permissions_for_all_prior_native_chains(chain, missing):
    multiworld = setup_multiworld(
        GammaWorld, options={"checks_story_milestones": 1, "rewards_quest_keys": 1}
    )
    world = multiworld.worlds[1]
    catalogue = json.loads((ROOT / "src/gamma_archipelago/catalog.json").read_text())
    identities = {
        row["id"]
        for row in catalogue["locations"]
        if row.get("tasks") and catalogue["quest_gates"][row["tasks"][0]] == chain
    }
    locations = [loc for loc in multiworld.get_locations(1) if loc.address in identities]
    assert locations
    state = CollectionState(multiworld)
    for key in ("Living Legend", "Mortal Sin", "Operation Afterglow"):
        if key != missing:
            state.collect(world.create_item("Quest Key: " + key))
    assert all(not location.can_reach(state) for location in locations)
    state.collect(world.create_item("Quest Key: " + missing))
    assert all(location.can_reach(state) for location in locations)
