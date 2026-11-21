"""CommonClient scouting; the game only sends bounded owned-location requests."""

from typing import TYPE_CHECKING

from gamma_archipelago.catalog import LOCATION_CATEGORIES, SIDE_TASK_MILESTONE_BASE
from gamma_archipelago.notice_text import clean_label
from gamma_archipelago.scouting import ScoutedReward

if TYPE_CHECKING:
    from .client import GammaContext


def preview_locations(context: "GammaContext") -> set[int]:
    pending = context.session.allowed_locations - context.session.checked_locations
    groups = (
        sorted(
            identity
            for identity in pending
            if SIDE_TASK_MILESTONE_BASE < identity <= SIDE_TASK_MILESTONE_BASE + 10000
        ),
        sorted(
            identity
            for identity in pending
            if LOCATION_CATEGORIES.get(identity) == "checks_faction_standing"
        ),
    )
    return {group[0] for group in groups if group}


async def poll(context: "GammaContext") -> None:
    configuration, session = context.configuration, context.session
    if configuration is None or session is None:
        return
    requested = (
        context.bridge.read_scout_requests(
            session.session_key, configuration.digest, session.allowed_locations
        )
        if configuration.option("scouting_mode")
        else frozenset()
    )
    previews = preview_locations(context) if configuration.option("reward_previews") else set()
    shops = (
        {
            identity
            for identity in session.allowed_locations
            if LOCATION_CATEGORIES.get(identity) == "checks_shop_purchases"
        }
        if configuration.option("playability_logic")
        else set()
    )
    wanted = set(requested) | previews | shops
    hinting = configuration.option("scouting_mode") == 2
    for hint in (False, True):
        batch = sorted(
            identity
            for identity in wanted
            if (hinting and identity in requested and identity not in context.checked_locations)
            == hint
            and identity not in (context.scouting_hints if hint else context.scouting_sent)
        )[:64]
        if batch:
            await context.send_msgs(
                [{"cmd": "LocationScouts", "locations": batch, "create_as_hint": 2 if hint else 0}]
            )
            (context.scouting_hints if hint else context.scouting_sent).update(batch)
    rewards = []
    for location in sorted(wanted & context.locations_info.keys()):
        item = context.locations_info[location]
        if item.player not in context.slot_info:
            continue
        name = context.item_names.lookup_in_slot(item.item, item.player)
        if name.startswith("Unknown item"):
            continue
        rewards.append(
            ScoutedReward(
                location,
                item.player,
                item.flags,
                clean_label(context.player_names.get(item.player, f"Player {item.player}")),
                clean_label(name),
            )
        )
    context.scouting_sequence += 1
    context.bridge.write_scouted(
        session.session_key,
        configuration.digest,
        context.scouting_epoch,
        context.scouting_sequence,
        tuple(rewards),
    )
