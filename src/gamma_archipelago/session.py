"""One owner for validated receipt history and monotonic location checks."""

import hashlib
import json
from dataclasses import dataclass, field

from .catalog import ALL_LOCATION_IDS, ITEM_SECTIONS, LOCATION_IDS, MAX_ITEMS
from .notifications import MAX_NOTICES, Notice, validate_notice
from .protocol import GameSnapshot, ProtocolError, validate_session_key


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
    notices: dict[str, Notice] = field(default_factory=dict)
    configuration_key: str | None = None
    configuration_bound: bool = False
    allowed_locations: frozenset[int] = LOCATION_IDS
    locations_bound: bool = False

    def bind_locations(self, locations: frozenset[int]) -> None:
        if not locations or len(locations) > MAX_ITEMS or not locations <= ALL_LOCATION_IDS:
            raise ProtocolError("Unsupported seed check manifest")
        if self.locations_bound and locations != self.allowed_locations:
            raise ProtocolError("Seed check manifest changed within the same session")
        self.allowed_locations, self.locations_bound = locations, True

    def bind_configuration(self, key: str | None) -> None:
        if key is not None:
            validate_session_key(key)
        if self.configuration_bound and self.configuration_key != key:
            raise ProtocolError("Generation options changed within the same session")
        self.configuration_key, self.configuration_bound = key, True

    def add_notice(self, notice: Notice) -> None:
        validate_notice(notice)
        if notice.identity not in self.notices and len(self.notices) >= MAX_NOTICES:
            raise ProtocolError("Notice history exceeds the supported bound")
        self.notices[notice.identity] = notice

    def accept_confirmed(self, checked: frozenset[int]) -> None:
        if not checked <= self.allowed_locations:
            raise ProtocolError("Server confirmed an unsupported location")
        self.checked_locations.update(checked)

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
        if not snapshot.checked_locations <= self.allowed_locations:
            raise ProtocolError("Game reported a location disabled in this seed")
        self.checked_locations.update(snapshot.checked_locations)
        return tuple(sorted(self.checked_locations))
