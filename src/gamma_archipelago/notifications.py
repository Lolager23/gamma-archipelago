"""Bounded, data-only PDA notices; item application remains the save's authority."""

import re
from dataclasses import dataclass

from .catalog import GAME, ITEM_EFFECTS, ITEM_IDS, MAX_ITEMS
from .notice_text import TransferMessage, clean_label, render_english
from .protocol import ProtocolError, validate_session_key

MAX_NOTICES = MAX_ITEMS * 2
MAX_NOTICE_BATCH = 16
MAX_ACK_BYTES = 1048576
_NUMBER = r"(?:0|[1-9][0-9]{0,9})"
_ITEM = r"-?(?:0|[1-9][0-9]{0,15})"
MAX_NETWORK_ID = 2**53 - 1
NOTICE_ID = re.compile(rf"(?:r:{_NUMBER}|s:{_NUMBER}:{_NUMBER}:{_ITEM})")


class NoticeSessionMismatch(ProtocolError):
    """A previous seed's notice acknowledgements must not suppress this seed."""


def _valid_identity(value: str) -> bool:
    if not NOTICE_ID.fullmatch(value):
        return False
    if value.startswith("r:"):
        return int(value[2:]) < MAX_ITEMS
    item = value.rsplit(":", 1)[1]
    return item != "-0" and abs(int(item)) <= MAX_NETWORK_ID


def is_unlock(item_id: int, game: str) -> bool:
    """Foreign progression flags do not imply equipment/permission semantics."""
    return game == GAME and ITEM_EFFECTS.get(item_id) in {
        "unlock",
        "skill",
        "progressive_tools",
        "convenience",
    }


def reward_message(player: str, item: str, *, unlock: bool, outgoing: bool) -> str:
    player, item = clean_label(player), clean_label(item)
    kind = ("sent_" if outgoing else "received_") + ("unlock" if unlock else "item")
    return render_english(TransferMessage(kind, player, item))


@dataclass(frozen=True)
class Notice:
    identity: str
    minimum_received: int
    text: str
    transfer: TransferMessage | None = None


def transfer_notice(
    identity: str,
    minimum_received: int,
    player: str,
    item: str,
    *,
    item_id: int,
    game: str,
    outgoing: bool,
) -> Notice:
    kind = ("sent_" if outgoing else "received_") + (
        "unlock" if is_unlock(item_id, game) else "item"
    )
    message = TransferMessage(
        kind,
        clean_label(player),
        clean_label(item),
        item_id if game == GAME and item_id in ITEM_IDS else 0,
    )
    return Notice(identity, minimum_received, render_english(message), message)


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
    if notice.transfer is not None:
        if notice.text != render_english(notice.transfer):
            raise ProtocolError("Transfer fallback does not match its semantic fields")
        sent = notice.transfer.kind.startswith("sent_")
        if sent != notice.identity.startswith("s:"):
            raise ProtocolError("Transfer direction does not match its identity")
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
    semantic = any(notice.transfer is not None for notice in notices)
    lines = [f"GAMMA_AP_NOTICES|{2 if semantic else 1}", f"session|{session_key}"]
    for notice in notices:
        validate_notice(notice)
        prefix = f"notice|{notice.identity}|{notice.minimum_received}|"
        message = notice.transfer
        if message is None:
            lines.append(prefix + ("text|" if semantic else "") + notice.text.encode("utf-8").hex())
        else:
            lines.append(
                prefix + f"{message.kind}|{message.player.encode('utf-8').hex()}|"
                f"{message.item.encode('utf-8').hex()}|{message.local_item_id}"
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
