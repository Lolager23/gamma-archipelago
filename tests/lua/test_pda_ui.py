from pathlib import Path
from xml.etree import ElementTree

import pytest

from .test_tracker import state_for, view

ROOT = Path(__file__).resolve().parents[2]


def load_ui(lua, *, xml_filename="gamma_ap_pda.xml", strings_filename="st_gamma_ap_pda.xml"):
    root = ElementTree.parse(ROOT / "mod/gamedata/configs/ui" / xml_filename).getroot()
    nodes = {}

    def record(element, prefix=""):
        name = prefix + element.tag
        nodes[name] = lua.table_from(element.attrib)
        text = element.find("text")
        nodes[name].initial_text = text.text if text is not None else None
        for child in element:
            if child.tag != "text":
                record(child, name + ":")

    for element in root:
        record(element)
    lua.globals().xml_nodes = lua.table_from(nodes)
    lua.globals().translations = lua.table_from(
        {
            node.get("id"): node.findtext("text")
            for node in ElementTree.parse(
                ROOT / "mod/gamedata/configs/text/eng" / strings_filename
            ).getroot()
        }
    )
    lua.execute(r"""
        super=function() end
        clock=1000; time_global=function() return clock end
        local methods={}
        methods.SetWndSize=function(self,size) self.width,self.height=size.x,size.y end
        methods.SetWndPos=function(self,pos) self.x,self.y=pos.x,pos.y end
        methods.GetWidth=function(self) return self.width end
        methods.GetHeight=function(self) return self.height end
        methods.Show=function(self,value) self.shown=value end
        methods.IsShown=function(self) return self.shown~=false end
        methods.Enable=function(self,value)
            assert(type(value)=='boolean','native Enable expects a boolean')
            self.enabled=value
        end
        methods.IsEnabled=function(self) return self.enabled~=false end
        methods.SetTextColor=function(self,value) self.color=value end
        methods.OnMouse=function(self,x,y,event) self.delegated_mouse=event; return false end
        methods.GetAbsoluteRect=function(self,rect)
            local x,y=self.x,self.y
            local parent=self.parent
            while parent do x=x+parent.x; y=y+parent.y; parent=parent.parent end
            rect:set(x,y,x+self.width,y+self.height)
        end
        methods.SetText=function(self,text,...)
            assert(select('#',...)==0,'native SetText accepts exactly one string')
            self.text=text
        end
        methods.GetText=function(self) return self.text or "" end
        methods.SetTextComplexMode=function(self,value) self.complex=value end
        methods.AdjustHeightToText=function(self)
            assert(self.complex)
            local count=0
            local newline=string.char(92)..'n'
            for line in (self.text..newline):gmatch('(.-)'..newline) do
                count=count+math.max(1,math.ceil(#line/math.max(1,math.floor(self.width/8))))
            end
            self.height=16*count
        end
        methods.Register=function() end
        methods.Update=function(self)
            assert(not self.lua_owner or self.lua_owner[1],
                'native Update reached a Lua-collected window')
            for _,child in ipairs(self.children or {}) do methods.Update(child) end
            for _,child in ipairs(self.items or {}) do methods.Update(child) end
        end
        methods.AddCallback=function(self,name,event,callback)
            self.callbacks=self.callbacks or {}; self.callbacks[name]=callback
        end
        methods.Clear=function(self)
            self.items={}; self.position=0; self.selected=-1; self.cleared=(self.cleared or 0)+1
        end
        methods.AddWindow=function(self,row,owned)
            assert(owned and row.width<=self.width)
            -- The native binding stores a pointer but has no luabind adopt policy.
            row=row.native_pointer or row
            local previous=self.items[#self.items]
            row.y=previous and previous.y+previous.height+self.interval or 0
            self.items[#self.items+1]=row
        end
        methods.GetCurrentScrollPos=function(self) return self.position end
        methods.SetScrollPos=function(self,value) self.position=value end
        methods.ScrollToBegin=function(self) self.position=0 end
        local function native_window()
            return setmetatable({children={}}, {__index=methods})
        end
        methods.ShowSelectedItem=methods.Show -- The native binding aliases Show, not selection.
        methods.GetSelectedIndex=function(self) return self.selected or -1 end
        methods.SetSelectedIndex=function(self,value)
            if self.can_select then self.selected=value end
        end
        methods.AddTextItem=function(self,value)
            -- Native factory: returned handles do not own/delete the native row.
            local row,text=native_window(),native_window()
            row.width,row.height=self.width-20,48
            text.width,text.height,text.text=row.width,16,value
            row.children[1]=text; row.GetTextItem=function() return text end
            methods.AddWindow(self,row,true)
            text_controls[#text_controls+1]=text
            return row
        end
        CUIWindow=function()
            local native=native_window()
            local handle=setmetatable({native_pointer=native}, {
                __index=native,__newindex=function(_,key,value) native[key]=value end})
            native.lua_owner=setmetatable({handle}, {__mode='v'})
            return handle
        end
        CUIScriptWnd=methods
        vector2=function() return {set=function(self,x,y) self.x,self.y=x,y; return self end} end
        cursor={x=0,y=0}; GetCursorPosition=function() return cursor end
        Frect=function() return {set=function(self,x1,y1,x2,y2)
            self.x1,self.y1,self.x2,self.y2=x1,y1,x2,y2; return self end} end
        class=function(name) return function(base)
            local env=getfenv(2); local cls={}; cls.__index=cls
            setmetatable(cls,{__index=base,__call=function()
                local self=setmetatable({children={}},cls); self:__init(); return self
            end}); env[name]=cls
        end end
        text_controls={}
        local function init(node,parent,target)
            local attr=assert(xml_nodes[node],node)
            local control=target or native_window()
            control.node=node
            control.x,control.y=tonumber(attr.x) or 0,tonumber(attr.y) or 0
            control.width,control.height=tonumber(attr.width),tonumber(attr.height)
            if parent then parent.children[#parent.children+1]=control; control.parent=parent end
            if attr.initial_text then control.text=game.translate_string(attr.initial_text) end
            return control
        end
        CScriptXmlInit=function() return {ParseFile=function() end,
            InitWindow=function(self,node,index,target) assert(index==0); init(node,nil,target) end,
            InitScrollView=function(self,node,parent)
                local control=init(node,parent); control.items={}; control.position=0
                control.interval=tonumber(xml_nodes[node].vert_interval) or 0
                return control
            end,
            InitListBox=function(self,node,parent)
                local control=init(node,parent); control.items={}; control.position=0
                control.interval=tonumber(xml_nodes[node].vert_interval) or 0
                control.can_select=tonumber(xml_nodes[node].can_select)==1
                return control
            end,
            InitTextWnd=function(self,node,parent)
                local control=init(node,parent); text_controls[#text_controls+1]=control
                return control
            end,
            InitEditBox=function(self,node,parent) return init(node,parent) end,
            InitStatic=function(self,node,parent) return init(node,parent) end,
            Init3tButton=function(self,node,parent)
                local button=init(node,parent); local text=native_window()
                button.TextControl=function() return text end; return button
            end} end
        game={translate_string=function(key) return translations[key] or key end}
        ui_events={BUTTON_CLICKED=10,LIST_ITEM_CLICKED=35,WINDOW_RBUTTON_DOWN=1,
            WINDOW_RBUTTON_UP=4,WINDOW_LBUTTON_DOWN=0}
        pda={set_active_subdialog=function(section) return 'original:'..section end}
        callbacks={}; RegisterScriptCallback=function(name,callback) callbacks[name]=callback end
    """)
    module = lua.globals().load_ap_module(str(ROOT / "mod/gamedata/scripts/gamma_ap_pda.script"))
    lua.globals().gamma_ap_pda = module
    return module


def panel_text(panel):
    def texts(control):
        return ([control.text] if control.text else []) + [
            text for child in control.children.values() for text in texts(child)
        ]

    return "\n".join(text for item in panel["items"].values() for text in texts(item))


def test_native_text_parser_does_not_receive_raw_newlines_that_merge_rows(lua):
    module = load_ui(lua)
    lua.globals().gamma_ap_game = lua.table(tracker_view=lambda: view(lua, state_for(lua)))
    module.get_ui()
    controls = list(lua.globals().text_controls.values())
    assert controls
    assert all("\n" not in (control.text or "") for control in controls)


@pytest.mark.parametrize("aspect", [4 / 3, 16 / 9, 21 / 9])
def test_page_content_starts_below_native_pda_tabs(aspect):
    # The custom tab is attached to the PDA background at y=-34; tabs are y=23,h=27.
    root = ElementTree.parse(ROOT / "mod/gamedata/configs/ui/gamma_ap_pda.xml").getroot()
    main = root.find("main")
    origin = float(main.get("y")) if main is not None else 0
    summary = root.find("summary")
    scale = (768 / aspect) / 1024
    assert (origin + float(summary.get("y")) - 34) * scale >= (23 + 27 + 8) * scale


def test_tab_preserves_delegates_refreshes_filters_and_bounds_all_pages(lua):
    module = load_ui(lua)
    lua.globals().gamma_ap_game = lua.table(tracker_view=lambda: view(lua, state_for(lua)))
    assert module.install() is True
    assert module.install() is True
    assert lua.globals().pda.set_active_subdialog("eptTasks") == "original:eptTasks"
    window = lua.globals().pda.set_active_subdialog("eptArchipelago")
    assert "Rewards applied" in panel_text(window.summary)
    window.Update(window)
    window.Update(window)
    lua.globals().clock = 2000
    window.Update(window)
    for name in ("region", "status", "next", "previous", "refresh", "progression", "checks"):
        window.callbacks[name]()
    window.region_index = 999
    window.refresh(window)
    assert window.region_index == 1
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
    assert "disabled" in panel_text(window.summary)
    assert not list(window.details["items"].values())
    assert not list(window.progress["items"].values())
    state = state_for(lua)
    state.session_key = None
    lua.globals().gamma_ap_game.tracker_view = lambda: view(lua, state)
    window.refresh(window)
    assert "matching AP" in panel_text(window.summary)


def test_scout_selection_and_next_milestone_rewards_are_displayed_from_metadata(lua):
    module = load_ui(lua)
    state = state_for(lua)
    current = view(lua, state)
    current.scouting_enabled = True
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
    assert "Reward: Toolkit | Recipient: Friend" in panel_text(window.selection)
    assert "Waiting for scouting data" in panel_text(window.progress)
    window.details.SetSelectedIndex(window.details, 1)
    window.callbacks["check_list"]()
    window.callbacks["scout"]()
    assert requested == [28052002]
    assert "Requested" in panel_text(window.notice)


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
