import json
from types import MappingProxyType

import numpy as np
import pytest

from ppe import analysis as an
from ppe import compliance as c
from ppe.class_map import ClassMap
from ppe.detector import Detector
from ppe.zone import Polygon, ZoneIncursionDetector

CMAP = ClassMap("deadbeef", "test", MappingProxyType({0: "person", 1: "helmet", 2: "no_helmet", 3: "safety_vest", 4: "no_safety_vest"}))


class FakeDetector(Detector):
    def __init__(self, raw):
        self.raw, self.calls = raw, 0

    def detect(self, frame):
        self.calls += 1
        return list(self.raw)


FRAME = np.zeros((480, 640, 3), np.uint8)
P = (0, 0.95, 100, 50, 300, 450)               # person
H = (1, 0.90, 150, 55, 250, 120)               # helmet
V = (3, 0.90, 130, 200, 270, 330)              # vest
NV_STRONG = (4, 0.71, 130, 200, 270, 330)
NV_WEAK = (4, 0.32, 130, 200, 270, 330)


def analyze(raw, **kw):
    return an.FrameAnalyzer(FakeDetector(raw), CMAP, **kw).analyze("f1", FRAME, 1.25)


def test_compliant_worker_end_to_end():
    r = analyze([P, H, V])
    assert [p.state for p in r.people] == [c.COMPLIANT] and r.rules == () and (r.width, r.height) == (640, 480)


def test_missing_vest_detection_is_unknown_not_violation():
    r = analyze([P, H])
    assert r.people[0].state == c.UNKNOWN and r.rules == ()


def test_explicit_strong_negative_raises_the_rule():
    r = analyze([P, H, NV_STRONG])
    assert r.people[0].state == c.VEST_MISSING and r.rules == (c.RULE_VEST_MISSING,)


def test_weak_negative_and_conflict_do_not_raise_rules():
    assert analyze([P, H, NV_WEAK]).rules == ()
    r = analyze([P, H, V, NV_STRONG])                              # the Pexels clip failure mode
    assert r.people[0].state == c.UNKNOWN and r.people[0].vest_conflict and r.rules == ()


def test_weak_negative_next_to_a_clear_vest_is_ignored_not_a_conflict():
    assert analyze([P, H, V, NV_WEAK]).people[0].state == c.COMPLIANT


def test_confidence_floor_and_unmapped_classes_are_dropped():
    r = analyze([P, (0, 0.10, 400, 50, 500, 450), (9, 0.99, 0, 0, 10, 10), H, V])
    assert len(r.people) == 1 and {d.label for d in r.detections} == {"person", "helmet", "safety_vest"}


def test_zone_incursion_uses_foot_point_and_is_reported():
    zone = ZoneIncursionDetector(Polygon(((0, 300), (640, 300), (640, 480), (0, 480))))
    r = analyze([P, H, V], zone_detector=zone)                    # feet at y=450 are inside the zone
    assert len(r.incursions) == 1 and c.RULE_ZONE_INCURSION in r.rules


def test_json_is_versioned_complete_and_deterministic():
    raw = [P, H, V, NV_STRONG]                                    # conflicting vest evidence
    a, b = analyze(raw), analyze(list(reversed(raw)))
    ja, jb = an.to_json(a), an.to_json(b)
    d = json.loads(ja)
    assert d["schema_version"] == "1.2" and d["frame_id"] == "f1" and d["timestamp"] == 1.25
    assert set(d) == {"schema_version", "frame_id", "timestamp", "width", "height", "detections", "people", "unassigned_ppe", "zone_incursions", "rules", "events"}
    assert d["people"][0]["state"] == "UNKNOWN" and d["people"][0]["index"] == 0
    assert json.loads(jb)["people"] == d["people"] and json.loads(jb)["rules"] == d["rules"]     # model output order is irrelevant


def test_no_identity_fields_in_output():
    text = an.to_json(analyze([P, H, V])).lower()
    for banned in ("name", "face", "identity", "track_id", "person_id"):
        assert banned not in text


def test_negative_floor_below_positive_floor_rejected():
    with pytest.raises(ValueError):
        an.FrameAnalyzer(FakeDetector([]), CMAP, min_confidence=0.5, min_negative_confidence=0.3)


def test_frame_without_shape_still_works():
    r = an.FrameAnalyzer(FakeDetector([P, H, V]), CMAP).analyze("f", object())
    assert r.width is None and r.height is None and r.people[0].state == c.COMPLIANT
