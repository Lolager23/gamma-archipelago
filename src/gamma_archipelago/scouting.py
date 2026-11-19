"""Optional, bounded scouting metadata; these records can never acknowledge items."""

import re
from dataclasses import dataclass

from .notice_text import clean_label
from .protocol import ProtocolError, validate_session_key

MAX_SCOUTS = 512
MAX_SCOUT_BYTES = 1048576
_EPOCH = re.compile(r"[0-9a-f]{16}")


@dataclass(frozen=True)
class ScoutedReward:
    location: int
    recipient: int
    flags: int
    player: str
    item: str


def decode_requests(
    content: str, key: str, configuration: str, allowed: frozenset[int]
) -> frozenset[int]:
    validate_session_key(key)
    validate_session_key(configuration)
    if not content.isascii() or len(content) > MAX_SCOUT_BYTES or not content.endswith("\n"):
        raise ProtocolError("Scouting requests are incomplete or oversized")
    lines = content.splitlines()
    if len(lines) < 4 or lines[:3] != [
        "GAMMA_AP_SCOUTS|1",
        f"session|{key}",
        f"configuration|{configuration}",
    ]:
        raise ProtocolError("Scouting request protocol/session/configuration mismatch")
    ids = []
    for line in lines[3:-1]:
        if not re.fullmatch(r"request\|[1-9][0-9]{0,9}", line):
            raise ProtocolError("Malformed scouting request")
        ids.append(int(line.removeprefix("request|")))
    if (
        len(ids) > MAX_SCOUTS
        or len(set(ids)) != len(ids)
        or not set(ids) <= allowed
        or lines[-1] != f"end|{len(ids)}"
    ):
        raise ProtocolError("Scouting requests exceed their enabled manifest or repeat an ID")
    return frozenset(ids)


def encode_scouted(
    key: str, configuration: str, epoch: str, sequence: int, rewards: tuple[ScoutedReward, ...]
) -> str:
    validate_session_key(key)
    validate_session_key(configuration)
    if not _EPOCH.fullmatch(epoch) or type(sequence) is not int or not 0 <= sequence <= 9999999999:
        raise ProtocolError("Invalid scouting heartbeat")
    if len(rewards) > MAX_SCOUTS or len({reward.location for reward in rewards}) != len(rewards):
        raise ProtocolError("Scouting metadata is oversized or repeats a check")
    lines = [
        "GAMMA_AP_SCOUTED|1",
        f"session|{key}",
        f"configuration|{configuration}",
        f"heartbeat|{epoch}|{sequence}",
    ]
    for reward in rewards:
        for value, minimum, maximum in (
            (reward.location, 1, 2147483647),
            (reward.recipient, 1, 9999999999),
            (reward.flags, 0, 7),
        ):
            if type(value) is not int or not minimum <= value <= maximum:
                raise ProtocolError("Scouting metadata has an invalid ID or flags")
        for label in (reward.player, reward.item):
            if type(label) is not str or not label or label != clean_label(label):
                raise ProtocolError("Scouted labels must be sanitized bounded text")
        lines.append(
            f"item|{reward.location}|{reward.recipient}|{reward.flags}|"
            f"{reward.player.encode('utf-8').hex()}|{reward.item.encode('utf-8').hex()}"
        )
    lines.append(f"end|{len(rewards)}")
    return "\n".join(lines) + "\n"
