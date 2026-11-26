"""One bounded request queue for game-originated room chat and hints."""

from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from gamma_archipelago.notice_text import clean_label

if TYPE_CHECKING:
    from .client import GammaContext


def connected(context: "GammaContext") -> bool:
    socket = getattr(context.server, "socket", None)
    return bool(
        context.server and context.slot and (socket is None or (socket.open and not socket.closed))
    )


def address_label(address: str | None) -> str:
    if not address:
        return "Server address unavailable"
    try:
        parsed = urlsplit(address if "://" in address else "ws://" + address)
        host, port = parsed.hostname, parsed.port
    except ValueError:
        return "Configured server"
    if not host:
        return "Configured server"
    if ":" in host:
        return clean_label(host + (f" (port {port})" if port else ""))
    return clean_label(host + (f":{port}" if port else ""))


class GameInteraction:
    def __init__(self) -> None:
        self.acknowledged: dict[str, int] = {}
        self.last_game: str | None = None
        self.heartbeat = 0

    async def poll(self, context: "GammaContext") -> None:
        online = connected(context)
        self.heartbeat += 1
        context.bridge.write_connection_status(
            context.session.session_key,
            context.room.epoch,
            self.heartbeat,
            connected=online,
            address=address_label(context.server_address),
            game_epoch=self.last_game,
            acknowledged=self.acknowledged.get(self.last_game, 0),
            confirmed=len(context.checked_locations),
            hint_points=context.hint_points or 0,
            hint_cost=context.hint_cost or 0,
            total=len(context.server_locations),
        )

        if online:
            request = context.bridge.read_commands(context.session.session_key, context.room.epoch)
            if request is not None:
                epoch, commands = request
                self.last_game = epoch
                previous = self.acknowledged.get(epoch, commands[0].sequence - 1 if commands else 0)
                for command in commands:
                    if command.sequence <= previous:
                        continue
                    if command.sequence != previous + 1:
                        break  # A partial/gapped queue cannot advance its acknowledgement.
                    text = command.text
                    if command.kind == "loaded":
                        player = clean_label(context.player_names.get(context.slot, "Player"))
                        text = player + " loaded GAMMA and entered the Zone."
                    await context.send_msgs([{"cmd": "Say", "text": text}])
                    previous = command.sequence
                    self.acknowledged[epoch] = previous
                # A process lifetime cache only; no server/save ownership changes.
                if len(self.acknowledged) > 8:
                    del self.acknowledged[next(iter(self.acknowledged))]
