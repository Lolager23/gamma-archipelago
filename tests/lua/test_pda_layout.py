from xml.etree import ElementTree

import pytest

from .test_pda_ui import ROOT, load_ui, panel_text
from .test_tracker import state_for, view


def test_long_check_names_grow_clickable_rows_and_keep_reward_details_in_their_own_view(lua):
    module = load_ui(lua)
    current = view(lua, state_for(lua))
    current.rows[1].region = "A long translated settlement name " * 6
    current.rows[1].name = "A long translated quest name " * 30
    current.rows[1].reason = "Requirement with CRLF\r\nand a second line\rand third\nline " * 6
    current.scouted = lua.table_from(
        {current.rows[1].id: lua.table(item="Lengthy reward " * 15, player="Player " * 10)}
    )
    lua.globals().gamma_ap_game = lua.table(tracker_view=lambda: current)
    window = module.get_ui()
    row = window.details["items"][1]
    text = row.children[1]
    assert text.height > 16 and row.height > text.y + text.height
    assert text.x + text.width <= row.width
    assert "\\n" in text.text and "\n" not in text.text
    reason, reward = window.selection["items"].values()
    assert "\\n" in reason.text and "\n" not in reason.text
    assert reward.y > reason.y + reason.height
    assert reward.y + reward.height > window.selection.height
    following = window.details["items"][2]
    assert following.y > row.y + row.height
    assert row.y + row.height > window.details.height  # Native scrolling contains overflow.


def test_summary_and_progression_are_separate_wrapping_scroll_rows(lua):
    module = load_ui(lua)
    current = view(lua, state_for(lua))
    current.problem = "A lengthy engine problem with a line break\n" * 20
    current.delivery = "Pending supplies\nStill waiting"
    current.goal_complete = True
    current.progression = lua.table_from(["Very long progression permission " * 12] * 15)
    current.progression_groups = None  # Retain display compatibility with older view snapshots.
    lua.globals().gamma_ap_game = lua.table(tracker_view=lambda: current)
    window = module.get_ui()
    assert "Completed" in panel_text(window.summary)
    assert len(window.summary["items"]) == 3
    assert len(window.notice["items"]) == 2
    assert len(window.progress["items"]) == 17
    for panel in (window.notice, window.progress):
        rows = list(panel["items"].values())
        assert rows[-1].y + rows[-1].height > panel.height
        for first, second in zip(rows, rows[1:], strict=False):
            assert second.y > first.y + first.height
        assert all(row.complex and "\n" not in row.text for row in rows)
    window.progress.position = 100
    window.callbacks["progression"]()
    assert window.progress.position == 100
    assert window.progress_page.IsShown(window.progress_page)
    assert not window.checks_page.IsShown(window.checks_page)
    window.callbacks["checks"]()
    assert not window.progress_page.IsShown(window.progress_page)


@pytest.mark.parametrize("section", ["summary", "details", "selection", "progress", "notice"])
def test_refresh_preserves_scroll_and_does_not_recreate_unchanged_widgets(lua, section):
    module = load_ui(lua)
    current = view(lua, state_for(lua))
    lua.globals().gamma_ap_game = lua.table(tracker_view=lambda: current)
    window = module.get_ui()
    panel = window[section]
    panel.position = 42
    clears = panel.cleared
    window.refresh(window)
    assert panel.position == 42 and panel.cleared == clears
    if section == "summary":
        current.completed += 1
    elif section == "details":
        current.rows[1].name = "Changed check name"
    elif section == "selection":
        current.rows[1].reason = "Changed access requirements"
    elif section == "notice":
        current.connection_status = "Connected"
    else:
        current.kills += 1
    window.refresh(window)
    assert panel.position == 42 and panel.cleared == clears + 1
    if section == "details":
        window.callbacks["next"]()
        assert panel.position == 0


def test_rebinding_clears_stale_rows_selection_and_cache_before_showing_the_new_view(lua):
    module = load_ui(lua)
    current = view(lua, state_for(lua))
    current.stash_delivery = "A stash delivery"
    lua.globals().gamma_ap_game = lua.table(tracker_view=lambda: current)
    window = module.get_ui()
    assert "A stash delivery" in panel_text(window.notice)
    current.bound = False
    window.refresh(window)
    assert window.selected_id is None and not len(window.details["items"])
    assert all(not len(window[name]["items"]) for name in ("progress", "selection", "notice"))
    assert window.page.text == "" and not window.buttons.scout.IsEnabled(window.buttons.scout)
    current.bound = True
    window.refresh(window)
    assert window.selected_id == current.rows[1].id and len(window.details["items"]) > 0


def test_multiline_field_boundaries_cannot_collide_in_the_refresh_cache(lua):
    module = load_ui(lua)
    lua.globals().gamma_ap_game = lua.table(tracker_view=lambda: view(lua, state_for(lua)))
    window = module.get_ui()
    window.render_text(window, "summary", lua.table_from(["A\nB", "C"]))
    assert window.summary["items"][1].text == "A\\nB"
    window.render_text(window, "summary", lua.table_from(["A", "B\nC"]))
    assert window.summary["items"][1].text == "A"
    assert window.summary["items"][2].text == "B\\nC"


def test_xml_viewports_and_buttons_are_bounded_and_do_not_overlap():
    root = ElementTree.parse(ROOT / "mod/gamedata/configs/ui/gamma_ap_pda.xml").getroot()
    main = root.find("main")

    def check(nodes, width, height):
        boxes = []
        for node in nodes:
            x, y, w, h = (float(node.get(key)) for key in ("x", "y", "width", "height"))
            assert x >= 0 and y >= 0 and x + w <= width and y + h <= height
            boxes.append((node.tag, x, y, x + w, y + h))
        for index, first in enumerate(boxes):
            for second in boxes[index + 1 :]:
                assert not (
                    first[1] < second[3]
                    and second[1] < first[3]
                    and first[2] < second[4]
                    and second[2] < first[4]
                ), (first[0], second[0])

    # The two pages intentionally share a rectangle and are mutually exclusive.
    common = [node for node in root if node.tag != "main" and not node.tag.endswith("_row")]
    for page in ("checks_page", "progress_page"):
        check(
            [node for node in common if not node.tag.endswith("_page") or node.tag == page],
            float(main.get("width")),
            float(main.get("height")),
        )
        parent = root.find(page)
        check(list(parent), float(parent.get("width")), float(parent.get("height")))
