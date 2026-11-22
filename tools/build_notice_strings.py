"""Build the English translator reference from owned templates and stable reward IDs."""

from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element, SubElement, indent, tostring

from gamma_archipelago.notice_causes import CAUSE_TEMPLATES, cause_for_check, value_key
from gamma_archipelago.notice_text import CAUSAL_TEMPLATES, ENGLISH_TEMPLATES, JOIN_TEMPLATE
from gamma_archipelago.paths import require_safe_child


def generate_notice_strings(root: Path, catalogue: dict[str, Any]) -> None:
    strings = Element("string_table")
    entries = {"gamma_ap_notice_" + key: value for key, value in ENGLISH_TEMPLATES.items()}
    entries.update(
        {"gamma_ap_notice_" + key + "_cause": value for key, value in CAUSAL_TEMPLATES.items()}
    )
    entries.update({"gamma_ap_cause_" + key: value for key, value in CAUSE_TEMPLATES.items()})
    for row in catalogue["locations"]:
        cause = cause_for_check(row["id"], row["name"])
        if cause.kind not in {"check", "source"}:
            entries[value_key(cause)] = cause.value
    entries["gamma_ap_notice_joined"] = JOIN_TEMPLATE
    entries["gamma_ap_tool_permission_required"] = "AP permission required to use: "
    entries["gamma_ap_tool_session_required"] = "Restore a valid AP session before using this kit"
    entries.update({f"gamma_ap_reward_{row['id']}": row["name"] for row in catalogue["items"]})
    for key, value in sorted(entries.items()):
        SubElement(SubElement(strings, "string", id=key), "text").text = value
    indent(strings, space="    ")
    destination = require_safe_child(root, "mod/gamedata/configs/text/eng/st_gamma_ap_notices.xml")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(
        b'<?xml version="1.0" encoding="utf-8"?>\n' + tostring(strings, encoding="utf-8") + b"\n"
    )
