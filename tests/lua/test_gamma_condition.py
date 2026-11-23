import pytest

from .test_equipment_checks import equipment_game, gear
from .test_equipment_classes import fresh, native
from .test_workshop import poll, state_of


def parts_api(lua, values):
    lua.execute("""
        arti_jamming={has_parts=function() return true end}
        part_rows={};part_names='barrel, bolt';read_calls=0
        item_parts={get_parts_con=function(object,id,evaluate)
            assert(id==nil and evaluate==false);read_calls=read_calls+1
            if part_error then error('parts unavailable') end
            return part_rows
        end}
        itms_manager={ini_parts={r_string_ex=function(self,section,key)
            assert(section=='con_parts_list' and key=='smg_base');return part_names
        end}}
    """)
    lua.globals().part_rows = lua.table_from(values)


@pytest.mark.parametrize(
    "values,minimum,expected",
    [
        ({"barrel": 20, "bolt": 40}, 65, False),
        ({"barrel": 64, "bolt": 66}, 65, True),
        ({"barrel": 64.9, "bolt": 64.9}, 65, False),
        ({"barrel": 100, "bolt": 100}, 100, True),
        ({"barrel": 99, "bolt": 100}, 100, False),
        ({"barrel": 0, "bolt": 0}, 0, False),
        ({"barrel": 1, "bolt": 0}, 0, True),
        ({"barrel": -1, "bolt": 100}, 65, False),
        ({"barrel": 100}, 65, False),
        ({"barrel": "65", "bolt": 65}, 65, False),
        ({"barrel": float("nan"), "bolt": 65}, 65, False),
        ({"barrel": float("inf"), "bolt": 65}, 65, False),
        ({"barrel": -2, "bolt": 100}, 65, False),
        ({"barrel": -0.5, "bolt": 100}, 65, False),
    ],
)
def test_firearm_threshold_uses_mean_of_native_parts_not_forced_engine_condition(
    lua, values, minimum, expected
):
    state = fresh(lua, equipment_check_condition=minimum)
    module = native(lua)
    lua.globals().metadata.smg = lua.table(
        kind="w_smg", repair_type="pistol", parent_section="smg_base"
    )
    parts_api(lua, values | {"smg_base": 83, "unrelated": 100})
    item = lua.table(
        section=lua.eval("function() return 'smg' end"),
        condition=lua.eval("function() return .83 end"),
    )
    assert module.usable_condition(state, item) is expected
    assert lua.globals().read_calls == 1


@pytest.mark.parametrize(
    "setup",
    [
        "arti_jamming.has_parts=nil",
        "arti_jamming.has_parts=function() error('unavailable') end",
        "itms_manager=nil",
        "item_parts=nil",
        "part_error=true",
        "part_rows=nil",
        "part_rows='partial'",
        "part_names=nil",
        "part_names=''",
        "part_names='barrel,barrel'",
        "part_names=string.rep('x',513)",
        "part_names='a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q';part_rows={};"
        "for name in part_names:gmatch('[^,]+') do part_rows[name]=100 end",
    ],
)
def test_unavailable_or_invalid_gamma_parts_never_fall_back_to_forced_83_percent(lua, setup):
    state = fresh(lua)
    module = native(lua)
    lua.globals().metadata.smg_base = lua.table(kind="w_smg", repair_type="pistol")
    parts_api(lua, {"barrel": 100, "bolt": 100})
    lua.execute(setup)
    item = lua.table(
        section=lua.eval("function() return 'smg_base' end"),
        condition=lua.eval("function() return .83 end"),
    )
    assert module.usable_condition(state, item) is False


def test_partless_firearms_legacy_sessions_and_armour_keep_native_condition(lua):
    state = fresh(lua)
    module = native(lua)
    lua.globals().metadata.smg_base = lua.table(kind="w_smg")
    parts_api(lua, {})
    lua.execute("arti_jamming.has_parts=function() return false end")
    item = lua.table(
        section=lua.eval("function() return 'smg_base' end"),
        condition=lua.eval("function() return .65 end"),
    )
    assert module.usable_condition(state, item)
    lua.execute("arti_jamming.has_parts=function() error('must not read armour') end")
    lua.globals().metadata.smg_base.kind = "o_light"
    assert module.usable_condition(state, item)
    state.configuration.options.equipment_class_progression = 0
    lua.globals().metadata.smg_base.kind = "w_smg"
    assert module.usable_condition(state, item)
    assert lua.globals().read_calls == 0


def test_smg_and_repair_grade_checks_wait_for_average_parts_to_reach_threshold(lua):
    game, engine, _ = equipment_game(
        lua,
        checks_weapon_tiers=1,
        content_progression=1,
        equipment_class_progression=1,
        rewards_starting_gear_unlocks=1,
        playability_logic=0,
    )
    lua.execute("ini_sys.section_exist=function() return true end")
    game.on_game_start()
    engine.creation.new_game_faction = None
    poll(game, engine)
    engine.active = gear(lua, 50, "smg", "w_smg", 0.83)
    engine.meta.smg.repair_type = "pistol"
    engine.meta.smg.parent_section = "smg_base"
    parts_api(lua, {"barrel": 20, "bolt": 40, "smg_base": 83})
    module = lua.globals().gamma_ap_equipment_checks
    state = state_of(lua, game)
    assert module.poll(state, state.configuration)
    assert not state.checks[28052751]
    smg = lua.globals().gamma_ap_catalog.weapon_locations.smg
    assert not state.checks[smg]
    lua.globals().part_rows.barrel = 64
    lua.globals().part_rows.bolt = 66
    assert module.poll(state, state.configuration)
    assert state.checks[smg] and state.checks[28052751]
    lua.globals().part_rows.barrel = 1
    assert module.poll(state, state.configuration)
    assert state.checks[smg]  # Earned checks remain monotonic after deterioration.
