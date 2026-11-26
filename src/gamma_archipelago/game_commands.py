"""Data-only, bounded game requests and authenticated connection diagnostics."""

import re
from dataclasses import dataclass

from .protocol import ProtocolError, validate_session_key
from .room_feed import safe_text

MAX_COMMAND_BYTES = 40000


class RequestIdentityMismatch(ProtocolError):
    """An old game/companion challenge is safe to ignore."""


@dataclass(frozen=True)
class GameRequest:
    sequence: int
    kind: str
    text: str


def _token(value: str) -> str:
    if not re.fullmatch("[0-9a-f]{16}", value):
        raise ProtocolError("Invalid game communication epoch")
    return value


def _number(value: str) -> int:
    if not re.fullmatch("0|[1-9][0-9]{0,8}", value):
        raise ProtocolError("Invalid game communication counter")
    return int(value)


def decode_requests(
    content: str, key: str, configuration: str | None, target: str
) -> tuple[str, tuple[GameRequest, ...]]:
    validate_session_key(key)
    if configuration is not None:
        validate_session_key(configuration)
    _token(target)
    lines = content.splitlines()
    if (
        len(content) > MAX_COMMAND_BYTES
        or not content.endswith("\n")
        or len(lines) < 6
        or lines[0] != "GAMMA_AP_COMMANDS|1"
        or not lines[3].startswith("game|")
    ):
        raise ProtocolError("Game requests are incomplete or belong to another session/connection")
    if (
        lines[1:3] != ["session|" + key, "configuration|" + (configuration or "-")]
        or lines[4] != "target|" + target
    ):
        raise RequestIdentityMismatch("Game request belongs to another session/connection")
    epoch = _token(lines[3][5:])
    if len(lines) > 38 or lines[-1] != f"end|{len(lines) - 6}":
        raise ProtocolError("Game request count mismatch")
    result = []
    previous = 0
    for line in lines[5:-1]:
        parts = line.split("|")
        if len(parts) != 4 or parts[0] != "request":
            raise ProtocolError("Malformed game request")
        sequence = _number(parts[1])
        if sequence <= previous or parts[2] not in {"loaded", "say"}:
            raise ProtocolError("Invalid game request order or kind")
        try:
            if not re.fullmatch("(?:[0-9a-f]{2})*", parts[3]):
                raise ValueError("Noncanonical hex")
            text = bytes.fromhex(parts[3]).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as error:
            raise ProtocolError("Invalid game request text encoding") from error
        # Outbound chat is hex-encoded data; sanitize PDA markup only on display.
        if len(text.encode("utf-8")) > 512 or any(
            ord(char) < 32 or ord(char) == 127 for char in text
        ):
            raise ProtocolError("Unsafe or oversized game request text")
        if (parts[2] == "loaded") != (text == ""):
            raise ProtocolError("Game request payload does not match its kind")
        result.append(GameRequest(sequence, parts[2], text))
        previous = sequence
    return epoch, tuple(result)


def encode_status(
    key: str,
    configuration: str | None,
    epoch: str,
    heartbeat: int,
    *,
    connected: bool,
    address: str,
    game_epoch: str | None,
    acknowledged: int,
    confirmed: int,
    hint_points: int,
    hint_cost: int,
    total: int,
) -> str:
    validate_session_key(key)
    if configuration is not None:
        validate_session_key(configuration)
    _token(epoch)
    if game_epoch is not None:
        _token(game_epoch)
    for number in (heartbeat, acknowledged, confirmed, hint_points, hint_cost, total):
        if type(number) is not int or not 0 <= number <= 999999999:
            raise ProtocolError("Invalid connection status counter")
    if type(connected) is not bool or safe_text(address) != address or not address:
        raise ProtocolError("Invalid connection status label")
    return "\n".join(
        [
            "GAMMA_AP_STATUS|1",
            "session|" + key,
            "configuration|" + (configuration or "-"),
            f"heartbeat|{epoch}|{heartbeat}",
            f"connection|{int(connected)}|{address.encode('utf-8').hex()}",
            f"ack|{game_epoch or '-'}|{acknowledged}",
            f"confirmed|{confirmed}",
            f"hint|{hint_points}|{hint_cost}|{total}",
            "end|1",
            "",
        ]
    )
