"""Reserve recipe permissions in a verified three-step opening."""

from typing import TYPE_CHECKING, Any

from BaseClasses import Item, Location, LocationProgressType
from Options import OptionError

from .analysis import early_checks

if TYPE_CHECKING:
    from . import GammaWorld


def _reserve(world: "GammaWorld", item: Item, plan: dict[Location, Item]) -> None:
    reached = early_checks(world, placements=plan)
    candidates = [
        row
        for row in world.multiworld.get_unfilled_locations()
        if row in reached
        and row not in plan
        and row.progress_type != LocationProgressType.EXCLUDED
        and row.name not in world.multiworld.worlds[row.player].options.exclude_locations.value
        and row.can_fill(world.multiworld.state, item, False)
        and (item.name not in world.options.local_items.value or row.player == world.player)
        and (item.name not in world.options.non_local_items.value or row.player != world.player)
    ]
    if not candidates:
        raise OptionError(
            "Recipe access needs enough permitted checks in the first three paced steps; "
            "add early checks, precollect recipes, relax locality/plando, "
            "or disable playability logic"
        )
    candidates = sorted(
        candidates,
        key=lambda row: (row.player, row.address or 0, row.name),
    )
    location = world.random.choice(candidates)
    plan[location] = item


def place_recipes(world: "GammaWorld", catalog: dict[str, Any]) -> None:
    # Keep the old all-zones contract, whose locked opening can lack this capacity.
    if (
        not world.configuration.option("playability_logic")
        or not world.configuration.option("regional_progression")
        or "rewards_recipe_access" not in world.configuration.rewards
    ):
        return
    names = {
        row["name"] for row in catalog["items"] if row.get("category") == "rewards_recipe_access"
    }
    items = [
        item
        for item in world.multiworld.itempool
        if item.player == world.player and item.name in names
    ]
    world.random.shuffle(items)
    plan: dict[Location, Item] = {}
    for item in items:
        _reserve(world, item, plan)
    reached = early_checks(world, placements=plan)
    for row in world.multiworld.get_locations():
        item = plan.get(row, row.item)
        if item and item.player == world.player and item.name in names and row not in reached:
            raise OptionError("Placed recipe access conflicts with the first three paced steps")
    for location, item in plan.items():
        location.place_locked_item(item)
        world.multiworld.itempool.remove(item)
        world.opening_placements.append(
            {"location": location.name, "item": item.name, "finder": str(location.player)}
        )
