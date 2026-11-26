import asyncio
from functools import wraps
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from CommonClient import CommonContext
from NetUtils import ClientStatus, NetworkItem, NetworkSlot
from worlds.gamma import client as adapter

from gamma_archipelago.catalog import ITEM_SECTIONS, LOCATION_IDS
from gamma_archipelago.protocol import GameSnapshot, ProtocolError
from gamma_archipelago.session import make_session_key

ITEMS = tuple(ITEM_SECTIONS)


def run_async(test):
    @wraps(test)
    def wrapped(*args, **kwargs):
        return asyncio.run(test(*args, **kwargs))

    return wrapped


def connected_context(slot_data=None):
    bridge = SimpleNamespace(
        write_history=lambda *_: None,
        write_notices=lambda *_: None,
        reset_notices=lambda *_: None,
        write_confirmed=lambda *_: None,
        write_configuration=lambda *_: None,
        read_game=lambda _: None,
        read_scout_requests=lambda *_: frozenset(),
        write_scouted=lambda *_: None,
        write_presence=lambda *_: None,
        write_room_feed=lambda *_: None,
    )
    context = adapter.GammaContext(bridge=bridge)
    context.server_seed_name = "pilot-seed"
    context.team = 0
    context.slot = 1
    context.server = object()
    context.on_package(
        "Connected", {"slot_data": slot_data or {"schema_version": 1, "pilot": True}}
    )
    return context


@run_async
async def test_expanded_seed_manifest_is_checked_before_bridge_publication():
    from gamma_archipelago.catalog import MAP_LOCATION_IDS as ALL_LOCATION_IDS
    from gamma_archipelago.configuration import build_configuration, defaults

    configuration = build_configuration(defaults())
    slot = {
        "schema_version": 3,
        "pilot": False,
        "configuration": configuration.to_values(),
        "configuration_key": configuration.digest,
        "location_ids": sorted(ALL_LOCATION_IDS),
    }
    context = connected_context(slot)
    assert context.bridge.allowed_locations == ALL_LOCATION_IDS
    assert context.session.allowed_locations == ALL_LOCATION_IDS
    for manifest in ([], sorted(LOCATION_IDS), [42], None):
        with pytest.raises(ProtocolError, match="manifest"):
            connected_context({**slot, "location_ids": manifest})
    with pytest.raises(ProtocolError, match="pilot world"):
        connected_context({**slot, "schema_version": 3.0})


@run_async
async def test_settlement_only_client_rejects_map_checks_without_losing_goal_observation():
    from gamma_archipelago.catalog import enabled_location_ids
    from gamma_archipelago.configuration import build_configuration, defaults

    configuration = build_configuration({**defaults(), "checks_maps": 0, "checks_settlements": 1})
    allowed = enabled_location_ids(configuration.checks)
    context = connected_context(
        {
            "schema_version": 3,
            "pilot": False,
            "configuration": configuration.to_values(),
            "configuration_key": configuration.digest,
            "location_ids": sorted(allowed),
        }
    )
    assert context.session.allowed_locations == allowed
    context.send_msgs = AsyncMock()
    context.bridge.read_game = lambda key: GameSnapshot(key, 0, frozenset(), True)
    await context.poll_game_once()
    assert context.send_msgs.call_args.args[0][-1]["status"] == ClientStatus.CLIENT_GOAL
    context.bridge.read_game = lambda key: GameSnapshot(key, 0, LOCATION_IDS, False)
    with pytest.raises(ProtocolError, match="disabled"):
        await context.poll_game_once()


@run_async
async def test_custom_side_task_manifest_is_used_by_the_client():
    from gamma_archipelago.catalog import enabled_location_ids
    from gamma_archipelago.configuration import build_configuration, defaults

    configuration = build_configuration(
        {
            **defaults(),
            "checks_maps": 0,
            "checks_side_task_milestones": 1,
            "side_task_milestones": [1, 7, 10000],
        }
    )
    allowed = enabled_location_ids(
        configuration.checks, configuration.kill_milestones, configuration.side_task_milestones
    )
    context = connected_context(
        {
            "schema_version": 3,
            "pilot": False,
            "configuration": configuration.to_values(),
            "configuration_key": configuration.digest,
            "location_ids": sorted(allowed),
        }
    )
    assert context.session.allowed_locations == allowed


@run_async
async def test_configured_stash_item_manifests_and_history_are_validated():
    from gamma_archipelago.catalog import ITEM_IDS, MAP_LOCATION_IDS
    from gamma_archipelago.configuration import build_configuration, defaults

    configuration = build_configuration({**defaults(), "rewards_loot_stashes": 1})
    slot = {
        "schema_version": 3,
        "pilot": False,
        "configuration": configuration.to_values(),
        "configuration_key": configuration.digest,
        "location_ids": sorted(MAP_LOCATION_IDS),
        "item_ids": sorted(
            ITEM_IDS
            - {
                *range(28051801, 28052000),
                *range(28051201, 28051205),
                *range(28051301, 28051309),
                *range(28051401, 28051405),
                *range(28051501, 28051504),
                *range(28051601, 28051610),
                *range(28051701, 28051733),
                *range(28053001, 28053005),
                *range(28053101, 28053161),
            }
        ),
    }
    context = connected_context(slot)
    custom = next(
        iter(
            ITEM_IDS
            - set(ITEM_SECTIONS)
            - {
                *range(28051801, 28052000),
                *range(28051201, 28051205),
                *range(28051301, 28051309),
                *range(28051401, 28051405),
                *range(28051501, 28051504),
                *range(28051601, 28051610),
                *range(28051701, 28051733),
                *range(28053001, 28053005),
                *range(28053101, 28053161),
            }
        )
    )
    context.items_received = [NetworkItem(custom, 1, 2)]
    context.on_package("ReceivedItems", {})
    assert context.session.item_ids == (custom,)
    for invalid in ([], [42], None):
        with pytest.raises(ProtocolError, match="item manifest"):
            connected_context({**slot, "item_ids": invalid})
    with pytest.raises(ProtocolError, match="schema 3"):
        connected_context({**slot, "schema_version": 2})


@run_async
async def test_seed_configuration_is_validated_and_bound_before_bridge_publication():
    from gamma_archipelago.configuration import build_configuration, defaults, legacy_defaults

    configuration = build_configuration(legacy_defaults())
    slot = {
        "schema_version": 1,
        "pilot": True,
        "configuration": configuration.to_values(),
        "configuration_key": configuration.digest,
    }
    context = connected_context(slot)
    assert context.session.configuration_key == configuration.digest
    context.on_package("Connected", {"slot_data": slot})
    generic = build_configuration(defaults())
    with pytest.raises(ProtocolError, match="schema 2"):
        connected_context(
            {**slot, "configuration": generic.to_values(), "configuration_key": generic.digest}
        )
    for values in [[], {"unknown": 1}]:
        with pytest.raises(ProtocolError, match="[Cc]onfiguration"):
            context.on_package("Connected", {"slot_data": {**slot, "configuration": values}})
    with pytest.raises(ProtocolError, match="digest"):
        context.on_package("Connected", {"slot_data": {**slot, "configuration_key": "b" * 64}})
    with pytest.raises(ProtocolError, match="changed"):
        context.on_package("Connected", {"slot_data": {"schema_version": 1, "pilot": True}})


@run_async
async def test_v2_requires_configuration_and_legacy_cannot_apply_restrictions():
    from gamma_archipelago.configuration import build_configuration, defaults

    configuration = build_configuration({**defaults(), "starting_pda": 1})
    slot = {
        "schema_version": 2,
        "pilot": False,
        "configuration": configuration.to_values(),
        "configuration_key": configuration.digest,
    }
    context = connected_context(slot)
    assert context.require_configuration is True
    assert context.session.configuration_key == configuration.digest
    with pytest.raises(ProtocolError, match="schema 2"):
        connected_context({**slot, "schema_version": 1, "pilot": True})


@run_async
async def test_named_incoming_and_foreign_outgoing_notices_deduplicate_self_transfers():
    context = connected_context()
    context.player_names.update({1: "Owen", 2: "Friend"})
    context.slot_info[2] = NetworkSlot("Friend", "Foreign Game", 1)
    context.item_names.update_game("Foreign Game", {"Moon Key": 42})
    context.location_names.update_game("Foreign Game", {"Friend's Check": 3})
    context.location_names.update_game(context.game, {"Synthetic Check": 99})
    context.items_received = [NetworkItem(ITEMS[0], 3, 2)]
    context.on_package("ReceivedItems", {})
    assert context.session.notices["r:0"].text == (
        'Friend gave you "Basic Toolkit" by completing "Friend\'s Check".'
    )
    transfer = {"type": "ItemSend", "receiving": 2, "item": NetworkItem(42, 99, 1)}
    context.on_package("PrintJSON", transfer)
    context.on_package("PrintJSON", transfer)
    assert context.session.notices["s:99:2:42"].text == (
        'You sent "Moon Key" to Friend by completing "Synthetic Check".'
    )
    context.on_package("PrintJSON", {**transfer, "receiving": 1})
    context.on_package("PrintJSON", {**transfer, "type": "Hint"})
    context.on_package("PrintJSON", {**transfer, "item": None})
    context.on_package("PrintJSON", {**transfer, "item": NetworkItem(42, 99, 2)})
    context.on_package("PrintJSON", {**transfer, "receiving": "2"})
    context.on_package("PrintJSON", {**transfer, "receiving": 9})
    assert len(context.session.notices) == 2


@run_async
async def test_reconstructs_confirmed_outgoing_notices_after_a_new_client_connects():
    context = connected_context()
    context.send_msgs = AsyncMock()
    context.checked_locations = {ITEMS[0] + 1000}
    location = next(iter(context.checked_locations))
    context.player_names[2] = "Friend"
    context.slot_info[2] = NetworkSlot("Friend", "Foreign Game", 1)
    context.on_package("RoomUpdate", {})
    await context.poll_game_once()
    assert context.send_msgs.call_args.args[0] == [
        {"cmd": "LocationScouts", "locations": [location], "create_as_hint": 0}
    ]
    context.locations_info[location] = NetworkItem(42, location, 2)
    context.on_package("LocationInfo", {})
    assert not context.session.notices  # Data package is not ready yet.
    context.item_names.update_game("Foreign Game", {"Moon Key": 42})
    context.on_package("DataPackage", {})
    assert context.session.notices[f"s:{location}:2:42"].text == (
        'You sent "Moon Key" to Friend by entering Cordon.'
    )
    context.locations_info[99] = NetworkItem(42, 99, 2)
    context.on_package("LocationInfo", {})
    assert len(context.session.notices) == 1  # Unchecked scouts never announce a transfer.
    context.sent_notice(NetworkItem(42, location, 9), 9)
    context.items_received = [NetworkItem(42, location, 2)]
    context.received_notices()  # Unknown incoming name waits for its package too.
    context.session = None
    context.received_notices()
    context.sent_notice(NetworkItem(42, location, 2), 2)


@run_async
async def test_client_uses_common_context_and_validates_world_identity():
    context = connected_context()
    assert isinstance(context, CommonContext)
    assert context.session.session_key == make_session_key("pilot-seed", 0, 1)
    context.on_package("Ignored", {})
    context.on_package("Connected", {"slot_data": {"schema_version": 1, "pilot": True}})
    context.server_seed_name = "wrong-seed"
    with pytest.raises(ProtocolError, match="Restart"):
        context.on_package("Connected", {"slot_data": {"schema_version": 1, "pilot": True}})
    with pytest.raises(ProtocolError, match="pilot"):
        context.on_package("Connected", {"slot_data": {}})
    assert context.session is None


@run_async
async def test_reconnect_does_not_truncate_an_existing_receipt_history():
    context = connected_context()
    context.items_received = [NetworkItem(ITEMS[0], 1, 1)]
    context.on_package("ReceivedItems", {})
    context.items_received = []
    context.on_package("Connected", {"slot_data": {"schema_version": 1, "pilot": True}})
    assert context.session.item_ids == ITEMS[:1]


def test_poll_sends_monotonic_checks_and_goal_only_from_a_complete_game_snapshot():
    async def exercise():
        context = connected_context()
        context.send_msgs = AsyncMock()
        await context.poll_game_once()
        context.send_msgs.assert_not_called()
        context.bridge.read_game = lambda key: GameSnapshot(key, 0, LOCATION_IDS, True)
        await context.poll_game_once()
        assert context.send_msgs.call_args.args[0] == [
            {"cmd": "LocationChecks", "locations": sorted(LOCATION_IDS)},
            {"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL},
        ]
        context.bridge.read_game = lambda key: GameSnapshot(key, 0, frozenset(), False)
        await context.poll_game_once()
        assert len(context.send_msgs.call_args.args[0]) == 1
        context.server = None
        await context.poll_game_once()
        context.server = object()
        context.slot = None
        await context.poll_game_once()
        context.session = None
        await context.poll_game_once()

    asyncio.run(exercise())


def test_authentication_uses_the_upstream_methods(monkeypatch):
    async def exercise():
        context = connected_context()
        context.password = None
        context.get_username = AsyncMock()
        context.send_connect = AsyncMock()
        upstream = AsyncMock()
        monkeypatch.setattr(CommonContext, "server_auth", upstream)
        await context.server_auth(True)
        upstream.assert_awaited_once()
        await context.server_auth(False)
        assert context.get_username.await_count == 2
        assert context.send_connect.await_count == 2

    asyncio.run(exercise())


@run_async
async def test_default_client_constructs_only_the_development_bridge(monkeypatch):
    calls = []
    monkeypatch.setattr(adapter, "FileBridge", lambda *args, **kwargs: calls.append((args, kwargs)))
    adapter.GammaContext()
    assert str(calls[0][0][0]).replace("\\", "/") == "D:/AnomalyAP"
    assert calls[0][1]["allowed_root"] == calls[0][0][0]


@run_async
async def test_watcher_logs_repeated_failures_once_and_recovers(monkeypatch, caplog):
    context = connected_context()
    outcomes = [OSError("read failed"), OSError("read failed"), ProtocolError("bad file"), None]

    async def poll():
        outcome = outcomes.pop(0)
        if not outcomes:
            context.exit_event.set()
        if outcome:
            raise outcome

    context.poll_game_once = poll
    waits = []

    async def wait(awaitable, timeout):
        awaitable.close()
        waits.append(timeout)
        if len(waits) == 1:
            raise TimeoutError

    monkeypatch.setattr(adapter.asyncio, "wait_for", wait)
    await adapter.watch_game(context)
    assert len(caplog.records) == 2
    assert context.last_error is None
    assert waits == [0.5] * 4


def test_client_lifecycle_cleans_up_background_tasks(monkeypatch):
    contexts = []

    class Context:
        def __init__(self, address, password, *, bridge=None):
            self.exit_event = asyncio.Event()
            self.exit_event.set()
            self.shutdown = AsyncMock()
            self.run_cli = lambda: None
            contexts.append(self)

    async def idle(_):
        await asyncio.Event().wait()

    monkeypatch.setattr(adapter, "GammaContext", Context)
    monkeypatch.setattr(adapter, "server_loop", idle)
    monkeypatch.setattr(adapter, "watch_game", idle)
    adapter.launch("--name", "GammaPilot", "--connect", "localhost:38281")
    assert contexts[0].auth == "GammaPilot"
    contexts[0].shutdown.assert_awaited_once()


@run_async
async def test_unconnected_item_packet_does_not_write_a_snapshot():
    context = connected_context()
    context.session = None
    context.on_package("ReceivedItems", {})


@run_async
async def test_selected_alternate_goal_configures_the_bridge_goal_protocol():
    from gamma_archipelago.catalog import MAP_LOCATION_IDS
    from gamma_archipelago.configuration import build_configuration, defaults

    configuration = build_configuration({**defaults(), "goal": 1})
    context = connected_context(
        {
            "schema_version": 3,
            "pilot": False,
            "configuration": configuration.to_values(),
            "configuration_key": configuration.digest,
            "location_ids": sorted(MAP_LOCATION_IDS),
        }
    )
    assert context.bridge.pilot_goal is False


@run_async
async def test_legacy_equipment_manifest_keeps_only_selected_permissions_enabled():
    from gamma_archipelago.catalog import MAP_LOCATION_IDS, enabled_item_ids
    from gamma_archipelago.configuration import build_configuration, defaults

    configuration = build_configuration(
        {
            **defaults(),
            "equipment_class_progression": 0,
            "starting_pda": 2,
            "rewards_starting_gear_unlocks": 1,
        }
    )
    selected = enabled_item_ids(configuration.rewards, configuration.gear)
    slot = {
        "schema_version": 3,
        "pilot": False,
        "configuration": configuration.to_values(),
        "configuration_key": configuration.digest,
        "location_ids": sorted(MAP_LOCATION_IDS),
    }
    for manifest in (sorted(selected), sorted(enabled_item_ids(configuration.rewards))):
        context = connected_context({**slot, "item_ids": manifest})
        assert context.session.allowed_items == selected
        with pytest.raises(ProtocolError, match="unsupported item"):
            context.session.accept_history((28051601,))
    with pytest.raises(ProtocolError, match="manifest"):
        connected_context(
            {**slot, "location_ids": [float(value) for value in sorted(MAP_LOCATION_IDS)]}
        )


@run_async
async def test_reused_seed_identity_rejects_old_configuration_game_snapshots(tmp_path):
    from gamma_archipelago.bridge import FileBridge
    from gamma_archipelago.catalog import MAP_LOCATION_IDS
    from gamma_archipelago.configuration import build_configuration, defaults

    old = build_configuration(defaults())
    current = build_configuration({**defaults(), "starting_money": 50})
    bridge = FileBridge(tmp_path, allowed_root=tmp_path)
    context = adapter.GammaContext(bridge=bridge)
    context.server_seed_name, context.team, context.slot = "reused-seed", 0, 1
    context.server, context.send_msgs = object(), AsyncMock()
    context.on_package(
        "Connected",
        {
            "slot_data": {
                "schema_version": 3,
                "pilot": False,
                "configuration": current.to_values(),
                "configuration_key": current.digest,
                "location_ids": sorted(MAP_LOCATION_IDS),
            }
        },
    )
    key = context.session.session_key
    source = bridge.directory / "outgoing.txt"
    body = "received|0\ncheck|28052001\ngoal|0\nend|1\n"
    source.write_text(f"GAMMA_AP_OUT|1\nsession|{key}\n" + body)
    with pytest.raises(ProtocolError):
        await context.poll_game_once()
    context.send_msgs.assert_not_called()
    source.write_text(f"GAMMA_AP_OUT|3\nsession|{key}\nconfiguration|{old.digest}\n" + body)
    with pytest.raises(ProtocolError):
        await context.poll_game_once()
    context.send_msgs.assert_not_called()
    source.write_text(f"GAMMA_AP_OUT|3\nsession|{key}\nconfiguration|{current.digest}\n" + body)
    await context.poll_game_once()
    assert context.send_msgs.call_args.args[0][0] == {
        "cmd": "LocationChecks",
        "locations": [28052001],
    }


@run_async
async def test_connection_clears_old_notices_before_publishing_new_settings(tmp_path):
    from gamma_archipelago.bridge import FileBridge
    from gamma_archipelago.catalog import MAP_LOCATION_IDS
    from gamma_archipelago.configuration import build_configuration, defaults
    from gamma_archipelago.notifications import Notice, encode_notices

    bridge = FileBridge(tmp_path, allowed_root=tmp_path)
    key = make_session_key("reused-seed", 0, 1)
    bridge.write_notices(key, (Notice("s:28052001:2:42", 0, "Old transfer"),))
    acknowledgements = bridge.directory / "notices_ack.txt"
    acknowledgements.write_text("old incomplete acknowledgements")
    original = bridge.write_configuration

    def publish(*args):
        assert (bridge.directory / "notices.txt").read_text() == encode_notices(key, ())
        original(*args)

    bridge.write_configuration = publish
    context = adapter.GammaContext(bridge=bridge)
    context.server_seed_name, context.team, context.slot = "reused-seed", 0, 1
    configuration = build_configuration({**defaults(), "starting_money": 50})
    context.on_package(
        "Connected",
        {
            "slot_data": {
                "schema_version": 3,
                "pilot": False,
                "configuration": configuration.to_values(),
                "configuration_key": configuration.digest,
                "location_ids": sorted(MAP_LOCATION_IDS),
            }
        },
    )
    assert acknowledgements.read_text() == "old incomplete acknowledgements"
