from BaseClasses import CollectionState
from test.general import setup_multiworld
from worlds.gamma import GammaWorld

from gamma_archipelago.presets import presets


def test_real_ap_access_does_not_assume_cordon_military_for_the_third_faction():
    multi = setup_multiworld(GammaWorld, options=presets()["living_legend"], seed=903)
    state = CollectionState(multi)
    assert multi.get_location("Discovery: 2 Distinct Faction Types", 1).can_reach(state)
    third = multi.get_location("Discovery: 3 Distinct Faction Types", 1)
    assert not third.can_reach(state)
    state.collect(multi.worlds[1].create_item("Zone Key: Great Swamps"), True)
    assert third.can_reach(state)
