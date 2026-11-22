"""Seeded starting-permission candidates and honest unresolved settings previews."""

from collections.abc import Mapping
from typing import TYPE_CHECKING

from .equipment_classes import GROUPS, count_with_aliases
from .equipment_classes import enabled as class_enabled
from .opening import opening_permissions
from .pool_budget import PoolBudget, budget_pool

if TYPE_CHECKING:
    from .configuration import SeedConfiguration


def unlock_candidates(
    configuration: "SeedConfiguration", held: Mapping[str, int]
) -> tuple[str, ...]:
    gear = dict(configuration.gear)
    permitted = count_with_aliases(configuration, lambda name: held.get(name, 0))
    return tuple(
        GROUPS["firearms"]["item_name"]
        if group == "firearms" and class_enabled(configuration)
        else "Equipment Unlock: " + title
        for group, title in (("pda", "PDA"), ("firearms", "Firearms"), ("detector", "Detector"))
        if gear["starting_" + group] == 2 and not permitted("Equipment Unlock: " + title)
    )


def preview_budget(
    configuration: "SeedConfiguration", ids: frozenset[int]
) -> tuple[PoolBudget, dict[str, object]]:
    if not configuration.option("random_starting_unlock"):
        plan = budget_pool(configuration, ids)
        return plan, plan.report()
    candidates = unlock_candidates(configuration, {})
    plans = [budget_pool(configuration, ids, starting={name: 1}) for name in candidates]
    # Validate every possible roll and show the most demanding protected opening.
    plan = max(plans, key=lambda row: len(opening_permissions(configuration, dict(row.starting))))
    report = plan.report()
    report.pop("required_progression")
    report["starting_items"] = {"One seed-random equipment permission": 1}
    report["random_starting_unlock_choices"] = {
        name: row.report() for name, row in zip(candidates, plans, strict=True)
    }
    return plan, report
