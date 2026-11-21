"""Reserve explicit local starting permissions before zone-route reservations."""

from typing import TYPE_CHECKING, Any

from BaseClasses import CollectionState, LocationProgressType
from Options import OptionError

from gamma_archipelago.opening import opening_checks, opening_permissions
from gamma_archipelago.starting import starting_level

if TYPE_CHECKING:
    from . import GammaWorld


def request_activity_opener(world: "GammaWorld", catalog: dict[str, Any]) -> None:
    """Avoid filling a locked opening with several mutually dependent tool items."""
    # A free baseline rank is one finite check, not an opened quest/combat route.
    quiet = {
        row["id"]
        for row in catalog["locations"]
        if row["category"] in {"checks_maps", "checks_settlements"}
        or (row["category"] == "checks_rank_milestones" and row["minimum"] == 0)
    }
    opportunities = [
        loc
        for loc in world.multiworld.get_locations(world.player)
        if loc.address
        and loc.progress_type != LocationProgressType.EXCLUDED
        and loc.address not in quiet
    ]
    state = CollectionState(world.multiworld)
    state.sweep_for_advancements()
    if any(loc.can_reach(state) for loc in opportunities):
        return
    remaining = {
        item.name: item for item in world.multiworld.itempool if item.player == world.player
    }
    candidates = []
    for group in ("PDA", "Detector", "Firearms", "Melee"):
        name = "Equipment Unlock: " + group
        if name in remaining:
            capable = state.copy()
            capable.collect(remaining[name], True)
            if any(loc.can_reach(capable) for loc in opportunities):
                candidates.append(name)
    if candidates:
        # Upstream chooses an eligible local/remote check. No location is reserved
        # here, and an existing stronger user request remains authoritative.
        early = world.multiworld.early_items[world.player]
        local = world.multiworld.local_early_items[world.player]
        if any(early.get(name, 0) or local.get(name, 0) for name in candidates):
            return
        name = world.random.choice(candidates)
        early[name] = max(1, early.get(name, 0))


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
    allowed = opening_checks(
        frozenset(row.address for row in locations),
        frozenset(),
        zoned,
        starting_level(world.configuration),
    )
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
        if item is None or name in world.options.non_local_items.value:
            continue
        location = next(
            (row for row in candidates if row.can_fill(world.multiworld.state, item, True)), None
        )
        if location is not None:
            location.place_locked_item(item)
            pool.remove(item)
            world.opening_placements.append({"location": location.name, "item": name})
            break
