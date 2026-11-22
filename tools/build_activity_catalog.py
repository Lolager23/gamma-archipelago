"""Generate shared regional opportunity metadata, without installation-specific assets."""

import json
from dataclasses import asdict
from typing import Any

from gamma_archipelago.playability import FRIENDLY_FACTIONS, NORTH, RANK_PROXY
from gamma_archipelago.settlement_access import SETTLEMENT_RULES


def encoded(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        return "{" + ",".join(encoded(item) for item in value) + "}"
    return (
        "{" + ",".join(f"[{json.dumps(key)}]={encoded(item)}" for key, item in value.items()) + "}"
    )


def activity_lines(catalog: dict[str, Any]) -> list[str]:
    lines = ["activity_rules = {"]
    for row in catalog["locations"]:
        if "logic" in row:
            lines.append(f"    [{row['id']}]={encoded(row['logic'])},")
    lines.extend(["}", "activity_regions = " + encoded(catalog["activity_regions"])])
    lines.append("settlement_rules = {")
    lines.extend(f"    [{id}]={encoded(asdict(rule))}," for id, rule in SETTLEMENT_RULES.items())
    lines.append("}")
    lines.append("rank_goodwill_proxy = " + encoded({str(k): v for k, v in RANK_PROXY.items()}))
    lines.append("northern_equipment_regions = " + encoded(list(NORTH)))
    projections = {
        "quest_zone_gates": catalog["quest_zone_gates"],
        "tool_use_items": {
            row["id"]: {
                key: row[key] for key in ("tool_key", "tool_section", "permission", "category")
            }
            | {"tier": row.get("kit_tier", 0), "name": row["name"]}
            for row in catalog["items"]
            if "tool_key" in row
        },
        "opening_economy": catalog["opening_economy"],
        "friendly_goodwill_factions": {name: True for name in sorted(FRIENDLY_FACTIONS)},
        "melter_sections": {
            row["id"]: row["melter_section"] for row in catalog["items"] if "melter_section" in row
        },
        "story_arcs": {
            row["id"]: row["story_arc"] for row in catalog["locations"] if "story_arc" in row
        },
        "tool_stash_levels": {
            row["id"]: row["tool_level"] for row in catalog["items"] if "tool_level" in row
        },
        "weather_levels": {level: True for level in catalog["weather_levels"]},
        "weapon_grade_locations": {
            row["repair_type"]: row["id"] for row in catalog["locations"] if "weapon_grade" in row
        },
        "weapon_grade_ids": {
            row["id"]: True for row in catalog["locations"] if "weapon_grade" in row
        },
        "protected_stash_items": {
            row["id"]: True for row in catalog["items"] if row.get("protect_psi")
        },
    }
    lines.extend(name + " = " + encoded(values) for name, values in projections.items())
    return lines
