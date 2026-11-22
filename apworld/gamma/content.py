"""Local tool capabilities and legacy stash claims never consume reward slots."""

from typing import TYPE_CHECKING

from BaseClasses import Item, ItemClassification, Location, Region

from gamma_archipelago.content_progression import TOOL_CLAIMS, TOOL_STASHES
from gamma_archipelago.tool_permissions import TOOL_CAPABILITIES, TOOL_TIERS, enabled

if TYPE_CHECKING:
    from . import GammaWorld


def add_tool_claims(
    world: "GammaWorld",
    regions: dict[str, Region],
    location_type: type[Location],
    item_type: type[Item],
) -> None:
    if (
        not world.configuration.option("content_progression")
        or "rewards_progressive_tools" not in world.configuration.rewards
    ):
        return
    direct = enabled(world.configuration)
    items, events = (TOOL_TIERS, TOOL_CAPABILITIES) if direct else (TOOL_STASHES, TOOL_CLAIMS)
    region = world.multiworld.get_region("Menu", world.player) if direct else regions["l01_escape"]
    for tier, (coordinates, event) in enumerate(zip(items, events, strict=True)):
        claim = location_type(world.player, event, None, region)
        prior = events[tier - 1] if tier else None
        claim.access_rule = lambda state, coordinates=coordinates, prior=prior: (
            state.has(coordinates, world.player)
            and (prior is None or state.has(prior, world.player))
        )
        claim.place_locked_item(
            item_type(event, ItemClassification.progression, None, world.player)
        )
        region.locations.append(claim)


def order_tool_items(player: int, items: list[Item]) -> None:
    """Reverse fill places the few constrained tool tiers before flexible rewards."""
    tiers = {
        name: tier for names in (TOOL_STASHES, TOOL_TIERS) for tier, name in enumerate(names, 1)
    }
    positions = [index for index, item in enumerate(items) if item.player == player]
    owned = sorted((items[index] for index in positions), key=lambda item: tiers.get(item.name, 0))
    for index, item in zip(positions, owned, strict=True):
        items[index] = item
