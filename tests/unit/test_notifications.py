import pytest

from gamma_archipelago.notifications import (
    MAX_ACK_BYTES,
    MAX_NOTICE_BATCH,
    MAX_NOTICES,
    Notice,
    NoticeSessionMismatch,
    clean_label,
    decode_acknowledgements,
    encode_notices,
    is_unlock,
    pending_batch,
    reward_message,
    validate_notice,
)
from gamma_archipelago.protocol import ProtocolError
from gamma_archipelago.session import SessionCoordinator

KEY = "a" * 64


def test_only_explicit_known_permissions_use_unlock_wording(monkeypatch):
    from gamma_archipelago import notifications

    monkeypatch.setitem(notifications.ITEM_EFFECTS, 42, "unlock")
    assert is_unlock(42, notifications.GAME)
    assert not is_unlock(42, "Foreign Game")
    assert not is_unlock(28051001, notifications.GAME)


def ack(*identities, key=KEY):
    return "\n".join(
        ["GAMMA_AP_NOTICES_ACK|1", f"session|{key}", *identities, f"end|{len(identities)}", ""]
    )


def test_unicode_labels_keep_names_but_cannot_inject_lines_or_pda_markup():
    assert clean_label("  Оуэн\n%c[red]<x>|\u202e ") == "Оуэн c red x"
    assert clean_label("\n%[]<>") == "Archipelago"
    assert len(clean_label("A" * 200)) == 96
    assert (
        reward_message("Owen", "Toolkit", unlock=False, outgoing=False) == "Owen gave you a Toolkit"
    )
    assert reward_message("Owen", "Zone", unlock=True, outgoing=False) == "Owen unlocked your Zone"
    assert reward_message("Owen", "Zone", unlock=True, outgoing=True) == "You unlocked Owen's Zone"
    assert reward_message("Owen", "Rupees", unlock=False, outgoing=True) == "You gave Owen Rupees"


@pytest.mark.parametrize(
    "notice",
    [
        Notice("bad", 0, "x"),
        Notice("r:4000", 4001, "x"),
        Notice("s:01:2:3", 0, "x"),
        Notice("r:0", True, "x"),
        Notice("r:0", -1, "x"),
        Notice("r:0", 4001, "x"),
        Notice("r:0", 0, "x"),
        Notice("s:1:2:3", 1, "x"),
        Notice("r:0", 1, ""),
        Notice("r:0", 1, "x" * 2049),
        Notice("r:0", 1, "%c[red]"),
        Notice("r:0", 1, "injected\nline"),
    ],
)
def test_invalid_notices_cannot_cross_the_bridge(notice):
    with pytest.raises(ProtocolError):
        validate_notice(notice)


def test_batches_are_bounded_deduplicated_and_have_safe_utf8_hex_fields():
    notices = tuple(
        Notice(f"r:{index}", index + 1, "Оуэн gave you a Bandage") for index in range(20)
    )
    selected = pending_batch(notices, frozenset({"r:0"}))
    assert len(selected) == MAX_NOTICE_BATCH and selected[0].identity == "r:1"
    encoded = encode_notices(KEY, selected)
    assert encoded.startswith(f"GAMMA_AP_NOTICES|1\nsession|{KEY}\nnotice|r:1|2|")
    assert "Оуэн".encode().hex() in encoded and encoded.endswith("end|16\n")
    assert encode_notices(KEY, ()).endswith("end|0\n")
    for invalid in [notices, (notices[0], notices[0])]:
        with pytest.raises(ProtocolError, match="batch"):
            encode_notices(KEY, invalid)


@pytest.mark.parametrize(
    "content",
    [
        "x" * (MAX_ACK_BYTES + 1),
        ack()[:-1],
        "\n",
        ack().replace("ACK|1", "ACK|2"),
        ack().replace("session|", "wrong|"),
        ack(key="bad"),
        ack("r:0", "r:0"),
        ack("r:4000"),
        ack("bad"),
        ack().replace("end|0", "end|01"),
        ack(*(f"s:{index}:2:3" for index in range(MAX_NOTICES + 1))),
    ],
)
def test_malformed_or_unbounded_acknowledgements_are_rejected(content):
    with pytest.raises(ProtocolError):
        decode_acknowledgements(content, KEY)


def test_acknowledgements_bind_to_a_seed_and_notice_history_is_bounded():
    assert decode_acknowledgements(ack("r:0", "s:3:2:4"), KEY) == {"r:0", "s:3:2:4"}
    with pytest.raises(NoticeSessionMismatch):
        decode_acknowledgements(ack(key="b" * 64), KEY)
    session = SessionCoordinator(KEY)
    notice = Notice("r:0", 1, "Owen gave you a Toolkit")
    session.add_notice(notice)
    session.add_notice(notice)
    assert list(session.notices.values()) == [notice]
    session.notices = {
        f"s:{index}:2:3": Notice(f"s:{index}:2:3", 0, "Owen") for index in range(MAX_NOTICES)
    }
    with pytest.raises(ProtocolError, match="bound"):
        session.add_notice(notice)
