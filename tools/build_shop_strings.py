"""Generate translation-ready offer names and descriptions from the catalogue."""

from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element, SubElement, indent, tostring

from gamma_archipelago.paths import require_safe_child


def generate_shop_strings(root: Path, catalogue: dict[str, Any]) -> None:
    strings = Element("string_table")
    entries = {
        "open": "AP shop",
        "back": "Trader goods",
        "title": "Archipelago contracts",
        "buy": "Buy for %s RU",
        "purchased": "Purchased",
        "uncertain": "Payment needs review",
        "balance": "Your money: %s RU",
        "hidden": "Assigned reward is hidden.",
        "reward": "Scouted reward: %s for %s",
        "footer": (
            "One purchase per check. Rewards are sent through your AP companion. "
            "Close trade to resume normal reward delivery."
        ),
    }
    for row in catalogue["locations"]:
        if row["category"] == "checks_shop_purchases":
            entries[f"name_{row['id']}"] = row["name"].removeprefix("AP Shop: ")
            entries[f"description_{row['id']}"] = row["description"]
    for key, text in sorted(entries.items()):
        SubElement(SubElement(strings, "string", id="gamma_ap_shop_" + key), "text").text = text
    indent(strings, space="    ")
    destination = require_safe_child(root, "mod/gamedata/configs/text/eng/st_gamma_ap_shop.xml")
    destination.write_bytes(tostring(strings, encoding="utf-8") + b"\n")
