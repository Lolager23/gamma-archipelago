"""One file writer per direction; incomplete game snapshots are never interpreted as commands."""

import os
from pathlib import Path

from .catalog import LOCATION_IDS, MAX_SNAPSHOT_BYTES
from .configuration import SeedConfiguration, encode_configuration
from .notifications import (
    MAX_ACK_BYTES,
    Notice,
    NoticeSessionMismatch,
    decode_acknowledgements,
    encode_notices,
    pending_batch,
)
from .paths import require_isolated_root, require_safe_child
from .protocol import (
    GameSnapshot,
    ProtocolError,
    decode_outgoing,
    encode_confirmed,
    encode_incoming,
)


class FileBridge:
    def __init__(self, game_root: Path, *, allowed_root: Path) -> None:
        self.game_root = require_isolated_root(game_root, allowed_root)
        self.directory = require_safe_child(self.game_root, "appdata/archipelago")
        self.directory.mkdir(parents=True, exist_ok=True)
        self.allowed_locations = LOCATION_IDS

    def write_history(
        self, session_key: str, item_ids: tuple[int, ...], configuration_key: str | None = None
    ) -> None:
        content = encode_incoming(session_key, item_ids, configuration_key)
        self._write_atomic("incoming", content)

    def _write_atomic(self, name: str, content: str) -> None:
        destination = require_safe_child(self.game_root, f"appdata/archipelago/{name}.txt")
        temporary = require_safe_child(self.game_root, f"appdata/archipelago/{name}.tmp")
        with temporary.open("w", encoding="ascii", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)

    def write_notices(self, session_key: str, notices: tuple[Notice, ...]) -> None:
        source = require_safe_child(self.game_root, "appdata/archipelago/notices_ack.txt")
        try:
            with source.open("r", encoding="ascii") as stream:
                seen = decode_acknowledgements(stream.read(MAX_ACK_BYTES + 1), session_key)
        except (FileNotFoundError, NoticeSessionMismatch):
            seen = frozenset()
        except UnicodeDecodeError as exc:
            raise ProtocolError("Notice acknowledgements must be ASCII data") from exc
        self._write_atomic("notices", encode_notices(session_key, pending_batch(notices, seen)))

    def write_confirmed(self, session_key: str, location_ids: frozenset[int]) -> None:
        self._write_atomic("confirmed_checks", encode_confirmed(session_key, location_ids))

    def write_configuration(
        self, session_key: str, configuration: SeedConfiguration, expanded: bool = False
    ) -> None:
        self._write_atomic(
            "configuration", encode_configuration(session_key, configuration, expanded)
        )

    def read_game(self, session_key: str) -> GameSnapshot | None:
        source = require_safe_child(self.game_root, "appdata/archipelago/outgoing.txt")
        try:
            with source.open("r", encoding="ascii") as stream:
                content = stream.read(MAX_SNAPSHOT_BYTES + 1)
        except FileNotFoundError:
            return None
        except UnicodeDecodeError as exc:
            raise ProtocolError("Game snapshot must be ASCII data") from exc
        return decode_outgoing(content, session_key, self.allowed_locations)
