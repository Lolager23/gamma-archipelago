import pytest

from gamma_archipelago.configuration import build_configuration, defaults, encode_configuration
from gamma_archipelago.protocol import encode_incoming

from .test_game_adapter import load_game, saved_state

KEY = "a" * 64
CONFIG_PATH = "D:/AnomalyAP/appdata/archipelago\\configuration.txt"


def configured_game(lua, **values):
    game, engine = load_game(lua)
    lua.execute("""
        engine.objects={}; engine.meta={}; engine.money=1000
        engine.creation={new_game_faction='stalker',new_game_loadout='detector,pda,gun,knife,medkit'}
        axr_main={config={
            r_value=function(self,section,key) return engine.creation[key] end,
            w_value=function(self,section,key,value) engine.creation[key]=value end,
        }}
        ini_sys={r_string_ex=function(self,section,key)
            return engine.meta[section] and engine.meta[section][key]
        end}
        level.object_by_id=function(id) return engine.objects[id] end
        db.actor.iterate_inventory=function(self,fn)
            for _,object in pairs(engine.objects) do fn(self,object) end
        end
        db.actor.money=function() return engine.money end
        db.actor.give_money=function(self,amount)
            if engine.fail_money then error('money failed') end
            engine.money=engine.money+amount
        end
        alife_release=function(object)
            if engine.fail_release=='error' then error('release failed') end
            if engine.fail_release then return false end
            engine.objects[object:id()]=nil
            return true
        end
        add_item=function(id,section,class,kind,ammo)
            engine.meta[section]={class=class,kind=kind}
            local object={amount=ammo or 0}
            object.id=function() return id end
            object.section=function() return section end
            object.ammo_get_count=function(self) return self.amount end
            object.ammo_set_count=function(self,count)
                if not engine.ignore_ammo then self.amount=count end
                if engine.fail_ammo then error('ammo setter failed') end
            end
            engine.objects[id]=object
            return object
        end
    """)
    add = lua.globals().add_item
    add(1, "detector", "DET_SIMP", "i_device", 0)
    add(2, "pda", "D_PDA", "i_device", 0)
    add(3, "gun", "WP_PM", "w_pistol", 0)
    add(4, "knife", "WP_KNIFE", "w_melee", 0)
    add(5, "medkit", "S_FOOD", "i_medical", 0)
    add(6, "medkit", "S_FOOD", "i_medical", 0)
    add(7, "ammo", "AMMO", "w_ammo", 100)
    add(8, "food", "S_FOOD", "i_food", 0)
    add(9, "food", "S_FOOD", "i_food", 0)
    add(10, "quest_token", "II_ATTCH", "i_quest", 0)
    configuration = build_configuration({**defaults(), **values})
    engine.files[CONFIG_PATH] = encode_configuration(KEY, configuration)
    engine.files["D:/AnomalyAP/appdata/archipelago\\incoming.txt"] = encode_incoming(
        KEY, (28051003,), configuration.digest
    )
    return game, engine, configuration


def test_new_game_omits_selected_gear_before_grants_and_never_strips_earned_gear(lua):
    game, engine, configuration = configured_game(
        lua,
        starting_detector=1,
        starting_pda=1,
        no_starting_weapons=1,
        starting_ammo=50,
        starting_medicine=50,
        starting_food=50,
        starting_money=25,
    )
    game.on_game_start()
    assert engine.creation.new_game_loadout == "medkit"
    game.load_state(lua.table())  # A new game's empty loader table retains preparation.
    game.actor_on_update()
    assert not list(engine.created.values())  # Original loadout hasn't finished yet.
    engine.creation.new_game_faction = None
    engine.now += 500
    game.actor_on_update()
    assert not any(engine.objects[index] for index in (1, 2, 3, 4))
    assert engine.objects[7].amount == 50 and engine.money == 250
    assert engine.objects[5] is not None and engine.objects[6] is None
    assert engine.objects[8] is not None and engine.objects[9] is None
    assert engine.objects[10] is not None
    assert list(engine.created.values()) == ["bandage"]
    state = saved_state(lua, game)
    assert state.gamma_archipelago_v1.loadout_initialized is True
    lua.globals().add_item(100, "pda", "D_PDA", "i_device", 0)
    game.load_state(state)
    engine.now += 500
    game.actor_on_update()
    assert engine.objects[100] is not None and engine.money == 250
    assert len(engine.created) == 1
    assert lua.globals().gamma_ap_loadout.pda_available(state.gamma_archipelago_v1)


def test_existing_character_is_refused_for_a_restricted_seed_without_inventory_removal(lua):
    game, engine, _ = configured_game(lua, starting_pda=1)
    engine.creation.new_game_faction = None
    game.on_game_start()
    game.actor_on_update()
    assert engine.objects[2] is not None and not len(engine.created)
    assert any("fresh character" in value for value in engine.logs.values())


def test_normal_config_and_legacy_saves_keep_all_inventory(lua):
    game, engine, _ = configured_game(lua)
    engine.creation.new_game_faction = None
    game.on_game_start()
    game.actor_on_update()
    assert engine.objects[1] is not None and engine.money == 1000
    assert saved_state(lua, game).gamma_archipelago_v1.loadout_initialized


@pytest.mark.parametrize(
    "failure", ["release_false", "release_error", "ammo", "ammo_ignored", "money"]
)
def test_retry_uses_original_targets_instead_of_repeatedly_halving_inventory(lua, failure):
    game, engine, _ = configured_game(lua, starting_detector=1, starting_ammo=50, starting_money=50)
    game.on_game_start()
    engine.creation.new_game_faction = None
    if failure.startswith("release"):
        engine.fail_release = "error" if failure == "release_error" else True
    elif failure == "ammo":
        engine.fail_ammo = True
    elif failure == "ammo_ignored":
        engine.ignore_ammo = True
    else:
        engine.fail_money = True
    game.actor_on_update()
    assert not len(engine.created)
    engine.fail_release = False
    engine.fail_ammo = engine.ignore_ammo = engine.fail_money = False
    stored = saved_state(lua, game)
    assert stored.gamma_archipelago_v1.loadout_plan is not None
    game.load_state(stored)
    engine.now += 500
    game.actor_on_update()
    assert engine.objects[7].amount == 50 and engine.money == 500
    assert len(engine.created) == 1


def test_large_starter_loadout_is_bounded_and_reused_ids_are_never_deleted(lua):
    game, engine, _ = configured_game(lua, starting_detector=1)
    for identity in range(20, 60):
        lua.globals().add_item(identity, "detector", "DET_SIMP", "i_device", 0)
    game.on_game_start()
    engine.creation.new_game_faction = None
    game.actor_on_update()
    assert not len(engine.created)
    pending = saved_state(lua, game).gamma_archipelago_v1
    unfinished = next(action for action in pending.loadout_plan.actions.values() if not action.done)
    lua.globals().add_item(unfinished.id, "earned_quest_item", "II_ATTCH", "i_quest", 0)
    engine.now += 500
    game.actor_on_update()
    assert engine.objects[unfinished.id] is not None and not len(engine.created)
    engine.objects[unfinished.id] = None  # Missing already-removed targets are idempotent.
    engine.now += 500
    game.actor_on_update()
    assert len(engine.created) == 1


@pytest.mark.parametrize(
    "section,cls,kind,expected",
    [
        ("x", "D_PDA", "", "pda"),
        ("x", "DET_SIMP", "", "detector"),
        ("x", "WP_BINOC", "", "utilities"),
        ("device_flashlight", "", "", "utilities"),
        ("device_torch", "", "", "utilities"),
        ("x", "", "w_melee", "melee"),
        ("x", "G_F1", "", "explosives"),
        ("x", "G_RGD5", "", "explosives"),
        ("x", "", "w_explosive", "explosives"),
        ("ammo_new", "", "", "ammo"),
        ("x", "WP_AK74", "", "firearms"),
        ("x", "", "w_rifle", "firearms"),
        ("x", "E_HLMET", "", "helmet"),
        ("x", "", "o_helmet", "helmet"),
        ("x", "EQ_BAKPK", "", "backpack"),
        ("x", "", "i_backpack", "backpack"),
        ("x", "E_STLK", "", "outfit"),
        ("x", "", "o_heavy", "outfit"),
        ("x", "", "i_drink", "food"),
        ("x", "", "i_tool", "tools"),
        ("x", "", "i_repair", "tools"),
        ("x", "", "i_device", "utilities"),
        ("unknown", "", "", None),
    ],
)
def test_equipment_groups_use_class_and_kind_metadata(lua, section, cls, kind, expected):
    _, engine, _ = configured_game(lua)
    engine.meta[section] = lua.table_from({"class": cls, "kind": kind})
    assert lua.globals().gamma_ap_equipment.group(section) == expected


def test_missing_or_mismatched_configuration_refuses_delivery_and_pda_waits_for_a_device(lua):
    game, engine, configuration = configured_game(lua, starting_pda=1)
    original = engine.files[CONFIG_PATH]
    engine.files[CONFIG_PATH] = None
    game.on_game_start()
    game.actor_on_update()
    assert not len(engine.created)
    engine.files[CONFIG_PATH] = original.replace(configuration.digest, "b" * 64)
    engine.now += 500
    game.actor_on_update()
    assert not len(engine.created)
    engine.files[CONFIG_PATH] = original
    game.on_game_start()
    engine.creation.new_game_faction = None
    game.actor_on_update()
    state = saved_state(lua, game).gamma_archipelago_v1
    assert not lua.globals().gamma_ap_loadout.pda_available(state)
    state.configuration_key = "b" * 64
    parsed = lua.globals().gamma_ap_configuration.parse(original, KEY, configuration.digest)
    assert lua.globals().gamma_ap_loadout.apply(state, parsed)[0] is False
