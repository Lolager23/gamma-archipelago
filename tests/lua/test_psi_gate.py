from .test_stashes import poll, progress, stash_game


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
