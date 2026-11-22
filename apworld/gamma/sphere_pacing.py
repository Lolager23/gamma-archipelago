"""Bounded placement repair using existing access rules, never invented check gates."""

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from BaseClasses import CollectionState, Location, MultiWorld
from Fill import swap_location_item
from Options import OptionError

from gamma_archipelago.catalog import GAME

from .analysis import PROGRESSIVE_REWARDS, early_checks

if TYPE_CHECKING:
    from . import GammaWorld


@dataclass
class Trace:
    waves: dict[str, dict[Location, int]]
    collisions: list[tuple[str, int, str, int, list[Location]]]
    valid: bool
    state: CollectionState

    @property
    def score(self) -> int:
        return sum(len(rows) - 1 for _, _, _, _, rows in self.collisions)


def _worlds(multiworld: MultiWorld) -> list["GammaWorld"]:
    return [
        cast("GammaWorld", world)
        for player in multiworld.player_ids
        for world in [multiworld.worlds[player]]
        if world.game == GAME and world.configuration.option("progressive_sphere_pacing")
    ]


def _owners(multiworld: MultiWorld, worlds: list["GammaWorld"]) -> set[int]:
    players = {world.player for world in worlds}
    return players | {
        identity
        for identity, group in multiworld.groups.items()
        if group["game"] == GAME
        and group["players"] & players
        and group["item_pool"] & PROGRESSIVE_REWARDS
    }


def _progressive(location: Location, players: set[int]) -> bool:
    return bool(
        location.address is not None
        and location.item
        and location.item.player in players
        and location.item.name in PROGRESSIVE_REWARDS
    )


def _waves(multiworld: MultiWorld, settle: bool) -> tuple[dict[Location, int], CollectionState]:
    state = CollectionState(multiworld)
    remaining = set(multiworld.get_filled_locations())
    events = [row for row in remaining if row.address is None]
    waves = {}
    number = 0
    while remaining:
        if settle:
            state.sweep_for_advancements(locations=events)
            remaining.difference_update(state.advancements)
        rows = sorted(
            (row for row in remaining if row.can_reach(state)),
            key=lambda row: (row.player, row.address or 0, row.name),
        )
        if not rows:
            break
        number += 1
        for row in rows:
            waves[row] = number
            state.collect(row.item, True, row)
        remaining.difference_update(rows)
    return waves, state


def _trace(multiworld: MultiWorld, players: set[int]) -> Trace:
    collapsed, state = _waves(multiworld, True)
    actual, _ = _waves(multiworld, False)
    waves = {"network": collapsed, "upstream": actual}
    collisions = []
    for model, mapping in waves.items():
        groups = defaultdict(list)
        for row, number in mapping.items():
            if _progressive(row, players):
                groups[(row.item.player, row.item.name, number)].append(row)
        for (player, name, number), rows in groups.items():
            if len(rows) > 1:
                collisions.append((model, player, name, number, rows))
    collisions.sort(key=lambda row: (row[3], row[0], row[1], row[2]))
    required = [
        row
        for row in multiworld.get_filled_locations()
        if row.address is not None and (row.player in players or _progressive(row, players))
    ]
    valid = all(row in collapsed for row in required) and all(
        multiworld.completion_condition[player](state) for player in multiworld.player_ids
    )
    return Trace(waves, collisions, valid, state)


def _recipes_on_time(worlds: list["GammaWorld"]) -> bool:
    protected = [
        world
        for world in worlds
        if world.configuration.option("regional_progression")
        and world.configuration.option("playability_logic")
    ]
    if not protected:
        return True
    reached = early_checks(protected[0], 3)
    for world in protected:
        gifts = {item.name for item in world.multiworld.precollected_items[world.player]}
        for row in world.multiworld.get_filled_locations():
            item = row.item
            if (
                row.address is not None
                and item.player == world.player
                and item.name.startswith("Recipe Access:")
                and item.name not in gifts
                and row not in reached
            ):
                return False
    return True


def _candidates(
    world: "GammaWorld", trace: Trace, players: set[int], source: Location, model: str, number: int
) -> list[Location]:
    item = source.item
    candidates = []
    for row, wave in trace.waves[model].items():
        if (
            wave <= number
            or row.address is None
            or row.locked
            or _progressive(row, players)
            or row.item.advancement
        ):
            continue
        if row.can_fill(trace.state, item, False) and source.can_fill(trace.state, row.item, False):
            candidates.append(row)
    world.random.shuffle(candidates)
    candidates.sort(key=lambda row: trace.waves[model][row])
    return candidates[:256]


def _improve(
    world: "GammaWorld", worlds: list["GammaWorld"], trace: Trace, players: set[int]
) -> Trace | None:
    for model, _, _, number, rows in trace.collisions:
        movable = [row for row in rows if not row.locked]
        world.random.shuffle(movable)
        for source in movable:
            for destination in _candidates(world, trace, players, source, model, number):
                swap_location_item(source, destination)
                try:
                    candidate = _trace(world.multiworld, players)
                    usable = (
                        candidate.valid
                        and candidate.score < trace.score
                        and _recipes_on_time(worlds)
                        and all(
                            trace.waves[model].keys() <= candidate.waves[model].keys()
                            for model in trace.waves
                        )
                    )
                finally:
                    swap_location_item(source, destination)
                if usable:
                    swap_location_item(source, destination)
                    return candidate
    return None


def _restore(snapshot: dict[Location, tuple]) -> None:
    for row, (item, locked) in snapshot.items():
        row.item, row.locked = item, locked
        item.location = row


def pace(multiworld: MultiWorld) -> None:
    worlds = _worlds(multiworld)
    if not worlds:
        return
    players = _owners(multiworld, worlds)
    snapshot = {row: (row.item, row.locked) for row in multiworld.get_filled_locations()}
    complete = False
    try:
        for attempt in range(4):
            if attempt:
                _restore(snapshot)
            trace = _trace(multiworld, players)
            for _ in range(64 * len(worlds)):
                if trace.valid and not trace.collisions and _recipes_on_time(worlds):
                    for row in snapshot:
                        if _progressive(row, players):
                            row.locked = True
                    complete = True
                    return
                trace = _improve(worlds[0], worlds, trace, players) if trace.collisions else None
                if trace is None:
                    break
        raise OptionError(
            "Cannot separate progressive tiers into distinct AP spheres without "
            "breaking access or early recipes. Enable more gated checks, increase "
            "initial tiers, revise fixed placements, or disable progressive_sphere_pacing."
        )
    finally:
        if not complete:
            _restore(snapshot)


def validate(multiworld: MultiWorld) -> None:
    worlds = _worlds(multiworld)
    if worlds:
        trace = _trace(multiworld, _owners(multiworld, worlds))
        if not trace.valid or trace.collisions or not _recipes_on_time(worlds):
            raise OptionError(
                "Final placements violate progressive_sphere_pacing; a later fill "
                "or balancing stage changed the verified spheres. Review fixed "
                "placements/progression balancing or disable the pacing option."
            )
