import asyncio
from unittest.mock import AsyncMock

from NetUtils import NetworkItem, NetworkSlot
from test.general import setup_multiworld
from test_client import connected_context
from worlds.gamma import GammaWorld, scouting

from gamma_archipelago.configuration import build_configuration, defaults


def configured_context(**options):
    world = setup_multiworld(GammaWorld, seed=55, options=options).worlds[1]
    context = connected_context(world.fill_slot_data())
    context.send_msgs = AsyncMock()
    context.published = []
    context.bridge.write_scouted = lambda *args: context.published.append(args)
    return context


def test_scouting_uses_real_locations_and_foreign_recipient_data_without_acknowledging_items():
    async def exercise():
        context = configured_context(scouting_mode=2)
        identity = min(context.session.allowed_locations)
        context.bridge.read_scout_requests = lambda *_: frozenset({identity})
        context.locations_info[identity] = NetworkItem(42, identity, 2, 1)
        context.slot_info = {2: NetworkSlot("Friend", "Foreign Game", 0)}
        context.player_names = {2: "Friend"}
        context.item_names.lookup_in_slot = lambda identity, slot: "Foreign Key"
        await scouting.poll(context)
        assert context.send_msgs.call_args.args[0] == [
            {"cmd": "LocationScouts", "locations": [identity], "create_as_hint": 2}
        ]
        assert context.published[-1][-1][0].item == "Foreign Key"
        assert not context.session.item_ids and not context.session.checked_locations
        count = context.send_msgs.await_count
        await scouting.poll(context)
        assert context.send_msgs.await_count == count
        assert context.published[-1][3] == 2
        context.checked_locations.add(identity)
        await scouting.poll(context)
        assert context.send_msgs.call_args.args[0][0]["create_as_hint"] == 0
        context.configuration = None
        await scouting.poll(context)

    asyncio.run(exercise())


def test_next_milestone_previews_respect_option_and_advance_after_completion():
    async def exercise():
        context = configured_context(
            checks_side_task_milestones=1, checks_faction_standing=1, reward_previews=1
        )
        first = scouting.preview_locations(context)
        assert len(first) == 2
        await scouting.poll(context)
        assert set(context.send_msgs.call_args.args[0][0]["locations"]) == first
        assert context.send_msgs.call_args.args[0][0]["create_as_hint"] == 0
        context.session.checked_locations.update(first)
        assert not first & scouting.preview_locations(context)
        context.session.checked_locations.update(context.session.allowed_locations)
        assert not scouting.preview_locations(context)
        await scouting.poll(context)
        disabled = configured_context()
        await scouting.poll(disabled)
        disabled.send_msgs.assert_not_called()

    asyncio.run(exercise())


def test_unknown_metadata_is_deferred_and_requests_are_batched():
    async def exercise():
        context = configured_context(checks_artefacts=1, scouting_mode=1)
        wanted = frozenset(context.session.allowed_locations)
        context.bridge.read_scout_requests = lambda *_: wanted
        identity = min(wanted)
        context.locations_info[identity] = NetworkItem(42, identity, 2)
        await scouting.poll(context)
        assert len(context.send_msgs.call_args.args[0][0]["locations"]) == 64
        assert not context.published[-1][-1]
        context.slot_info = {2: NetworkSlot("Friend", "Foreign Game", 0)}
        context.item_names.lookup_in_slot = lambda *_: "Unknown item 42"
        await scouting.poll(context)
        assert not context.published[-1][-1]
        context.item_names.lookup_in_slot = lambda *_: "%c[red]Foreign Key"
        await scouting.poll(context)
        assert context.published[-1][-1][0].item == "c red Foreign Key"
        context.session = None
        await scouting.poll(context)

    asyncio.run(exercise())


def test_shop_and_standing_checks_are_finite_and_exclude_progression_by_default():
    from BaseClasses import LocationProgressType

    world = setup_multiworld(
        GammaWorld, options={"checks_maps": 0, "checks_shops": 1, "checks_faction_standing": 1}
    ).worlds[1]
    assert len(world.fill_slot_data()["location_ids"]) == 7
    assert all(
        location.progress_type == LocationProgressType.EXCLUDED
        for location in world.multiworld.get_locations(1)
        if location.address is not None
    )


def test_added_default_settings_preserve_legacy_configuration_identity():
    configuration = build_configuration(defaults())
    legacy = {
        name: value
        for name, value in defaults().items()
        if name
        not in {"scouting_mode", "reward_previews", "checks_shops", "checks_faction_standing"}
    }
    assert configuration.digest == build_configuration(legacy).digest
