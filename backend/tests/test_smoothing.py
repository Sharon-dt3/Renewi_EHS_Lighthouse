import pytest
from ppe.smoothing import Incident, SustainedDetector

R = "PPE_VEST_MISSING"


def feed(det, times, rules_by_time):
    out = []
    for t in times:
        out += det.update(t, rules_by_time(t))
    return out


def test_nothing_fires_before_hold_time():
    d = SustainedDetector(1.5, 1.0)
    assert feed(d, [0.0, 0.5, 1.0, 1.4], lambda t: {R}) == []


def test_fires_once_when_hold_reached_and_not_again():
    d = SustainedDetector(1.5, 1.0)
    inc = feed(d, [i * 0.5 for i in range(12)], lambda t: {R})        # 5.5 seconds of continuous violation
    assert len(inc) == 1 and inc[0].rule == R and inc[0].started_at == 0.0 and inc[0].detected_at == 1.5


def test_single_frame_flicker_never_fires():
    d = SustainedDetector(1.5, 1.0)
    assert feed(d, [i * 0.25 for i in range(40)], lambda t: {R} if abs(t - 5.0) < 1e-9 else set()) == []


def test_intermittent_detections_within_gap_still_count():
    d = SustainedDetector(1.5, 1.0)
    on = {0.0, 0.25, 0.75, 1.25, 1.75}                               # misses at 0.5, 1.0, 1.5 but never a >1 s gap
    inc = feed(d, [i * 0.25 for i in range(8)], lambda t: {R} if t in on else set())
    assert len(inc) == 1 and inc[0].detected_at == 1.75


def test_gap_longer_than_max_gap_resets_the_run():
    d = SustainedDetector(1.5, 1.0)
    on = {0.0, 0.5, 1.0, 3.0, 3.5, 4.0}                              # 2 s hole splits two 1.0 s runs: neither reaches 1.5 s
    assert feed(d, [i * 0.5 for i in range(10)], lambda t: {R} if t in on else set()) == []


def test_rearms_after_the_rule_disappears_then_returns():
    d = SustainedDetector(1.0, 0.5)
    times = [i * 0.25 for i in range(40)]
    on = lambda t: {R} if (t < 2.0 or t >= 6.0) else set()
    inc = feed(d, times, on)
    assert [round(i.started_at, 2) for i in inc] == [0.0, 6.0]       # two separate episodes, one incident each


def test_rules_are_independent():
    d = SustainedDetector(1.0, 1.0)
    inc = feed(d, [0.0, 0.5, 1.0, 1.5], lambda t: {R, "ZONE_INCURSION"} if t >= 0 else set())
    assert sorted(i.rule for i in inc) == [R, "ZONE_INCURSION"]


def test_works_at_any_frame_rate():
    for dt in (0.1, 0.25, 0.5):
        d = SustainedDetector(1.5, 1.0)
        n = int(3 / dt) + 1
        inc = feed(d, [i * dt for i in range(n)], lambda t: {R})
        assert len(inc) == 1 and abs(inc[0].detected_at - 1.5) < dt


def test_sparse_sampling_cannot_fire_and_this_is_documented_behaviour():
    d = SustainedDetector(1.5, 1.0)
    assert feed(d, [0.0, 2.0, 4.0, 6.0], lambda t: {R}) == []         # samples further apart than max_gap: needs sample_fps >= 1/max_gap


def test_timestamps_must_not_go_backwards():
    d = SustainedDetector()
    d.update(1.0, set())
    with pytest.raises(ValueError):
        d.update(0.5, set())


def test_invalid_settings_rejected():
    with pytest.raises(ValueError):
        SustainedDetector(-1, 1)
    with pytest.raises(ValueError):
        SustainedDetector(1.5, 0)
