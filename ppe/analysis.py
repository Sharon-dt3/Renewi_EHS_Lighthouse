"""One shared frame analysis used by the CLI scripts and, later, the API.

frame -> Detector -> normalised detections (class map, confidence floor) -> per-worker compliance
      -> optional zone check -> frame-level rule flags -> versioned JSON.

No identity, no tracking: person indices are local to one frame.
"""
import json
from dataclasses import dataclass
from typing import Any, Optional, Tuple

from ppe import compliance as comp
from ppe.class_map import ClassMap
from ppe.detections import Detection
from ppe.detector import Detector
from ppe.pipeline import DetectionNormalizer
from ppe.zone import ZoneIncursionDetector, foot_point

ANALYSIS_SCHEMA_VERSION = "1.2"


# PUBLIC_INTERFACE
@dataclass(frozen=True)
class PersonEvent:
    """Immediate safety observation, not a sustained incident or tracked identity."""

    index: int
    state: str
    position: Tuple[float, float]
    zone_incursion: bool
    rules: Tuple[str, ...]


# PUBLIC_INTERFACE
@dataclass(frozen=True)
class FrameAnalysis:
    """Immutable frame findings with immediate events and aggregate smoothing rules."""

    frame_id: str
    timestamp: Optional[float]
    width: Optional[int]
    height: Optional[int]
    detections: Tuple[Detection, ...]
    people: Tuple[comp.PersonCompliance, ...]
    unassigned_ppe: Tuple[Detection, ...]
    incursions: Tuple[Detection, ...]
    rules: Tuple[str, ...]
    events: Tuple[PersonEvent, ...] = ()


# PUBLIC_INTERFACE
class FrameAnalyzer:
    """Analyze a source frame into conservative PPE and per-person zone events."""

    def __init__(self, detector: Detector, class_map: ClassMap, min_confidence: float = 0.25,
                 min_negative_confidence: float = 0.5, zone_detector: Optional[ZoneIncursionDetector] = None) -> None:
        if min_negative_confidence < min_confidence:
            raise ValueError("min_negative_confidence must not be below min_confidence")
        self._detector = detector
        self._normalizer = DetectionNormalizer(class_map, min_confidence)
        self._min_neg = float(min_negative_confidence)
        self._zone = zone_detector

    # PUBLIC_INTERFACE
    def analyze(self, frame_id: str, frame: Any, timestamp: Optional[float] = None) -> FrameAnalysis:
        """Return frame-local findings; zone observations are immediate, not smoothed."""
        shape = getattr(frame, "shape", None)
        h, w = (int(shape[0]), int(shape[1])) if shape is not None and len(shape) >= 2 else (None, None)
        if self._zone:
            if w is None or h is None:
                raise ValueError("Zone analysis requires source-frame dimensions")
            self._zone.validate_frame(w, h)
        detections = self._normalizer.normalize(self._detector.detect(frame))
        people, unassigned = comp.evaluate(detections, self._min_neg)
        incursions = self._zone.persons_inside(detections) if self._zone else []
        rules = comp.active_rules(people, incursions)
        # Match the actual detection objects, not box overlap or frame-wide flags.
        inside = {id(d) for d in incursions}
        events = []
        for p in people:
            zone_incursion = id(p.person) in inside
            person_rules = comp.active_rules([p], [p.person] if zone_incursion else [])
            if person_rules:
                events.append(PersonEvent(p.index, p.state, foot_point(p.person.box),
                                          zone_incursion, tuple(sorted(person_rules))))
        return FrameAnalysis(frame_id, timestamp, w, h, tuple(detections), tuple(people), tuple(unassigned),
                             tuple(incursions), tuple(sorted(rules)), tuple(events))


def _det(d: Detection) -> dict:
    b = d.box
    return {"label": d.label, "confidence": round(d.confidence, 4), "box": [round(b.x1, 1), round(b.y1, 1), round(b.x2, 1), round(b.y2, 1)]}


# PUBLIC_INTERFACE
def to_dict(a: FrameAnalysis) -> dict:
    """Serialize schema 1.2 with exact source-pixel foot points and combined events."""
    events = {event.index: event for event in a.events}
    return {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "frame_id": a.frame_id, "timestamp": a.timestamp, "width": a.width, "height": a.height,
        "detections": [_det(d) for d in a.detections],
        "people": [{"index": p.index, "box": _det(p.person)["box"], "confidence": round(p.person.confidence, 4), "state": p.state,
                    "helmet": p.helmet, "vest": p.vest, "helmet_conflict": p.helmet_conflict, "vest_conflict": p.vest_conflict,
                    "foot_point": list(foot_point(p.person.box)),
                    "zone_incursion": events[p.index].zone_incursion if p.index in events else False,
                    "rules": list(events[p.index].rules) if p.index in events else []}
                   for p in a.people],
        "unassigned_ppe": [_det(d) for d in a.unassigned_ppe],
        "zone_incursions": [_det(d) for d in a.incursions],
        "events": [{"person_index": e.index, "state": e.state, "foot_point": list(e.position),
                    "zone_incursion": e.zone_incursion, "rules": list(e.rules)} for e in a.events],
        "rules": list(a.rules),
    }


# PUBLIC_INTERFACE
def to_json(a: FrameAnalysis) -> str:
    """Return deterministic JSON for a frame analysis."""
    return json.dumps(to_dict(a), sort_keys=True)
