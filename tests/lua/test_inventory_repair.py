"""Native inventory maintenance needs its consumables, not AP workshop access."""

import pytest

from .test_tool_permissions import KITS, kit_game
from .test_workshop import poll, state_of


def repair_item(lua, section="gun_oil", kind="i_repair"):
    lua.execute("""
        repair_items={}
        IsItem=function(group,section) return group=='repair' and repair_items[section] end
    """)
    lua.globals().repair_items[section] = lua.table(pistol=True)
    return lua.globals().add_item(50, section, "II_ATTCH", kind, 0)


@pytest.mark.parametrize("section", ["gun_oil", "cleaning_kit_p", "sewing_kit_a"])
@pytest.mark.parametrize("classes", [0, 1])
def test_native_consumables_repair_without_tools_or_workshop_permission(lua, section, classes):
    game, engine, _ = kit_game(
        lua,
        equipment_class_progression=classes,
        starting_tools=2,
        rewards_starting_gear_unlocks=1,
        rewards_workshop_access=1,
    )
    game.on_game_start()
    engine.creation.new_game_faction = None
    poll(game, engine)
    item = repair_item(lua, section)
    lua.execute("""
        ui_inventory.UIInventory.Action_Use=function() return 'native',nil,3 end
        ui_inventory.UIInventory.Action_Custom=function() return 'native',nil,3 end
    """)
    poll(game, engine)
    state = state_of(lua, game)
    assert not state.unlocks.gear_tools and not state.unlocks.workshop_repair
    assert lua.globals().gamma_ap_workshop.tools_level(state) == 0
    api = lua.globals().ui_inventory.UIInventory
    assert api.Action_Use(lua.table(), item) == ("native", None, 3)
    assert api.Action_Custom(lua.table(), item, "bag", 7, 1) == ("native", None, 3)
    flags = lua.table(ret_value=True)
    game.actor_on_item_before_use(item, flags)
    assert flags.ret_value is True
    # A previous mod's veto stays intact.
    flags.ret_value = False
    game.actor_on_item_before_use(item, flags)
    assert flags.ret_value is False
    dialog = lua.table(obj=item)
    assert lua.globals().item_repair.UIRepair.OnRepair(dialog, 7) == ("native", 7)
    assert engine.work_calls == 1
    assert lua.globals().ui_workshop.UIWorkshopRepair.Repair(lua.table()) is False
    assert lua.globals().ui_inventory.UIInventory.RMode_RepairYes(lua.table()) is False
    assert engine.work_calls == 1
    assert engine.objects[50] is not None
    game.load_state(lua.table(gamma_archipelago_v1=state))
    poll(game, engine)
    assert lua.globals().item_repair.UIRepair.OnRepair(dialog) == "native"
    assert engine.work_calls == 2


@pytest.mark.parametrize("id_,key,section,shortcut", KITS)
def test_toolkits_cannot_claim_the_inventory_repair_exemption(lua, id_, key, section, shortcut):
    game, engine, _ = kit_game(lua)
    item = repair_item(lua, section)
    state = state_of(lua, game)
    module = lua.globals().gamma_ap_tool_permissions
    assert not module.inventory_repair(section)
    # Even a native misclassification must not make a toolkit a consumable.
    assert (
        lua.globals().item_repair.UIRepair.OnRepair(lua.table(obj=item, section="gun_oil")) is False
    )
    assert engine.work_calls == 0 and module.reason(state, key)


def test_inventory_repair_classifier_handles_native_true_missing_and_unsupported_metadata(lua):
    game, engine, _ = kit_game(lua)
    item = repair_item(lua)
    module = lua.globals().gamma_ap_tool_permissions
    lua.globals().repair_items.gun_oil = True
    assert module.inventory_repair("gun_oil")
    assert not module.inventory_repair("unknown")
    state = state_of(lua, game)
    state.refused_save = True
    state.session_key = None
    # A rejected AP save must not disable ordinary native maintenance.
    assert (
        lua.globals().gamma_ap_workshop.allowed(state, "inventory_repair", lua.table(obj=item))
        is True
    )
    for code in (
        "IsItem=nil",
        "IsItem=function() error('unsupported item registry') end",
        "IsItem=function() return 'invalid' end",
    ):
        lua.execute(code)
        assert not module.inventory_repair("gun_oil")
        assert lua.globals().item_repair.UIRepair.OnRepair(lua.table(obj=item)) is False
    assert lua.globals().item_repair.UIRepair.OnRepair(lua.table()) is False
    assert engine.work_calls == 0


def test_a_weapon_with_a_repair_action_keeps_its_equipment_restriction(lua):
    game, engine, _ = kit_game(lua, starting_melee=2, rewards_starting_gear_unlocks=1)
    game.on_game_start()
    engine.creation.new_game_faction = None
    poll(game, engine)
    item = repair_item(lua, "wpn_knife", "w_melee")
    state = state_of(lua, game)
    assert lua.globals().gamma_ap_tool_permissions.inventory_repair("wpn_knife")
    assert lua.globals().gamma_ap_gear_locks.locked(state, item)
