from .test_stashes import poll, progress, stash_game


def test_psi_pickup_veto_does_not_block_the_next_ordinary_item(lua):
    game, engine = stash_game(lua, items=(), rewards_progression_stashes=1)
    poll(game, engine)
    helmet = lua.globals().add_item(50, "good_psy_helmet", "II_ATTCH", "i_quest", 0)
    bandage = lua.globals().add_item(51, "bandage", "S_FOOD", "i_medical", 0)
    pickup = lua.globals().bind_stalker_ext.actor_on_item_before_pickup
    assert pickup(helmet) is False
    assert pickup(bandage) is True


def test_native_calibrated_helmet_cannot_bypass_the_enabled_orange_stash_claim(lua):
    game, engine = stash_game(lua, items=(28051201,), rewards_progression_stashes=1)
    lua.execute("""
        engine.dropped={}
        db.actor.drop_item=function(self,item)
            engine.dropped[item:id()]=true; engine.objects[item:id()]=nil
        end
    """)
    poll(game, engine)
    item = lua.globals().add_item(50, "good_psy_helmet", "II_ATTCH", "i_quest", 0)
    flags = lua.table(ret_value=True)
    game.actor_on_item_before_pickup(item, flags)
    assert flags.ret_value is False
    game.actor_on_item_take(item)
    assert engine.dropped[50]
    lua.globals().make_cache(30, "esc_treasure_3", "l01_escape", 65535, "invbox")
    poll(game, engine)
    game.physic_object_on_use_callback(engine.boxes[30], lua.globals().db.actor)
    poll(game, engine)
    assert progress(lua, game).unlocks.calibrated_psi
    flags.ret_value = True
    game.actor_on_item_before_pickup(item, flags)
    assert flags.ret_value


def test_ordinary_psi_acquisition_is_unchanged_when_progression_stashes_are_disabled(lua):
    game, engine = stash_game(lua, items=())
    poll(game, engine)
    item = lua.globals().add_item(50, "good_psy_helmet", "II_ATTCH", "i_quest", 0)
    flags = lua.table(ret_value=True)
    game.actor_on_item_before_pickup(item, flags)
    assert flags.ret_value
    assert engine.objects[50]


def test_psi_only_poll_keeps_its_bounded_passive_protection_safeguard(lua):
    game, engine = stash_game(lua, items=(), rewards_progression_stashes=1)
    poll(game, engine)
    lua.execute("""
        engine.dropped={}
        db.actor.drop_item=function(self,item)
            if engine.fail_drop then error('drop failed') end
            engine.dropped[item:id()]=true;engine.objects[item:id()]=nil
        end
    """)
    for id_ in range(50, 83):
        lua.globals().add_item(id_, "good_psy_helmet", "II_ATTCH", "i_quest", 0)
    lua.globals().add_item(90, "pda", "D_PDA", "i_device", 0)
    engine.fail_drop = True
    poll(game, engine)
    assert not list(engine.dropped.keys()) and engine.objects[90] is not None
    engine.fail_drop = False
    poll(game, engine)
    assert len(list(engine.dropped.keys())) == 32, list(engine.logs.values())
    poll(game, engine)
    assert len(list(engine.dropped.keys())) == 33 and engine.objects[90] is not None
