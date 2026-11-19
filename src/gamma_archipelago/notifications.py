"""Bounded, data-only PDA notices; item application remains the save's authority."""

import re
from dataclasses import dataclass

from .catalog import GAME, ITEM_EFFECTS, MAX_ITEMS
from .protocol import ProtocolError, validate_session_key

MAX_NOTICES = MAX_ITEMS * 2
MAX_NOTICE_BATCH = 16
MAX_ACK_BYTES = 1048576
_NUMBER = r"(?:0|[1-9][0-9]{0,9})"
NOTICE_ID = re.compile(rf"(?:r:{_NUMBER}|s:{_NUMBER}:{_NUMBER}:{_NUMBER})")


class NoticeSessionMismatch(ProtocolError):
    """A previous seed's notice acknowledgements must not suppress this seed."""


def _valid_identity(value: str) -> bool:
    return bool(NOTICE_ID.fullmatch(value)) and (
        not value.startswith("r:") or int(value[2:]) < MAX_ITEMS
    )


def clean_label(value: str) -> str:
    """Keep Unicode names while removing PDA markup, delimiters and control text."""
    cleaned = "".join(
        character if character.isprintable() and character not in "%[]<>|" else " "
        for character in value[:96]
    )
    return " ".join(cleaned.split()) or "Archipelago"


def is_unlock(item_id: int, game: str) -> bool:
    """Foreign progression flags do not imply equipment/permission semantics."""
    return game == GAME and ITEM_EFFECTS.get(item_id) in {"unlock", "skill"}


def reward_message(player: str, item: str, *, unlock: bool, outgoing: bool) -> str:
    player, item = clean_label(player), clean_label(item)
    if outgoing:
        return f"You unlocked {player}'s {item}" if unlock else f"You gave {player} {item}"
    return f"{player} unlocked your {item}" if unlock else f"{player} gave you a {item}"


@dataclass(frozen=True)
class Notice:
    identity: str
    minimum_received: int
    text: str


def validate_notice(notice: Notice) -> None:
    if not _valid_identity(notice.identity):
        raise ProtocolError("Invalid notice identity")
    if type(notice.minimum_received) is not int or not 0 <= notice.minimum_received <= MAX_ITEMS:
        raise ProtocolError("Invalid notice receipt boundary")
    if notice.identity.startswith("r:"):
        if notice.minimum_received != int(notice.identity[2:]) + 1:
            raise ProtocolError("Incoming notice does not match its receipt index")
    elif notice.minimum_received != 0:
        raise ProtocolError("Outgoing notice must not depend on a local reward")
    if (
        not notice.text
        or len(notice.text.encode("utf-8")) > 2048
        or any(not character.isprintable() or character in "%[]<>|" for character in notice.text)
    ):
        raise ProtocolError("Unsafe or oversized PDA notice text")


def encode_notices(session_key: str, notices: tuple[Notice, ...]) -> str:
    validate_session_key(session_key)
    if len(notices) > MAX_NOTICE_BATCH or len({notice.identity for notice in notices}) != len(
        notices
    ):
        raise ProtocolError("Notice batch is too large or repeats an identity")
    lines = ["GAMMA_AP_NOTICES|1", f"session|{session_key}"]
    for notice in notices:
        validate_notice(notice)
        lines.append(
            f"notice|{notice.identity}|{notice.minimum_received}|{notice.text.encode('utf-8').hex()}"
        )
    lines.append(f"end|{len(notices)}")
    return "\n".join(lines) + "\n"


def decode_acknowledgements(content: str, session_key: str) -> frozenset[str]:
    validate_session_key(session_key)
    if len(content.encode("utf-8")) > MAX_ACK_BYTES or not content.endswith("\n"):
        raise ProtocolError("Notice acknowledgements are oversized or incomplete")
    lines = content.splitlines()
    if (
        len(lines) < 3
        or lines[0] != "GAMMA_AP_NOTICES_ACK|1"
        or not lines[1].startswith("session|")
    ):
        raise ProtocolError("Notice acknowledgements have an unsupported protocol")
    saved_key = lines[1].removeprefix("session|")
    validate_session_key(saved_key)
    if saved_key != session_key:
        raise NoticeSessionMismatch("Notice acknowledgements belong to another session")
    identities = lines[2:-1]
    if (
        len(identities) > MAX_NOTICES
        or len(set(identities)) != len(identities)
        or any(not _valid_identity(identity) for identity in identities)
        or lines[-1] != f"end|{len(identities)}"
    ):
        raise ProtocolError("Malformed notice acknowledgements")
    return frozenset(identities)


def pending_batch(notices: tuple[Notice, ...], seen: frozenset[str]) -> tuple[Notice, ...]:
    return tuple(notice for notice in notices if notice.identity not in seen)[:MAX_NOTICE_BATCH]
