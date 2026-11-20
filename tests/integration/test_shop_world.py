import asyncio

import pytest
from BaseClasses import CollectionState, LocationProgressType
from test.general import setup_multiworld
from test_client import connected_context
from worlds.gamma import GammaWorld

from gamma_archipelago.configuration import build_configuration, defaults
from gamma_archipelago.discovery import configured_location_ids
from gamma_archipelago.web_planner import metadata, preview

SHOPS = set(range(28052921, 28052930))


@pytest.mark.parametrize("enabled,policy,count", [(0, 0, 0), (1, 0, 9), (1, 1, 0), (1, 2, 9)])
def test_paid_shop_toggle_world_client_and_missable_policy_agree(enabled, policy, count):
    world = setup_multiworld(
        GammaWorld, options=dict(checks_shop_purchases=enabled, optional_check_policy=policy)
    ).worlds[1]
    locations = [
        location for location in world.multiworld.get_locations(1) if location.address in SHOPS
    ]
    assert len(locations) == count
    assert all(
        (location.progress_type == LocationProgressType.EXCLUDED) == (policy == 0)
        for location in locations
    )
    data = world.fill_slot_data()

    async def exercise():
        context = connected_context(data)
        assert context.session.allowed_locations == configured_location_ids(world.configuration)

    asyncio.run(exercise())
    assert len(set(data["location_ids"]) & SHOPS) == count


def test_shop_and_ordinary_purchase_checks_remain_independent_and_prices_are_previewed():
    legacy = preview({**defaults(), "checks_shops": 1}, {})
    paid = preview({**defaults(), "checks_shop_purchases": 1}, {})
    assert not SHOPS & {row["id"] for row in legacy["checks"]}
    offers = [row for row in paid["checks"] if row["id"] in SHOPS]
    assert paid["shop_cost_ru"] == 75000 and legacy["shop_cost_ru"] == 0
    assert len(offers) == 9 and sum(row["price"] for row in offers) == 75000
    assert {row["price"] for row in offers} == {2500, 7500, 15000}
    assert all(row["description"] and row["merchant"] for row in offers)
    assert any(
        row["key"] == "checks_shop_purchases" and row["count"] == 9 for row in metadata()["checks"]
    )
    values = defaults()
    values.pop("checks_shop_purchases")
    assert build_configuration(values).digest == build_configuration(defaults()).digest


def test_new_client_accepts_an_unchanged_legacy_slot_without_the_added_toggle():
    world = setup_multiworld(GammaWorld).worlds[1]
    data = world.fill_slot_data()
    digest, locations = data["configuration_key"], set(data["location_ids"])
    data["configuration"].pop("checks_shop_purchases")

    async def exercise():
        context = connected_context(data)
        assert context.configuration.digest == digest
        assert context.session.allowed_locations == locations

    asyncio.run(exercise())


def test_shop_world_locations_follow_the_same_regional_keys_as_the_game_adapter():
    world = setup_multiworld(
        GammaWorld, options=dict(checks_shop_purchases=1, rewards_zone_keys=1)
    ).worlds[1]
    state = CollectionState(world.multiworld)
    cordon = world.multiworld.get_location("AP Shop: Sidorovich - Rookie Trade Contract", 1)
    rostok = world.multiworld.get_location("AP Shop: Barman - Rostok Trade Contract", 1)
    assert cordon.can_reach(state) and not rostok.can_reach(state)
    state.collect(world.create_item("Zone Key: Garbage"), True)
    state.collect(world.create_item("Zone Key: Rostok"), True)
    assert rostok.can_reach(state)
