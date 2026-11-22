from collections import Counter

from gamma_archipelago.activity_requirements import RegionalRequirement


def test_repeated_regions_are_queried_once_and_no_result_survives_an_ap_state_change():
    allowed = {"a"}
    calls = Counter()

    def reachable(region):
        calls[region] += 1
        return region in allowed

    rule = RegionalRequirement((("a", "b"), ("a", "c")), 2, ("a",))
    assert rule.accessible(reachable)
    assert calls == {"a": 1}
    allowed.clear()
    assert not rule.accessible(reachable)
    assert calls == {"a": 2}


def test_false_region_results_are_shared_within_a_single_source_count_query():
    calls = Counter()

    def reachable(region):
        calls[region] += 1
        return region == "c"

    assert RegionalRequirement((("a", "b"), ("a", "c")), 1).accessible(reachable)
    assert calls == {"a": 1, "b": 1, "c": 1}
