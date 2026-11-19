import pytest

from gamma_archipelago.probe_report import ProbeFormatError, parse_line, summarize

LINE = "GAMMA_AP_PROBE|1|1|1000|level|l01_escape|-|l01_escape|-"


def test_parser_accepts_engine_prefix_crlf_and_canonical_observations():
    item = parse_line("[engine prefix] " + LINE + "\r\n")
    assert item.sequence == 1 and item.clock_ms == 1000
    assert item.event == "level" and item.level == "l01_escape"
    assert item.values == ("-", "l01_escape", "-")
    assert parse_line("unrelated game log") is None


@pytest.mark.parametrize(
    "invalid",
    [
        "GAMMA_AP_PROBE|1",
        LINE.replace("|1|1|", "|2|1|"),
        LINE.replace("|1|1000|", "|01|1000|"),
        LINE.replace("|1|1000|", "|0|1000|"),
        LINE.replace("|1|1000|", "|257|1000|"),
        LINE.replace("1000", "-1"),
        LINE.replace("|level|", "|unknown|"),
        LINE.replace("l01_escape", "bad field"),
        LINE.replace("l01_escape", "a" * 97),
        LINE + "|extra",
    ],
)
def test_parser_rejects_malformed_oversized_or_unknown_fields(invalid):
    with pytest.raises(ProbeFormatError):
        parse_line(invalid)


def test_summary_counts_observations_and_errors_without_claiming_acceptance():
    report = summarize(
        [
            "unrelated save filename stays private",
            LINE,
            LINE,
            LINE.replace("|level|l01_escape|", "|started|-|"),
            "GAMMA_AP_PROBE|bad",
        ]
    )
    assert report["counts"] == {"level": 2, "started": 1}
    assert report["levels"] == ["l01_escape"]
    assert report["malformed_lines"] == 1
    assert report["acceptance"] == "not assessed"
    assert summarize([])["counts"] == {}


def test_summary_rejects_unbounded_probe_logs():
    with pytest.raises(ProbeFormatError, match="Too many"):
        summarize(LINE for _ in range(10001))
