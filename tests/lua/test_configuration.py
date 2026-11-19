import pytest

from gamma_archipelago.configuration import build_configuration, defaults, encode_configuration
from gamma_archipelago.protocol import encode_incoming

from .assertions import assert_lua_error

KEY = "a" * 64
CONFIG = build_configuration(defaults())
VALID = encode_configuration(KEY, CONFIG)


@pytest.mark.parametrize(
    "content",
    [
        None,
        "x" * 131073,
        "partial",
        "\n",
        "GAMMA_AP_CONFIG|1\n",
        VALID.replace("option|goal|0", "option|unknown|0"),
        VALID.replace("option|goal|0", "option|goal|01"),
        VALID.replace("option|goal|0", "option|goal|6"),
        VALID.replace("option|goal|0\n", ""),
        VALID.replace("option|goal|0", "option|checks_maps|1"),
        VALID.replace("threshold|kill_milestones|10", "threshold|unknown|10"),
        VALID.replace("threshold|kill_milestones|10", "threshold|kill_milestones|0"),
        VALID.replace("threshold|kill_milestones|10", "threshold|kill_milestones|10001"),
        VALID.replace("threshold|kill_milestones|25", "threshold|kill_milestones|10"),
        VALID.replace("threshold|kill_milestones|10", "broken"),
        VALID.replace("digest|", "wrong|"),
        VALID.replace("GAMMA_AP_CONFIG|1", "GAMMA_AP_CONFIG|3"),
    ],
)
def test_configuration_rejects_partial_unknown_repeated_and_invalid_values(lua, content):
    # Recompute framing where a removed record would otherwise stop at count validation.
    if content and content.startswith("GAMMA_AP_CONFIG") and content.endswith("\n"):
        lines = content.splitlines()
        lines[-1] = f"end|{len(lines) - 4}"
        content = "\n".join(lines) + "\n"
    assert_lua_error(lua.globals().gamma_ap_configuration.parse(content, KEY, CONFIG.digest))


def test_configuration_requires_threshold_lists_and_caps_their_length(lua):
    module = lua.globals().gamma_ap_configuration
    lines = VALID.splitlines()
    assert_lua_error(module.parse(VALID.replace("end|44", "end|43"), KEY, CONFIG.digest))
    records = [line for line in lines[3:-1] if not line.startswith("threshold|kill_milestones|")]
    missing = "\n".join([*lines[:3], *records, f"end|{len(records)}", ""])
    assert_lua_error(module.parse(missing, KEY, CONFIG.digest))
    many = [f"threshold|kill_milestones|{number}" for number in range(1, 22)]
    content = "\n".join([*lines[:3], *records, *many, f"end|{len(records) + len(many)}", ""])
    assert_lua_error(module.parse(content, KEY, CONFIG.digest))
    excessive = "\n".join([*lines[:3], *(["option|goal|0"] * 129), "end|129", ""])
    assert_lua_error(module.parse(excessive, KEY, CONFIG.digest))
    assert_lua_error(module.parse(VALID, "b" * 64, CONFIG.digest))
    assert_lua_error(module.parse(VALID, KEY, "b" * 64))
    parsed = module.parse(VALID, KEY, CONFIG.digest)
    assert parsed.options.checks_maps == 1


def test_v2_incoming_requires_a_well_formed_configuration_identity(lua):
    protocol = lua.globals().gamma_ap_protocol
    valid = encode_incoming(KEY, (28051001,), CONFIG.digest)
    assert protocol.parse_incoming(valid).configuration_key == CONFIG.digest
    assert_lua_error(protocol.parse_incoming(valid.replace(CONFIG.digest, "bad")))
    assert_lua_error(protocol.parse_incoming(valid.replace("configuration|", "wrong|")))
