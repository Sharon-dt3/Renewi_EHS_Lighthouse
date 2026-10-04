import json
from scripts import val04_zone_cases as v

ROWS = [{"t": 2.0, "person_observations": [
            {"foot_point": [900.0, 950.0], "zone_incursion": False, "confidence": 0.8},
            {"foot_point": [1500.0, 650.0], "zone_incursion": True, "confidence": 0.7}]},
        {"t": 4.0, "person_observations": []}]
TOL, TT = 150, 0.13


def case(id_, t, exp, feet):
    return {"id": id_, "t": t, "expected": exp, "feet": feet}


def test_match_mismatch_and_not_detected_are_distinct():
    assert v.score_case(case("a", 2.0, "outside", [940, 960]), ROWS, TOL, TT)["outcome"] == "MATCH"
    assert v.score_case(case("b", 2.0, "inside", [940, 960]), ROWS, TOL, TT)["outcome"] == "MISMATCH"      # detected, wrong side
    assert v.score_case(case("c", 2.0, "outside", [200, 200]), ROWS, TOL, TT)["outcome"] == "NOT_DETECTED"  # nobody near
    assert v.score_case(case("d", 4.0, "outside", [900, 900]), ROWS, TOL, TT)["outcome"] == "NOT_DETECTED"  # empty frame
    assert v.score_case(case("e", 9.0, "outside", [900, 900]), ROWS, TOL, TT)["outcome"] == "NO_FRAME"


def test_it_reads_the_systems_flag_and_picks_the_nearest_person():
    r = v.score_case(case("a", 2.0, "inside", [1480, 640]), ROWS, TOL, TT)
    assert r["outcome"] == "MATCH" and r["system"] == "inside" and r["distance_px"] < 30


def test_constructed_boundary_on_exact_floats_behaves_edge_inclusive():
    out = v.constructed_boundary((1431.2345678901234, 667.0001234567891))
    assert out["outcome"] == "MATCH"
    assert out["results"] == {"edge_through_foot": True, "edge_0.001px_below_foot": False,
                              "edge_0.001px_above_foot": True, "foot_exactly_on_a_corner": True}
