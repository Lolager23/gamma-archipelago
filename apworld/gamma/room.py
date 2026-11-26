"""Transient, bounded AP room news. This cache never owns checks or receipts."""

import secrets
from collections import deque
from copy import deepcopy
from typing import TYPE_CHECKING, Any

from NetUtils import NetworkItem

from gamma_archipelago.notice_causes import CAUSE_TEMPLATES
from gamma_archipelago.notice_text import clean_label
from gamma_archipelago.notifications import is_unlock
from gamma_archipelago.room_feed import MAX_MESSAGES, RoomMessage, safe_text

from .notices import source_cause

if TYPE_CHECKING:
    from .client import GammaContext


class RoomFeed:
    def __init__(self) -> None:
        self.epoch = secrets.token_hex(8)
        self.heartbeat = 0
        self.sequence = 0
        self.messages: deque[RoomMessage] = deque(maxlen=MAX_MESSAGES)
        self.transfers: dict[tuple[int, int, int, int], tuple[NetworkItem, int]] = {}
        self.seen: deque[tuple[int, int, int, int]] = deque(maxlen=4000)

    def append(self, text: str) -> None:
        text = safe_text(text)
        if text:
            self.sequence += 1
            self.messages.append(RoomMessage(self.sequence, text))

    def receive(self, context: "GammaContext", command: str, arguments: dict[str, Any]) -> None:
        if command == "Print":
            text = arguments.get("text")
            if type(text) is str:
                self.append(text)
        elif command == "PrintJSON":
            kind = arguments.get("type")
            if kind == "ItemSend":
                item, recipient = arguments.get("item"), arguments.get("receiving")
                if (
                    isinstance(item, NetworkItem)
                    and type(recipient) is int
                    and item.player != context.slot
                    and recipient != context.slot
                ):
                    identity = (item.player, item.location, recipient, item.item)
                    if identity not in self.seen and len(self.transfers) < 4000:
                        self.transfers[identity] = (item, recipient)
            elif kind in {"Chat", "ServerChat", "CommandResult", "Hint", "Join", "Part", "Goal"}:
                data = arguments.get("data")
                if isinstance(data, list):
                    self.append(context.jsontotextparser(deepcopy(data)))
        self.resolve(context)

    def resolve(self, context: "GammaContext") -> None:
        for identity, (item, recipient) in tuple(self.transfers.items()):
            if recipient not in context.slot_info:
                continue
            name = context.item_names.lookup_in_slot(item.item, recipient)
            cause = source_cause(context, item.location, item.player)
            if name.startswith("Unknown item") or cause is None:
                continue
            finder = clean_label(context.player_names.get(item.player, f"Player {item.player}"))
            receiver = clean_label(context.player_names.get(recipient, f"Player {recipient}"))
            unlock = is_unlock(item.item, context.slot_info[recipient].game)
            action = (
                f'unlocked "{clean_label(name)}" for'
                if unlock
                else f'gave "{clean_label(name)}" to'
            )
            reason = CAUSE_TEMPLATES[cause.kind].format(value=cause.value)
            self.append(f"{finder} {action} {receiver} {reason}.")
            self.seen.append(identity)
            del self.transfers[identity]

    def publish(self, context: "GammaContext") -> None:
        self.heartbeat += 1
        context.bridge.write_room_feed(
            context.session.session_key,
            context.bridge.configuration_key,
            self.epoch,
            self.heartbeat,
            tuple(self.messages),
        )
