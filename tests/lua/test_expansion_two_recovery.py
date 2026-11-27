"""One ordered receipt history combines permissions, consumables and keyed effects."""

from .test_workshop import craft_dialog, poll, state_of, tool_game


def test_combined_reward_history_recovers_partial_delivery_and_rolls_back_permissions(lua):
    history = (28051801,) * 3 + (28051813, 28051821, 28051901, 28051911)
    game, engine, _ = tool_game(
        lua,
        history,
        rewards_workshop_access=1,
        rewards_recipe_access=1,
        rewards_supply_medical=1,
        rewards_convenience=1,
        permission_supplies=1,
    )
    lua.execute("""
        engine.weights={other=7}
        weight={add_weight=function(key,amount,force)
            assert(force==true); engine.weights[key]=amount; return true
        end,remove_weight=function(key) engine.weights[key]=nil end}
    """)
    early = state_of(lua, game)
    assert early.received_count == 1
    assert lua.globals().ui_workshop.UIWorkshopCraft.Craft(craft_dialog(lua, 1)) is False
    for _ in range(20):
        poll(game, engine)
        if state_of(lua, game).received_count == 5 and state_of(lua, game).deliveries[6]:
            break
    partial = state_of(lua, game)
    assert partial.received_count == 5 and partial.deliveries[6].next_action == 2
    before = list(engine.created.values())
    game.load_state(lua.table(gamma_archipelago_v1=partial))
    for _ in range(10):
        poll(game, engine)
        if state_of(lua, game).received_count == len(history):
            break
    assert state_of(lua, game).received_count == len(history)
    assert list(engine.created.values()) == before + [
        "medkit_army",
        "medkit_scientic",
        "bandage",
        "bandage",
        "antirad",
        "morphine",
        "drug_antidot",
    ]
    assert engine.weights.gamma_archipelago_carry == 5 and engine.weights.other == 7
    assert lua.globals().ui_workshop.UIWorkshopCraft.Craft(craft_dialog(lua, 3)) == "native"
    created = list(engine.created.values())
    game.load_state(lua.table(gamma_archipelago_v1=state_of(lua, game)))
    poll(game, engine)
    assert list(engine.created.values()) == created
    assert engine.weights.gamma_archipelago_carry == 5
    game.load_state(lua.table(gamma_archipelago_v1=early))
    poll(game, engine)
    assert engine.weights.gamma_archipelago_carry is None and engine.weights.other == 7
    assert lua.globals().ui_workshop.UIWorkshopCraft.Craft(craft_dialog(lua, 1)) is False
    # Real older-save loading must also restore native spawned inventory. The Lua
    # mock deliberately leaves it visible, so this test makes no exactly-once claim.
    for _ in range(20):
        poll(game, engine)
        if state_of(lua, game).received_count == len(history):
            break
    assert state_of(lua, game).received_count == len(history)
    assert engine.weights.gamma_archipelago_carry == 5
