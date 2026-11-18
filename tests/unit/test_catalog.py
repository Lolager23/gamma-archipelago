import json
from importlib.resources import files

from gamma_archipelago.catalog import ITEM_NAMES, ITEM_SECTIONS, LOCATION_IDS, LOCATION_NAMES


def test_pilot_catalogue_has_unique_stable_ids_and_explicit_item_sections():
    catalogue = json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text())
    assert len(ITEM_NAMES) == len(ITEM_SECTIONS) == len(catalogue["items"]) == 3
    assert len(LOCATION_NAMES) == len(LOCATION_IDS) == len(catalogue["locations"]) == 3
    assert all(0 < value < 2**31 for value in [*ITEM_SECTIONS, *LOCATION_IDS])
    assert set(ITEM_SECTIONS.values()) == {"itm_basickit", "medkit", "bandage"}
