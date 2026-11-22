"""Opaque labels do not need English articles or player-name possessives."""

import json
from dataclasses import replace
from pathlib import Path
from xml.etree import ElementTree

import pytest

from gamma_archipelago.catalog import GAME
from gamma_archipelago.notice_text import TransferMessage, render_english
from gamma_archipelago.notifications import Notice, encode_notices, transfer_notice, validate_notice
from gamma_archipelago.protocol import ProtocolError

ROOT = Path(__file__).resolve().parents[2]
KEY = "a" * 64


@pytest.mark.parametrize("item", ["100 Rupees", "Arrows", "an Artifact", "PDA", "{player}"])
@pytest.mark.parametrize(
    ("kind", "template"),
    [
        ("received_item", 'James gave you "{}".'),
        ("received_unlock", 'James unlocked your "{}".'),
        ("sent_item", 'You sent "{}" to James.'),
        ("sent_unlock", 'You unlocked "{}" for James.'),
    ],
)
def test_grammar_handles_plural_currency_acronym_and_foreign_labels(kind, template, item):
    assert render_english(TransferMessage(kind, "James", item)) == template.format(item)
    assert render_english(TransferMessage(kind, "{item}", item)).count("{item}") >= 1


@pytest.mark.parametrize(
    "message",
    [
        TransferMessage("bad", "James", "Reward"),
        TransferMessage([], "James", "Reward"),
        TransferMessage("sent_item", "", "Reward"),
        TransferMessage("sent_item", "James", "A" * 97),
        TransferMessage("sent_item", "James", "%c[red]"),
        TransferMessage("sent_item", "James", 1),
        TransferMessage("sent_item", "James", "Reward", True),
        TransferMessage("sent_item", "James", "Reward", 999),
    ],
)
def test_invalid_semantic_fields_are_rejected(message):
    with pytest.raises(ProtocolError):
        render_english(message)


def test_semantic_snapshot_supports_mixed_legacy_records_and_foreign_id_collisions():
    foreign = transfer_notice(
        "s:3:2:28051001",
        0,
        "James",
        "Foreign",
        item_id=28051001,
        game="Foreign Game",
        outgoing=True,
    )
    owned = transfer_notice(
        "r:0", 1, "Friend", "Toolkit", item_id=28051001, game=GAME, outgoing=False
    )
    assert foreign.transfer.local_item_id == 0
    assert owned.transfer.local_item_id == 28051001
    encoded = encode_notices(KEY, (foreign, owned, Notice("r:1", 2, "Legacy")))
    assert encoded.startswith("GAMMA_AP_NOTICES|2\n")
    assert "notice|r:1|2|text|4c6567616379" in encoded
    assert "|sent_item|4a616d6573|466f726569676e|0" in encoded
    with pytest.raises(ProtocolError, match="fallback"):
        validate_notice(replace(owned, text="Different"))
    with pytest.raises(ProtocolError, match="direction"):
        validate_notice(replace(owned, identity="s:3:2:4", minimum_received=0))


def test_generated_reference_covers_exactly_templates_and_catalogue_rewards():
    from gamma_archipelago.notice_causes import CAUSE_TEMPLATES, cause_for_check, value_key
    from gamma_archipelago.notice_text import CAUSAL_TEMPLATES, ENGLISH_TEMPLATES, JOIN_TEMPLATE

    catalogue = json.loads((ROOT / "src/gamma_archipelago/catalog.json").read_text())
    xml = ElementTree.parse(ROOT / "mod/gamedata/configs/text/eng/st_gamma_ap_notices.xml")
    actual = {node.attrib["id"]: node.findtext("text") for node in xml.getroot()}
    expected = {"gamma_ap_notice_" + key: value for key, value in ENGLISH_TEMPLATES.items()}
    expected.update(
        {"gamma_ap_notice_" + key + "_cause": value for key, value in CAUSAL_TEMPLATES.items()}
    )
    expected.update({"gamma_ap_cause_" + key: value for key, value in CAUSE_TEMPLATES.items()})
    for row in catalogue["locations"]:
        cause = cause_for_check(row["id"], row["name"])
        if cause.kind not in {"check", "source"}:
            expected[value_key(cause)] = cause.value
    expected["gamma_ap_notice_joined"] = JOIN_TEMPLATE
    expected["gamma_ap_tool_permission_required"] = "AP permission required to use: "
    expected["gamma_ap_tool_session_required"] = "Restore a valid AP session before using this kit"
    expected.update({f"gamma_ap_reward_{row['id']}": row["name"] for row in catalogue["items"]})
    assert actual == expected
