from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from test_client import connected_context, run_async
from worlds.gamma.interaction import address_label, connected

from gamma_archipelago.game_commands import GameRequest
from gamma_archipelago.protocol import ProtocolError


@run_async
async def test_world_entry_is_room_chat_once_per_process_request_not_per_level_or_reconnect():
    context = connected_context()
    context.player_names[1] = "Owen"
    context.send_msgs = AsyncMock()
    context.bridge.read_commands = lambda *_: ("a" * 16, (GameRequest(1, "loaded", ""),))
    context.bridge.write_connection_status = Mock()
    for _ in range(3):
        await context.poll_game_once()
    chats = [
        call.args[0][0]
        for call in context.send_msgs.call_args_list
        if call.args[0][0]["cmd"] == "Say"
    ]
    assert chats == [{"cmd": "Say", "text": "Owen loaded GAMMA and entered the Zone."}]
    context.on_package("Connected", {"slot_data": {"schema_version": 1, "pilot": True}})
    await context.poll_game_once()
    assert context.interaction.acknowledged["a" * 16] == 1
    assert context.bridge.write_connection_status.call_args.kwargs["acknowledged"] == 1


@run_async
async def test_chat_offline_acknowledgements_gaps_and_companion_restart_resume():
    context = connected_context()
    context.send_msgs = AsyncMock()
    context.server = None
    context.bridge.write_connection_status = Mock()
    context.bridge.read_commands = Mock(return_value=("a" * 16, (GameRequest(8, "say", "!hint"),)))
    await context.poll_game_once()
    assert context.bridge.write_connection_status.call_args.kwargs["connected"] is False
    assert not context.bridge.read_commands.called
    context.server = SimpleNamespace(socket=SimpleNamespace(open=True, closed=False))
    await context.poll_game_once()
    assert context.send_msgs.call_args.args[0] == [{"cmd": "Say", "text": "!hint"}]
    context.bridge.read_commands.return_value = ("a" * 16, (GameRequest(10, "say", "gap"),))
    await context.poll_game_once()
    assert context.interaction.acknowledged["a" * 16] == 8
    context.bridge.read_commands.return_value = ("a" * 16, ())
    await context.poll_game_once()
    for i in range(9):
        context.bridge.read_commands.return_value = (f"{i:016x}", (GameRequest(1, "say", "Hello"),))
        await context.poll_game_once()
    assert len(context.interaction.acknowledged) == 8


@run_async
async def test_communication_failure_does_not_block_checks_and_logging_is_bounded(caplog):
    context = connected_context()
    context.bridge.read_commands = Mock(side_effect=ProtocolError("Partial request"))
    context.bridge.read_game = Mock(return_value=None)
    await context.poll_game_once()
    await context.poll_game_once()
    assert context.bridge.read_game.call_count == 2
    assert caplog.text.count("Partial request") == 1
    context.bridge.read_commands = lambda *_: None
    await context.poll_game_once()
    assert context.last_communication_error is None


def test_address_status_never_exposes_credentials_and_checks_real_socket_state():
    assert (
        address_label("ws://user:password@example.com:4444/private?secret=yes")
        == "example.com:4444"
    )
    assert address_label("localhost:4444") == "localhost:4444"
    assert address_label("ws://[::1]:4444") == "::1 (port 4444)"
    assert address_label("example.com") == "example.com"
    assert address_label(None) == "Server address unavailable"
    assert address_label("ws://host:bad") == "Configured server"
    assert address_label("ws://") == "Configured server"
    context = SimpleNamespace(
        server=SimpleNamespace(socket=SimpleNamespace(open=True, closed=False)), slot=1
    )
    assert connected(context)
    context.server.socket.closed = True
    assert not connected(context)
    context.server.socket = None
    assert not connected(context)


@run_async
async def test_socket_closing_during_send_keeps_request_pending_until_reconnect():
    from websockets.exceptions import ConnectionClosedError

    context = connected_context()
    context.bridge.read_commands = lambda *_: ("a" * 16, (GameRequest(1, "say", "Hello"),))
    context.send_msgs = AsyncMock(side_effect=ConnectionClosedError(None, None))
    await context.poll_game_once()
    assert not context.interaction.acknowledged
    context.send_msgs = AsyncMock()
    await context.poll_game_once()
    assert context.interaction.acknowledged["a" * 16] == 1


@run_async
async def test_disconnect_between_queued_messages_never_acknowledges_the_unsent_tail():
    context = connected_context()
    context.bridge.read_commands = lambda *_: (
        "a" * 16,
        (GameRequest(1, "say", "First"), GameRequest(2, "say", "Second")),
    )

    async def send(_):
        context.server.socket.closed = True

    context.send_msgs = AsyncMock(side_effect=send)
    await context.poll_game_once()
    assert context.interaction.acknowledged["a" * 16] == 1
    context.server.socket.closed = False
    context.send_msgs = AsyncMock()
    await context.poll_game_once()
    assert context.send_msgs.call_args.args[0] == [{"cmd": "Say", "text": "Second"}]
    assert context.interaction.acknowledged["a" * 16] == 2
