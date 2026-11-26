"""Use upstream CommonClient for authentication, websockets, reconnect and item sync."""

import asyncio
import logging
import secrets
from argparse import Namespace
from contextlib import suppress
from pathlib import Path
from typing import Any

from CommonClient import CommonContext, get_base_parser, server_loop
from NetUtils import ClientStatus, NetworkItem

from gamma_archipelago.bridge import FileBridge
from gamma_archipelago.catalog import (
    GAME,
    ITEM_SECTIONS,
    LOCATION_IDS,
    enabled_item_ids,
)
from gamma_archipelago.configuration import (
    ConfigurationError,
    SeedConfiguration,
    build_configuration,
    legacy_defaults,
)
from gamma_archipelago.content_progression import configured_item_ids
from gamma_archipelago.discovery import configured_location_ids
from gamma_archipelago.notice_text import clean_label
from gamma_archipelago.paths import DEFAULT_GAME_ROOT
from gamma_archipelago.protocol import ProtocolError, validate_id_manifest, validate_session_key
from gamma_archipelago.session import SessionCoordinator, make_session_key

from .interaction import GameInteraction
from .notices import received as received_notices
from .notices import sent as sent_notice
from .room import RoomFeed
from .scouting import poll as poll_scouting

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
        self.configuration: SeedConfiguration | None = None
        self.require_configuration = False
        self.expanded = False
        self.scouting_sent: set[int] = set()
        self.scouting_hints: set[int] = set()
        self.scouting_epoch = secrets.token_hex(8)
        self.scouting_sequence = 0
        self.presence_sequence = 0
        self.last_presence_error: str | None = None
        self.room = RoomFeed()
        self.interaction = GameInteraction()
        self.hint_points = 0
        self.last_communication_error: str | None = None

    async def server_auth(self, password_requested: bool = False) -> None:
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        await self.get_username()
        await self.send_connect()

    def on_package(self, command: str, arguments: dict[str, Any]) -> None:
        if command == "Connected":
            slot_data = arguments.get("slot_data", {})
            version = slot_data.get("schema_version")
            if type(version) is not int or not (
                (version == 1 and slot_data.get("pilot") is True)
                or (
                    version in (2, 3, 4)
                    and slot_data.get("pilot") is False
                    and "configuration" in slot_data
                )
            ):
                self.session = None
                raise ProtocolError("This client requires the GAMMA integration pilot world")
            seed_identity = self.server_seed_name
            if version == 4:
                fingerprint = slot_data.get("generation_identity")
                validate_session_key(fingerprint)
                seed_identity += "|generation|" + fingerprint
            elif "generation_identity" in slot_data:
                raise ProtocolError("Generation identity requires schema 4")
            key = make_session_key(seed_identity, self.team, self.slot)
            if self.session and self.session.session_key != key:
                raise ProtocolError("Restart the companion client before changing seed or slot")
            configuration_key = None
            self.configuration = None
            if "configuration" in slot_data:
                values = slot_data["configuration"]
                if not isinstance(values, dict):
                    raise ProtocolError("Generation configuration must be an object")
                try:
                    self.configuration = build_configuration(values)
                    configuration_key = self.configuration.digest
                except ConfigurationError as error:
                    raise ProtocolError(f"Invalid generation configuration: {error}") from error
                if slot_data.get("configuration_key") != configuration_key:
                    raise ProtocolError("Generation configuration digest does not match")
                if version == 1 and self.configuration.to_values() != legacy_defaults():
                    raise ProtocolError("Expanded configuration requires schema 2")
                if version == 2 and (
                    self.configuration.checks != {"checks_maps"}
                    or self.configuration.rewards
                    or self.configuration.goal != "pilot_tour"
                    or any(mode == 2 for _, mode in self.configuration.gear)
                ):
                    raise ProtocolError("Expanded checks and rewards require schema 3")
            self.expanded = version in (3, 4)
            allowed = configured_location_ids(self.configuration) if self.expanded else LOCATION_IDS
            if self.expanded:
                validate_id_manifest(slot_data.get("location_ids"), allowed, "check")
            item_ids = (
                configured_item_ids(self.configuration)
                if self.expanded
                else frozenset(ITEM_SECTIONS)
            )
            if "item_ids" in slot_data:
                legacy = (
                    enabled_item_ids(self.configuration.rewards)
                    if self.expanded
                    and not self.configuration.option("equipment_class_progression")
                    else item_ids
                )
                manifest = slot_data["item_ids"]
                expected = legacy if manifest == sorted(legacy) else item_ids
                validate_id_manifest(manifest, expected, "item")
            self.session = self.session or SessionCoordinator(key)
            self.session.bind_configuration(configuration_key)
            self.session.bind_locations(allowed)
            self.session.bind_items(item_ids)
            # A seed name/team/slot may be reused with different settings. Clear
            # client-owned notices before exposing its new configuration/history.
            # Game-owned acknowledgements remain the save's responsibility.
            self.bridge.reset_notices(key)
            self.bridge.allowed_locations = allowed
            self.bridge.pilot_goal = (
                self.configuration is None or self.configuration.goal == "pilot_tour"
            )
            self.require_configuration = version in (2, 3, 4)
            self.bridge.configuration_key = (
                configuration_key if self.require_configuration else None
            )
            if self.require_configuration:
                self.bridge.write_configuration(
                    self.session.session_key, self.configuration, self.expanded
                )
            self.scout_requested.clear()
            self.scouting_sent.clear()
            self.scouting_hints.clear()
            self.scouting_epoch = secrets.token_hex(8)
            self.scouting_sequence = 0
            self.presence_sequence = 0
        if command in ("Connected", "RoomUpdate") and self.session:
            self.session.accept_confirmed(frozenset(self.checked_locations))
            self.bridge.write_confirmed(self.session.session_key, frozenset(self.checked_locations))
        if command in ("Connected", "ReceivedItems") and self.session:
            if command == "ReceivedItems":
                self.session.accept_history(tuple(item.item for item in self.items_received))
                self.received_notices()
            required_config = self.session.configuration_key if self.require_configuration else None
            self.bridge.write_history(
                self.session.session_key, self.session.item_ids, required_config
            )
        if self.session:
            self.room.receive(self, command, arguments)
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
        received_notices(self)

    def sent_notice(self, item: NetworkItem, recipient: int) -> None:
        sent_notice(self, item, recipient)

    def publish_presence(self) -> None:
        self.presence_sequence += 1
        try:
            self.bridge.write_presence(
                self.session.session_key,
                self.bridge.configuration_key,
                self.scouting_epoch,
                self.presence_sequence,
                clean_label(self.player_names.get(self.slot, self.auth or f"Player {self.slot}")),
            )
        except (OSError, ProtocolError) as error:
            message = str(error)
            if message != self.last_presence_error:
                logger.warning("GAMMA PDA presence: %s", message)
            self.last_presence_error = message
        else:
            self.last_presence_error = None

    async def poll_game_once(self) -> None:
        if not self.session:
            return
        try:
            await self.interaction.poll(self)
            self.last_communication_error = None
        except (OSError, ProtocolError) as error:
            message = str(error)
            if message != self.last_communication_error:
                logger.warning("GAMMA communication: %s", message)
            self.last_communication_error = message
        if not self.server or not self.slot:
            return
        self.publish_presence()
        self.room.publish(self)
        missing = sorted(self.checked_locations - self.scout_requested)[:64]
        if missing:
            await self.send_msgs(
                [{"cmd": "LocationScouts", "locations": missing, "create_as_hint": 0}]
            )
            self.scout_requested.update(missing)
        self.bridge.write_notices(self.session.session_key, tuple(self.session.notices.values()))
        snapshot = self.bridge.read_game(self.session.session_key)
        if snapshot is None:
            await poll_scouting(self)
            return
        checked = self.session.observe_game(snapshot)
        packets = [{"cmd": "LocationChecks", "locations": list(checked)}]
        if snapshot.goal_complete:
            packets.append({"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL})
        await self.send_msgs(packets)
        await poll_scouting(self)


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
    bridge = configured_bridge(
        getattr(arguments, "game_root", None), getattr(arguments, "appdata_root", None)
    )
    context = GammaContext(arguments.connect, arguments.password, bridge=bridge)
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


def configured_bridge(game_root: Path | None, appdata_root: Path | None) -> FileBridge | None:
    if game_root is None:
        if appdata_root is not None:
            raise ValueError("--appdata-root requires --game-root")
        return None
    from gamma_archipelago.installation import inspect_installation, require_enrolled

    installation = inspect_installation(game_root, appdata_root=appdata_root)
    require_enrolled(installation)
    return FileBridge(
        installation.game_root,
        allowed_root=installation.game_root,
        appdata_root=installation.appdata_root,
    )


def launch(*arguments: str) -> None:
    logging.basicConfig(level=logging.INFO)
    parser = get_base_parser(description="GAMMA Archipelago companion")
    parser.add_argument("--name", required=True, help="Archipelago slot name")
    parser.add_argument("--game-root", type=Path, help="Explicitly enrolled Anomaly installation")
    parser.add_argument("--appdata-root", type=Path, help="Explicit active appdata override")
    asyncio.run(run(parser.parse_args(arguments)))
