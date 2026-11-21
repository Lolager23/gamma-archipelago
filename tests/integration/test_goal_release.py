"""A quick goal releases unchecked locations through the real AP server."""

import asyncio
import json
from functools import partial

import Generate
import Main
import MultiServer
import pytest
import websockets
from NetUtils import ClientStatus
from test_expanded_server import until
from worlds.gamma.client import GammaContext

from gamma_archipelago.bridge import FileBridge
from gamma_archipelago.presets import presets

pytestmark = [pytest.mark.integration, pytest.mark.server]


@pytest.mark.parametrize("mode", ["goal", "auto"])
def test_dialogue_victory_releases_unvisited_checks_without_faking_game_visits(tmp_path, mode):
    players, output = tmp_path / "players", tmp_path / "output"
    players.mkdir()
    (players / "Pilot.yaml").write_text(
        json.dumps(
            {
                "name": "Pilot",
                "game": "S.T.A.L.K.E.R. GAMMA",
                "S.T.A.L.K.E.R. GAMMA": presets()["pilot"],
            }
        )
    )
    args = Generate.mystery_argparse(
        [
            "--player_files_path",
            str(players),
            "--outputpath",
            str(output),
            "--seed",
            "2026112006",
            "--spoiler",
            "0",
            "--log_level",
            "warning",
        ]
    )
    generated, seed = Generate.main(args)
    Main.main(generated, seed)
    (archive,) = output.glob("*.zip")

    async def exercise():
        server = MultiServer.Context("127.0.0.1", 0, None, None, 1, 10, False, release_mode=mode)
        server.load(str(archive))
        root = tmp_path / "game"
        client = GammaContext(bridge=FileBridge(root, allowed_root=root))
        client.auth = "Pilot"
        try:
            async with websockets.serve(
                partial(MultiServer.server, ctx=server), "127.0.0.1", 0
            ) as listener:
                await client.connect(f"127.0.0.1:{listener.sockets[0].getsockname()[1]}")
                await until(lambda: client.session is not None)
                assert client.configuration.goal == "talk_sidorovich"
                # Ordered Get response is a barrier after the rejected pre-goal release.
                await client.send_msgs(
                    [
                        {"cmd": "Say", "text": "!release"},
                        {"cmd": "Get", "keys": ["pilot_release_barrier"]},
                    ]
                )
                await until(lambda: "pilot_release_barrier" in client.stored_data)
                assert not server.location_checks[(client.team, client.slot)]
                checked = 28052001  # Cordon only; Garbage/Rostok remain unvisited.
                lines = [
                    "GAMMA_AP_OUT|3",
                    f"session|{client.session.session_key}",
                    f"configuration|{client.configuration.digest}",
                    "received|0",
                    f"check|{checked}",
                    "goal|1",
                    "end|1",
                    "",
                ]
                (client.bridge.directory / "outgoing.txt").write_text("\n".join(lines))
                await client.poll_game_once()
                await until(
                    lambda: (
                        server.client_game_state[(client.team, client.slot)]
                        == ClientStatus.CLIENT_GOAL
                    )
                )
                if mode == "goal":
                    assert server.location_checks[(client.team, client.slot)] == {checked}
                    await client.send_msgs([{"cmd": "Say", "text": "!release"}])
                await until(lambda: client.checked_locations == client.session.allowed_locations)
                await until(
                    lambda: len(client.items_received) == len(client.session.allowed_locations)
                )
                # Server confirmation does not rewrite the actor-owned observation file.
                assert (client.bridge.directory / "outgoing.txt").read_text() == "\n".join(lines)
                assert len(client.checked_locations) == 33
        finally:
            await client.shutdown()

    asyncio.run(exercise())
