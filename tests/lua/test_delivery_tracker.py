from .test_stashes import poll, progress, stash_game


def test_received_stash_coordinates_are_distinct_from_claimed_supplies(lua):
    game, engine = stash_game(lua)
    poll(game, engine)
    view = game.tracker_view()
    assert view.applied == 1
    assert view.stash_delivery == "Stash deliveries: 1 coordinates received, 0 claimed"
    state = progress(lua, game)
    record = state.stashes.records[1]
    game.physic_object_on_use_callback(engine.boxes[record.cache_id], lua.globals().db.actor)
    assert (
        game.tracker_view().stash_delivery == "Stash deliveries: 1 coordinates received, 1 claimed"
    )
