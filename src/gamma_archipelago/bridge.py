"""One file writer per direction; incomplete game snapshots are never interpreted as commands."""

import os
from pathlib import Path

from .catalog import MAX_SNAPSHOT_BYTES
from .paths import require_isolated_root, require_safe_child
from .protocol import GameSnapshot, ProtocolError, decode_outgoing, encode_incoming


class FileBridge:
    def __init__(self, game_root: Path, *, allowed_root: Path) -> None:
        self.game_root = require_isolated_root(game_root, allowed_root)
        self.directory = require_safe_child(self.game_root, "appdata/archipelago")
        self.directory.mkdir(parents=True, exist_ok=True)

    def write_history(self, session_key: str, item_ids: tuple[int, ...]) -> None:
        content = encode_incoming(session_key, item_ids)
        destination = require_safe_child(self.game_root, "appdata/archipelago/incoming.txt")
        temporary = require_safe_child(self.game_root, "appdata/archipelago/incoming.tmp")
        with temporary.open("w", encoding="ascii", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)

    def read_game(self, session_key: str) -> GameSnapshot | None:
        source = require_safe_child(self.game_root, "appdata/archipelago/outgoing.txt")
        try:
            with source.open("r", encoding="ascii") as stream:
                content = stream.read(MAX_SNAPSHOT_BYTES + 1)
        except FileNotFoundError:
            return None
        except UnicodeDecodeError as exc:
            raise ProtocolError("Game snapshot must be ASCII data") from exc
        return decode_outgoing(content, session_key)
