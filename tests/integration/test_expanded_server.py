"""Real expanded multiworld traffic with synthetic game snapshots; no engine launch."""

import asyncio
import json
import zlib
from functools import partial

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
from gamma_archipelago.presets import presets

pytestmark = [pytest.mark.integration, pytest.mark.server]


async def until(predicate):
    async with asyncio.timeout(20):
        while not predicate():
            await asyncio.sleep(0.01)


def write_snapshot(client, *, received=0):
    allowed = sorted(client.session.allowed_locations)
    lines = [
        "GAMMA_AP_OUT|3",
        f"session|{client.session.session_key}",
        f"configuration|{client.configuration.digest}",
        f"received|{received}",
    ]
    lines.extend(f"check|{identity}" for identity in allowed)
    lines.extend(["goal|1", f"end|{len(allowed)}", ""])
    (client.bridge.directory / "outgoing.txt").write_text("\n".join(lines), encoding="ascii")


@pytest.mark.parametrize(
    "preset,goal,seed",
    [
        ("mvp", 2, 20261119),
        ("mvp", 2, 20261120),
        ("extended", 4, 20261121),
        ("extended", 4, 20261122),
        ("full_story", 4, 20261301),
        ("full_story", 4, 20261302),
        *[("full_story", goal, 20261200 + goal) for goal in range(9)],
    ],
)
def test_two_gamma_slots_and_foreign_game_transfer_restart_and_each_goal(
    tmp_path, preset, goal, seed
):
    players, output = tmp_path / "players", tmp_path / "output"
    players.mkdir()
    values = {**presets()[preset], "goal": goal}
    if seed in (20261301, 20261302):
        values["starting_location"] = seed - 20261300
    scout_case = seed == 20261119
    expansion_case = seed in (20261121, 20261122)
    legacy_tools = seed == 20261122
    tool_counts = (
        {28051202: 1, 28051203: 1, 28051204: 1}
        if legacy_tools
        else {28051801: 3, 28051834: 1, 28051835: 1, 28051836: 1}
    )
    initial_tools = {28051202: 1, 28051203: 1} if legacy_tools else {28051801: 2}
    if expansion_case:
        values.update(
            rewards_convenience=1,
            random_starting_unlock=1,
            mutant_discovery_mode=1,
            artefact_discovery_mode=1,
            mutant_filler_tail=5,
            artefact_filler_tail=5,
            rewards_supply_ammunition=1,
            supply_ammo_calibre=4,
            mutant_discovery_count=15,
            artefact_discovery_count=20,
            discovery_exclusions=["mutant:bibliotekar", "artefact:af_compass"],
            start_inventory={"Equipment Unlock: PDA": 1, "Zone Key: Garbage": 1},
            start_inventory_from_pool={
                "Progression Stash: Basic Tools": 1,
                "Progression Stash: Advanced Tools": 1,
            }
            if legacy_tools
            else {"Progressive Tools": 2},
            tool_use_permissions=0 if legacy_tools else 1,
            generation_preview=1,
            non_local_items=["Zone Key: Agroprom"],
        )
    if scout_case:
        values.update(
            scouting_mode=2,
            reward_previews=1,
            checks_shops=1,
            checks_shop_purchases=1,
            checks_faction_standing=1,
            checks_side_task_milestones=1,
        )
    for name in ("GammaAlpha", "GammaBeta"):
        (players / f"{name}.yaml").write_text(
            json.dumps(
                {"name": name, "game": "S.T.A.L.K.E.R. GAMMA", "S.T.A.L.K.E.R. GAMMA": values}
            )
        )
    (players / "QuestHelper.yaml").write_text("name: QuestHelper\ngame: APQuest\nAPQuest: {}\n")
    arguments = Generate.mystery_argparse(
        [
            "--player_files_path",
            str(players),
            "--outputpath",
            str(output),
            "--seed",
            str(seed),
            "--spoiler",
            "0",
            "--log_level",
            "warning",
        ]
    )
    generated, actual_seed = Generate.main(arguments)
    filled = Main.main(generated, actual_seed)
    if expansion_case:
        for player in (1, 2):
            key = next(
                item
                for item in filled.itempool
                if item.player == player and item.name == "Zone Key: Agroprom"
            )
            assert key.location.player != player
    (archive,) = output.glob("*.zip")

    async def exercise():
        server = MultiServer.Context("127.0.0.1", 0, None, None, 1, 10, False)
        server.load(str(archive))
        clients = []
        quest = CommonContext()
        quest.game, quest.auth, quest.items_handling = "APQuest", "QuestHelper", 0b111

        async def auth(_password_requested=False):
            await quest.send_connect()

        quest.server_auth = auth
        try:
            async with websockets.serve(
                partial(MultiServer.server, ctx=server), "127.0.0.1", 0
            ) as listener:
                address = f"127.0.0.1:{listener.sockets[0].getsockname()[1]}"
                for name in ("GammaAlpha", "GammaBeta"):
                    root = tmp_path / name
                    client = GammaContext(bridge=FileBridge(root, allowed_root=root))
                    client.auth = name
                    clients.append(client)
                    await client.connect(address)
                    await until(lambda client=client: client.session is not None)
                    if expansion_case:
                        await until(lambda client=client: len(client.session.item_ids) >= 4)
                        assert all(
                            client.session.item_ids.count(id_) == count
                            for id_, count in initial_tools.items()
                        )
                        assert client.expanded and client.require_configuration
                await quest.connect(address)
                await until(lambda: quest.slot is not None)
                if scout_case:
                    first = clients[0]
                    requests = first.bridge.directory / "scout_requests.txt"
                    requests.write_text(
                        "\n".join(
                            [
                                "GAMMA_AP_SCOUTS|1",
                                f"session|{first.session.session_key}",
                                f"configuration|{first.configuration.digest}",
                                "request|28052901",
                                "end|1",
                                "",
                            ]
                        ),
                        encoding="ascii",
                    )
                    await first.poll_game_once()
                    await until(lambda: 28052901 in first.locations_info)
                    await until(
                        lambda: (
                            not first.item_names.lookup_in_slot(
                                first.locations_info[28052901].item,
                                first.locations_info[28052901].player,
                            ).startswith("Unknown item")
                        )
                    )
                    await first.poll_game_once()
                    assert (
                        "item|28052901|"
                        in (first.bridge.directory / "scouted_items.txt").read_text()
                    )
                    assert any(
                        hint.location == 28052901 for hint in server.hints[(first.team, first.slot)]
                    )
                    assert not server.location_checks[(first.team, first.slot)]
                    assert not first.session.item_ids
                    assert not first.session.notices
                await quest.send_msgs(
                    [{"cmd": "LocationChecks", "locations": list(server.locations[quest.slot])}]
                )
                for client in clients:
                    write_snapshot(client)
                    await client.poll_game_once()
                for client in clients:
                    expected = len(client.session.allowed_locations) + (4 if expansion_case else 0)
                    await until(
                        lambda client=client, expected=expected: (
                            len(client.items_received) == expected
                        )
                    )
                    await until(
                        lambda client=client, expected=expected: (
                            len(client.session.item_ids) == expected
                        )
                    )
                    assert server.location_checks[(client.team, client.slot)] == set(
                        client.session.allowed_locations
                    )
                    assert (
                        server.client_game_state[(client.team, client.slot)]
                        == ClientStatus.CLIENT_GOAL
                    )
                    write_snapshot(client, received=expected)
                    await client.poll_game_once()
                    assert len(client.session.notices) >= expected
                    if expansion_case:
                        assert all(
                            client.session.item_ids.count(id_) == count
                            for id_, count in tool_counts.items()
                        )
                        assert client.session.item_ids.count(28051911) == 3
                assert any(item.player != clients[0].slot for item in clients[0].items_received)
                await until(lambda: any(key.startswith("s:") for key in clients[0].session.notices))
                original = clients[0]
                key, history = original.session.session_key, original.session.item_ids
                notices = set(original.session.notices)
                # An older game acknowledgement may replay delivery but must not
                # truncate server history or remove checks.
                write_snapshot(original, received=0)
                await original.poll_game_once()
                assert original.session.item_ids == history
                server.save_filename = str(tmp_path / "expanded.apsave")
                server.saving = True
                assert server.save(now=True)
                await original.shutdown()
                restored = MultiServer.Context("127.0.0.1", 0, None, None, 1, 10, False)
                restored.load(str(archive))
                restored.set_save(
                    restricted_loads(zlib.decompress((tmp_path / "expanded.apsave").read_bytes()))
                )
                fresh = GammaContext(bridge=original.bridge)
                fresh.auth = "GammaAlpha"
                clients.append(fresh)
                async with websockets.serve(
                    partial(MultiServer.server, ctx=restored), "127.0.0.1", 0
                ) as restarted:
                    await fresh.connect(f"127.0.0.1:{restarted.sockets[0].getsockname()[1]}")
                    await until(
                        lambda: fresh.session is not None and fresh.session.item_ids == history
                    )
                    assert fresh.session.session_key == key
                    # Recovery is deliberately bounded to 64 scouts per poll.
                    # Model the production watcher across every required batch.
                    for _ in range((len(fresh.checked_locations) + 63) // 64):
                        await fresh.poll_game_once()
                        await until(lambda: fresh.scout_requested <= fresh.locations_info.keys())
                    await until(lambda: notices <= fresh.session.notices.keys())
                    assert (
                        restored.client_game_state[(fresh.team, fresh.slot)]
                        == ClientStatus.CLIENT_GOAL
                    )
                    assert fresh.session.checked_locations == original.session.checked_locations
                    await fresh.shutdown()
        finally:
            for client in clients:
                await client.shutdown()
            await quest.shutdown()

    asyncio.run(exercise())
