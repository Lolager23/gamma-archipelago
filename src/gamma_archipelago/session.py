"""One owner for validated receipt history and monotonic location checks."""

import hashlib
import json
from dataclasses import dataclass, field

from .catalog import ITEM_SECTIONS, MAX_ITEMS
from .protocol import GameSnapshot, ProtocolError


def make_session_key(seed_name: str, team: int, slot: int) -> str:
    if not seed_name or type(team) is not int or type(slot) is not int or team < 0 or slot < 1:
        raise ProtocolError("A nonempty seed, nonnegative team and positive slot are required")
    identity = json.dumps([seed_name, team, slot], separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(identity.encode("ascii")).hexdigest()


@dataclass
class SessionCoordinator:
    """Coordinates values, without performing network, filesystem or game operations."""

    session_key: str
    item_ids: tuple[int, ...] = ()
    checked_locations: set[int] = field(default_factory=set)

    def accept_history(self, item_ids: tuple[int, ...]) -> None:
        if len(item_ids) > MAX_ITEMS or any(item_id not in ITEM_SECTIONS for item_id in item_ids):
            raise ProtocolError("Server history contains an unsupported item or exceeds the limit")
        if item_ids[: len(self.item_ids)] != self.item_ids:
            raise ProtocolError("Server item history changed or became shorter; resynchronise")
        self.item_ids = item_ids

    def observe_game(self, snapshot: GameSnapshot) -> tuple[int, ...]:
        if snapshot.session_key != self.session_key:
            raise ProtocolError("Refusing a game save from another session")
        if snapshot.received_count > len(self.item_ids):
            raise ProtocolError("Game has acknowledged items that the server has not supplied")
        self.checked_locations.update(snapshot.checked_locations)
        return tuple(sorted(self.checked_locations))
