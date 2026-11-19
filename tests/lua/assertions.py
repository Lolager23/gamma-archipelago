"""Distinguish Lua's (nil, error) returns from an accepted table with no index zero."""


def assert_lua_error(result: object) -> None:
    assert isinstance(result, tuple) and len(result) == 2
    assert result[0] is None and isinstance(result[1], str) and result[1]
