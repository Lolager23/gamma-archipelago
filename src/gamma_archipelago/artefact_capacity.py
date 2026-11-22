"""Resolve optional artefact checks from non-filler demand before regions exist."""

from collections import Counter
from collections.abc import Mapping
from typing import TYPE_CHECKING

from .configuration import build_configuration
from .discovery import configured_location_ids
from .pool_budget import CARRY, protected_checks, required_counts
from .reward_quantities import requested, useful_count

if TYPE_CHECKING:
    from .configuration import SeedConfiguration


def resolve_capacity(
    configuration: "SeedConfiguration",
    excluded: frozenset[int] = frozenset(),
    starting: Mapping[str, int] | None = None,
    from_pool: Mapping[str, int] | None = None,
) -> "SeedConfiguration":
    values = {**configuration.to_values(), "artefact_overflow_count": 0}
    base = build_configuration(values)
    if not (
        base.option("content_progression")
        and base.option("artefact_discovery_mode")
        and "checks_artefacts" in base.checks
        and base.option("artefact_discovery_count") in (0, 40)
        and "rewards_artefact_melter" in base.rewards
    ):
        return base
    collected, depleted = Counter(starting or {}), Counter(from_pool or {})
    gifts = collected - depleted
    ids = configured_location_ids(base)
    required = required_counts(base, ids, gifts)
    extras = requested(base) - (gifts - required_counts(base, ids, {}))
    carry = max(0, 3 - gifts[CARRY]) if "rewards_convenience" in base.rewards else 0
    nonfiller = useful_count(required + extras + Counter({CARRY: carry}) - depleted)
    ceiling = max(0, base.option("artefact_extra_ceiling") - 40)
    for extra in range(min(20, ceiling) + 1):
        candidate = build_configuration({**values, "artefact_overflow_count": extra})
        ids = configured_location_ids(candidate)
        eligible = len(ids - protected_checks(candidate, ids, excluded & ids))
        if nonfiller <= eligible:
            return candidate
    # The strict pool budget reports the remaining capacity failure. Never add
    # checks just to fit filler, or silently discard the requested useful items.
    return candidate
