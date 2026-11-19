import asyncio
from dataclasses import dataclass

import pytest
from Options import PlandoItem
from test.general import setup_multiworld
from test_client import connected_context
from worlds.gamma import GammaWorld
from worlds.gamma.identity import _data, generation_identity

from gamma_archipelago.protocol import ProtocolError
from gamma_archipelago.session import make_session_key


def test_common_constraints_have_bound_schema4_identity_and_default_worlds_keep_schema3():
    async def exercise():
        default = setup_multiworld(GammaWorld).worlds[1]
        assert generation_identity(default) is None
        assert default.fill_slot_data()["schema_version"] == 3
        first = setup_multiworld(GammaWorld, options={"local_items": ["Medkit"]}).worlds[1]
        second = setup_multiworld(GammaWorld, options={"local_items": ["Bandage"]}).worlds[1]
        a, b = first.fill_slot_data(), second.fill_slot_data()
        assert a["schema_version"] == b["schema_version"] == 4
        assert a["generation_identity"] != b["generation_identity"]
        context = connected_context(a)
        assert context.expanded and context.require_configuration
        assert context.session.session_key == make_session_key(
            "pilot-seed|generation|" + a["generation_identity"], 0, 1
        )
        with pytest.raises(ProtocolError, match="Restart"):
            context.on_package("Connected", {"slot_data": b})
        with pytest.raises(ProtocolError, match="schema 4"):
            connected_context({**a, "schema_version": 3})
        for value in (None, False, "bad", "f" * 65):
            with pytest.raises(ProtocolError, match="Session key"):
                connected_context({**a, "generation_identity": value})

    asyncio.run(exercise())


def test_plando_and_set_constraints_have_deterministic_data_only_identity():
    world = setup_multiworld(GammaWorld).worlds[1]
    world.options.plando_items.value = [
        PlandoItem(items=["Medkit"], locations=["Cordon: First Arrival"], world={1})
    ]
    first = generation_identity(world)
    assert first == generation_identity(world) and len(first) == 64
    assert _data(frozenset({"b", "a"})) == ["a", "b"]

    @dataclass
    class Payload:
        value: int

    assert _data(Payload(1)) == {"value": 1}
    with pytest.raises(TypeError, match="Unsupported"):
        _data(object())
