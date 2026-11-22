"""Generate shared regional opportunity metadata, without installation-specific assets."""

import json
from dataclasses import asdict
from typing import Any

from gamma_archipelago.playability import NORTH, RANK_PROXY
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
    return lines
