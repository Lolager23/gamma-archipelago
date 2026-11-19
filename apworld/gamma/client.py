"""Use upstream CommonClient for authentication, websockets, reconnect and item sync."""

import asyncio
import logging
from argparse import Namespace
from contextlib import suppress
from typing import Any

from CommonClient import CommonContext, get_base_parser, server_loop
from NetUtils import ClientStatus, NetworkItem

from gamma_archipelago.bridge import FileBridge
from gamma_archipelago.catalog import GAME
from gamma_archipelago.notifications import Notice, is_unlock, reward_message
from gamma_archipelago.paths import DEFAULT_GAME_ROOT
from gamma_archipelago.protocol import ProtocolError
from gamma_archipelago.session import SessionCoordinator, make_session_key

logger = logging.getLogger("Client")


class GammaContext(CommonContext):
    game = GAME
    items_handling = 0b111

    def __init__(
        self,
        server_address: str | None = None,
        password: str | None = None,
        *,
        bridge: FileBridge | None = None,
    ) -> None:
        super().__init__(server_address, password)
        self.bridge = bridge or FileBridge(DEFAULT_GAME_ROOT, allowed_root=DEFAULT_GAME_ROOT)
        self.session: SessionCoordinator | None = None
        self.last_error: str | None = None
        self.scout_requested: set[int] = set()

    async def server_auth(self, password_requested: bool = False) -> None:
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        await self.get_username()
        await self.send_connect()

    def on_package(self, command: str, arguments: dict[str, Any]) -> None:
        if command == "Connected":
            slot_data = arguments.get("slot_data", {})
            if slot_data.get("schema_version") != 1 or slot_data.get("pilot") is not True:
                self.session = None
                raise ProtocolError("This client requires the GAMMA integration pilot world")
            key = make_session_key(self.server_seed_name, self.team, self.slot)
            if self.session and self.session.session_key != key:
                raise ProtocolError("Restart the companion client before changing seed or slot")
            self.session = self.session or SessionCoordinator(key)
            self.scout_requested.clear()
        if command in ("Connected", "RoomUpdate") and self.session:
            self.session.accept_confirmed(frozenset(self.checked_locations))
            self.bridge.write_confirmed(self.session.session_key, frozenset(self.checked_locations))
        if command in ("Connected", "ReceivedItems") and self.session:
            if command == "ReceivedItems":
                self.session.accept_history(tuple(item.item for item in self.items_received))
                self.received_notices()
            self.bridge.write_history(self.session.session_key, self.session.item_ids)
        if command == "PrintJSON" and self.session:
            item = arguments.get("item")
            recipient = arguments.get("receiving")
            if (
                arguments.get("type") == "ItemSend"
                and isinstance(item, NetworkItem)
                and item.player == self.slot
                and type(recipient) is int
                and recipient != self.slot
                and recipient in self.slot_info
            ):
                self.sent_notice(item, recipient)
        if command in ("LocationInfo", "DataPackage", "RoomUpdate") and self.session:
            self.received_notices()
            for location, item in self.locations_info.items():
                if location in self.checked_locations and item.player != self.slot:
                    self.sent_notice(item, item.player)

    def received_notices(self) -> None:
        if self.session is None:
            return
        for index, item in enumerate(self.items_received):
            name = self.item_names.lookup_in_game(item.item)
            if name.startswith("Unknown item"):
                continue
            self.session.add_notice(
                Notice(
                    f"r:{index}",
                    index + 1,
                    reward_message(
                        self.player_names.get(item.player, f"Player {item.player}"),
                        name,
                        unlock=is_unlock(item.item, GAME),
                        outgoing=False,
                    ),
                )
            )

    def sent_notice(self, item: NetworkItem, recipient: int) -> None:
        if self.session is None or recipient not in self.slot_info:
            return
        name = self.item_names.lookup_in_slot(item.item, recipient)
        if name.startswith("Unknown item"):
            return
        self.session.add_notice(
            Notice(
                f"s:{item.location}:{recipient}:{item.item}",
                0,
                reward_message(
                    self.player_names.get(recipient, f"Player {recipient}"),
                    name,
                    unlock=is_unlock(item.item, self.slot_info[recipient].game),
                    outgoing=True,
                ),
            )
        )

    async def poll_game_once(self) -> None:
        if not self.session or not self.server or not self.slot:
            return
        missing = sorted(self.checked_locations - self.scout_requested)[:64]
        if missing:
            await self.send_msgs(
                [{"cmd": "LocationScouts", "locations": missing, "create_as_hint": 0}]
            )
            self.scout_requested.update(missing)
        self.bridge.write_notices(self.session.session_key, tuple(self.session.notices.values()))
        snapshot = self.bridge.read_game(self.session.session_key)
        if snapshot is None:
            return
        checked = self.session.observe_game(snapshot)
        packets = [{"cmd": "LocationChecks", "locations": list(checked)}]
        if snapshot.goal_complete:
            packets.append({"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL})
        await self.send_msgs(packets)


async def watch_game(context: GammaContext) -> None:
    while not context.exit_event.is_set():
        try:
            await context.poll_game_once()
            context.last_error = None
        except (OSError, ProtocolError) as error:
            message = str(error)
            if message != context.last_error:
                logger.error("GAMMA bridge: %s", message)
                context.last_error = message
        with suppress(TimeoutError):
            await asyncio.wait_for(context.exit_event.wait(), timeout=0.5)


async def run(arguments: Namespace) -> None:
    context = GammaContext(arguments.connect, arguments.password)
    context.auth = arguments.name
    context.server_task = asyncio.create_task(server_loop(context), name="AP server")
    watcher = asyncio.create_task(watch_game(context), name="GAMMA bridge")
    context.run_cli()
    try:
        await context.exit_event.wait()
    finally:
        watcher.cancel()
        await asyncio.gather(watcher, return_exceptions=True)
        await context.shutdown()


def launch(*arguments: str) -> None:
    logging.basicConfig(level=logging.INFO)
    parser = get_base_parser(description="GAMMA Archipelago integration pilot")
    parser.add_argument("--name", required=True, help="Archipelago slot name")
    asyncio.run(run(parser.parse_args(arguments)))
