"""Exploration checks on the supported Anomaly/GAMMA level graph."""

import json
from importlib.resources import files

from BaseClasses import Item, ItemClassification, Location, LocationProgressType, Region, Tutorial
from Options import OptionError
from worlds.AutoWorld import WebWorld, World

from gamma_archipelago.activity_requirements import unreliable_check_ids
from gamma_archipelago.catalog import (
    KILL_MILESTONE_BASE,
    LOCATION_NAMES,
    SIDE_TASK_MILESTONE_BASE,
)
from gamma_archipelago.configuration import OPTION_NAMES, SeedConfiguration, build_configuration
from gamma_archipelago.content_progression import (
    configured_item_ids,
)
from gamma_archipelago.content_progression import (
    protected as content_protected,
)
from gamma_archipelago.discovery import configured_location_ids, protected_tail_ids
from gamma_archipelago.pool_budget import PoolBudget
from gamma_archipelago.starting_unlock import unlock_candidates

from .goals import add_goal_events, set_goal_rule
from .identity import generation_identity
from .opening import place_opening, request_activity_opener
from .options import GammaOptions
from .pool import build_pool
from .preview import write_preview
from .rules import apply_access_rules
from .zone_fill import place_zone_keys, prefer_early_hub

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
    pool_budget: PoolBudget
    opening_placements: list[dict[str, str]]
    configuration: SeedConfiguration
    item_name_to_id = {item["name"]: item["id"] for item in _catalog["items"]}
    location_name_to_id = LOCATION_NAMES

    def generate_early(self) -> None:
        try:
            values = self.options.as_dict(*OPTION_NAMES)
            if values["starting_location"] == 3:
                values["starting_location"] = self.random.randrange(3)
            self.configuration = build_configuration(values)
            if self.configuration.option("random_starting_unlock"):
                held = self.options.start_inventory.value | {
                    name: max(count, self.options.start_inventory.value.get(name, 0))
                    for name, count in self.options.start_inventory_from_pool.value.items()
                }
                candidates = unlock_candidates(self.configuration, held)
                if candidates:
                    self.multiworld.push_precollected(
                        self.create_item(self.random.choice(candidates))
                    )
            from collections import Counter

            from gamma_archipelago.artefact_capacity import resolve_capacity

            held = Counter(self.options.start_inventory.value)
            held.update(self.options.start_inventory_from_pool.value)
            held.update(item.name for item in self.multiworld.precollected_items[self.player])
            self.configuration = resolve_capacity(
                self.configuration,
                frozenset(
                    self.location_name_to_id[name] for name in self.options.exclude_locations.value
                ),
                held,
                self.options.start_inventory_from_pool.value,
            )
        except ValueError as error:
            raise OptionError(str(error)) from error

    def create_item(self, name: str) -> GammaItem:
        from gamma_archipelago.settlement_access import NEUTRALITY_ITEMS

        definition = next(item for item in _catalog["items"] if item["name"] == name)
        classification = getattr(ItemClassification, definition["classification"])
        if (
            name in NEUTRALITY_ITEMS
            and self.options.settlement_reputation_logic.value
            and self.options.checks_settlements.value
            and self.options.rewards_faction_reputation.value
        ):
            classification = ItemClassification.progression
        if (
            self.options.playability_logic.value
            and self.options.rewards_faction_reputation.value
            and (
                self.options.checks_rank_milestones.value
                or self.options.checks_faction_standing.value
                or self.options.checks_armour_tiers.value
                or self.options.checks_weapon_tiers.value
            )
            and definition.get("effect") == "reputation"
        ):
            classification = ItemClassification.progression
        return GammaItem(name, classification, definition["id"], self.player)

    def create_regions(self) -> None:
        menu = Region("Menu", self.player, self.multiworld)
        self.multiworld.regions.append(menu)
        regions = {}
        for level in _catalog["levels"]:
            region = Region(level["id"], self.player, self.multiworld)
            regions[level["id"]] = region
            self.multiworld.regions.append(region)
        from gamma_archipelago.starting import starting_level

        menu.connect(regions[starting_level(self.configuration)])
        add_goal_events(self, regions, GammaLocation, GammaItem)
        from .content import add_tool_claims

        add_tool_claims(self, regions, GammaLocation, GammaItem)
        if "rewards_progression_stashes" in self.configuration.rewards:
            claim = GammaLocation(
                self.player, "Claim Cordon Psi Stash", None, regions["l01_escape"]
            )
            claim.access_rule = lambda state: state.has(
                "Progression Stash: Calibrated Psi Helmet", self.player
            )
            claim.place_locked_item(
                GammaItem(
                    "Calibrated Psi Protection", ItemClassification.progression, None, self.player
                )
            )
            regions["l01_escape"].locations.append(claim)
        for source, destination in _catalog["connections"]:
            regions[source].connect(regions[destination])
            regions[destination].connect(regions[source])
        allowed = configured_location_ids(self.configuration)
        protected = protected_tail_ids(self.configuration, allowed) | unreliable_check_ids(
            self.configuration
        )
        from gamma_archipelago.playability import fragile_ids
        from gamma_archipelago.playability import protected as practical_protected
        from gamma_archipelago.settlement_access import protected_settlements

        protected |= protected_settlements(self.configuration) | practical_protected(
            self.configuration
        )
        protected |= content_protected(self.configuration)
        fragile = fragile_ids(self.configuration)
        for location in _catalog["locations"]:
            if location["id"] not in allowed:
                continue
            region = regions.get(location["level"], menu)
            check = GammaLocation(self.player, location["name"], location["id"], region)
            if location["id"] in protected or (
                location["id"] in fragile
                and self.configuration.option("optional_check_policy") == 0
            ):
                check.progress_type = LocationProgressType.EXCLUDED
            if location.get("tasks") and "rewards_quest_keys" in self.configuration.rewards:
                permission = _catalog["quest_gates"][location["tasks"][0]]
                key_names = tuple(
                    item["name"]
                    for item in _catalog["items"]
                    if item.get("permission") in _catalog["quest_key_requirements"][permission]
                )
                check.access_rule = lambda state, names=key_names: all(
                    state.has(name, self.player) for name in names
                )
            region.locations.append(check)
        if "checks_kill_milestones" in self.configuration.checks:
            for count in self.configuration.kill_milestones:
                menu.locations.append(
                    GammaLocation(
                        self.player,
                        _catalog["milestones"]["checks_kill_milestones"]["name"].format(
                            count=count
                        ),
                        KILL_MILESTONE_BASE + count,
                        menu,
                    )
                )
        if "checks_side_task_milestones" in self.configuration.checks:
            for count in self.configuration.side_task_milestones:
                menu.locations.append(
                    GammaLocation(
                        self.player,
                        _catalog["milestones"]["checks_side_task_milestones"]["name"].format(
                            count=count
                        ),
                        SIDE_TASK_MILESTONE_BASE + count,
                        menu,
                    )
                )

    def create_items(self) -> None:
        build_pool(self, _catalog)

    def set_rules(self) -> None:
        apply_access_rules(self, _catalog)
        from .playability import restrict_placements, restrict_tool_stashes

        restrict_placements(self, _catalog)
        restrict_tool_stashes(self, _catalog)
        set_goal_rule(self, _catalog)

    def pre_fill(self) -> None:
        from .settlement_fill import request_neutrality_opener

        place_opening(self, _catalog)
        from .early_equipment import place_equipment

        place_equipment(self, _catalog)
        request_activity_opener(self, _catalog)
        request_neutrality_opener(self)
        place_zone_keys(self, _catalog)
        prefer_early_hub(self, _catalog)

    def fill_slot_data(self) -> dict[str, object]:
        identity = generation_identity(self)
        return {
            "schema_version": 4 if identity else 3,
            **({"generation_identity": identity} if identity else {}),
            "pilot": False,
            "goal": "visit_all_pilot_regions"
            if self.configuration.goal == "pilot_tour"
            else self.configuration.goal,
            "configuration": self.configuration.to_values(),
            "configuration_key": self.configuration.digest,
            "location_ids": sorted(
                location.address
                for location in self.multiworld.get_locations(self.player)
                if location.address is not None
            ),
            "item_ids": sorted(configured_item_ids(self.configuration)),
        }

    def get_filler_item_name(self) -> str:
        return "Bandage"

    def generate_output(self, output_directory: str) -> None:
        write_preview(self, output_directory)
