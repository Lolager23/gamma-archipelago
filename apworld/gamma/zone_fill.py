"""Guarantee a local exploration chain without asking general fill to break cycles."""

from Options import OptionError


def place_zone_keys(world, catalog):
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
    while keys:
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
        target = world.random.choice(frontier)
        item = keys.pop(target)
        location = world.multiworld.get_location(checks[previous], world.player)
        location.place_locked_item(item)
        world.multiworld.itempool.remove(item)
        visited.add(target)
        previous = target
