from dataclasses import replace

import pytest

from gamma_archipelago.catalog import ALL_LOCATION_IDS, GAME, KILL_MILESTONE_BASE
from gamma_archipelago.notice_causes import CAUSE_TEMPLATES, CheckCause, cause_for_check
from gamma_archipelago.notice_text import TransferMessage, render_english
from gamma_archipelago.notifications import Notice, encode_notices, transfer_notice
from gamma_archipelago.protocol import ProtocolError


@pytest.mark.parametrize(
    ("identity", "ending"),
    [
        (28052003, "by entering Rostok."),
        (28052101, "by entering Rookie Village."),
        (28052808, "for reaching Legend rank."),
        (KILL_MILESTONE_BASE + 1, "by killing 1 hostile."),
        (KILL_MILESTONE_BASE + 15, "by killing 15 hostiles."),
        (28140015, "by killing 15 distinct mutant types."),
    ],
)
def test_requested_announcement_endings_follow_the_actual_check(identity, ending):
    message = TransferMessage("sent_unlock", "Owen", "PDA", cause=cause_for_check(identity, ""))
    assert render_english(message) == 'You unlocked "PDA" for Owen ' + ending


def test_every_published_check_has_a_bounded_translatable_cause(monkeypatch):
    kinds = set()
    for identity in ALL_LOCATION_IDS:
        cause = cause_for_check(identity, "Unused fallback")
        text = render_english(TransferMessage("received_item", "Friend", "Reward", cause=cause))
        assert text.endswith(".") and cause.value not in ("", "Unused fallback")
        kinds.add(cause.kind)
    fallback = cause_for_check(99, "Foreign check")
    assert fallback == CheckCause("check", "Foreign check")
    kinds.add(fallback.kind)
    assert kinds == set(CAUSE_TEMPLATES) - {"source"}
    from gamma_archipelago import notice_causes

    monkeypatch.setitem(
        notice_causes._checks, 99, {"name": "Future check", "category": "future_category"}
    )
    assert cause_for_check(99, "Ignored") == CheckCause("check", "Future check")


@pytest.mark.parametrize(
    "cause",
    [
        "bad",
        CheckCause([], "x"),
        CheckCause("bad", "x"),
        CheckCause("enter", ""),
        CheckCause("enter", "x" * 97),
        CheckCause("enter", "%c[red]"),
        CheckCause("enter", "a\nb"),
        CheckCause("enter", 1),
        CheckCause("enter", "a  b"),
    ],
)
def test_unsafe_or_unknown_check_causes_never_cross_the_bridge(cause):
    with pytest.raises(ProtocolError):
        render_english(TransferMessage("received_item", "Friend", "Reward", cause=cause))


def test_v3_mixed_batches_keep_v1_v2_compatibility_and_stable_identities():
    causal = transfer_notice(
        "r:0",
        1,
        "Friend",
        "PDA",
        item_id=28051602,
        game=GAME,
        outgoing=False,
        cause=CheckCause("enter", "Rostok"),
    )
    plain = transfer_notice("r:1", 2, "Friend", "PDA", item_id=28051602, game=GAME, outgoing=False)
    text = encode_notices("a" * 64, (causal, plain, Notice("s:3:2:5", 0, "Old text")))
    assert text.startswith("GAMMA_AP_NOTICES|3\n")
    assert "|enter|526f73746f6b\n" in text and "|none|\n" in text
    assert "|text|" in text and causal.identity == "r:0"
    assert encode_notices("a" * 64, (plain,)).startswith("GAMMA_AP_NOTICES|2\n")
    assert encode_notices("a" * 64, (replace(causal, transfer=None),)).startswith(
        "GAMMA_AP_NOTICES|1\n"
    )
