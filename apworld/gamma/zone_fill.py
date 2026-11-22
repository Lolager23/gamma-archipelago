"""Only sparse exploration pools need an explicit anti-cycle fallback."""

from typing import TYPE_CHECKING, Any

from BaseClasses import CollectionState, LocationProgressType
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
    # Only extra checks usable before any zone key can break a sparse opening
    # cycle. Story-only checks behind the first area key do not provide that slack.
    network = [row for row in world.multiworld.get_locations(world.player) if row.address]
    map_names = {row["name"] for row in catalog["locations"] if row["category"] == "checks_maps"}
    zone_names = {
        row["name"] for row in catalog["items"] if row.get("category") == "rewards_zone_keys"
    }
    extra = [
        row
        for row in network
        if row.name not in map_names and row.progress_type != LocationProgressType.EXCLUDED
    ]
    if (
        world.configuration.option("quest_zone_logic")
        and "checks_story_milestones" in world.configuration.checks
        and "rewards_quest_keys" in world.configuration.rewards
    ):
        return  # Keyed introductory quests provide checks before northern shutdowns.
    opening = CollectionState(world.multiworld)
    if (
        world.configuration.option("quest_zone_logic")
        and not extra
        and dict(world.configuration.gear)["starting_pda"] == 2
        and not opening.has("Equipment Unlock: PDA", world.player)
        and sum(row.can_reach(opening) for row in network if row.name in map_names) < 2
    ):
        raise OptionError(
            "Quest-restricted map-only starts need another reliable check category "
            "or a starting PDA/adjacent key; otherwise the PDA locks northern progression"
        )
    capable = CollectionState(world.multiworld)
    for item in world.multiworld.itempool:
        if item.player == world.player and item.name not in zone_names:
            capable.collect(item, True)
    filled = world.multiworld.get_filled_locations(world.player)
    capable.sweep_for_advancements(locations=filled)
    if any(
        row.name not in map_names
        and row.progress_type != LocationProgressType.EXCLUDED
        and row.can_reach(capable)
        for row in network
    ):
        return
    previous = starting_level(world.configuration)
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
    while keys:
        visited = {level for level in checks if capable.can_reach_region(level, world.player)}
        adjacent = {
            target
            for a, b in catalog["connections"]
            for source, target in ((a, b), (b, a))
            if source in visited
        }
        frontier = []
        for target, key in sorted(keys.items()):
            if target not in adjacent:
                continue
            trial = capable.copy()
            trial.collect(key, True)
            trial.sweep_for_advancements(locations=filled)
            if trial.can_reach_region(target, world.player):
                frontier.append(target)
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
        capable.collect(item, True)
        capable.sweep_for_advancements(locations=filled)
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
