"""Finite discovery rosters and configured location selection."""

import json
from importlib.resources import files
from typing import TYPE_CHECKING

from .catalog import enabled_location_ids
from .playability import fragile_ids

if TYPE_CHECKING:
    from .configuration import SeedConfiguration

_data = json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text("utf-8"))
GROUPS = {
    "mutant": "checks_mutant_first_kills",
    "faction": "checks_faction_first_kills",
    "artefact": "checks_artefacts",
}
SOURCES: dict[str, dict[str, int]] = {
    group: {
        f"{group}:{row['key']}": row["id"]
        for row in _data["locations"]
        if row["category"] == category and "quota_group" not in row
    }
    for group, category in GROUPS.items()
}
QUOTAS: dict[str, tuple[int, ...]] = {
    group: tuple(row["id"] for row in _data["locations"] if row.get("quota_group") == group)
    for group in GROUPS
}
TOKENS = frozenset(token for roster in SOURCES.values() for token in roster)
MISSABLE_IDS = frozenset(row["id"] for row in _data["locations"] if row.get("missable"))


def normalize_exclusions(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, set, frozenset)) or len(value) > len(TOKENS):
        raise ValueError("Discovery exclusions must be a bounded list/set of canonical type tokens")
    if any(type(token) is not str or token not in TOKENS for token in value):
        raise ValueError("Unknown discovery exclusion; use mutant:, faction: or artefact: tokens")
    if len(set(value)) != len(value):
        raise ValueError("Discovery exclusions must not repeat a token")
    return tuple(sorted(value))


def configured_location_ids(configuration: "SeedConfiguration") -> frozenset[int]:
    ids = set(
        enabled_location_ids(
            configuration.checks, configuration.kill_milestones, configuration.side_task_milestones
        )
    )
    excluded = set(configuration.discovery_exclusions)
    for group, category in GROUPS.items():
        roster = SOURCES[group]
        qualifying = set(roster) - excluded
        ids.difference_update(roster.values())
        if category not in configuration.checks:
            continue
        if configuration.option(f"{group}_discovery_mode"):
            count = configuration.option(f"{group}_discovery_count") or len(qualifying)
            if not 1 <= count <= len(qualifying):
                raise ValueError(f"{group} discovery quota exceeds its qualifying roster")
            ids.update(QUOTAS[group][:count])
        else:
            ids.update(roster[token] for token in qualifying)
    if configuration.option("optional_check_policy") == 1:
        ids.difference_update(fragile_ids(configuration))
    protected_tail_ids(configuration, frozenset(ids))
    if not ids:
        raise ValueError("The configured exclusions leave no checks")
    return frozenset(ids)


def protected_tail_ids(
    configuration: "SeedConfiguration", check_ids: frozenset[int]
) -> frozenset[int]:
    """Reserve the final X generic discoveries for filler, never a named rare type."""
    result: set[int] = set()
    for group in ("mutant", "artefact"):
        tail = configuration.option(f"{group}_filler_tail")
        if not tail:
            continue
        if GROUPS[group] not in configuration.checks or not configuration.option(
            f"{group}_discovery_mode"
        ):
            raise ValueError(f"{group} filler tail requires enabled generic discovery checks")
        count = configuration.option(f"{group}_discovery_count") or len(
            set(SOURCES[group]) - set(configuration.discovery_exclusions)
        )
        selected = QUOTAS[group][:count]
        if tail > len(selected):
            raise ValueError(f"{group} filler tail exceeds its configured discovery quota")
        result.update(selected[-tail:])
    return frozenset(result) & check_ids
