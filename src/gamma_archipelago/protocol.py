"""Strict data-only snapshots shared with Lua; no executable commands cross the bridge."""

import re
from dataclasses import dataclass

from .catalog import ALL_LOCATION_IDS, ITEM_IDS, LOCATION_IDS, MAX_ITEMS, MAX_SNAPSHOT_BYTES


class ProtocolError(ValueError):
    """A snapshot is incomplete, incompatible or belongs to another session."""


@dataclass(frozen=True)
class GameSnapshot:
    session_key: str
    received_count: int
    checked_locations: frozenset[int]
    goal_complete: bool


def validate_session_key(value: str) -> None:
    if re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ProtocolError("Session key must contain 64 lowercase hexadecimal characters")


def _number(value: str) -> int:
    if re.fullmatch(r"0|[1-9][0-9]{0,9}", value) is None:
        raise ProtocolError("Expected a canonical nonnegative integer")
    return int(value)


def encode_incoming(
    session_key: str, item_ids: tuple[int, ...], configuration_key: str | None = None
) -> str:
    validate_session_key(session_key)
    if len(item_ids) > MAX_ITEMS or any(item_id not in ITEM_IDS for item_id in item_ids):
        raise ProtocolError("Incoming history contains too many items or an unsupported item")
    lines = [f"GAMMA_AP_IN|{2 if configuration_key is not None else 1}", f"session|{session_key}"]
    if configuration_key is not None:
        validate_session_key(configuration_key)
        lines.append(f"configuration|{configuration_key}")
    lines.extend(f"item|{index}|{item_id}" for index, item_id in enumerate(item_ids))
    lines.append(f"end|{len(item_ids)}")
    return "\n".join(lines) + "\n"


def encode_confirmed(session_key: str, location_ids: frozenset[int]) -> str:
    validate_session_key(session_key)
    if len(location_ids) > MAX_ITEMS or not location_ids <= ALL_LOCATION_IDS:
        raise ProtocolError("Confirmed checks contain an unsupported location")
    lines = ["GAMMA_AP_CONFIRMED|1", f"session|{session_key}"]
    lines.extend(f"check|{identity}" for identity in sorted(location_ids))
    lines.append(f"end|{len(location_ids)}")
    return "\n".join(lines) + "\n"


def decode_outgoing(
    content: str,
    session_key: str,
    allowed_locations: frozenset[int] = LOCATION_IDS,
    *,
    pilot_goal: bool = True,
    configuration_key: str | None = None,
) -> GameSnapshot:
    validate_session_key(session_key)
    if configuration_key is not None:
        validate_session_key(configuration_key)
    if len(content.encode("utf-8")) > MAX_SNAPSHOT_BYTES or not content.endswith("\n"):
        raise ProtocolError("Snapshot is oversized or missing its final newline")
    lines = content.splitlines()
    version = 3 if configuration_key is not None else (1 if pilot_goal else 2)
    received_index = 3 if configuration_key is not None else 2
    if len(lines) < received_index + 3 or lines[0] != f"GAMMA_AP_OUT|{version}":
        raise ProtocolError("Unsupported or incomplete game snapshot")
    if lines[1] != f"session|{session_key}":
        raise ProtocolError("Game snapshot belongs to another seed or slot")
    if configuration_key is not None and lines[2] != f"configuration|{configuration_key}":
        raise ProtocolError("Game snapshot belongs to another configuration")
    if not lines[received_index].startswith("received|") or lines[-2] not in ("goal|0", "goal|1"):
        raise ProtocolError("Snapshot fields are missing or out of order")
    received_count = _number(lines[received_index].removeprefix("received|"))
    if received_count > MAX_ITEMS:
        raise ProtocolError("Received count exceeds the supported history size")
    checks = []
    for line in lines[received_index + 1 : -2]:
        if not line.startswith("check|"):
            raise ProtocolError("Unexpected snapshot field")
        location_id = _number(line.removeprefix("check|"))
        if location_id not in allowed_locations or location_id in checks:
            raise ProtocolError("Unknown or duplicate location")
        checks.append(location_id)
    if lines[-1] != f"end|{len(checks)}":
        raise ProtocolError("Snapshot trailer does not match its check count")
    goal = lines[-2] == "goal|1"
    if (
        pilot_goal
        and goal
        and allowed_locations >= LOCATION_IDS
        and not frozenset(checks) >= LOCATION_IDS
    ):
        raise ProtocolError("Pilot completion requires every pilot location")
    return GameSnapshot(session_key, received_count, frozenset(checks), goal)
