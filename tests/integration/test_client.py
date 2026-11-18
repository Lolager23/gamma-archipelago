import asyncio
from functools import wraps
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from CommonClient import CommonContext
from NetUtils import ClientStatus, NetworkItem
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


def connected_context():
    bridge = SimpleNamespace(write_history=lambda *_: None, read_game=lambda _: None)
    context = adapter.GammaContext(bridge=bridge)
    context.server_seed_name = "pilot-seed"
    context.team = 0
    context.slot = 1
    context.server = object()
    context.on_package("Connected", {"slot_data": {"schema_version": 1, "pilot": True}})
    return context


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
        def __init__(self, address, password):
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
