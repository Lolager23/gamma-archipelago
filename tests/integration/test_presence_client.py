import asyncio

from test_client import connected_context

from gamma_archipelago.protocol import ProtocolError


def test_presence_names_live_connection_only_and_reconnect_epoch_changes():
    async def exercise():
        context = connected_context()
        published = []
        context.bridge.write_presence = lambda *args: published.append(args)
        context.player_names[1] = "Owen %c[red]"
        await context.poll_game_once()
        await context.poll_game_once()
        assert [row[3] for row in published] == [1, 2]
        assert published[-1][-1] == "Owen c red"
        first_epoch = published[-1][2]
        context.server = None
        await context.poll_game_once()
        assert len(published) == 2
        context.server = object()
        context.on_package("Connected", {"slot_data": {"schema_version": 1, "pilot": True}})
        await context.poll_game_once()
        assert published[-1][2] != first_epoch and published[-1][3] == 1
        context.player_names.clear()
        context.auth = "SlotName"
        await context.poll_game_once()
        assert published[-1][-1] == "SlotName"
        context.auth = None
        await context.poll_game_once()
        assert published[-1][-1] == "Player 1"

    asyncio.run(exercise())


def test_presence_file_failure_does_not_block_game_transport_and_errors_are_bounded(caplog):
    async def exercise():
        context = connected_context()
        observed = []
        context.bridge.read_game = lambda key: observed.append(key)

        def failed(*args):
            raise OSError("Presence path is unavailable")

        context.bridge.write_presence = failed
        await context.poll_game_once()
        await context.poll_game_once()
        assert len(observed) == 2
        assert caplog.text.count("Presence path is unavailable") == 1

        def malformed(*args):
            raise ProtocolError("Presence label invalid")

        context.bridge.write_presence = malformed
        await context.poll_game_once()
        assert len(observed) == 3 and "Presence label invalid" in caplog.text
        context.bridge.write_presence = lambda *args: None
        await context.poll_game_once()
        assert context.last_presence_error is None

    asyncio.run(exercise())
