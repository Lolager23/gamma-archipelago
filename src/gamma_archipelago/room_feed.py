"""Bounded room presentation snapshots, separate from saved reward acknowledgements."""

import re
from dataclasses import dataclass

from .protocol import ProtocolError, validate_session_key

MAX_MESSAGES = 64
MAX_TEXT_BYTES = 2048
MAX_SEQUENCE = 999999999
MAX_FEED_BYTES = 280000


@dataclass(frozen=True)
class RoomMessage:
    sequence: int
    text: str


def safe_text(value: str) -> str:
    text = "".join(char if char.isprintable() and char not in "%[]<>|" else " " for char in value)
    return " ".join(text.split()).encode("utf-8")[:MAX_TEXT_BYTES].decode("utf-8", "ignore")


def encode_feed(
    key: str,
    configuration: str | None,
    epoch: str,
    heartbeat: int,
    messages: tuple[RoomMessage, ...],
) -> str:
    validate_session_key(key)
    if configuration is not None:
        validate_session_key(configuration)
    if not re.fullmatch("[0-9a-f]{16}", epoch):
        raise ProtocolError("Invalid room feed epoch")
    if type(heartbeat) is not int or not 1 <= heartbeat <= MAX_SEQUENCE:
        raise ProtocolError("Invalid room heartbeat")
    if len(messages) > MAX_MESSAGES:
        raise ProtocolError("Too many room messages")
    lines = [
        "GAMMA_AP_ROOM|1",
        "session|" + key,
        "configuration|" + (configuration or "-"),
        f"heartbeat|{epoch}|{heartbeat}",
    ]
    previous = 0
    for message in messages:
        if type(message.sequence) is not int or not previous < message.sequence <= MAX_SEQUENCE:
            raise ProtocolError("Room messages must have increasing sequence numbers")
        if not message.text or safe_text(message.text) != message.text:
            raise ProtocolError("Unsafe or oversized room message")
        lines.append(f"message|{message.sequence}|{message.text.encode('utf-8').hex()}")
        previous = message.sequence
    return "\n".join([*lines, f"end|{len(messages)}", ""])
