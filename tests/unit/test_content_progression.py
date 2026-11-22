from collections import Counter

from gamma_archipelago.configuration import build_configuration, defaults
from gamma_archipelago.content_progression import (
    TOOL_CLAIMS,
    TOOL_STASHES,
    configured_item_ids,
    melter_check,
    protected,
    required_copy,
    tool_level,
)
from gamma_archipelago.discovery import QUOTAS, configured_location_ids
from gamma_archipelago.presets import presets


def config(**values):
    return build_configuration(defaults() | {"tool_use_permissions": 0} | values)


def test_tool_tiers_require_contiguous_permissions_and_preserve_legacy_copies():
    held = Counter({TOOL_CLAIMS[2]: 1})
    assert tool_level(held.__getitem__) == 0
    held[TOOL_CLAIMS[0]] = 1
    assert tool_level(held.__getitem__) == 1
    held[TOOL_CLAIMS[1]] = 1
    assert tool_level(held.__getitem__) == 3
    assert tool_level(Counter({"Progressive Tools": 2}).__getitem__) == 2
    assert 28051202 in configured_item_ids(config(rewards_progressive_tools=1))
    assert 28051202 not in configured_item_ids(
        config(rewards_progressive_tools=1, content_progression=0)
    )


def test_melter_capability_and_required_pool_copies_follow_selected_checks():
    row = dict(category="checks_artefacts", quota_group="artefact", minimum=21)
    enabled = config(checks_artefacts=1, rewards_artefact_melter=1)
    assert melter_check(enabled, row)
    assert not melter_check(config(content_progression=0), row)
    assert not melter_check(enabled, {**row, "minimum": 20})
    assert protected(config(checks_artefacts=1, rewards_artefact_melter=0))
    assert not protected(enabled)
    assert required_copy(enabled, dict(name="Artefact Melter")) == 1
    assert required_copy(config(), dict(name="Artefact Melter")) == 0
    assert required_copy(enabled, dict(name="Progressive Tools", copies=3)) == 0
    assert (
        required_copy(config(content_progression=0), dict(name="Progressive Tools", copies=3)) == 3
    )
    assert (
        required_copy(config(content_progression=0), dict(name=TOOL_STASHES[0], tool_level=1)) == 0
    )
    assert required_copy(enabled, dict(name=TOOL_STASHES[0], tool_level=1)) == 1


def test_fresh_artefact_ceiling_and_story_toggles_preserve_explicit_legacy_seeds():
    values = presets()["full_story"]
    full = build_configuration(values)
    ids = configured_location_ids(full)
    assert set(QUOTAS["artefact"][:40]) <= ids
    assert not set(QUOTAS["artefact"][40:]) & ids
    assert {28052621, 28052643, 28052653} <= ids
    selected = build_configuration(
        values | {"checks_mortal_sin": 0, "checks_operation_afterglow": 0}
    )
    assert 28052621 in configured_location_ids(selected)
    assert not {28052643, 28052653} & configured_location_ids(selected)
    legacy = build_configuration(values | {"content_progression": 0, "artefact_discovery_count": 0})
    assert set(QUOTAS["artefact"]) <= configured_location_ids(legacy)
    assert not {28052751, 28052752, 28052753, 28052754} & configured_location_ids(legacy)
    only = config(checks_maps=0, checks_mortal_sin=1)
    assert 28052643 in configured_location_ids(only) and 28052621 not in configured_location_ids(
        only
    )


def test_every_progression_stash_uses_a_verified_native_container():
    import json
    from importlib.resources import files

    catalog = json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text())
    assert all(
        row["cache"] in catalog["stash_containers"]
        for row in catalog["items"]
        if row.get("effect") == "progression_stash"
    )


def test_starting_cash_is_not_reused_and_hostile_reputation_is_not_a_friendly_trader_proxy():
    from gamma_archipelago.playability import allowed, early_check

    settings = config(
        starting_pda=2,
        starting_firearms=2,
        rewards_starting_gear_unlocks=1,
        rewards_faction_reputation=1,
    )
    held = Counter({"Faction Goodwill: army": 12})
    cash = dict(category="checks_shop_purchases", key="esc_m_trader_1", price=2500)
    assert allowed(settings, cash, held.__getitem__, lambda _: False)
    assert not allowed(
        config(**(settings.to_values() | {"starting_money": 25})),
        cash,
        held.__getitem__,
        lambda _: False,
    )
    assert not allowed(
        settings,
        {**cash, "key": "bar_visitors_barman_stalker_trader_1"},
        held.__getitem__,
        lambda _: False,
    )
    assert not allowed(
        settings,
        dict(category="checks_rank_milestones", minimum=49999),
        held.__getitem__,
        lambda _: False,
    )
    held["Equipment Unlock: PDA"] = 1
    assert allowed(
        settings,
        dict(category="checks_rank_milestones", minimum=49999),
        held.__getitem__,
        lambda _: False,
    )
    assert not allowed(
        settings,
        dict(category="checks_faction_standing", minimum=3000),
        held.__getitem__,
        lambda _: False,
    )
    held["Faction Goodwill: stalker"] = 12
    assert allowed(
        settings,
        dict(category="checks_faction_standing", minimum=3000),
        held.__getitem__,
        lambda _: False,
    )
    assert not early_check(
        dict(category="checks_settlements", level="l01_escape", hostile_settlement_faction="army"),
        frozenset({"l01_escape"}),
    )


def test_disabled_content_additions_do_not_change_legacy_wire_records():
    from gamma_archipelago.configuration import encode_configuration, legacy_defaults

    legacy = build_configuration(legacy_defaults())
    wire = encode_configuration("a" * 64, legacy, True)
    for key in (
        "checks_emissions",
        "checks_psi_storms",
        "checks_mortal_sin",
        "checks_operation_afterglow",
        "rewards_artefact_melter",
        "content_progression",
        "infinite_stamina",
    ):
        assert "option|" + key + "|" not in wire
