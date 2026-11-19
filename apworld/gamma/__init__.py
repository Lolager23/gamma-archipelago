"""Three-check integration pilot; progression expansion belongs to later branches."""

import json
from importlib.resources import files

from BaseClasses import Item, ItemClassification, Location, Region, Tutorial
from Options import OptionError
from worlds.AutoWorld import WebWorld, World

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
    """Explore Cordon, Garbage and Rostok to prove the GAMMA/AP integration."""

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
        for name, location_id in self.location_name_to_id.items():
            menu.locations.append(GammaLocation(self.player, name, location_id, menu))
        self.multiworld.regions.append(menu)

    def create_items(self) -> None:
        self.multiworld.itempool.extend(self.create_item(name) for name in self.item_name_to_id)

    def set_rules(self) -> None:
        self.multiworld.completion_condition[self.player] = lambda state: all(
            state.can_reach_location(name, self.player) for name in self.location_name_to_id
        )

    def fill_slot_data(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "pilot": True,
            "goal": "visit_all_pilot_regions",
            "configuration": self.configuration.to_values(),
            "configuration_key": self.configuration.digest,
        }

    def get_filler_item_name(self) -> str:
        return "Bandage"
