import pytest

from .test_game_adapter import saved_state
from .test_settlements import configured_settlements, smart
from .test_tracker import rows


def test_generated_diplomacy_rules_match_every_typed_catalogue_field(lua):
    from dataclasses import asdict

    from gamma_archipelago.settlement_access import SETTLEMENT_RULES

    actual = lua.globals().gamma_ap_catalog.settlement_rules
    assert set(actual) == set(SETTLEMENT_RULES)
    for id, rule in SETTLEMENT_RULES.items():
        assert dict(actual[id]) == asdict(rule)


def native(lua, goodwill=0, relation=-2000):
    lua.execute("""goodwill=0;relation=-2000;queries={}
        character_community=function() return 'actor_stalker' end
        relation_registry={community_goodwill=function(faction)
            queries[faction]=(queries[faction] or 0)+1;return goodwill end,
            set_community_goodwill=function(_,_,target) goodwill=target end,
            community_relation=function() return relation end}""")
    lua.globals().goodwill, lua.globals().relation = goodwill, relation


def configured(lua):
    game, engine, _ = configured_settlements(lua, rewards_faction_reputation=1)
    native(lua)
    lua.execute("db.actor.id=function() return 0 end")
    return game, engine, saved_state(lua, game).gamma_archipelago_v1


def test_native_settlement_waits_for_real_neutrality_and_accepts_natural_goodwill(lua):
    game, _, _ = configured(lua)
    name = "esc_smart_terrain_3_16"
    for goodwill in (0, 1000):
        lua.globals().goodwill = goodwill
        game.actor_on_interaction("smarts", smart(lua, name), name)
        assert not saved_state(lua, game).gamma_archipelago_v1.checks[28052103]
    lua.globals().goodwill = 1001
    game.actor_on_interaction("smarts", smart(lua, name), name)
    assert saved_state(lua, game).gamma_archipelago_v1.checks[28052103]
    game.load_state(saved_state(lua, game))
    lua.globals().goodwill = -3000
    assert saved_state(lua, game).gamma_archipelago_v1.checks[28052103]


def test_tracker_uses_receipts_without_native_observations_and_live_standing_when_supplied(lua):
    _, _, state = configured(lua)
    module = lua.globals().gamma_ap_settlement_access
    assert "0 / 5" in module.reason(state, 28052103)
    state.applied_items = lua.table_from([28051307] * 4)
    assert "4 / 5" in module.reason(state, 28052103)
    state.applied_items[5] = 28051307
    assert module.reason(state, 28052103) is None
    standing = module.standing(state)
    assert "remains hostile" in module.reason(state, 28052103, standing)
    assert lua.globals().queries.army == 1  # Two bases share one query.
    lua.globals().goodwill = 1250
    assert module.reason(state, 28052103, module.standing(state)) is None
    assert module.reason(state, 28052101) is None
    assert "Filler-only" in module.reason(state, 28052113)[1]
    snapshot = lua.globals().gamma_ap_tracker.snapshot(state, 0, None, False, standing)
    checks = {row.id: row for row in rows(snapshot)}
    assert "remains hostile" in checks[28052103].reason
    assert "Filler-only" in checks[28052113].reason


@pytest.mark.parametrize("value", [None, "bad", 0.5, float("inf"), float("nan"), 2147483648])
@pytest.mark.parametrize("field", ["goodwill", "relation"])
def test_unavailable_or_malformed_native_standing_fails_closed_without_a_check(lua, value, field):
    game, _, state = configured(lua)
    lua.globals()[field] = value
    module = lua.globals().gamma_ap_settlement_access
    allowed, error = module.native_allowed(state, 28052103)
    assert allowed is None and "Cannot verify" in error
    assert "could not be verified" in module.reason(state, 28052103, module.standing(state))
    name = "esc_smart_terrain_3_16"
    game.actor_on_interaction("smarts", smart(lua, name), name)
    assert not saved_state(lua, game).gamma_archipelago_v1.checks[28052103]


def test_legacy_and_no_reward_routes_do_not_call_native_apis_and_remain_optional(lua):
    game, _, _ = configured_settlements(lua)
    state = saved_state(lua, game).gamma_archipelago_v1
    module = lua.globals().gamma_ap_settlement_access
    lua.globals().relation_registry = None
    assert module.native_allowed(state, 28052103)
    assert "Filler-only" in module.reason(state, 28052103)[1]
    state.configuration.options.settlement_reputation_logic = 0
    assert module.reason(state, 28052103) is None
    assert not list(module.standing(state))
    state.configuration = None
    assert module.native_allowed(state, 28052103)


def test_missing_native_api_fails_closed_in_an_active_reputation_seed(lua):
    _, _, state = configured(lua)
    lua.globals().relation_registry = None
    allowed, error = lua.globals().gamma_ap_settlement_access.native_allowed(state, 28052103)
    assert allowed is None and "native goodwill APIs" in error


@pytest.mark.parametrize("community", [None, "", "none", 123])
def test_invalid_actor_community_never_reaches_native_relation_bindings(lua, community):
    _, _, state = configured(lua)
    lua.globals().community_result = community
    lua.execute("character_community=function() return community_result end")
    allowed, _ = lua.globals().gamma_ap_settlement_access.native_allowed(state, 28052103)
    assert allowed is None and not list(lua.globals().queries)


@pytest.mark.parametrize("id", [-1, 65535, "bad", 0.5])
def test_invalid_actor_id_never_reaches_native_relation_bindings(lua, id):
    _, _, state = configured(lua)
    lua.globals().actor_id = id
    lua.execute("db.actor.id=function() return actor_id end")
    allowed, _ = lua.globals().gamma_ap_settlement_access.native_allowed(state, 28052103)
    assert allowed is None and not list(lua.globals().queries)


def test_earned_floor_restores_negative_standing_before_entry_and_survives_saved_history(lua):
    game, _, state = configured(lua)
    state.applied_items = lua.table_from([28051307] * 5)
    module = lua.globals().gamma_ap_settlement_access
    floors = module.minimum_goodwill(state)
    assert floors.army == 1250 and floors.bandit is None
    assert module.minimum_goodwill(state, 28051308).bandit == 250
    lua.globals().goodwill = -3000
    assert lua.globals().gamma_ap_reputation.reconcile(state)
    assert lua.globals().goodwill == 1250
    lua.globals().goodwill = 4000
    assert lua.globals().gamma_ap_reputation.reconcile(state)
    assert lua.globals().goodwill == 4000
    state.applied_items = lua.table_from([28051307] * 20)
    assert module.minimum_goodwill(state).army == 3000
    state.refused_save = True
    assert not list(module.minimum_goodwill(state))
    state.refused_save = False
    state.configuration.options.checks_settlements = 0
    assert not list(module.minimum_goodwill(state))


def test_floor_api_failure_is_reported_without_replaying_rewards(lua):
    game, _, state = configured(lua)
    state.applied_items = lua.table_from([28051307] * 5)
    lua.globals().relation_registry.set_community_goodwill = lua.eval(
        "function() error('cannot restore floor') end"
    )
    ok, error = lua.globals().gamma_ap_reputation.reconcile(state)
    assert not ok and "same target will retry" in error
    lua.globals().relation_registry = None
    ok, error = lua.globals().gamma_ap_reputation.reconcile(state)
    assert not ok and "personal goodwill API" in error


@pytest.mark.parametrize("id", [-1, 65535, "bad", 0.5])
def test_floor_reconciliation_rejects_invalid_actor_identity(lua, id):
    _, _, state = configured(lua)
    state.applied_items = lua.table_from([28051307] * 5)
    lua.globals().actor_id = id
    lua.execute("db.actor.id=function() return actor_id end")
    ok, error = lua.globals().gamma_ap_reputation.reconcile(state)
    assert not ok and "invalid value" in error and not list(lua.globals().queries)


def test_older_saved_configuration_without_the_new_setting_keeps_original_entry_behaviour(lua):
    game, _, _ = configured_settlements(
        lua, rewards_faction_reputation=1, settlement_reputation_logic=0
    )
    saved = saved_state(lua, game)
    saved.gamma_archipelago_v1.configuration.options.settlement_reputation_logic = None
    lua.globals().relation_registry = None
    game.load_state(saved)
    state = saved_state(lua, game).gamma_archipelago_v1
    assert not state.refused_save
    assert (state.configuration.options.settlement_reputation_logic or 0) == 0
    name = "esc_smart_terrain_3_16"
    game.actor_on_interaction("smarts", smart(lua, name), name)
    assert saved_state(lua, game).gamma_archipelago_v1.checks[28052103]


@pytest.mark.parametrize("enabled", [0, 1])
def test_older_addon_wire_ignores_disabled_setting_and_refuses_enabled_new_logic(lua, enabled):
    from gamma_archipelago.configuration import build_configuration, defaults, encode_configuration

    from .test_loadout import KEY

    config = build_configuration(defaults() | {"settlement_reputation_logic": enabled})
    lua.globals().gamma_ap_catalog.config_limits.settlement_reputation_logic = None
    lua.globals().gamma_ap_catalog.config_defaults.settlement_reputation_logic = None
    packet = encode_configuration(KEY, config)
    result = lua.globals().gamma_ap_configuration.parse(packet, KEY, config.digest)
    if enabled:
        assert result[0] is None and "invalid configuration option" in result[1]
    else:
        assert result.options.settlement_reputation_logic is None
