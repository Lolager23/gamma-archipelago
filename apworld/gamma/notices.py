"""Translate authenticated AP source metadata into optional PDA notices."""

from typing import TYPE_CHECKING

from NetUtils import NetworkItem

from gamma_archipelago.catalog import ALL_LOCATION_IDS, GAME
from gamma_archipelago.notice_causes import CheckCause, cause_for_check
from gamma_archipelago.notice_text import clean_label
from gamma_archipelago.notifications import MAX_NETWORK_ID, transfer_notice

if TYPE_CHECKING:
    from .client import GammaContext


def source_cause(context: "GammaContext", location: int, slot: int) -> CheckCause | None:
    if type(location) is not int or abs(location) > MAX_NETWORK_ID or type(slot) is not int:
        return None
    if slot == context.slot or (slot == 0 and location < 0):
        game = GAME
    elif slot in context.slot_info:
        game = context.slot_info[slot].game
    else:
        return None
    if game == GAME and location in ALL_LOCATION_IDS:
        return cause_for_check(location, "")
    name = context.location_names.lookup_in_game(location, game)
    if type(name) is not str or name == f"Unknown location (ID: {location})":
        return None  # Metadata may arrive later; reward application never waits here.
    return CheckCause("source" if location < 0 else "check", clean_label(name))


def received(context: "GammaContext") -> None:
    if context.session is None:
        return
    for index, item in enumerate(context.items_received):
        name = context.item_names.lookup_in_game(item.item)
        if name.startswith("Unknown item"):
            continue
        cause = source_cause(context, item.location, item.player)
        if cause is None:
            continue
        context.session.add_notice(
            transfer_notice(
                f"r:{index}",
                index + 1,
                context.player_names.get(item.player, f"Player {item.player}"),
                name,
                item_id=item.item,
                game=GAME,
                outgoing=False,
                cause=cause,
            )
        )


def sent(context: "GammaContext", item: NetworkItem, recipient: int) -> None:
    if context.session is None or recipient not in context.slot_info:
        return
    name = context.item_names.lookup_in_slot(item.item, recipient)
    if name.startswith("Unknown item"):
        return
    cause = source_cause(context, item.location, context.slot)
    if cause is None:
        return
    context.session.add_notice(
        transfer_notice(
            f"s:{item.location}:{recipient}:{item.item}",
            0,
            context.player_names.get(recipient, f"Player {recipient}"),
            name,
            item_id=item.item,
            game=context.slot_info[recipient].game,
            outgoing=True,
            cause=cause,
        )
    )
