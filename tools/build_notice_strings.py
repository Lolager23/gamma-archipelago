"""Build the English translator reference from owned templates and stable reward IDs."""

from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element, SubElement, indent, tostring

from gamma_archipelago.notice_text import ENGLISH_TEMPLATES
from gamma_archipelago.paths import require_safe_child


def generate_notice_strings(root: Path, catalogue: dict[str, Any]) -> None:
    strings = Element("string_table")
    entries = {"gamma_ap_notice_" + key: value for key, value in ENGLISH_TEMPLATES.items()}
    entries.update({f"gamma_ap_reward_{row['id']}": row["name"] for row in catalogue["items"]})
    for key, value in sorted(entries.items()):
        SubElement(SubElement(strings, "string", id=key), "text").text = value
    indent(strings, space="    ")
    destination = require_safe_child(root, "mod/gamedata/configs/text/eng/st_gamma_ap_notices.xml")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(
        b'<?xml version="1.0" encoding="utf-8"?>\n' + tostring(strings, encoding="utf-8") + b"\n"
    )
