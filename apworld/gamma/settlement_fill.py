"""A bounded upstream early request for otherwise cramped reputation-only pools."""

from collections import Counter
from typing import TYPE_CHECKING

from BaseClasses import CollectionState, LocationProgressType
from Options import OptionError

from gamma_archipelago.settlement_access import NEUTRALITY_ITEMS, required_reputation, requirement

if TYPE_CHECKING:
    from . import GammaWorld


def request_neutrality_opener(world: "GammaWorld") -> None:
    locations = [loc for loc in world.multiworld.get_locations(world.player) if loc.address]
    quotas = required_reputation(world.configuration, frozenset(loc.address for loc in locations))
    if not quotas:
        return
    initial = CollectionState(world.multiworld)
    capable = initial.copy()
    for item in world.multiworld.itempool:
        if item.player == world.player and item.name not in NEUTRALITY_ITEMS:
            capable.collect(item, True)
    needed = {
        name: max(0, count - initial.count(name, world.player)) for name, count in quotas.items()
    }
    eligible = [loc for loc in locations if loc.progress_type != LocationProgressType.EXCLUDED]
    if sum(loc.can_reach(capable) for loc in eligible) >= sum(needed.values()):
        return
    benefits = Counter(
        rule.name
        for loc in locations
        if (rule := requirement(world.configuration, loc.address)) and needed[rule.name]
    )
    # Military opens two bases; one-base quotas can consume the last free checks
    # before either remaining quota is complete. Never fix an item to a location.
    name = max(sorted(benefits), key=benefits.get)
    if sum(loc.can_reach(initial) for loc in eligible) < needed[name]:
        raise OptionError("Sparse neutrality logic needs more initially available checks")
    early = world.multiworld.early_items[world.player]
    local = world.multiworld.local_early_items[world.player]
    early[name] = max(early.get(name, 0), needed[name] - local.get(name, 0))
