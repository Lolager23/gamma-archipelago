import json
from pathlib import Path

import pytest
from BaseClasses import ItemClassification
from Fill import distribute_items_restrictive
from Options import OptionError
from test.general import setup_multiworld
from worlds.apquest.world import APQuestWorld
from worlds.gamma import GammaWorld

from gamma_archipelago.catalog import GAME, ITEM_NAMES, LOCATION_NAMES

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


def test_world_generation_rejects_unsupported_options_instead_of_ignoring_them():
    world = generate(123).worlds[1]
    world.options.checks_settlements.value = 1
    with pytest.raises(OptionError, match="Not implemented"):
        world.generate_early()


def test_one_thousand_pilot_seeds_are_fully_filled_and_beatable():
    for seed in range(1000):
        multiworld = generate(seed)
        locations = multiworld.get_locations(1)
        assert len(locations) == 33
        assert {location.item.name for location in locations} == set(ITEM_NAMES)
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
