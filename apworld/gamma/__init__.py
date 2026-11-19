"""Exploration checks on the supported Anomaly/GAMMA level graph."""

import json
from importlib.resources import files

from BaseClasses import Item, ItemClassification, Location, Region, Tutorial
from Options import OptionError
from worlds.AutoWorld import WebWorld, World

from gamma_archipelago.catalog import LOCATION_IDS
from gamma_archipelago.configuration import OPTION_NAMES, SeedConfiguration, build_configuration

from .options import GammaOptions

_catalog = json.loads(files(__package__).joinpath("catalog.json").read_text(encoding="utf-8"))


class GammaWeb(WebWorld):
    tutorials = [
        Tutorial(
            "GAMMA pilot setup",
            "Install the isolated GAMMA add-on and companion client.",
            "English",
            "setup_en.md",
            "setup/en",
            ["Owen Welch"],
        )
    ]


class GammaItem(Item):
    game = _catalog["game"]


class GammaLocation(Location):
    game = _catalog["game"]


class GammaWorld(World):
    """Explore the Zone; independent check and reward categories expand the seed."""

    game = _catalog["game"]
    web = GammaWeb()
    required_client_version = (0, 6, 8)
    options_dataclass = GammaOptions
    options: GammaOptions
    configuration: SeedConfiguration
    item_name_to_id = {item["name"]: item["id"] for item in _catalog["items"]}
    location_name_to_id = {location["name"]: location["id"] for location in _catalog["locations"]}

    def generate_early(self) -> None:
        try:
            self.configuration = build_configuration(self.options.as_dict(*OPTION_NAMES))
        except ValueError as error:
            raise OptionError(str(error)) from error

    def create_item(self, name: str) -> GammaItem:
        definition = next(item for item in _catalog["items"] if item["name"] == name)
        classification = getattr(ItemClassification, definition["classification"])
        return GammaItem(name, classification, definition["id"], self.player)

    def create_regions(self) -> None:
        menu = Region("Menu", self.player, self.multiworld)
        self.multiworld.regions.append(menu)
        regions = {}
        for level in _catalog["levels"]:
            region = Region(level["id"], self.player, self.multiworld)
            regions[level["id"]] = region
            self.multiworld.regions.append(region)
        menu.connect(regions["l01_escape"])
        for source, destination in _catalog["connections"]:
            regions[source].connect(regions[destination])
            regions[destination].connect(regions[source])
        for location in _catalog["locations"]:
            if location["category"] not in self.configuration.checks:
                continue
            region = regions[location["level"]]
            region.locations.append(
                GammaLocation(self.player, location["name"], location["id"], region)
            )

    def create_items(self) -> None:
        self.multiworld.itempool.extend(self.create_item(name) for name in self.item_name_to_id)
        extra = len(self.multiworld.get_locations(self.player)) - len(self.item_name_to_id)
        self.multiworld.itempool.extend(
            self.create_item(self.get_filler_item_name()) for _ in range(extra)
        )

    def set_rules(self) -> None:
        self.multiworld.completion_condition[self.player] = lambda state: all(
            state.can_reach_region(location["level"], self.player)
            for location in _catalog["locations"]
            if location["id"] in LOCATION_IDS
        )

    def fill_slot_data(self) -> dict[str, object]:
        return {
            "schema_version": 3,
            "pilot": False,
            "goal": "visit_all_pilot_regions",
            "configuration": self.configuration.to_values(),
            "configuration_key": self.configuration.digest,
            "location_ids": sorted(
                location.address for location in self.multiworld.get_locations(self.player)
            ),
        }

    def get_filler_item_name(self) -> str:
        return "Bandage"
