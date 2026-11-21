import pytest

from gamma_archipelago.configuration import (
    ConfigurationError,
    build_configuration,
    defaults,
    encode_configuration,
)
from gamma_archipelago.starting import STARTS, starting_level


def test_legacy_start_options_preserve_digest_and_wire_and_random_preview_is_explicit():
    values = defaults()
    legacy = {
        key: value
        for key, value in values.items()
        if key not in {"ap_start", "starting_faction", "starting_location"}
    }
    before = build_configuration(legacy)
    after = build_configuration(values)
    assert before.digest == after.digest
    wire = encode_configuration("a" * 64, after, expanded=True)
    assert not any(
        "option|" + key + "|" in wire
        for key in ("ap_start", "starting_faction", "starting_location")
    )
    assert starting_level(after) == "l01_escape"
    configured = build_configuration({**values, "ap_start": 1, "starting_location": 2})
    assert starting_level(configured) == "l05_bar" and configured.digest != before.digest
    preview = build_configuration({**values, "ap_start": 1, "starting_location": 3})
    assert (
        starting_level(preview) == "l01_escape"
    )  # No claim that settings-only preview rolled a start.
    assert len(STARTS) == 3 and all(row["key"] and row["name"] and row["level"] for row in STARTS)


@pytest.mark.parametrize(
    "change", [{"starting_location": 4}, {"starting_faction": 1}, {"ap_start": True}]
)
def test_unknown_start_settings_are_refused(change):
    with pytest.raises(ConfigurationError):
        build_configuration({**defaults(), **change})
