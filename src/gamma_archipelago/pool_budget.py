"""Budget required permissions before useful rewards or filler, including starting items."""

import json
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.resources import files

from .catalog import MAX_ITEMS, enabled_item_ids
from .configuration import SeedConfiguration
from .discovery import MISSABLE_IDS, configured_location_ids, protected_tail_ids
from .opening import opening_checks, opening_permissions
from .starting import starting_level

_catalog = json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text("utf-8"))
_items = {row["name"]: row for row in _catalog["items"]}
CARRY = "Carry Capacity +5 kg"


@dataclass(frozen=True)
class PoolBudget:
    required: tuple[str, ...]
    convenience: tuple[str, ...]
    filler_slots: int
    network_checks: int
    eligible_checks: int
    starting: tuple[tuple[str, int], ...]
    from_pool: tuple[tuple[str, int], ...]

    def report(self) -> dict[str, object]:
        return {
            "required_progression": dict(Counter(self.required)),
            "required_copies": len(self.required),
            "remaining_progression_copies": len(self.required)
            - sum(count for name, count in self.from_pool if name in self.required),
            "guaranteed_useful": dict(Counter(self.convenience)),
            "filler_slots": self.filler_slots,
            "network_checks": self.network_checks,
            "eligible_checks": self.eligible_checks,
            "starting_items": dict(self.starting),
            "starting_from_pool": dict(self.from_pool),
        }


def _counts(values: Mapping[str, int], enabled: frozenset[int]) -> Counter[str]:
    result: Counter[str] = Counter()
    for name, count in values.items():
        if name not in _items or _items[name]["id"] not in enabled:
            raise ValueError("Starting items must belong to the enabled reward manifest")
        if type(count) is not int or not 0 <= count <= MAX_ITEMS:
            raise ValueError("Starting item counts must be bounded nonnegative integers")
        if count:
            result[name] = count
    return result


def budget_pool(
    configuration: SeedConfiguration,
    check_ids: frozenset[int],
    excluded: frozenset[int] = frozenset(),
    starting: Mapping[str, int] | None = None,
    from_pool: Mapping[str, int] | None = None,
) -> PoolBudget:
    if (
        not check_ids
        or not check_ids <= configured_location_ids(configuration)
        or not excluded <= check_ids
    ):
        raise ValueError("Pool checks must be a nonempty subset of this seed's enabled manifest")
    enabled = enabled_item_ids(configuration.rewards, configuration.gear)
    collected = _counts(starting or {}, enabled)
    depleted = _counts(from_pool or {}, enabled)
    if any(count > collected[name] for name, count in depleted.items()):
        raise ValueError("Starting-from-pool items must already be precollected by Archipelago")
    if len(check_ids) + collected.total() > MAX_ITEMS:
        raise ValueError("Generated and starting item history exceeds the supported receipt limit")
    gifts = collected - depleted
    required: Counter[str] = Counter()
    for name, row in _items.items():
        if row["id"] in enabled and row["classification"] == "progression":
            if row.get("category") == "rewards_zone_keys" and row.get("level") == starting_level(
                configuration
            ):
                continue  # The chosen starting zone is always accessible.
            required[name] = max(0, row.get("copies", 1) - gifts[name])
    if configuration.option("optional_check_policy") == 0:
        excluded = excluded | (MISSABLE_IDS & check_ids)
    excluded = excluded | protected_tail_ids(configuration, check_ids)
    slots, eligible = len(check_ids), len(check_ids - excluded)
    remaining_required = sum(max(0, count - depleted[name]) for name, count in required.items())
    if required.total() > slots or remaining_required > eligible:
        raise ValueError(
            "The selected check pool cannot hold required progression rewards in reliable checks"
        )
    convenience = 0
    if "rewards_convenience" in configuration.rewards:
        convenience = min(
            max(0, 3 - gifts[CARRY]),
            slots - required.total(),
            eligible - remaining_required + depleted[CARRY],
        )
        if convenience == 0 and not collected[CARRY]:
            raise ValueError("Convenience rewards need a reliable check after required progression")
    guaranteed = required + Counter({CARRY: convenience})
    if any(count > guaranteed[name] for name, count in depleted.items()):
        raise ValueError("Starting-from-pool requests must fit guaranteed permission/carry copies")
    zone_remaining = any(
        row.get("category") == "rewards_zone_keys" and required[name] > depleted[name]
        for name, row in _items.items()
    )
    critical = opening_permissions(configuration, collected)
    if len(critical) > len(
        opening_checks(check_ids, excluded, zone_remaining, starting_level(configuration))
    ):
        raise ValueError(
            "Protected opening needs more reliable Cordon checks: enable settlements, "
            "relax locked starting gear, or select the legacy/challenge opening"
        )
    return PoolBudget(
        tuple(required.elements()),
        (CARRY,) * convenience,
        slots - required.total() - convenience,
        slots,
        eligible,
        tuple(sorted(collected.items())),
        tuple(sorted(depleted.items())),
    )
