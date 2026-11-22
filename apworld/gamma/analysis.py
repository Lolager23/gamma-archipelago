"""Logical spheres and deliberately slower one-tier-per-step planning."""

import json
from collections import defaultdict
from importlib.resources import files
from typing import TYPE_CHECKING

from BaseClasses import CollectionState, Item, Location

from gamma_archipelago.content_progression import TOOL_CLAIMS
from gamma_archipelago.tool_permissions import TOOL_CAPABILITIES

TOOL_EVENTS = TOOL_CLAIMS + TOOL_CAPABILITIES

if TYPE_CHECKING:
    from . import GammaWorld

_data = json.loads(files(__package__).joinpath("catalog.json").read_text("utf-8"))


def _chains() -> dict[str, str]:
    result = {}
    for row in _data["locations"]:
        category = row["category"]
        if category in {"checks_knife_tiers", "checks_armour_tiers", "checks_rank_milestones"}:
            result[row["name"]] = category
        elif category == "checks_gear_upgrades":
            result[row["name"]] = category + row["key"]
        elif row.get("weapon_grade"):
            result[row["name"]] = "weapon_grade"
    result.update(dict.fromkeys(TOOL_EVENTS, "tool_claim"))
    return result


CHAINS = _chains()
ORDER = {row["name"]: index for index, row in enumerate(_data["locations"])}
ORDER.update({name: index for index, name in enumerate(TOOL_CLAIMS)})
ORDER.update({name: index for index, name in enumerate(TOOL_CAPABILITIES)})
PROGRESSIVE_REWARDS = {row["name"] for row in _data["items"] if "class_group" in row} | {
    "Progressive Tools"
}


def _collect(
    state: CollectionState, pending: list[tuple[Item, Location]], paced: bool
) -> list[tuple[Item, Location]]:
    deferred, applied = [], set()
    for item, location in pending:
        key = (item.player, item.name)
        chain = (
            paced
            and state.multiworld.game[item.player] == _data["game"]
            and item.name in PROGRESSIVE_REWARDS
        )
        if chain and key in applied:
            deferred.append((item, location))
        else:
            state.collect(item, True, location)
            if chain:
                applied.add(key)
    return deferred


def _reachable(
    world: "GammaWorld", state: CollectionState, remaining: set[Location], paced: bool
) -> list[Location]:
    reachable = [row for row in remaining if row.can_reach(state)]
    if not paced:
        return reachable
    heads: dict[tuple[int, str], Location] = {}
    for row in remaining:
        group = CHAINS.get(row.name) if world.multiworld.game[row.player] == world.game else None
        if group:
            key = (row.player, group)
            if key not in heads or ORDER[row.name] < ORDER[heads[key].name]:
                heads[key] = row
    return [
        row
        for row in reachable
        if world.multiworld.game[row.player] != world.game
        or row.name not in CHAINS
        or heads[(row.player, CHAINS[row.name])] is row
    ]


def _entry(player: int, rows: list[Location], number: int, spoilers: bool) -> dict[str, object]:
    checks = [row for row in rows if row.player == player and row.address is not None]
    result: dict[str, object] = {
        "step": number,
        "checks": len(checks),
        "categories": dict(_categories(checks)),
        "local_events": [row.name for row in rows if row.player == player and row.address is None],
    }
    if spoilers:
        result["available_checks"] = [
            {"location": row.name, "item": row.item.name, "recipient": row.item.player}
            for row in checks
        ]
    return result


def analyse(world: "GammaWorld", paced: bool, spoilers: bool) -> dict[str, object]:
    multiworld = world.multiworld
    state = CollectionState(multiworld)
    remaining = set(multiworld.get_filled_locations())
    waves, goal_step = [], None
    pending: list[tuple[Item, Location]] = []
    while remaining or pending:
        # Ordinary local goal events settle without consuming a planning step.
        events = [
            row
            for row in remaining
            if row.address is None
            and (
                not paced
                or row.name not in TOOL_EVENTS
                or multiworld.game[row.player] != world.game
            )
        ]
        state.sweep_for_advancements(locations=events)
        remaining.difference_update(state.advancements)
        if goal_step is None and multiworld.completion_condition[world.player](state):
            goal_step = len(waves)
        reachable = _reachable(world, state, remaining, paced)
        if not reachable and not pending:
            break
        rows = sorted(reachable, key=lambda row: (row.player, row.address or 0, row.name))
        entry = _entry(world.player, rows, len(waves) + 1, spoilers)
        waves.append(entry)
        pending = _collect(state, pending + [(row.item, row) for row in rows], paced)
        if pending:
            entry["deferred_reward_count"] = len(pending)
            if spoilers:
                entry["deferred_rewards"] = [item.name for item, _ in pending]
        remaining.difference_update(rows)
    goal = bool(multiworld.completion_condition[world.player](state))
    return {
        "method": "one tier per chain per step" if paced else "Archipelago logical spheres",
        "steps": waves,
        "goal_reachable": goal,
        "goal_step": goal_step if goal_step is not None else len(waves) if goal else None,
        "unreachable_checks": sum(
            row.player == world.player and row.address is not None for row in remaining
        ),
        "time_estimate": "No measured travel, combat or ALife waiting is implied.",
    }


def _categories(checks: list[Location]) -> defaultdict[str, int]:
    categories = {row["name"]: row["category"] for row in _data["locations"]}
    counts: defaultdict[str, int] = defaultdict(int)
    for row in checks:
        counts[categories.get(row.name, "dynamic_milestones")] += 1
    return counts
