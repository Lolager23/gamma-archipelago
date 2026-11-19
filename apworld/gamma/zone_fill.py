"""Guarantee a local exploration chain without asking general fill to break cycles."""

from typing import TYPE_CHECKING, Any

from Options import OptionError

if TYPE_CHECKING:
    from . import GammaWorld


def place_zone_keys(world: "GammaWorld", catalog: dict[str, Any]) -> None:
    if "rewards_zone_keys" not in world.configuration.rewards:
        return
    visited = {"l01_escape"}
    previous = "l01_escape"
    checks = {
        row["level"]: row["name"]
        for row in catalog["locations"]
        if row["category"] == "checks_maps"
    }
    if set(checks.values()) & world.options.exclude_locations.value:
        raise OptionError("Zone-key exploration checks cannot be excluded")
    levels = {
        row["name"]: row["level"]
        for row in catalog["items"]
        if row.get("category") == "rewards_zone_keys"
    }
    keys = {
        levels[item.name]: item
        for item in world.multiworld.itempool
        if item.player == world.player and item.name in levels
    }
    if any(item.name in world.options.non_local_items.value for item in keys.values()):
        raise OptionError(
            "Zone-key progression must remain local; "
            "remove remaining zone keys from non_local_items"
        )
    held = {item.name for item in world.multiworld.precollected_items[world.player]}
    held_levels = {level for name, level in levels.items() if name in held}
    while keys:
        changed = True
        while changed:
            before = len(visited)
            for a, b in catalog["connections"]:
                if a in visited and b in held_levels:
                    visited.add(b)
                if b in visited and a in held_levels:
                    visited.add(a)
            changed = len(visited) > before
        frontier = sorted(
            {
                target
                for a, b in catalog["connections"]
                for source, target in ((a, b), (b, a))
                if source in visited
                and target in keys
                and (
                    target not in {"l10_radar", "l10u_bunker", "l08u_brainlab"}
                    or "l08_yantar" in visited
                )
            }
        )
        if not frontier:
            raise OptionError("Zone-key graph cannot reach every remaining destination")
        if world.configuration.option("access_pacing"):
            hubs = ("l02_garbage", "l05_bar", "l08_yantar", "l03_agroprom", "l06_rostok")
            favored = [level for level in hubs if level in frontier]
            target = favored[0] if favored else world.random.choice(frontier)
        else:
            target = world.random.choice(frontier)
        item = keys.pop(target)
        location = world.multiworld.get_location(checks[previous], world.player)
        if location.item is not None:
            free = [
                world.multiworld.get_location(checks[level], world.player)
                for level in sorted(visited)
                if world.multiworld.get_location(checks[level], world.player).item is None
            ]
            if not free:
                raise OptionError("Zone route has no unreserved reachable map check")
            location = free[0]
        location.place_locked_item(item)
        world.multiworld.itempool.remove(item)
        visited.add(target)
        previous = target
