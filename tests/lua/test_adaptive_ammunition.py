import pytest

from gamma_archipelago.protocol import encode_incoming

from .test_loadout import KEY
from .test_workshop import INCOMING, poll, state_of, tool_game

AMMO = 28051903
FALLBACK = ["ammo_9x18_ap", "ammo_9x18_fmj", "ammo_9x18_pmm"]


def equipped(lua, engine, slot, classes):
    name = f"weapon_{slot}"
    item = lua.globals().add_item(100 + slot, name, "WP_PM", "w_pistol")
    engine.meta[name].ammo_class = classes
    engine.slots[slot] = item


def start(lua, weapons=()):
    game, engine, config = tool_game(lua, rewards_supply_ammunition=1, checks_gear_upgrades=0)
    for slot, classes in enumerate(weapons, 1):
        equipped(lua, engine, slot, classes)
    engine.files[INCOMING] = encode_incoming(KEY, (AMMO,), config.digest)
    poll(game, engine)
    return game, engine


@pytest.mark.parametrize(
    "weapons,types",
    [
        ((), FALLBACK),
        (("",), FALLBACK),
        (("ammo_9x18_fmj_bad,ammo_9x18_ap_verybad",), FALLBACK),
        (("ammo_9x19_fmj, ammo_9x19_ap, ammo_9x19_fmj_bad",), ["ammo_9x19_ap", "ammo_9x19_fmj"]),
        (
            ("ammo_5.45x39_fmj,ammo_5.45x39_ap", "ammo_9x19_fmj, ammo_5.45x39_ap"),
            ["ammo_5.45x39_ap", "ammo_5.45x39_fmj", "ammo_9x19_fmj"],
        ),
        (
            ("ammo_9x18_fmj,ammo_9x18_ap", "ammo_9x18_fmj,ammo_9x18_ap"),
            ["ammo_9x18_ap", "ammo_9x18_fmj"],
        ),
    ],
)
def test_equipped_ammo_is_deduplicated_and_delivered_three_native_boxes_each(lua, weapons, types):
    game, engine = start(lua, weapons)
    expected = [section for section in types for _ in range(3)]
    for _ in range(len(expected) - 1):
        poll(game, engine)
    state = state_of(lua, game)
    assert state.received_count == 1
    assert list(engine.created.values()) == expected
    assert list(state.deliveries[1].ammo_types.values()) == types
    assert lua.globals().gamma_ap_deliveries.validate(state)
    poll(game, engine)
    assert list(engine.created.values()) == expected


def test_selection_is_saved_before_first_creation_and_survives_swaps_and_reload(lua):
    game, engine = start(lua, ("ammo_5.45x39_fmj,ammo_5.45x39_ap",))
    saved = state_of(lua, game)
    assert saved.deliveries[1].next_action == 2
    equipped(lua, engine, 1, "ammo_9x19_fmj")
    game.load_state(lua.table(gamma_archipelago_v1=saved))
    saved.deliveries[1].ammo_types[1] = "changed_detached_copy"
    for _ in range(5):
        poll(game, engine)
    assert state_of(lua, game).received_count == 1
    assert list(engine.created.values()) == ["ammo_5.45x39_ap"] * 3 + ["ammo_5.45x39_fmj"] * 3


@pytest.mark.parametrize(
    "types",
    [
        None,
        {},
        {1: "ammo_9x18_fmj", 3: "ammo_9x18_ap"},
        {1: "ammo_9x18_fmj", 2: "ammo_9x18_ap"},
        {1: "ammo_9x18_ap", 2: "ammo_9x18_ap"},
        {1: "ammo_9x18_ap", "extra": "ammo_9x18_fmj"},
        {1: "medkit"},
        {1: "ammo_9x18_fmj_bad"},
        {1: "ammo_" + "x" * 100},
    ],
)
def test_damaged_saved_selection_is_refused(lua, types):
    game, _ = start(lua)
    state = state_of(lua, game)
    state.deliveries[1].ammo_types = None if types is None else lua.table_from(types)
    assert lua.globals().gamma_ap_deliveries.validate(state) is False


def test_missing_native_ammo_class_and_read_errors_do_not_create_unknown_objects(lua):
    game, engine, _ = tool_game(lua, rewards_supply_ammunition=1, checks_gear_upgrades=0)
    module = lua.globals().gamma_ap_ammunition
    lua.execute('ini_sys.r_string_ex=function() error("unavailable") end')
    types, reason = module.select()
    assert types is None and "pending" in reason
    assert not list(engine.created.values())
    assert state_of(lua, game).received_count == 0
    assert module.sections(lua.table_from(FALLBACK)) is None


def test_selection_bounds_refuse_excessive_lists_and_support_up_to_96_boxes(lua):
    game, engine, _ = tool_game(lua, rewards_supply_ammunition=1, checks_gear_upgrades=0)
    module = lua.globals().gamma_ap_ammunition
    types = [f"ammo_test_{index:02}" for index in range(32)]
    equipped(lua, engine, 13, ",".join(types))
    selected = module.select()
    assert list(selected.values()) == types
    assert len(module.sections(selected)) == 96
    equipped(lua, engine, 13, ",".join(types + ["ammo_test_32"]))
    assert module.select()[0] is None
    assert module.sections(lua.table_from(types + ["ammo_test_32"])) is None
    equipped(lua, engine, 13, "x" * 8193)
    assert "bound" in module.select()[1]


def test_missing_variant_is_skipped_and_invalid_native_class_uses_fallback(lua):
    game, engine, _ = tool_game(lua, rewards_supply_ammunition=1, checks_gear_upgrades=0)
    module = lua.globals().gamma_ap_ammunition
    equipped(lua, engine, 1, "ammo_9x19_fmj,ammo_9x19_ap,medkit, ammo_invalid-name")
    engine.missing_section = "ammo_9x19_ap"
    assert list(module.select().values()) == ["ammo_9x19_fmj"]
    lua.execute("""local prior=ini_sys.r_string_ex
        ini_sys.r_string_ex=function(self,section,key)
            if section=="ammo_9x19_fmj" and key=="class" then return "II_ATTCH" end
            return prior(self,section,key)
        end""")
    assert list(module.select().values()) == FALLBACK


def test_adaptive_metadata_cannot_be_attached_to_another_package(lua):
    game, _, _ = tool_game(lua, (28051901,), rewards_supply_medical=1)
    state = state_of(lua, game)
    state.deliveries[1].ammo_types = lua.table_from(FALLBACK)
    assert lua.globals().gamma_ap_deliveries.validate(state) is False
