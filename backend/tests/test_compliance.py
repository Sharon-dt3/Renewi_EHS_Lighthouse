import random
import pytest
from ppe import compliance as c
from ppe.detections import Box, Detection, Label


def det(label, x1, y1, x2, y2, conf=0.9):
    return Detection(label, conf, Box(x1, y1, x2, y2))


PERSON = det(Label.PERSON, 0, 0, 100, 300)
HELMET = det(Label.HELMET, 30, 5, 70, 40)
NO_HELMET = det(Label.NO_HELMET, 30, 5, 70, 40)
VEST = det(Label.SAFETY_VEST, 20, 80, 80, 200)
NO_VEST = det(Label.NO_SAFETY_VEST, 20, 80, 80, 200)


def state(*dets, min_neg=0.5):
    people, _ = c.evaluate(dets, min_neg)
    assert len(people) == 1
    return people[0]


def test_all_four_explicit_states_and_compliant():
    assert state(PERSON, HELMET, VEST).state == c.COMPLIANT
    assert state(PERSON, NO_HELMET, VEST).state == c.HELMET_MISSING
    assert state(PERSON, HELMET, NO_VEST).state == c.VEST_MISSING
    assert state(PERSON, NO_HELMET, NO_VEST).state == c.HELMET_AND_VEST_MISSING


def test_missing_detection_is_never_a_violation():
    assert state(PERSON).state == c.UNKNOWN                      # nothing detected for this worker
    assert state(PERSON, HELMET).state == c.UNKNOWN              # vest not seen: not "missing"
    assert state(PERSON, VEST).state == c.UNKNOWN
    p = state(PERSON, HELMET)
    assert p.vest is None and p.helmet is True


def test_conflicting_evidence_is_unknown_not_a_violation():
    p = state(PERSON, HELMET, VEST, NO_VEST)                     # the Pexels clip failure mode
    assert p.state == c.UNKNOWN and p.vest is None and p.vest_conflict is True
    p = state(PERSON, HELMET, NO_HELMET, VEST)
    assert p.state == c.UNKNOWN and p.helmet_conflict is True
    assert c.active_rules([p]) == set()


def test_weak_negative_is_not_trusted():
    weak = det(Label.NO_SAFETY_VEST, 20, 80, 80, 200, conf=0.32)
    p = state(PERSON, HELMET, weak)
    assert p.vest is None and p.state == c.UNKNOWN              # below the 0.5 negative floor
    assert state(PERSON, HELMET, weak, min_neg=0.3).state == c.VEST_MISSING   # floor is a setting, not a constant
    strong = det(Label.NO_SAFETY_VEST, 20, 80, 80, 200, conf=0.71)
    assert state(PERSON, HELMET, strong).state == c.VEST_MISSING


def test_ppe_goes_to_smallest_containing_person_and_is_deterministic():
    big = det(Label.PERSON, 0, 0, 200, 400)
    small = det(Label.PERSON, 50, 50, 150, 250)
    vest = det(Label.SAFETY_VEST, 80, 100, 120, 180)             # centre inside both people
    results = []
    for seed in range(6):
        d = [big, small, vest, HELMET]
        random.Random(seed).shuffle(d)
        people, _ = c.evaluate(d)
        results.append([(p.person.box.area, p.vest) for p in people])
    assert all(r == results[0] for r in results)                 # model output order does not matter
    owners = {p.person.box.area: p.vest for p in c.evaluate([big, small, vest])[0]}
    assert owners[small.box.area] is True and owners[big.box.area] is None


def test_equal_area_tie_is_broken_by_position_not_input_order():
    a = det(Label.PERSON, 0, 0, 100, 100)
    b = det(Label.PERSON, 0, 0, 100, 100)                        # identical boxes
    vest = det(Label.SAFETY_VEST, 40, 40, 60, 60)
    people, _ = c.evaluate([b, a, vest])
    assert sum(1 for p in people if p.vest is True) == 1


def test_unassigned_ppe_never_invents_a_person():
    stray = det(Label.NO_SAFETY_VEST, 500, 500, 560, 600, conf=0.95)
    people, unassigned = c.evaluate([PERSON, stray])
    assert len(people) == 1 and unassigned == [stray] and people[0].state == c.UNKNOWN
    assert c.active_rules(people) == set()


def test_irrelevant_labels_are_ignored():
    assert state(PERSON, HELMET, VEST).state == c.COMPLIANT


def test_active_rules_mapping_and_zone():
    p1 = state(PERSON, NO_HELMET, VEST)
    p2 = state(PERSON, NO_HELMET, NO_VEST)
    assert c.active_rules([p1]) == {c.RULE_HELMET_MISSING}
    assert c.active_rules([p2]) == {c.RULE_HELMET_MISSING, c.RULE_VEST_MISSING}
    assert c.active_rules([], [PERSON]) == {c.RULE_ZONE_INCURSION}
    assert c.active_rules([state(PERSON, HELMET, VEST)]) == set()


def test_multiple_people_are_evaluated_independently():
    left = det(Label.PERSON, 0, 0, 100, 300); right = det(Label.PERSON, 200, 0, 300, 300)
    dets = [left, right, det(Label.HELMET, 30, 5, 70, 40), det(Label.SAFETY_VEST, 20, 80, 80, 200),
            det(Label.NO_HELMET, 230, 5, 270, 40), det(Label.SAFETY_VEST, 220, 80, 280, 200)]
    people, _ = c.evaluate(dets)
    assert [p.state for p in people] == [c.COMPLIANT, c.HELMET_MISSING]
    assert [p.index for p in people] == [0, 1]
