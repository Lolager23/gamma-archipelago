"""Live companion presentation only; presence cannot acknowledge checks or rewards."""

import re

from .notice_text import clean_label
from .protocol import ProtocolError, validate_session_key


def encode_presence(
    key: str, configuration: str | None, epoch: str, sequence: int, player: str
) -> str:
    validate_session_key(key)
    if configuration is not None:
        validate_session_key(configuration)
    if (
        type(epoch) is not str
        or re.fullmatch(r"[0-9a-f]{16}", epoch) is None
        or type(sequence) is not int
        or not 0 <= sequence <= 9999999999
    ):
        raise ProtocolError("Invalid presence heartbeat")
    if type(player) is not str or not player or player != clean_label(player):
        raise ProtocolError("Presence player must be bounded sanitized text")
    return "\n".join(
        [
            "GAMMA_AP_PRESENCE|1",
            f"session|{key}",
            f"configuration|{configuration or '-'}",
            f"heartbeat|{epoch}|{sequence}",
            f"player|{player.encode('utf-8').hex()}",
            "end|1",
            "",
        ]
    )
