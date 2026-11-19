"""Semantic PDA presentation, independent of receipts and the transport codec."""

from dataclasses import dataclass

from .catalog import ITEM_IDS
from .protocol import ProtocolError

ENGLISH_TEMPLATES = {
    "received_item": '{player} gave you "{item}".',
    "received_unlock": '{player} unlocked your "{item}".',
    "sent_item": 'You sent "{item}" to {player}.',
    "sent_unlock": 'You unlocked "{item}" for {player}.',
}


@dataclass(frozen=True)
class TransferMessage:
    kind: str
    player: str
    item: str
    local_item_id: int = 0


def clean_label(value: str) -> str:
    """Keep printable Unicode; remove PDA markup, delimiters and controls."""
    cleaned = "".join(
        character if character.isprintable() and character not in "%[]<>|" else " "
        for character in value[:96]
    )
    return " ".join(cleaned.split()) or "Archipelago"


def validate_transfer(message: TransferMessage) -> None:
    if type(message.kind) is not str or message.kind not in ENGLISH_TEMPLATES:
        raise ProtocolError("Unknown PDA transfer kind")
    for label in (message.player, message.item):
        if type(label) is not str or not label or clean_label(label) != label:
            raise ProtocolError("Transfer labels must be bounded sanitized text")
    if type(message.local_item_id) is not int or (
        message.local_item_id != 0 and message.local_item_id not in ITEM_IDS
    ):
        raise ProtocolError("Unknown localized GAMMA reward")


def render_english(message: TransferMessage) -> str:
    validate_transfer(message)
    # str.format substitutes values once: braces inside a slot/item label remain data.
    return ENGLISH_TEMPLATES[message.kind].format(player=message.player, item=message.item)
