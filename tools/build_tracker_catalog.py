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
                ("weapon_grade", "weapon_grade", ""),
            )
        )
        quota = quoted(row.get("quota_group", ""))
        minimum = row.get("minimum", 0)
        lines.append(
            f"    [{row['id']}]={{{fields}, quota={quota}, minimum={minimum},"
            f" price={row.get('price', 0)}, quests={{{permissions}}}}},"
        )
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
    lines.extend(["}", "shop_offers = {"])
    for row in catalogue["locations"]:
        if row["category"] == "checks_shop_purchases":
            lines.append(
                f"    [{row['id']}]={{shop={quoted(row['shop'])},level={quoted(row['level'])},"
                f"price={row['price']},name={quoted(row['name'])},"
                f"description={quoted(row['description'])}}},"
            )
    lines.extend(["}", "faction_standing_locations = {"])
    lines.extend(
        f"    [{row['minimum']}]={row['id']},"
        for row in catalogue["locations"]
        if row["category"] == "checks_faction_standing"
    )
    lines.extend(["}", "faction_standing_factions = {"])
    lines.extend(f"    {quoted(name)}," for name in catalogue.get("faction_standing_factions", []))
    lines.extend(["}", "discovery_sources = {"])
    groups = {
        "checks_mutant_first_kills": "mutant",
        "checks_faction_first_kills": "faction",
        "checks_artefacts": "artefact",
    }
    for row in catalogue["locations"]:
        group = groups.get(row["category"])
        if group and "quota_group" not in row:
            token = quoted(group + ":" + row["key"])
            lines.append(f"    [{row['id']}]={{group={quoted(group)},token={token}}},")
    lines.extend(["}", "discovery_quotas = {"])
    for group in groups.values():
        values = ",".join(
            str(row["id"]) for row in catalogue["locations"] if row.get("quota_group") == group
        )
        lines.append(f"    {group}={{{values}}},")
    lines.extend(["}", "missable_checks = {"])
    lines.extend(
        f"    [{row['id']}]=true," for row in catalogue["locations"] if row.get("missable")
    )
    lines.extend(["}", "delivery_contents = {"])
    for row in catalogue["items"]:
        if "supplies" in row or "tier_supplies" in row or "calibre_supplies" in row:
            tiers = row.get("calibre_supplies", row.get("tier_supplies", [row.get("supplies", [])]))
            values = ",".join(
                "{" + ",".join(quoted(section) for section in tier) + "}" for tier in tiers
            )
            lines.append(f"    [{row['id']}]={{{values}}},")
    lines.extend(["}", "delivery_legacy_contents = {"])
    for row in catalogue["items"]:
        if "legacy_supplies_v1" in row:
            sections = ",".join(quoted(section) for section in row["legacy_supplies_v1"])
            lines.append(f"    [{row['id']}]={{{sections}}},")
    return lines + ["}"]
