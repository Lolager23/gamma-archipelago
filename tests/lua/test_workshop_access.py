import pytest

from .test_workshop import craft_dialog, poll, state_of, tool_game


def test_workshop_receipts_unlock_only_the_corresponding_actions_and_survive_reload(lua):
    game, engine, _ = tool_game(
        lua, (28051811, 28051812, 28051813), rewards_progressive_tools=0, rewards_workshop_access=1
    )
    api = lua.globals().ui_workshop
    assert api.UIWorkshopRepair.Repair(lua.table()) == "native"
    assert api.UIWorkshopUpgrade.Upgrade(lua.table()) is False
    assert api.UIWorkshopCraft.Craft(craft_dialog(lua, 1)) is False
    saved = state_of(lua, game)
    poll(game, engine)
    assert api.UIWorkshopUpgrade.Upgrade(lua.table()) == "native"
    poll(game, engine)
    assert api.UIWorkshopCraft.Craft(craft_dialog(lua, 1)) == "native"
    assert not list(engine.created.values())
    current = state_of(lua, game)
    assert (
        current.unlocks.workshop_repair
        and current.unlocks.workshop_upgrade
        and current.unlocks.workshop_craft
    )
    game.load_state(lua.table(gamma_archipelago_v1=saved))
    assert api.UIWorkshopUpgrade.Upgrade(lua.table()) is False
    assert any(
        row.reason == "Workshop upgrade permission required"
        for row in game.tracker_view().rows.values()
        if row.category == "checks_gear_upgrades"
    )


@pytest.mark.parametrize(
    "identity,tiers", [(28051821, (1, 2, 3)), (28051822, (4,)), (28051823, (5,)), (28051824, (6,))]
)
def test_recipe_permissions_are_independent_and_follow_native_tool_groups(lua, identity, tiers):
    game, _, _ = tool_game(lua, (identity,), rewards_progressive_tools=0, rewards_recipe_access=1)
    api = lua.globals().ui_workshop
    for tier in range(1, 7):
        assert (api.UIWorkshopCraft.Craft(craft_dialog(lua, tier)) == "native") == (tier in tiers)
    assert api.UIWorkshopRepair.Repair(lua.table()) == "native"
    assert api.UIWorkshopUpgrade.Upgrade(lua.table()) == "native"
    state = state_of(lua, game)
    assert lua.globals().gamma_ap_workshop.allowed(state, "unknown", lua.table())[0] is False


def test_permissions_combine_with_progressive_tools_and_unknown_recipes_refuse(lua):
    game, _, _ = tool_game(lua, rewards_workshop_access=1, rewards_recipe_access=1)
    state = state_of(lua, game)
    module = lua.globals().gamma_ap_workshop
    state.unlocks.workshop_craft = True
    assert module.allowed(state, "craft", craft_dialog(lua, 1))[0] is False
    state.unlocks.recipe_general = True
    assert module.allowed(state, "craft", craft_dialog(lua, 1))[0] is False
    state.applied_items = lua.table_from([28051801])
    assert module.allowed(state, "craft", craft_dialog(lua, 1)) is True
    assert module.allowed(state, "craft", craft_dialog(lua, 2))[0] is False
    assert module.allowed(state, "craft", craft_dialog(lua, 7))[0] is False
    state.configuration.options.rewards_recipe_access = 0
    state.configuration.options.rewards_workshop_access = 0
    state.configuration.options.rewards_progressive_tools = 0
    assert module.allowed(state, "craft", lua.table()) is True
