"""Local physical tool-claim events never consume network reward slots."""

from typing import TYPE_CHECKING

from BaseClasses import Item, ItemClassification, Location, Region

from gamma_archipelago.content_progression import TOOL_CLAIMS, TOOL_STASHES

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
    for tier, (coordinates, event) in enumerate(zip(TOOL_STASHES, TOOL_CLAIMS, strict=True)):
        claim = location_type(world.player, event, None, regions["l01_escape"])
        prior = TOOL_CLAIMS[tier - 1] if tier else None
        claim.access_rule = lambda state, coordinates=coordinates, prior=prior: (
            state.has(coordinates, world.player)
            and (prior is None or state.has(prior, world.player))
        )
        claim.place_locked_item(
            item_type(event, ItemClassification.progression, None, world.player)
        )
        regions["l01_escape"].locations.append(claim)


def order_tool_items(player: int, items: list[Item]) -> None:
    """Reverse fill places the few constrained tool tiers before flexible rewards."""
    tiers = {name: tier for tier, name in enumerate(TOOL_STASHES, 1)}
    positions = [index for index, item in enumerate(items) if item.player == player]
    owned = sorted((items[index] for index in positions), key=lambda item: tiers.get(item.name, 0))
    for index, item in zip(positions, owned, strict=True):
        items[index] = item
