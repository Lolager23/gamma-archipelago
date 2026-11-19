from .test_pda_ui import load_ui
from .test_tracker import state_for, view


def test_open_tracker_survives_lua_collection_before_native_child_update(lua):
    module = load_ui(lua)
    current = view(lua, state_for(lua))
    lua.globals().gamma_ap_game = lua.table(tracker_view=lambda: current)
    window = module.get_ui()
    assert len(window.details["items"]) > 0
    lua.execute("collectgarbage('collect'); collectgarbage('collect')")
    window.Update(window)


def test_refreshed_rows_and_reopened_tracker_survive_native_updates_after_collection(lua):
    module = load_ui(lua)
    current = view(lua, state_for(lua))
    lua.globals().gamma_ap_game = lua.table(tracker_view=lambda: current)
    window = module.get_ui()
    for index in range(10):
        current.rows[1].reason = f"Changed requirement {index}"
        window.refresh(window)
        assert lua.eval("rawequal")(window, module.get_ui())
        lua.execute("collectgarbage('collect')")
        window.Update(window)
    current.bound = False
    window.refresh(window)
    lua.execute("collectgarbage('collect')")
    window.Update(window)
    current.bound = True
    module.get_ui()
    lua.execute("collectgarbage('collect')")
    window.Update(window)
