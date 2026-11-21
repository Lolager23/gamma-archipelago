"""Build the slot's budgeted pool; CommonClient and the game never choose seed items."""

from collections import Counter
from typing import TYPE_CHECKING, Any

from BaseClasses import LocationProgressType
from Options import OptionError

from gamma_archipelago.pool_budget import budget_pool
from gamma_archipelago.settlement_access import required_reputation

if TYPE_CHECKING:
    from . import GammaWorld

OPTIONAL = {
    "rewards_loot_stashes",
    "rewards_faction_reputation",
    "rewards_stat_levels",
    "rewards_supply_medical",
    "rewards_supply_maintenance",
    "rewards_supply_ammunition",
    "rewards_supply_expedition",
}


def build_pool(world: "GammaWorld", catalog: dict[str, Any]) -> None:
    locations = [
        row
        for row in world.multiworld.get_unfilled_locations(world.player)
        if row.address is not None
    ]
    if not locations:
        raise OptionError("The selected check pool cannot hold required progression rewards")
    excluded = frozenset(
        row.address
        for row in locations
        if row.progress_type == LocationProgressType.EXCLUDED
        or row.name in world.options.exclude_locations.value
    )
    starting = Counter(item.name for item in world.multiworld.precollected_items[world.player])
    try:
        world.pool_budget = budget_pool(
            world.configuration,
            frozenset(row.address for row in locations),
            excluded,
            starting,
            world.options.start_inventory_from_pool.value,
        )
    except ValueError as error:
        raise OptionError(str(error)) from error
    plan = world.pool_budget
    world.multiworld.itempool.extend(
        world.create_item(name) for name in plan.required + plan.convenience
    )
    names = [row["name"] for row in catalog["items"] if "category" not in row]
    neutrality = required_reputation(
        world.configuration, frozenset(row.address for row in locations)
    )
    optional = [
        row
        for row in catalog["items"]
        if row.get("category") in OPTIONAL
        and row["category"] in world.configuration.rewards
        and row["name"] not in neutrality
    ]
    # Excluded locations accept filler only, including after upstream pool depletion.
    useful_capacity = plan.eligible_checks - (
        len(plan.required) + len(plan.convenience) - sum(dict(plan.from_pool).values())
    )
    for index in range(plan.filler_slots):
        candidates = [
            row for row in optional if row["classification"] == "filler" or useful_capacity > 0
        ]
        if candidates and (index == 0 or (index > 3 and world.random.randrange(3) == 0)):
            weights = [row.get("filler_weight", 1) for row in candidates]
            row = (
                world.random.choices(candidates, weights=weights, k=1)[0]
                if any(weight != 1 for weight in weights)
                else world.random.choice(candidates)
            )
            name = row["name"]
            if row["classification"] != "filler":
                useful_capacity -= 1
        else:
            position = index - int(bool(optional))
            name = names[position] if 0 <= position < len(names) else world.get_filler_item_name()
            if name == "Basic Toolkit" and useful_capacity <= 0:
                name = world.get_filler_item_name()
            elif name == "Basic Toolkit":
                useful_capacity -= 1
        world.multiworld.itempool.append(world.create_item(name))
