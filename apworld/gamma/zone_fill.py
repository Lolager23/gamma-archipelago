"""Only sparse exploration pools need an explicit anti-cycle fallback."""

from typing import TYPE_CHECKING, Any

from Options import OptionError

from gamma_archipelago.starting import starting_level

if TYPE_CHECKING:
    from . import GammaWorld


def place_zone_keys(world: "GammaWorld", catalog: dict[str, Any]) -> None:
    if (
        "rewards_zone_keys" not in world.configuration.rewards
        or "checks_maps" not in world.configuration.checks
    ):
        return
    # Global activities currently require every zone, so they cannot provide
    # intermediate route checks. Expanded regional pools must use normal AP
    # fill instead of reserving keys onto map checks, including in multiworlds.
    network = [row for row in world.multiworld.get_locations(world.player) if row.address]
    map_names = {row["name"] for row in catalog["locations"] if row["category"] == "checks_maps"}
    if any(row.name not in map_names and row.parent_region.name != "Menu" for row in network):
        return
    previous = starting_level(world.configuration)
    visited = {previous}
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
            "Sparse zone-key progression must remain local; enable regional "
            "checks or remove remaining zone keys from non_local_items"
        )
    held = {item.name for item in world.multiworld.precollected_items[world.player]}
    held_levels = {level for name, level in levels.items() if name in held} | {
        "l01_escape",
        previous,
    }
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
                    or (
                        "l08_yantar" in visited
                        and (
                            "rewards_progression_stashes" not in world.configuration.rewards
                            or "l01_escape" in visited
                        )
                    )
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
        if not location.can_fill(world.multiworld.state, item, False):
            raise OptionError("Sparse zone route conflicts with location item restrictions")
        world.multiworld.push_item(location, item, False)
        world.multiworld.itempool.remove(item)
        visited.add(target)
        previous = target


def prefer_early_hub(world: "GammaWorld", catalog: dict[str, Any]) -> None:
    if not world.configuration.option("access_pacing"):
        return
    remaining = {item.name for item in world.multiworld.itempool if item.player == world.player}
    keys = {
        row["level"]: row["name"]
        for row in catalog["items"]
        if row.get("category") == "rewards_zone_keys" and row["name"] in remaining
    }
    for hub in ("l02_garbage", "l05_bar", "l08_yantar", "l03_agroprom", "l06_rostok"):
        if hub in keys:
            # Global early_items preserves non-local placement and the upstream
            # fallback when the requested item cannot fit the initial sphere.
            early = world.multiworld.early_items[world.player]
            early[keys[hub]] = max(1, early.get(keys[hub], 0))
            break
