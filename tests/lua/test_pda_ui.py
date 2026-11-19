from pathlib import Path

from .test_tracker import state_for, view

ROOT = Path(__file__).resolve().parents[2]


def load_ui(lua):
    lua.execute("""
        super=function() end
        clock=1000; time_global=function() return clock end
        CUIScriptWnd={SetWndRect=function() end, Register=function() end, Update=function() end,
            AddCallback=function(self,name,event,callback)
                self.callbacks=self.callbacks or {}; self.callbacks[name]=callback end}
        class=function(name) return function(base)
            local env=getfenv(2); local cls={}; cls.__index=cls
            setmetatable(cls,{__index=base,__call=function()
                local self=setmetatable({},cls); self:__init(); return self end}); env[name]=cls
        end end
        Frect=function() return {set=function(self) return self end} end
        CScriptXmlInit=function() return {ParseFile=function() end,
            InitTextWnd=function() return {SetText=function(self,text) self.text=text end} end,
            Init3tButton=function() local text={SetText=function(self,value) self.text=value end}
                return {TextControl=function() return text end} end} end
        game={translate_string=function(key) return key end}
        ui_events={BUTTON_CLICKED=1}
        pda={set_active_subdialog=function(section) return 'original:'..section end}
        callbacks={}; RegisterScriptCallback=function(name,callback) callbacks[name]=callback end
    """)
    module = lua.globals().load_ap_module(str(ROOT / "mod/gamedata/scripts/gamma_ap_pda.script"))
    lua.globals().gamma_ap_pda = module
    return module


def test_tab_preserves_delegates_refreshes_filters_and_bounds_all_pages(lua):
    module = load_ui(lua)
    lua.globals().gamma_ap_game = lua.table(tracker_view=lambda: view(lua, state_for(lua)))
    assert module.install() is True
    assert module.install() is True
    assert lua.globals().pda.set_active_subdialog("eptTasks") == "original:eptTasks"
    window = lua.globals().pda.set_active_subdialog("eptArchipelago")
    assert "Rewards applied" in window.summary.text
    window.Update(window)
    window.Update(window)
    lua.globals().clock = 2000
    window.Update(window)
    for name in ("region", "status", "next", "previous", "refresh", "progress_next"):
        window.callbacks[name]()
    window.region_index = 999
    window.progress_offset = 999
    window.refresh(window)
    assert window.region_index == 1 and window.progress_offset == 1
    assert lua.eval("rawequal")(module.get_ui(), window)
    lua.globals().game.translate_string = lambda key: "Localized"
    assert module.label("all", "fallback") == "Localized"
    lua.globals().pda = None
    assert module.install() is False
    module.on_game_start()
    assert lua.globals().callbacks.on_game_load is not None


def test_disabled_and_unbound_views_do_not_retain_previous_seed_rows(lua):
    module = load_ui(lua)
    lua.globals().gamma_ap_game = lua.table(
        tracker_view=lambda: view(lua, state_for(lua, pda_tracker=0))
    )
    window = module.get_ui()
    assert "disabled" in window.summary.text
    assert window.details.text == "" and window.progress.text == ""
    state = state_for(lua)
    state.session_key = None
    lua.globals().gamma_ap_game.tracker_view = lambda: view(lua, state)
    window.refresh(window)
    assert "matching AP" in window.summary.text


def test_scout_selection_and_next_milestone_rewards_are_displayed_from_metadata(lua):
    module = load_ui(lua)
    state = state_for(lua)
    current = view(lua, state)
    current.scouted = lua.table_from({28052001: lua.table(item="Toolkit", player="Friend")})
    current.previews = lua.table_from(
        [
            lua.table(id=28052001, label="Next side-task reward"),
            lua.table(id=28052002, label="Next faction-standing reward"),
        ]
    )
    requested = []

    def request(identity):
        requested.append(identity)
        return True, "Requested"

    lua.globals().gamma_ap_game = lua.table(tracker_view=lambda: current, request_scout=request)
    window = module.get_ui()
    assert "Toolkit -> Friend" in window.details.text
    assert "Waiting for scouting data" in window.progress.text
    window.callbacks["select"]()
    window.callbacks["scout"]()
    assert requested == [28052002]
    assert "Requested" in window.summary.text


def test_dxml_adds_one_tab_without_replacing_existing_tabs_and_is_idempotent(lua):
    module = lua.globals().load_ap_module(
        str(ROOT / "mod/gamedata/scripts/modxml_gamma_ap_pda.script")
    )
    lua.execute("""
        tab={attrs={width='550'},kids={}}
        first={attrs={id='eptTasks',x='0',width='79'}}
        last={attrs={id='eptLogs',x='476',width='79'}}
        buttons={first,last}; inserted=0
        xml={query=function(self,path) if path=='tab' then return {tab} else return buttons end end,
            getElementAttr=function(self,node) return node.attrs end,
            setElementAttr=function(self,node,values)
                for k,v in pairs(values) do node.attrs[k]=v end end,
            insertFromXMLString=function(self,text,parent,index) inserted=inserted+1;
                assert(text:find('eptArchipelago'));
                buttons[#buttons+1]={attrs={id='eptArchipelago'}} end}
    """)
    module.patch("ui/other.xml", lua.globals().xml)
    module.patch("ui/pda_16.xml", lua.globals().xml)
    assert lua.globals().inserted == 1
    assert lua.globals().last.attrs.x + lua.globals().last.attrs.width == 514
    module.patch("ui/pda_16.xml", lua.globals().xml)
    assert lua.globals().inserted == 1
    lua.execute("buttons={first}; tab.attrs.width=100")
    module.patch("ui/pda.xml", lua.globals().xml)
    lua.execute("tab.attrs.width=550; first.attrs.x=0; first.attrs.width=0")
    module.patch("ui/pda_219.xml", lua.globals().xml)
    lua.execute("xml.query=function() return {} end")
    module.patch("ui/pda_16.xml", lua.globals().xml)
    lua.execute("RegisterScriptCallback=function(name,callback) assert(name=='on_xml_read') end")
    module.on_xml_read()
