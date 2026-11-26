"""The selected native upgrade difficulty determines its AP tool permission."""

import pytest

from .test_workshop import TOOLS, state_of, tool_game, upgrade_dialog


def give_tools(lua, game, count):
    state = state_of(lua, game)
    state.applied_items = lua.table_from([TOOLS] * count)
    state.received_count = count
    game.load_state(lua.table(gamma_archipelago_v1=state))


@pytest.mark.parametrize("technician", [False, True])
@pytest.mark.parametrize("tier", [1, 2, 3])
@pytest.mark.parametrize("received", [0, 1, 2, 3])
def test_chevrons_require_matching_tool_tier_before_any_native_mutation(
    lua, technician, tier, received
):
    game, engine, _ = tool_game(lua)
    give_tools(lua, game, received)
    api = (
        lua.globals().ui_inventory.UIInventory.RMode_UpgradeYes
        if technician
        else lua.globals().ui_workshop.UIWorkshopUpgrade.Upgrade
    )
    permitted = received >= tier
    assert (api(upgrade_dialog(lua, tier, technician=technician)) == "native") == permitted
    assert engine.work_calls == int(permitted)
    if not permitted:
        assert ("Basic", "Advanced", "Expert")[tier - 1] in engine.tips[1]


def test_batch_requires_highest_new_tier_but_ignores_preinstalled_expert_upgrade(lua):
    game, engine, _ = tool_game(lua)
    give_tools(lua, game, 1)
    dialog = upgrade_dialog(lua, installed=("old_expert",))
    dialog.inst_upgr.old_expert = True
    dialog.upgr[1][5] = lua.table(section="old_expert", tier=3)
    api = lua.globals().ui_workshop.UIWorkshopUpgrade.Upgrade
    assert api(dialog) == "native"
    dialog.inst_upgr.advanced = True
    dialog.upgr[1][3] = lua.table(section="advanced", tier=2)
    assert api(dialog) is False and engine.work_calls == 1
    give_tools(lua, game, 2)
    assert api(dialog) == "native"
    dialog.inst_upgr.expert = True
    dialog.upgr[2] = lua.table_from({6: lua.table(section="expert", tier=3)})
    assert api(dialog) is False and engine.work_calls == 2
    give_tools(lua, game, 3)
    assert api(dialog) == "native" and engine.work_calls == 3


@pytest.mark.parametrize("technician", [False, True])
@pytest.mark.parametrize("tier", [None, 0, 4, 1.5, "1", True])
def test_unknown_or_invalid_difficulty_refuses_before_spending_or_installing(lua, technician, tier):
    game, engine, _ = tool_game(lua)
    give_tools(lua, game, 3)
    dialog = upgrade_dialog(lua, technician=technician)
    tree = dialog.upgr_tree if technician else dialog.upgr
    tree[1][1].tier = tier
    api = (
        lua.globals().ui_inventory.UIInventory.RMode_UpgradeYes
        if technician
        else lua.globals().ui_workshop.UIWorkshopUpgrade.Upgrade
    )
    assert api(dialog) is False and engine.work_calls == 0
    assert "difficulty" in engine.tips[1]


def test_disabled_tool_option_retains_native_delegation_without_upgrade_metadata(lua):
    game, _, _ = tool_game(lua, rewards_progressive_tools=0, rewards_workshop_access=1)
    state = state_of(lua, game)
    state.unlocks.workshop_upgrade = True
    assert lua.globals().gamma_ap_workshop.allowed(state, "upgrade", lua.table()) is True


def test_unresolved_batch_entry_and_missing_native_item_refuse_even_with_expert(lua):
    game, engine, _ = tool_game(lua)
    give_tools(lua, game, 3)
    dialog = upgrade_dialog(lua)
    dialog.inst_upgr.unknown = True
    api = lua.globals().ui_workshop.UIWorkshopUpgrade.Upgrade
    assert api(dialog) is False
    dialog.inst_upgr.unknown = None
    dialog.inst_upgr[1] = True
    assert api(dialog) is False
    assert api(lua.table()) is False
    assert engine.work_calls == 0


def test_existing_only_batch_is_a_noop_not_an_expert_requirement(lua):
    game, engine, _ = tool_game(lua)
    give_tools(lua, game, 1)
    dialog = upgrade_dialog(lua, 3, installed=("selected",))
    assert lua.globals().ui_workshop.UIWorkshopUpgrade.Upgrade(dialog) == "native"
    assert engine.work_calls == 1


@pytest.mark.parametrize("technician", [False, True])
@pytest.mark.parametrize("column,tier,received", [(5, 1, 1), (1, 2, 1), (1, 3, 2)])
def test_gamma_remapped_native_tier_is_authoritative(lua, technician, column, tier, received):
    game, engine, _ = tool_game(lua)
    give_tools(lua, game, received)
    dialog = upgrade_dialog(lua, technician=technician)
    tree = dialog.upgr_tree if technician else dialog.upgr
    tree[1] = lua.table_from({column: lua.table(section="selected", tier=tier)})
    if technician:
        dialog.upgr_last_col = column
    api = (
        lua.globals().ui_inventory.UIInventory.RMode_UpgradeYes
        if technician
        else lua.globals().ui_workshop.UIWorkshopUpgrade.Upgrade
    )
    assert (api(dialog) == "native") == (received >= tier)
    assert engine.work_calls == int(received >= tier)


def test_basic_tools_credit_new_upgrade_without_waiting_for_expert(lua):
    from .test_equipment_checks import equipment_game, gear, progress

    game, _, _ = equipment_game(lua, checks_gear_upgrades=1)
    state = progress(lua, game)
    state.configuration.options.rewards_progressive_tools = 1
    state.configuration.options.equipment_class_progression = 1
    state.applied_items = lua.table_from([TOOLS])
    state.received_count = 1
    item = gear(lua)
    module = lua.globals().gamma_ap_equipment_checks
    assert module.acquired(state, item)
    assert module.poll(state, state.configuration)
    assert state.equipment.counts.firearm == 0
    item.upgrades[1] = "one_chevron"
    assert module.poll(state, state.configuration)
    assert state.checks[28052731] and state.equipment.counts.firearm == 1
