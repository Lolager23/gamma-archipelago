import pytest

from .test_tracker import state_for


def menu(lua, **values):
    state = state_for(lua, ap_start=1, **values)
    lua.globals().configuration = state.configuration
    lua.execute("""
        engine={creation={},starts=0,delegate_calls=0}
        level={name=function() return 'l01_escape' end}
        game={translate_string=function(key)
            if key=='gamma_ap_start_locked' then return 'AP start: %s' end
            return key
        end}
        CUIMessageBoxEx=function() return {InitMessageBox=function() end,
            SetText=function(self,value) engine.warning=value end,ShowDialog=function() end} end
        ini_file=function() return {section_exist=function() return not engine.missing end} end
        axr_main={config={r_value=function(self,s,k) return engine.creation[k] end,
            w_value=function(self,s,k,v) engine.creation[k]=v end}}
        ui_mm_faction_select={UINewGame={
            LoadFaction=function(self,random,faction)
                self.selected_faction=faction;return 'faction' end,
            LoadMap=function(self) engine.delegate_calls=engine.delegate_calls+1;return 'map' end,
            OnSelectMap=function(self) return 'select' end,
            OnFactionClicked=function(self) return 'popup' end,
            OnStartGame=function(self)
                engine.starts=engine.starts+1;engine.start_map=self.selected_map
                return 'started'
            end}}
        window={list_map={ClearList=function() end,AddItem=function() end,
            SetText=function(self,text) engine.map_label=text end},UpdateMap=function() end,
            ck_warfare={SetCheck=function(self,value) engine.warfare=value end},
            ck_story={SetCheck=function(self,value) engine.story=value end}}
        setmetatable(window,{__index=ui_mm_faction_select.UINewGame})
    """)
    module = lua.globals().gamma_ap_start_menu
    assert module.install(lua.eval("function() return configuration end")) is True
    return lua.globals().window, lua.globals().engine


@pytest.mark.parametrize(
    "location,key", [(0, "rookie_village"), (1, "hidden_base"), (2, "lodging_house")]
)
def test_faction_and_location_are_fixed_before_the_native_start(lua, location, key):
    window, engine = menu(lua, starting_location=location, goal=4)
    assert window.LoadFaction(window, True, "monolith") == "faction"
    assert window.selected_faction == "stalker"
    window.LoadMap(window, True)
    assert window.selected_map == key and window.table_map[2] == key
    window.OnSelectMap(window)
    assert window.OnFactionClicked(window) is False and engine.warning.startswith("AP start")
    assert window.OnStartGame(window) == "started"
    assert engine.start_map == key and engine.story is True and engine.warfare is False


def test_start_requires_companion_and_supported_native_preset(lua):
    window, engine = menu(lua)
    lua.globals().configuration = None
    assert window.OnStartGame(window) is False
    assert engine.warning == "gamma_ap_start_required" and engine.starts == 0
    _, engine = menu(lua)
    window = lua.globals().window
    engine.missing = True
    assert window.OnStartGame(window) is False and engine.starts == 0
    lua.globals().configuration.options.starting_location = 3
    assert window.OnStartGame(window) is False


def test_legacy_configurations_delegate_and_late_wrappers_remain_composable(lua):
    window, engine = menu(lua)
    lua.globals().configuration.options.ap_start = 0
    assert window.LoadMap(window) == "map"
    assert window.OnFactionClicked(window) == "popup"
    assert window.OnSelectMap(window) == "select"
    assert window.OnStartGame(window) == "started"
    module = lua.globals().gamma_ap_start_menu
    assert module.install(lua.eval("function() return configuration end")) is True
    lua.execute("""
        local old=ui_mm_faction_select.UINewGame.LoadMap
        ui_mm_faction_select.UINewGame.LoadMap=function(...) return old(...) end
    """)
    assert module.install(lua.eval("function() return configuration end")) is True
    assert window.LoadMap(window) == "map" and engine.delegate_calls == 2
    lua.globals().ui_mm_faction_select = None
    assert module.install(None) is False
    lua.globals().ui_mm_faction_select = lua.table(UINewGame=lua.table())
    assert module.install(None) is False


def test_preparation_uses_the_native_creation_config_and_rejects_wrong_spawn(lua):
    menu(lua, starting_location=1, goal=4)
    start = lua.globals().gamma_ap_start
    config = lua.globals().configuration
    engine = lua.globals().engine
    assert start.prepare(config) == (True, False)
    engine.creation.new_game_faction = "monolith"
    assert start.prepare(config) == (True, True)
    assert engine.creation.new_game_faction == "stalker"
    assert engine.creation.new_game_map == "hidden_base" and engine.creation.new_game_story_mode
    state = state_for(lua, ap_start=1, starting_location=1)
    assert start.validate(state)[0] is False
    state.loadout_prepared = True
    assert start.validate(state)[0] is False
    lua.globals().level = lua.table(name=lua.eval("function() return 'k00_marsh' end"))
    assert start.validate(state) is True
    config.options.starting_location = 3
    assert start.prepare(config)[0] is False
    state.configuration = config
    assert start.validate(state)[0] is False
    config.options.ap_start = 0
    assert start.prepare(config) == (True, False)
    assert start.validate(state) is True
    assert start.level_name(None) == "l01_escape"


def test_coordinator_prepares_the_selected_ap_start_before_native_loadout_grants(lua):
    from .test_loadout import configured_game
    from .test_stashes import progress

    game, engine, _ = configured_game(lua, ap_start=1, starting_location=0, goal=4)
    engine.creation.new_game_faction = "monolith"
    game.on_game_start()
    assert engine.creation.new_game_faction == "stalker"
    assert engine.creation.new_game_map == "rookie_village"
    assert engine.creation.new_game_story_mode is True
    assert progress(lua, game).loadout_prepared


def test_legacy_quick_start_does_not_require_story_controls(lua):
    window, engine = menu(lua, quest_zone_logic=0)
    window.ck_story = None
    window.ck_warfare = None
    assert window.OnStartGame(window) == "started"
    assert engine.story is None


@pytest.mark.parametrize(
    "values",
    [
        {"goal": 7},
        {"goal": 8},
        {"checks_story_milestones": 1},
        {"checks_mortal_sin": 1},
        {"checks_operation_afterglow": 1},
    ],
)
def test_independent_story_checks_and_new_goals_enable_story_mode_before_start(lua, values):
    window, engine = menu(lua, **values)
    assert window.OnStartGame(window) == "started"
    assert engine.story is True
    engine.creation.new_game_faction = "stalker"
    assert lua.globals().gamma_ap_start.prepare(lua.globals().configuration) == (True, True)
    assert engine.creation.new_game_story_mode is True


def test_required_story_start_refuses_a_missing_native_story_control(lua):
    window, engine = menu(lua, goal=8)
    window.ck_story = None
    assert window.OnStartGame(window) is False
    assert engine.starts == 0 and engine.warning == "gamma_ap_start_unsupported"
