import json
from importlib.resources import files

from gamma_archipelago.catalog import (
    ALL_LOCATION_IDS,
    ITEM_NAMES,
    ITEM_SECTIONS,
    LOCATION_IDS,
    LOCATION_NAMES,
)


def test_pilot_catalogue_has_unique_stable_ids_and_explicit_item_sections():
    catalogue = json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text())
    assert len(ITEM_NAMES) == len(ITEM_SECTIONS) == len(catalogue["items"]) == 3
    assert len(LOCATION_NAMES) == len(ALL_LOCATION_IDS) == 10155
    assert len(catalogue["locations"]) == 155
    assert len(LOCATION_IDS) == 3
    assert all(0 < value < 2**31 for value in [*ITEM_SECTIONS, *LOCATION_IDS])
    assert set(ITEM_SECTIONS.values()) == {"itm_basickit", "medkit", "bandage"}


def test_direct_ap_rewards_cannot_inject_eligible_artefacts_asynchronously():
    catalogue = json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text())
    aliases = {
        alias
        for location in catalogue["locations"]
        if location["category"] == "checks_artefacts"
        for alias in location["aliases"]
    }
    assert aliases.isdisjoint(ITEM_SECTIONS.values())
