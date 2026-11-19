"""Generate the PDA's display projection from the authoritative catalogue."""

import json
from typing import Any


def tracker_lines(catalogue: dict[str, Any]) -> list[str]:
    def quoted(value: str) -> str:
        return json.dumps(value, ensure_ascii=False)

    lines = ["tracker_checks = {"]
    for row in catalogue["locations"]:
        keys = [catalogue["quest_gates"][row["tasks"][0]]] if row.get("tasks") else []
        required = sorted(
            {key for permission in keys for key in catalogue["quest_key_requirements"][permission]}
        )
        permissions = ",".join(quoted(key) for key in required)
        fields = ",".join(
            f"{key}={quoted(row.get(source, default))}"
            for key, source, default in (
                ("name", "name", ""),
                ("region", "level", "Menu"),
                ("category", "category", ""),
                ("key", "key", ""),
            )
        )
        lines.append(f"    [{row['id']}]={{{fields}, quests={{{permissions}}}}},")
    lines.extend(["}", "tracker_regions = {"])
    lines.extend(f"    [{quoted(row['id'])}]={quoted(row['name'])}," for row in catalogue["levels"])
    lines.extend(["}", "tracker_connections = {"])
    lines.extend(f"    {{{quoted(a)},{quoted(b)}}}," for a, b in catalogue["connections"])
    lines.extend(["}", "tracker_permissions = {"])
    lines.extend(
        f"    [{quoted(row['permission'])}]={quoted(row['name'])},"
        for row in catalogue["items"]
        if "permission" in row
    )
    lines.extend(["}", "tracker_item_names = {"])
    lines.extend(f"    [{row['id']}]={quoted(row['name'])}," for row in catalogue["items"])
    lines.extend(["}", "tracker_milestones = {"])
    for category, row in catalogue["milestones"].items():
        lines.append(f"    {category}={quoted(row['name'])},")
    lines.extend(["}", "shop_locations = {"])
    lines.extend(
        f"    [{quoted(row['key'])}]={row['id']},"
        for row in catalogue["locations"]
        if row["category"] == "checks_shops"
    )
    lines.extend(["}", "faction_standing_locations = {"])
    lines.extend(
        f"    [{row['minimum']}]={row['id']},"
        for row in catalogue["locations"]
        if row["category"] == "checks_faction_standing"
    )
    lines.extend(["}", "faction_standing_factions = {"])
    lines.extend(f"    {quoted(name)}," for name in catalogue.get("faction_standing_factions", []))
    return lines + ["}"]
