"""Generate shared regional opportunity metadata, without installation-specific assets."""

import json
from typing import Any


def encoded(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return json.dumps(value)
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
    return lines
