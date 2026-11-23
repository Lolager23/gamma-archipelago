import pytest

from .test_equipment_checks import equipment_game, gear
from .test_loadout import configured_game
from .test_start_menu import menu
from .test_tool_permissions import kit_game
from .test_tracker import state_for
from .test_workshop import poll, state_of


def fresh(lua, **options):
    return state_for(
        lua, **({"equipment_class_progression": 1, "rewards_starting_gear_unlocks": 1} | options)
    )


def native(lua):
    lua.execute("""
        metadata={}
        ini_sys={r_string_ex=function(self,section,key) return (metadata[section] or {})[key] end,
            section_exist=function() return true end}
    """)
    return lua.globals().gamma_ap_equipment_classes


@pytest.mark.parametrize(
    "section", ["helm_bandana", "helm_cloth_mask", "helm_rp_bala", "helm_resp"]
)
@pytest.mark.parametrize("initial,allowed", [(0, False), (1, True)])
def test_gamma_novice_masks_use_light_helmet_permission(lua, section, initial, allowed):
    state = fresh(lua, initial_helmet_class=initial)
    module = native(lua)
    # GAMMA's enabled helmet repair-kit override uses an outfit repair type here.
    lua.globals().metadata[section] = lua.table(
        **{"class": "E_HLMET", "kind": "o_helmet", "repair_type": "outfit_novice"}
    )
    assert lua.globals().gamma_ap_equipment.group(section) == "helmet"
    assert module.section_tier(section, "helmet") == 1
    assert module.section_allowed(state, section) is allowed
    for repair, tier in [
        ("helmet_medium", 2),
        ("helmet_heavy", 3),
        ("helmet_exo", 4),
        ("unknown", 4),
    ]:
        lua.globals().metadata.other_helmet = lua.table(kind="o_helmet", repair_type=repair)
        assert module.section_tier("other_helmet", "helmet") == tier
        assert module.section_allowed(state, "other_helmet") is False


@pytest.mark.parametrize(
    "group,section,kind,repair,tier",
    [
        ("firearms", "rifle", "w_rifle", "rifle_5", 3),
        ("outfit", "suit", "o_medium", "outfit_medium", 3),
        ("helmet", "helmet", "o_helmet", "helmet_heavy", 3),
        ("backpack", "equ_military_pack", "i_backpack", "", 4),
    ],
)
def test_class_permission_depends_on_initial_tier_and_saved_receipts(
    lua, group, section, kind, repair, tier
):
    state = fresh(lua)
    module = native(lua)
    lua.globals().metadata[section] = lua.table(kind=kind, repair_type=repair)
    row = lua.globals().gamma_ap_catalog.equipment_classes.groups[group]
    assert module.section_tier(section, group) == tier
    assert module.level(state, group) == 1
    assert module.section_allowed(state, section) is False
    for index in range(1, tier):
        state.applied_items[index] = row.item_id
    assert module.level(state, group) == tier
    assert module.section_allowed(state, section) is True
    assert module.permitted(state, "melee") and module.permitted(state, "tools")
    assert module.item_enabled(state.configuration, row.item_id)
    assert not module.item_enabled(state.configuration, 28051604)
    assert module.item_enabled(state.configuration, 28051001)
    assert module.section_tier("unrecognised", group) == len(list(row.labels))
    assert module.section_tier("unclassified", "unknown") == 0
    assert module.level(state, "unknown") == 0
    assert module.permitted(state, None)
    state.configuration.options.equipment_class_progression = 0
    state.configuration.options["starting_" + group] = 2
    assert module.level(state, group) == 0
    state.unlocks["gear_" + group] = True
    assert module.level(state, group) == len(list(row.labels))
    assert module.check_reason(state, lua.table()) is None


def test_powered_outfits_and_unknown_classified_gear_require_top_tier(lua):
    state = fresh(lua)
    module = native(lua)
    section = next(iter(lua.globals().gamma_ap_catalog.powered_outfits))
    assert module.section_tier(section, "outfit") == 5
    assert module.check_reason(state, lua.table(category="checks_armour_tiers", key="4"))
    assert module.check_reason(
        state, lua.table(category="checks_weapon_tiers", key="rifle", weapon_grade="")
    )
    assert module.check_reason(
        state, lua.table(category="checks_weapon_tiers", key="grade_C", weapon_grade="C")
    )
    assert module.check_reason(state, lua.table(category="checks_maps")) is None
    state.configuration.options.initial_firearm_class = 0
    assert module.permitted(state, "firearms") is False
    assert module.item_enabled(state.configuration, 28053001)
    assert module.item_enabled(state.configuration, 28051601)
    state.configuration.options.rewards_starting_gear_unlocks = 0
    assert module.item_enabled(state.configuration, 28053001) is False
    assert module.supplies(state, 28053004) is False


@pytest.mark.parametrize(
    "minimum,condition,expected",
    [
        (65, 0.649, False),
        (65, 0.65, True),
        (0, 0, False),
        (0, 0.01, True),
        (100, 0.999, False),
        (100, 1, True),
        (65, 1.1, False),
    ],
)
def test_condition_threshold_is_inclusive_and_rejects_broken_or_invalid_gear(
    lua, minimum, condition, expected
):
    state = fresh(lua, equipment_check_condition=minimum)
    item = lua.table(condition=lua.eval(f"function() return {condition} end"))
    assert lua.globals().gamma_ap_equipment_classes.usable_condition(state, item) is expected


def test_condition_threshold_accepts_a_percentage_after_native_float_rounding(lua):
    import struct

    condition = struct.unpack("<f", struct.pack("<f", 0.65))[0]
    assert condition < 0.65
    state = fresh(lua, equipment_check_condition=65)
    item = lua.table(condition=lua.eval(f"function() return {condition} end"))
    assert lua.globals().gamma_ap_equipment_classes.usable_condition(state, item)


def test_generic_tools_supply_in_order_and_save_reload_never_regrants(lua):
    game, engine, _ = kit_game(lua, (28051801,) * 3, progressive_tool_receipts=1)
    for _ in range(3):
        poll(game, engine)
    state = state_of(lua, game)
    assert state.received_count == 3
    assert list(engine.created.values()) == ["itm_basickit", "itm_advancedkit", "itm_expertkit"]
    assert lua.globals().gamma_ap_tool_permissions.level(state) == 3
    assert lua.globals().gamma_ap_tool_permissions.reason(state, "expert") is None
    game.load_state(lua.table(gamma_archipelago_v1=state))
    poll(game, engine)
    assert len(list(engine.created)) == 3


def test_backpack_receipts_deliver_free_bags_without_optional_permission_supplies(lua):
    game, engine, config = kit_game(
        lua, (28053004,) * 4, equipment_class_progression=1, rewards_starting_gear_unlocks=1
    )
    game.on_game_start()
    engine.creation.new_game_faction = None
    for _ in range(4):
        poll(game, engine)
    state = state_of(lua, game)
    assert state.received_count == 4
    assert list(engine.created.values()) == [
        "wpn_knife",
        "itm_backpack",
        "equ_small_pack",
        "equ_small_military_pack",
        "equ_military_pack",
        "equ_tourist_pack",
    ]
    assert lua.globals().gamma_ap_equipment_classes.level(state, "backpack") == 5
    game.load_state(lua.table(gamma_archipelago_v1=state))
    poll(game, engine)
    assert len(list(engine.created)) == 6


def test_starting_gifts_keep_knife_and_grant_only_one_bag_with_uncertain_spawn_guard(lua):
    state = fresh(lua)
    native(lua)
    lua.execute("""
        db={actor={iterate_inventory=function() end}}
        spawns={}
        alife_create_item=function(section)
            if failed=='error' then error('uncertain spawn') end
            if failed then return nil end
            spawns[#spawns+1]=section;return {id=42}
        end
    """)
    supplies = lua.globals().gamma_ap_starting_supplies
    grants = supplies.plan(state)
    assert [g.section for g in grants.values()] == ["wpn_knife", "itm_backpack"]
    lua.globals().failed = True
    assert supplies.apply(state, grants)[0] is False
    lua.globals().failed = None
    assert supplies.apply(state, grants) is True
    assert supplies.apply(state, grants) is True
    assert len(list(lua.globals().spawns)) == 2
    copied = supplies.copy(grants)
    assert copied[1].created and copied[1] != grants[1]
    copied[1].created = False
    lua.globals().failed = "error"
    assert supplies.apply(state, copied)[0] is False
    lua.globals().failed = None
    assert supplies.apply(state, copied)[0] is False
    assert supplies.validate(lua.table(money=0, actions=lua.table(), grants=grants))
    grants[1].uncertain = True
    assert not supplies.validate(lua.table(money=0, actions=lua.table(), grants=grants))
    assert supplies.copy(None) is None and supplies.validate(None)
    assert supplies.apply(state, None) is True
    state.configuration.options.equipment_class_progression = 0
    assert supplies.plan(state) is None


def test_skipped_knife_and_repair_grades_credit_lower_checks_at_condition_threshold(lua):
    game, engine, _ = equipment_game(
        lua,
        checks_knife_tiers=1,
        checks_weapon_tiers=1,
        equipment_class_progression=1,
        initial_firearm_class=4,
        playability_logic=0,
    )
    lua.execute("ini_sys.section_exist=function() return true end")
    game.on_game_start()
    engine.creation.new_game_faction = None
    poll(game, engine)
    state = state_of(lua, game)
    engine.active = gear(lua, 1, "wpn_knife5", "w_melee", 0.649)
    module = lua.globals().gamma_ap_equipment_checks
    assert module.poll(state, state.configuration)
    assert not state.checks[28052721]
    engine.active.health = 0.65
    assert module.poll(state, state.configuration)
    assert all(state.checks[x] for x in range(28052721, 28052725))
    engine.active = gear(lua, 2, "rifle_d", "w_rifle", 0.65)
    engine.meta.rifle_d.repair_type = "rifle_7"
    assert module.poll(state, state.configuration)
    assert all(state.checks[x] for x in range(28052751, 28052755))


def test_loadout_filter_preserves_price_pairs_and_native_wrappers_on_failure(lua):
    window, engine = menu(
        lua, equipment_class_progression=1, rewards_starting_gear_unlocks=1, starting_pda=2
    )
    native(lua)
    lua.execute("""
        metadata={pistol={kind='w_pistol',repair_type='pistol'},rifle={kind='w_rifle',repair_type='rifle_5'},
            knife={kind='w_melee'},pda={class='D_PDA'}}
        local function container() return {cell={},Reinit=function(self,sections,prices)
            self.sections=sections;self.prices=prices end} end
        window.CC={inventory=container(),loadout=container()}
        ui_mm_faction_select.UINewGame.LoadLoadout=function(self)
            self.CC.inventory:Reinit({'knife','pda'},{0,10})
            self.CC.loadout:Reinit({'rifle','pistol'},{500,100})
            if engine.fail then error('native failed') end
            return 'loaded'
        end
        ui_mm_faction_select.UINewGame.On_CC_Mouse1=function() engine.paid=true;return true end
        original=window.CC.inventory.Reinit
        gamma_ap_start_menu.install(function() return configuration end)
    """)
    assert window.LoadLoadout(window) == "loaded"
    assert list(window.CC.inventory.sections.values()) == ["knife"]
    assert list(window.CC.loadout.sections.values()) == ["pistol"]
    assert list(window.CC.loadout.prices.values()) == [100]
    lua.execute("assert(window.CC.inventory.Reinit==original)")
    window.CC.loadout.cell[1] = lua.table(section="rifle")
    assert window.On_CC_Mouse1(window, "loadout", 1) is False and not engine.paid
    window.CC.loadout.cell[1].section = "pistol"
    assert window.On_CC_Mouse1(window, "loadout", 1) is True and engine.paid
    engine.fail = True
    with pytest.raises(Exception, match="native failed"):
        window.LoadLoadout(window)
    lua.execute("assert(window.CC.inventory.Reinit==original)")
    engine.fail = False
    window.CC.inventory.cell[1] = lua.table(
        section="rifle", IsShown=lua.eval("function() return true end")
    )
    assert window.OnStartGame(window) is False
    assert engine.starts == 0 and engine.warning == "gamma_ap_start_loadout_locked"
    window.CC.inventory.cell[1].section = "knife"
    assert window.OnStartGame(window) == "started"
    window.CC.inventory.cell[1].IsShown = lua.eval("function() return false end")
    assert window.OnStartGame(window) == "started"


@pytest.mark.parametrize(
    "value",
    [
        False,
        "broken",
        {"money": -1, "actions": {}},
        {"money": 0, "actions": {}, "grants": False},
        {"money": 0, "actions": {1: {"id": 1, "section": "x", "target": 0, "done": "yes"}}},
        {
            "money": 0,
            "actions": {},
            "grants": {1: {"section": "injected", "created": False, "uncertain": False}},
        },
    ],
)
def test_malformed_starting_plans_are_refused_before_copying(lua, value):
    from collections.abc import Mapping

    def table(value):
        return (
            lua.table_from({k: table(v) for k, v in value.items()})
            if isinstance(value, Mapping)
            else value
        )

    assert lua.globals().gamma_ap_starting_supplies.validate(table(value)) is False


def test_starting_plan_copies_existing_omission_actions_and_never_replaces_owned_knife(lua):
    game, engine, config = configured_game(
        lua,
        equipment_class_progression=1,
        rewards_starting_gear_unlocks=1,
        initial_backpack_class=0,
        initial_firearm_class=0,
    )
    lua.execute("ini_sys.section_exist=function() return true end")
    game.on_game_start()
    assert "knife" in engine.creation.new_game_loadout
    assert "gun" not in engine.creation.new_game_loadout
    engine.creation.new_game_faction = None
    poll(game, engine)
    state = state_of(lua, game)
    assert state.loadout_initialized and engine.objects[4] and not engine.objects[3]
    assert "wpn_knife" not in list(engine.created.values())
    assert "itm_backpack" not in list(engine.created.values())
    state.loadout_plan = lua.table(
        money=0,
        actions=lua.table(lua.table(id=2, section="pda", target=0, done=False)),
        grants=lua.table(),
    )
    copied = lua.globals().gamma_ap_loadout.copy_plan(state.loadout_plan)
    assert copied.actions[1].section == "pda" and not copied.actions[1].done
    assert lua.globals().gamma_ap_starting_supplies.validate(copied)


@pytest.mark.parametrize(
    "identity", ["nil", "0", "65535", "1.5", "function() error('id unavailable') end"]
)
def test_uncertain_initial_item_identity_never_retries_automatically(lua, identity):
    state = fresh(lua)
    native(lua)
    lua.execute(f"db={{actor={{}}}}; alife_create_item=function() return {{id={identity}}} end")
    module = lua.globals().gamma_ap_starting_supplies
    grants = lua.table(lua.table(section="wpn_knife", created=False, uncertain=False))
    assert module.apply(state, grants)[0] is False and grants[1].uncertain
    lua.execute("alife_create_item=function() error('must not retry') end")
    assert module.apply(state, grants)[0] is False


def test_medium_outfit_credits_lower_tier_only_with_condition_and_advanced_tools(lua):
    state = fresh(
        lua,
        checks_armour_tiers=1,
        rewards_progressive_tools=1,
        progressive_tool_receipts=1,
        initial_outfit_class=3,
        playability_logic=0,
    )
    native(lua)
    lua.execute("""
        metadata.medium={kind='o_medium',repair_type='outfit_medium'}
        outfit={section=function() return 'medium' end,condition=function() return .65 end}
        db={actor={item_in_slot=function(self,slot) return slot==7 and outfit or nil end}}
    """)
    module = lua.globals().gamma_ap_equipment_checks
    assert module.poll(state, state.configuration)
    assert not state.checks[28052701] and not state.checks[28052702]
    state.applied_items[1] = 28051801
    assert module.poll(state, state.configuration)
    assert state.checks[28052701] and not state.checks[28052702]
    state.applied_items[2] = 28051801
    assert module.poll(state, state.configuration)
    assert state.checks[28052702] and not state.checks[28052703]
