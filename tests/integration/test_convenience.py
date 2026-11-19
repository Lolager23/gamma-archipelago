import pytest
from Fill import distribute_items_restrictive
from Options import OptionError
from test.general import setup_multiworld
from test_generation_matrix import assert_seed
from worlds.gamma import GammaWorld

from gamma_archipelago.configuration import build_configuration, defaults


def test_convenience_has_at_most_three_useful_copies_and_fits_one_reliable_check():
    for count in (1, 2, 3, 5):
        world = setup_multiworld(
            GammaWorld,
            options=dict(
                rewards_convenience=1,
                checks_maps=0,
                checks_kill_milestones=1,
                kill_milestones=list(range(1, count + 1)),
            ),
        )
        assert sum(item.name == "Carry Capacity +5 kg" for item in world.itempool) == min(3, count)
        distribute_items_restrictive(world)
        assert world.can_beat_game()
    with pytest.raises(OptionError, match="reliable check"):
        setup_multiworld(
            GammaWorld, options=dict(rewards_convenience=1, checks_maps=0, checks_shops=1)
        )
    legacy = defaults()
    legacy.pop("rewards_convenience")
    assert build_configuration(legacy).digest == build_configuration(defaults()).digest


@pytest.mark.generation
def test_convenience_and_progression_share_a_bounded_pool():
    for seed in range(50):
        assert_seed(dict(rewards_convenience=1, rewards_zone_keys=1), seed)
