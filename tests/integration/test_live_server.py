"""A real upstream generator, MultiServer and CommonClient over a loopback websocket."""

import asyncio
from functools import partial
from pathlib import Path

import Generate
import Main
import MultiServer
import pytest
import websockets
from CommonClient import CommonContext
from NetUtils import ClientStatus
from worlds.gamma.client import GammaContext

from gamma_archipelago.bridge import FileBridge
from gamma_archipelago.catalog import ITEM_SECTIONS, LOCATION_IDS

ROOT = Path(__file__).resolve().parents[2]
pytestmark = [pytest.mark.integration, pytest.mark.server]


async def wait_until(predicate, *, seconds=10):
    async with asyncio.timeout(seconds):
        while not predicate():
            await asyncio.sleep(0.01)


@pytest.mark.parametrize("mixed_game", [False, True])
def test_real_generation_server_item_delivery_and_reconnect(tmp_path, mixed_game):
    output = tmp_path / "output"
    players = tmp_path / "players"
    players.mkdir()
    (players / "gamma.yaml").write_bytes((ROOT / "examples/pilot.yaml").read_bytes())
    if mixed_game:
        (players / "quest.yaml").write_text(
            "name: QuestPilot\ngame: Archipelago\nArchipelago: {}\n", encoding="utf-8"
        )
    arguments = Generate.mystery_argparse(
        [
            "--player_files_path",
            str(players),
            "--outputpath",
            str(output),
            "--seed",
            "20261118",
            "--spoiler",
            "0",
            "--log_level",
            "warning",
        ]
    )
    generated_arguments, seed = Generate.main(arguments)
    Main.main(generated_arguments, seed)
    archives = list(output.glob("*.zip"))
    assert len(archives) == 1

    async def exercise():
        server = MultiServer.Context("127.0.0.1", 0, None, None, 1, 10, False)
        server.load(str(archives[0]))
        bridge = FileBridge(tmp_path / "game", allowed_root=tmp_path / "game")
        client = GammaContext(bridge=bridge)
        client.auth = "GammaPilot"
        quest = None
        async with websockets.serve(
            partial(MultiServer.server, ctx=server), "127.0.0.1", 0
        ) as listener:
            address = f"127.0.0.1:{listener.sockets[0].getsockname()[1]}"
            try:
                await client.connect(address)
                await wait_until(lambda: client.session is not None)
                if mixed_game:
                    quest = CommonContext()
                    quest.game = "Archipelago"
                    quest.auth = "QuestPilot"
                    quest.items_handling = 0b111

                    async def authenticate(_password_requested=False):
                        await quest.send_connect()

                    quest.server_auth = authenticate
                    await quest.connect(address)
                    await wait_until(lambda: quest.slot is not None)
                    await quest.send_msgs(
                        [{"cmd": "LocationChecks", "locations": list(server.locations[quest.slot])}]
                    )
                key = client.session.session_key
                outgoing = ["GAMMA_AP_OUT|1", f"session|{key}", "received|0"]
                outgoing.extend(f"check|{value}" for value in sorted(LOCATION_IDS))
                outgoing.extend(["goal|1", "end|3", ""])
                (bridge.directory / "outgoing.txt").write_text(
                    "\n".join(outgoing), encoding="ascii"
                )
                await client.poll_game_once()
                await wait_until(lambda: len(client.items_received) == 3)
                assert {item.item for item in client.items_received} == set(ITEM_SECTIONS)
                assert server.location_checks[(client.team, client.slot)] == set(LOCATION_IDS)
                assert (
                    server.client_game_state[(client.team, client.slot)] == ClientStatus.CLIENT_GOAL
                )
                incoming = (bridge.directory / "incoming.txt").read_text()
                assert incoming.endswith("end|3\n")
                await client.disconnect()
                await client.connect(address)
                await wait_until(
                    lambda: client.server is not None and len(client.items_received) == 3
                )
                assert client.session.session_key == key
                assert client.session.item_ids and len(client.session.item_ids) == 3
                await client.poll_game_once()
                assert server.location_checks[(client.team, client.slot)] == set(LOCATION_IDS)
            finally:
                await client.shutdown()
                if quest is not None:
                    await quest.shutdown()

    asyncio.run(exercise())
