"""Place local equipment permissions before unrelated zone-key or rank chains."""

from typing import TYPE_CHECKING, Any

from BaseClasses import CollectionState, LocationProgressType
from Options import OptionError

from gamma_archipelago.catalog import KILL_MILESTONE_BASE, MAP_LOCATIONS, SIDE_TASK_MILESTONE_BASE
from gamma_archipelago.playability import early_check
from gamma_archipelago.starting import starting_level

if TYPE_CHECKING:
    from . import GammaWorld


def _definition(address: int, definitions: dict[int, dict[str, Any]]) -> dict[str, Any]:
    if address in definitions:
        return definitions[address]
    kill = address < SIDE_TASK_MILESTONE_BASE
    return {
        "level": "Menu",
        "category": "checks_kill_milestones" if kill else "checks_side_task_milestones",
        "minimum": address - (KILL_MILESTONE_BASE if kill else SIDE_TASK_MILESTONE_BASE),
    }


def place_equipment(world: "GammaWorld", catalog: dict[str, Any]) -> None:
    configuration = world.configuration
    if not (
        configuration.option("content_progression") and configuration.option("playability_logic")
    ):
        return
    if configuration.checks <= {"checks_maps", "checks_settlements"}:
        return  # Preserve the explicitly supported sparse exploration fallback.
    names = {
        row["name"]
        for row in catalog["items"]
        if row.get("category") == "rewards_starting_gear_unlocks"
    }
    items = [
        item
        for item in world.multiworld.itempool
        if item.player == world.player and item.name in names
    ]
    order = {
        "Equipment Unlock: " + group: index
        for index, group in enumerate(("PDA", "Firearms", "Detector", "Melee"))
    }
    world.random.shuffle(items)
    items.sort(key=lambda item: order.get(item.name, 4))
    remote = world.options.non_local_items.value
    for item in items:
        if item.name in remote:
            early = world.multiworld.early_items[world.player]
            early[item.name] = max(1, early.get(item.name, 0))
    local = [item for item in items if item.name not in remote]
    _place_local(world, catalog, local)


def _place_local(world: "GammaWorld", catalog: dict[str, Any], items: list) -> None:
    if not items:
        return
    start = starting_level(world.configuration)
    definitions = {row["id"]: row for row in catalog["locations"]}
    candidates = [
        row
        for row in world.multiworld.get_unfilled_locations(world.player)
        if row.address is not None
        and row.progress_type != LocationProgressType.EXCLUDED
        and row.name not in world.options.exclude_locations.value
        and not (
            "rewards_zone_keys" in world.configuration.rewards
            and row.address == MAP_LOCATIONS[start]
        )
        and early_check(_definition(row.address, definitions), frozenset({start}))
    ]
    state = CollectionState(world.multiworld)
    state.sweep_for_advancements(locations=world.multiworld.get_filled_locations(world.player))
    initial = state.copy()
    plan = []
    for item in items:
        available = [row for row in candidates if row.can_fill(state, item, True)]
        if not available:
            raise OptionError(
                "Early equipment needs more low-grind checks in the starting region; "
                "enable generic discoveries/tasks, reduce locks, or disable playability logic"
            )
        immediate = [row for row in available if row.can_fill(initial, item, True)]
        location = world.random.choice(immediate or available)
        candidates.remove(location)
        plan.append((location, item))
        state.collect(item, True)
    for location, item in plan:
        location.place_locked_item(item)
        world.multiworld.itempool.remove(item)
        world.opening_placements.append({"location": location.name, "item": item.name})
