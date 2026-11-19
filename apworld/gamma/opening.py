"""Reserve explicit local starting permissions before zone-route reservations."""

from typing import TYPE_CHECKING, Any

from BaseClasses import LocationProgressType
from Options import OptionError

from gamma_archipelago.opening import opening_checks, opening_permissions

if TYPE_CHECKING:
    from . import GammaWorld


def place_opening(world: "GammaWorld", catalog: dict[str, Any]) -> None:
    world.opening_placements = []
    if not world.configuration.option("opening_policy"):
        return
    pool = world.multiworld.itempool
    held = dict(world.pool_budget.starting)
    zone_names = {
        row["name"] for row in catalog["items"] if row.get("category") == "rewards_zone_keys"
    }
    zoned = any(item.player == world.player and item.name in zone_names for item in pool)
    locations = [
        row
        for row in world.multiworld.get_unfilled_locations(world.player)
        if row.address is not None
        and row.progress_type != LocationProgressType.EXCLUDED
        and row.name not in world.options.exclude_locations.value
    ]
    allowed = opening_checks(frozenset(row.address for row in locations), frozenset(), zoned)
    candidates = sorted(
        (row for row in locations if row.address in allowed), key=lambda row: row.address
    )
    names = opening_permissions(world.configuration, held)
    for name in names:
        if name in world.options.non_local_items.value:
            raise OptionError("Protected opening permissions must be local")
        item = next(
            (item for item in pool if item.player == world.player and item.name == name), None
        )
        if not candidates or item is None:
            raise OptionError(
                "Protected opening conflicts with placed items or exhausted Cordon checks"
            )
        location = candidates.pop(0)
        if not location.can_fill(world.multiworld.state, item, True):
            raise OptionError(
                "Protected opening permission cannot be placed behind its own requirements"
            )
        location.place_locked_item(item)
        pool.remove(item)
        world.opening_placements.append({"location": location.name, "item": name})
    for name in ("Medkit", "Bandage"):
        item = next(
            (item for item in pool if item.player == world.player and item.name == name), None
        )
        if candidates and item:
            location = candidates[0]
            location.place_locked_item(item)
            pool.remove(item)
            world.opening_placements.append({"location": location.name, "item": name})
            break
