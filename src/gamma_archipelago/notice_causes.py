"""Catalogue-backed descriptions of the check that produced a reward."""

import json
from dataclasses import dataclass
from importlib.resources import files

from .catalog import (
    KILL_MILESTONE_BASE,
    MAX_KILL_MILESTONE,
    MAX_SIDE_TASK_MILESTONE,
    SIDE_TASK_MILESTONE_BASE,
)

CAUSE_TEMPLATES = {
    "enter": "by entering {value}",
    "rank": "for reaching {value} rank",
    "mutant": 'by killing a mutant of type "{value}" for the first time',
    "faction": 'by defeating a member of faction "{value}" for the first time',
    "artefact": 'by finding "{value}"',
    "quest": 'by completing a task of type "{value}"',
    "story": 'by completing "{value}"',
    "armour": 'by reaching the "{value}" armour tier',
    "weapon": 'by using a firearm of class "{value}"',
    "knife": "by reaching knife tier {value}",
    "kill_one": "by killing {value} hostile",
    "kill_total": "by killing {value} hostiles",
    "side_one": "by completing {value} side task",
    "side_total": "by completing {value} side tasks",
    "mutant_types_one": "by killing {value} distinct mutant type",
    "mutant_types": "by killing {value} distinct mutant types",
    "faction_types_one": "by defeating a member of {value} distinct faction",
    "faction_types": "by defeating members of {value} distinct factions",
    "artefact_types_one": "by finding {value} distinct artefact type",
    "artefact_types": "by finding {value} distinct artefact types",
    "standing": "by reaching {value} faction goodwill",
    "shop": "by making your first purchase from {value}",
    "firearm_upgrades_one": "by installing {value} firearm upgrade",
    "firearm_upgrades": "by installing {value} firearm upgrades",
    "armour_upgrades_one": "by installing {value} armour upgrade",
    "armour_upgrades": "by installing {value} armour upgrades",
    "check": 'by completing "{value}"',
    "source": 'from "{value}"',
}


@dataclass(frozen=True)
class CheckCause:
    kind: str
    value: str


def value_key(cause: CheckCause) -> str:
    """Stable, data-only resource key; foreign check/source labels stay upstream text."""
    return "gamma_ap_cause_value_" + cause.kind + "_" + cause.value.encode("utf-8").hex()


_data = json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text("utf-8"))
_checks = {row["id"]: row for row in _data["locations"]}
_categories = {
    "checks_maps": "enter",
    "checks_settlements": "enter",
    "checks_rank_milestones": "rank",
    "checks_mutant_first_kills": "mutant",
    "checks_faction_first_kills": "faction",
    "checks_artefacts": "artefact",
    "checks_quest_types": "quest",
    "checks_story_milestones": "story",
    "checks_armour_tiers": "armour",
    "checks_weapon_tiers": "weapon",
    "checks_knife_tiers": "knife",
    "checks_faction_standing": "standing",
    "checks_shops": "shop",
}


def cause_for_check(identity: int, fallback: str) -> CheckCause:
    """Call only after identifying the source slot as GAMMA, never by ID alone."""
    for base, maximum, prefix in (
        (KILL_MILESTONE_BASE, MAX_KILL_MILESTONE, "kill"),
        (SIDE_TASK_MILESTONE_BASE, MAX_SIDE_TASK_MILESTONE, "side"),
    ):
        if base < identity <= base + maximum:
            count = identity - base
            return CheckCause(prefix + ("_one" if count == 1 else "_total"), str(count))
    row = _checks.get(identity)
    if row is None:
        return CheckCause("check", fallback)
    if "quota_group" in row:
        count = row["minimum"]
        kind = row["quota_group"] + "_types" + ("_one" if count == 1 else "")
        return CheckCause(kind, str(count))
    if row["category"] == "checks_gear_upgrades":
        count = row["threshold"]
        return CheckCause(row["key"] + "_upgrades" + ("_one" if count == 1 else ""), str(count))
    kind = _categories.get(row["category"], "check")
    name = row["name"]
    if kind == "enter":
        value = name.rsplit(":", 1)[0]
    elif kind == "knife":
        value = row["key"]
    elif kind == "standing":
        value = str(row["minimum"])
    elif kind == "check":
        value = name
    else:
        value = name.split(":", 1)[-1].strip()
    return CheckCause(kind, value)
