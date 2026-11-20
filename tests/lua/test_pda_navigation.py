from .test_pda_ui import load_ui, panel_text
from .test_tracker import state_for, view


def tracker(lua):
    module = load_ui(lua)
    current = view(lua, state_for(lua))
    requests = []

    def scout(identity):
        requests.append(identity)
        return True, "Requested"

    lua.globals().gamma_ap_game = lua.table(tracker_view=lambda: current, request_scout=scout)
    return module.get_ui(), current, requests


def mouse(lua, window, name, event="WINDOW_RBUTTON_DOWN"):
    rect = lua.globals().Frect()
    rect.set(rect, 0, 0, 0, 0)
    window.buttons[name].GetAbsoluteRect(window.buttons[name], rect)
    lua.globals().cursor.x, lua.globals().cursor.y = rect.x1 + 2, rect.y1 + 2
    return window.OnMouse(window, 0, 0, lua.globals().ui_events[event])


def test_right_click_reverses_region_and_status_filters_and_wraps_at_both_ends(lua):
    window, _, _ = tracker(lua)
    assert mouse(lua, window, "region") is True
    assert window.region_index == window.region_count
    window.callbacks["region"]()
    assert window.region_index == 1
    window.callbacks["region"]()
    window.offset, window.feedback = 9, "Old scout feedback"
    assert mouse(lua, window, "region") is True
    assert window.region_index == 1 and window.offset == 1 and window.feedback == ""
    for expected in (2, 1, 4, 3):
        assert mouse(lua, window, "status") is True
        assert window.status_index == expected
    assert mouse(lua, window, "refresh") is False
    assert mouse(lua, window, "status", "WINDOW_RBUTTON_UP") is False
    assert mouse(lua, window, "region", "WINDOW_LBUTTON_DOWN") is False
    window.callbacks["progression"]()
    assert mouse(lua, window, "region") is False
    window.callbacks["checks"]()
    window.buttons.region.Enable(window.buttons.region, False)
    assert mouse(lua, window, "region") is False


def test_empty_filter_and_unbound_views_disable_scouting_and_navigation(lua):
    window, current, requests = tracker(lua)
    assert window.status_index == 3  # Start with actionable checks.
    window.status_index = 2  # No completed checks yet.
    window.refresh(window)
    assert "No checks match" in panel_text(window.selection)
    assert window.selected_id is None
    for name in ("previous", "next", "scout"):
        assert not window.buttons[name].IsEnabled(window.buttons[name])
    window.callbacks["scout"]()
    window.details.selected = -1
    window.callbacks["check_list"]()
    assert requests == []
    current.bound = False
    window.feedback = "Old session feedback"
    window.refresh(window)
    assert mouse(lua, window, "region") is False
    current.bound = True
    window.refresh(window)
    assert window.feedback == "" and "Old session" not in panel_text(window.notice)


def test_click_selects_the_actual_row_and_keeps_its_id_after_live_changes(lua):
    window, current, requests = tracker(lua)
    window.details.SetSelectedIndex(window.details, 1)
    window.callbacks["check_list"]()
    chosen = current.rows[2].id
    assert window.selected_id == chosen
    clears = window.details.cleared
    window.callbacks["scout"]()
    assert requests == [chosen] and window.details.cleared == clears
    current.rows[1].status = "completed"
    window.refresh(window)
    assert window.selected_id == chosen and window.selected_index == 1
    current.rows[2].status = "completed"
    window.refresh(window)
    assert window.selected_id != chosen and window.feedback == ""
    assert "Requested" not in panel_text(window.notice)
    window.status_index = 2
    window.refresh(window)
    assert "has been completed" in panel_text(window.selection)
    assert "Requirements met" not in panel_text(window.selection)


def test_page_edges_and_named_rank_are_clear_and_progression_does_not_need_paging(lua):
    window, current, _ = tracker(lua)
    assert not window.buttons.previous.IsEnabled(window.buttons.previous)
    while window.buttons.next.IsEnabled(window.buttons.next):
        window.callbacks["next"]()
    assert not window.buttons.next.IsEnabled(window.buttons.next)
    assert window.buttons.previous.IsEnabled(window.buttons.previous)
    current.rank = 50000
    window.callbacks["progression"]()
    assert "Legend" in panel_text(window.progress)
    assert "Rank index" not in panel_text(window.progress)
    assert not window.checks_page.IsShown(window.checks_page)
    assert window.progress_page.IsShown(window.progress_page)
    nonempty = sum(bool(len(entries)) for entries in current.progression_groups.values())
    assert len(window.progress["items"]) == len(current.progression) + nonempty + 1
