"""A real upstream generator, MultiServer and CommonClient over a loopback websocket."""

import asyncio
import zlib
from functools import partial
from pathlib import Path

import Generate
import Main
import MultiServer
import pytest
import websockets
from CommonClient import CommonContext
from NetUtils import ClientStatus
from Utils import restricted_loads
from worlds.gamma.client import GammaContext

from gamma_archipelago.bridge import FileBridge
from gamma_archipelago.catalog import ITEM_SECTIONS
from gamma_archipelago.catalog import MAP_LOCATION_IDS as LOCATION_IDS

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
            "name: QuestPilot\ngame: APQuest\nAPQuest: {}\n", encoding="utf-8"
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
                    quest.game = "APQuest"
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
                outgoing = [
                    "GAMMA_AP_OUT|3",
                    f"session|{key}",
                    f"configuration|{client.configuration.digest}",
                    "received|0",
                ]
                outgoing.extend(f"check|{value}" for value in sorted(LOCATION_IDS))
                outgoing.extend(["goal|1", f"end|{len(LOCATION_IDS)}", ""])
                (bridge.directory / "outgoing.txt").write_text(
                    "\n".join(outgoing), encoding="ascii"
                )
                await client.poll_game_once()
                await wait_until(lambda: len(client.items_received) == len(LOCATION_IDS))
                presence = (bridge.directory / "presence.txt").read_text()
                assert f"session|{key}\n" in presence
                assert "player|" + b"GammaPilot".hex() in presence
                request = (
                    f"GAMMA_AP_COMMANDS|1\nsession|{key}\n"
                    f"configuration|{client.configuration.digest}\n"
                    f"game|{'a' * 16}\ntarget|{client.room.epoch}\n"
                    "request|1|loaded|\nend|1\n"
                )
                (bridge.directory / "game_requests.txt").write_text(request, encoding="ascii")
                await client.poll_game_once()
                await wait_until(
                    lambda: any(
                        "GammaPilot loaded GAMMA and entered the Zone." in message.text
                        for message in client.room.messages
                    )
                )
                await client.poll_game_once()
                assert (
                    sum(
                        "GammaPilot loaded GAMMA and entered the Zone." in message.text
                        for message in client.room.messages
                    )
                    == 1
                )
                initial_epoch = client.scouting_epoch
                assert {item.item for item in client.items_received} == set(ITEM_SECTIONS)
                assert {f"r:{index}" for index in range(3)} <= client.session.notices.keys()
                if mixed_game:
                    await wait_until(
                        lambda: any(
                            identity.startswith("s:") for identity in client.session.notices
                        )
                    )
                assert server.location_checks[(client.team, client.slot)] == set(LOCATION_IDS)
                assert (
                    server.client_game_state[(client.team, client.slot)] == ClientStatus.CLIENT_GOAL
                )
                incoming = (bridge.directory / "incoming.txt").read_text()
                assert incoming.endswith(f"end|{len(LOCATION_IDS)}\n")
                await client.disconnect()
                await client.connect(address)
                await wait_until(
                    lambda: (
                        client.server is not None
                        and len(client.items_received) == len(LOCATION_IDS)
                    )
                )
                assert client.session.session_key == key
                assert client.session.item_ids and len(client.session.item_ids) == len(LOCATION_IDS)
                await client.poll_game_once()
                assert client.scouting_epoch != initial_epoch
                assert client.scouting_epoch in (bridge.directory / "presence.txt").read_text()
                assert server.location_checks[(client.team, client.slot)] == set(LOCATION_IDS)
                # Persist the actual server state and reconnect to a new server
                # context, rather than treating socket reconnect as restart proof.
                server.save_filename = str(tmp_path / "pilot.apsave")
                server.saving = True
                assert server.save(now=True)
                restored = MultiServer.Context("127.0.0.1", 0, None, None, 1, 10, False)
                restored.load(str(archives[0]))
                restored.set_save(
                    restricted_loads(zlib.decompress(Path(server.save_filename).read_bytes()))
                )
                expected_notice_ids = set(client.session.notices)
                await client.shutdown()
                client = GammaContext(bridge=bridge)
                client.auth = "GammaPilot"
                async with websockets.serve(
                    partial(MultiServer.server, ctx=restored), "127.0.0.1", 0
                ) as restarted:
                    await client.connect(f"127.0.0.1:{restarted.sockets[0].getsockname()[1]}")
                    await wait_until(
                        lambda: (
                            client.server is not None
                            and len(client.items_received) == len(LOCATION_IDS)
                        )
                    )
                    assert client.session.session_key == key
                    assert restored.location_checks[(client.team, client.slot)] == set(LOCATION_IDS)
                    assert (
                        restored.client_game_state[(client.team, client.slot)]
                        == ClientStatus.CLIENT_GOAL
                    )
                    assert len(client.session.item_ids) == len(LOCATION_IDS)
                    await client.poll_game_once()
                    await wait_until(lambda: expected_notice_ids <= client.session.notices.keys())
                    assert (
                        (bridge.directory / "confirmed_checks.txt")
                        .read_text()
                        .endswith(f"end|{len(LOCATION_IDS)}\n")
                    )
                    await client.disconnect()
            finally:
                await client.shutdown()
                if quest is not None:
                    await quest.shutdown()

    asyncio.run(exercise())
