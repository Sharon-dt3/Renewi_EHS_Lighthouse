"""Per-worker PPE compliance from detections (DEC-04 in the implementation plan).

Principles
- A missing detection is never evidence. Only explicit negative classes (no_helmet, no_safety_vest) count against a worker.
- Conflicting or incomplete evidence gives UNKNOWN, never a violation.
- Every PPE box belongs to at most one person: the smallest person box that contains the PPE box centre
  (ties broken by position), so repeated runs give identical results.
- No identity, no tracking: person indices are local to one frame.
"""
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Tuple

from ppe.detections import Detection, Label

COMPLIANT = "COMPLIANT"
HELMET_MISSING = "HELMET_MISSING"
VEST_MISSING = "VEST_MISSING"
HELMET_AND_VEST_MISSING = "HELMET_AND_VEST_MISSING"
UNKNOWN = "UNKNOWN"
STATES = (COMPLIANT, HELMET_MISSING, VEST_MISSING, HELMET_AND_VEST_MISSING, UNKNOWN)

RULE_HELMET_MISSING = "PPE_HELMET_MISSING"
RULE_VEST_MISSING = "PPE_VEST_MISSING"
RULE_ZONE_INCURSION = "ZONE_INCURSION"

_PPE = {Label.HELMET, Label.NO_HELMET, Label.SAFETY_VEST, Label.NO_SAFETY_VEST}


@dataclass(frozen=True)
class PersonCompliance:
    index: int                       # frame-local, not an identity
    person: Detection
    helmet: Optional[bool]           # True worn, False explicitly missing, None unknown or conflicting
    vest: Optional[bool]
    state: str
    helmet_conflict: bool = False
    vest_conflict: bool = False


def _centre(d: Detection) -> Tuple[float, float]:
    b = d.box
    return ((b.x1 + b.x2) / 2.0, (b.y1 + b.y2) / 2.0)


def _contains(person: Detection, point: Tuple[float, float]) -> bool:
    b = person.box
    return b.x1 <= point[0] <= b.x2 and b.y1 <= point[1] <= b.y2


def _order(persons: Sequence[Detection]) -> list:
    """Stable order so indices do not depend on model output order."""
    return sorted(range(len(persons)), key=lambda i: (persons[i].box.x1, persons[i].box.y1, persons[i].box.x2, persons[i].box.y2, i))


def associate(detections: Iterable[Detection]):
    """Return (persons in stable order, {person position: [ppe detections]}, unassigned ppe)."""
    dets = list(detections)
    persons = [d for d in dets if d.label == Label.PERSON]
    persons = [persons[i] for i in _order(persons)]
    owned = {i: [] for i in range(len(persons))}
    unassigned = []
    for d in dets:
        if d.label not in _PPE:
            continue
        c = _centre(d)
        candidates = [i for i, p in enumerate(persons) if _contains(p, c)]
        if not candidates:
            unassigned.append(d)
            continue
        owner = min(candidates, key=lambda i: (persons[i].box.area, i))
        owned[owner].append(d)
    return persons, owned, unassigned


def _verdict(positive: Sequence[Detection], negative: Sequence[Detection], min_negative: float):
    """Return (state True/False/None, conflict). Negatives below min_negative are ignored, not trusted."""
    strong_negative = [d for d in negative if d.confidence >= min_negative]
    if positive and strong_negative:
        return None, True
    if positive:
        return True, False
    if strong_negative:
        return False, False
    return None, False


def _state(helmet: Optional[bool], vest: Optional[bool]) -> str:
    if helmet is True and vest is True:
        return COMPLIANT
    if helmet is False and vest is True:
        return HELMET_MISSING
    if helmet is True and vest is False:
        return VEST_MISSING
    if helmet is False and vest is False:
        return HELMET_AND_VEST_MISSING
    return UNKNOWN


def evaluate(detections: Iterable[Detection], min_negative_confidence: float = 0.5):
    """Compliance for every person in one frame. Returns (list[PersonCompliance], unassigned PPE detections)."""
    persons, owned, unassigned = associate(detections)
    out = []
    for i, p in enumerate(persons):
        ppe = owned[i]
        helmet, h_conf = _verdict([d for d in ppe if d.label == Label.HELMET], [d for d in ppe if d.label == Label.NO_HELMET], min_negative_confidence)
        vest, v_conf = _verdict([d for d in ppe if d.label == Label.SAFETY_VEST], [d for d in ppe if d.label == Label.NO_SAFETY_VEST], min_negative_confidence)
        out.append(PersonCompliance(i, p, helmet, vest, _state(helmet, vest), h_conf, v_conf))
    return out, unassigned


def active_rules(people: Iterable[PersonCompliance], zone_incursions: Iterable[Detection] = ()) -> set:
    """Frame-level rule flags for smoothing. UNKNOWN never produces a rule."""
    rules = set()
    for p in people:
        if p.state in (HELMET_MISSING, HELMET_AND_VEST_MISSING):
            rules.add(RULE_HELMET_MISSING)
        if p.state in (VEST_MISSING, HELMET_AND_VEST_MISSING):
            rules.add(RULE_VEST_MISSING)
    if any(True for _ in zone_incursions):
        rules.add(RULE_ZONE_INCURSION)
    return rules
