from pathlib import Path
from xml.etree import ElementTree

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load_menu(lua):
    lua.execute("""
        menu_engine = {root='D:/AnomalyAP/appdata/', present=true, alive=true,
            valid_section=true, failure=false, creates={}, tips={}, logs={},
            feet={x=10,y=20,z=30}}
        db={actor={
            alive=function() return menu_engine.alive end,
            position=function() return menu_engine.feet end,
            level_vertex_id=function() return 101 end,
            game_vertex_id=function() return 202 end,
        }}
        getFS=function() return {update_path=function() return menu_engine.root end} end
        level={present=function() return menu_engine.present end}
        ini_sys={section_exist=function(self,section)
            assert(section=='itm_basickit'); return menu_engine.valid_section
        end}
        vector=function() return {set=function(self,x,y,z)
            self.x=x; self.y=y; self.z=z; return self
        end} end
        printf=function(format,value)
            menu_engine.logs[#menu_engine.logs+1]=string.format(format,value)
        end
        news_manager={send_tip=function(actor,id,timeout,sender,duration)
            assert(actor==db.actor and timeout==nil and sender==nil and duration==5000)
            menu_engine.tips[#menu_engine.tips+1]=id
        end}
        alife_create=function(...)
            local arguments={...}
            menu_engine.creates[#menu_engine.creates+1]=arguments
            if menu_engine.failure=='exception' then error('creation failed') end
            if menu_engine.failure then return nil end
            return {id=123}
        end
    """)
    loader = lua.globals().load_ap_module
    for name in ("actions", "mcm"):
        module = loader(str(ROOT / "mod/gamedata/scripts" / f"gamma_ap_{name}.script"))
        lua.globals()[f"gamma_ap_{name}"] = module
    return module, lua.globals().gamma_ap_actions, lua.globals().menu_engine


def test_menu_discovery_has_no_side_effect_and_localizes_its_controls(lua):
    menu, _, engine = load_menu(lua)
    definition = menu.on_mcm_load()
    assert definition.id == "gamma_archipelago" and definition.sh is True
    assert len(definition.gr) == 3
    title, description, button = definition.gr[1], definition.gr[2], definition.gr[3]
    assert title.type == "title" and description.type == "desc"
    assert button.type == "button" and button.id == "spawn_basic_tools"
    assert list(engine.creates.values()) == [] and list(engine.tips.values()) == []
    strings = ElementTree.parse(ROOT / "mod/gamedata/configs/text/eng/st_gamma_archipelago.xml")
    ids = [entry.attrib["id"] for entry in strings.getroot()]
    assert len(ids) == len(set(ids))
    assert {
        title.text,
        description.text,
        "ui_mcm_gamma_archipelago_spawn_basic_tools",
        "ui_mcm_gamma_archipelago_spawn_basic_tools_desc",
        "gamma_ap_tools_spawned",
        "gamma_ap_tools_spawn_failed",
    } <= set(ids)
    assert all(entry.findtext("text") for entry in strings.getroot())


def test_button_click_creates_exactly_one_unowned_toolkit_at_the_players_feet(lua):
    menu, _, engine = load_menu(lua)
    button = menu.on_mcm_load().gr[3]
    assert button.precondition is None
    assert button.functor[1]() is True
    created = list(engine.creates.values())
    assert len(created) == 1
    arguments = created[0]
    assert len(arguments) == 4  # No actor/owner ID or inventory insertion argument.
    assert arguments[1] == "itm_basickit" and arguments[3] == 101 and arguments[4] == 202
    assert (arguments[2].x, arguments[2].y, arguments[2].z) == (10, 20.2, 30)
    assert (engine.feet.x, engine.feet.y, engine.feet.z) == (10, 20, 30)
    assert list(engine.tips.values()) == ["gamma_ap_tools_spawned"]
    assert button.functor[1]() is True
    assert len(engine.creates) == 2  # One per explicit click, never from menu loading.


@pytest.mark.parametrize(
    "condition", ["main_menu", "no_actor", "dead", "normal_root", "other_root"]
)
def test_button_stays_visible_but_clicks_are_refused_when_unavailable(lua, condition):
    menu, actions, engine = load_menu(lua)
    if condition == "main_menu":
        engine.present = False
    elif condition == "no_actor":
        lua.globals().db.actor = None
    elif condition == "dead":
        engine.alive = False
    elif condition == "normal_root":
        engine.root = "D:/Anomaly/appdata/"
    else:
        engine.root = "D:/Other/appdata/"
    assert menu.on_mcm_load().gr[3].precondition is None
    assert actions.spawn_basic_tools() is False
    assert not list(engine.creates.values()) and not list(engine.tips.values())


def test_click_rechecks_player_state_after_the_menu_has_been_built(lua):
    menu, _, engine = load_menu(lua)
    button = menu.on_mcm_load().gr[3]
    assert button.precondition is None
    engine.alive = False
    assert button.functor[1]() is False
    assert not list(engine.creates.values())


@pytest.mark.parametrize("failure", ["missing_section", "nil", "exception"])
def test_failed_creation_reports_failure_without_false_success(lua, failure):
    _, actions, engine = load_menu(lua)
    if failure == "missing_section":
        engine.valid_section = False
    else:
        engine.failure = failure
    assert actions.spawn_basic_tools() is False
    assert len(engine.creates) == (0 if failure == "missing_section" else 1)
    assert list(engine.tips.values()) == ["gamma_ap_tools_spawn_failed"]


def test_windows_path_case_and_separators_do_not_disable_the_development_action(lua):
    _, actions, engine = load_menu(lua)
    engine.root = "D:\\ANOMALYAP\\appdata\\"
    assert actions.can_spawn() is True


def test_manual_toolkit_does_not_change_the_pilots_saved_checks_or_receipts(lua):
    _, actions, _ = load_menu(lua)
    pilot = lua.globals().load_ap_module(str(ROOT / "mod/gamedata/scripts/gamma_ap_game.script"))
    original = lua.table_from(
        {
            "session_key": "a" * 64,
            "received_count": 1,
            "checks": lua.table_from({28052001: True}),
            "applied_items": lua.table_from([28051002]),
        }
    )
    pilot.load_state(lua.table_from({"gamma_archipelago_v1": original}))
    assert actions.spawn_basic_tools() is True
    saved = lua.table()
    pilot.save_state(saved)
    result = saved.gamma_archipelago_v1
    assert result.session_key == original.session_key and result.received_count == 1
    assert dict(result.checks.items()) == {28052001: True}
    assert list(result.applied_items.values()) == [28051002]


def test_engine_bin_parent_path_is_the_same_development_appdata(lua):
    _, actions, engine = load_menu(lua)
    engine.root = "d:/anomalyap/bin/..\\appdata\\"
    assert actions.can_spawn() is True


def test_mcm_always_displays_the_button_even_when_opened_before_loading_a_save(lua):
    menu, _, engine = load_menu(lua)
    engine.present = False
    button = menu.on_mcm_load().gr[3]
    assert button.precondition is None
