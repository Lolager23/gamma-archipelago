"""Catalogue-backed regional opportunities; never infer native encounter probability."""

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .configuration import SeedConfiguration

_catalog = json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text("utf-8"))
_locations = {row["id"]: row for row in _catalog["locations"]}
_groups = {
    "mutant": "checks_mutant_first_kills",
    "faction": "checks_faction_first_kills",
    "artefact": "checks_artefacts",
}
_sources = {
    group: tuple(
        row
        for row in _locations.values()
        if row["category"] == category and "quota_group" not in row
    )
    for group, category in _groups.items()
}


@dataclass(frozen=True)
class RegionalRequirement:
    sources: tuple[tuple[str, ...], ...] = ()
    minimum: int = 0
    all_regions: tuple[str, ...] = ()
    reliable: bool = True

    def accessible(self, reachable: Callable[[str], bool]) -> bool:
        # A single view can reference one region through many source types.
        # Keep this cache local: AP state can change before the next query.
        known: dict[str, bool] = {}

        def available(region: str) -> bool:
            if region not in known:
                known[region] = reachable(region)
            return known[region]

        return (
            all(available(region) for region in self.all_regions)
            and sum(any(available(region) for region in source) for source in self.sources)
            >= self.minimum
        )


def regional_requirement(
    definition: Mapping[str, Any], configuration: "SeedConfiguration"
) -> RegionalRequirement:
    """Distinct quotas count distinct verified source types, never map count or repeats."""
    group = definition.get("quota_group")
    if group:
        sources = tuple(
            tuple(row["logic"]["any_regions"])
            for row in _sources[group]
            if row["logic"]["reliable"]
            and f"{group}:{row['key']}" not in configuration.discovery_exclusions
        )
        minimum = definition["minimum"]
        # An unverified final type stays an optional filler opportunity. It may
        # not increase the count used to justify a required progression item.
        return RegionalRequirement(sources, min(minimum, len(sources)), (), minimum <= len(sources))
    logic = definition.get("logic")
    if logic is not None:
        regions = tuple(logic["any_regions"])
        return RegionalRequirement(
            (regions,) if regions else (),
            int(bool(regions)),
            tuple(logic["all_regions"]),
            logic["reliable"],
        )
    regions = tuple(_catalog["activity_regions"].get(definition["category"], ()))
    return RegionalRequirement((regions,) if regions else (), int(bool(regions)))


@lru_cache(maxsize=128)
def unreliable_check_ids(configuration: "SeedConfiguration") -> frozenset[int]:
    """Keep unsupported per-type sources and quota excess out of progression budgets."""
    return frozenset(
        row["id"]
        for row in _locations.values()
        if not regional_requirement(row, configuration).reliable
    )
