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
from ppe.zone import ZoneIncursionDetector

ANALYSIS_SCHEMA_VERSION = "1.1"


@dataclass(frozen=True)
class FrameAnalysis:
    frame_id: str
    timestamp: Optional[float]
    width: Optional[int]
    height: Optional[int]
    detections: Tuple[Detection, ...]
    people: Tuple[comp.PersonCompliance, ...]
    unassigned_ppe: Tuple[Detection, ...]
    incursions: Tuple[Detection, ...]
    rules: Tuple[str, ...]


class FrameAnalyzer:
    def __init__(self, detector: Detector, class_map: ClassMap, min_confidence: float = 0.25,
                 min_negative_confidence: float = 0.5, zone_detector: Optional[ZoneIncursionDetector] = None) -> None:
        if min_negative_confidence < min_confidence:
            raise ValueError("min_negative_confidence must not be below min_confidence")
        self._detector = detector
        self._normalizer = DetectionNormalizer(class_map, min_confidence)
        self._min_neg = float(min_negative_confidence)
        self._zone = zone_detector

    def analyze(self, frame_id: str, frame: Any, timestamp: Optional[float] = None) -> FrameAnalysis:
        detections = self._normalizer.normalize(self._detector.detect(frame))
        people, unassigned = comp.evaluate(detections, self._min_neg)
        incursions = self._zone.persons_inside(detections) if self._zone else []
        rules = comp.active_rules(people, incursions)
        shape = getattr(frame, "shape", None)
        h, w = (int(shape[0]), int(shape[1])) if shape is not None and len(shape) >= 2 else (None, None)
        return FrameAnalysis(frame_id, timestamp, w, h, tuple(detections), tuple(people), tuple(unassigned),
                             tuple(incursions), tuple(sorted(rules)))


def _det(d: Detection) -> dict:
    b = d.box
    return {"label": d.label, "confidence": round(d.confidence, 4), "box": [round(b.x1, 1), round(b.y1, 1), round(b.x2, 1), round(b.y2, 1)]}


def to_dict(a: FrameAnalysis) -> dict:
    return {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "frame_id": a.frame_id, "timestamp": a.timestamp, "width": a.width, "height": a.height,
        "detections": [_det(d) for d in a.detections],
        "people": [{"index": p.index, "box": _det(p.person)["box"], "confidence": round(p.person.confidence, 4), "state": p.state,
                    "helmet": p.helmet, "vest": p.vest, "helmet_conflict": p.helmet_conflict, "vest_conflict": p.vest_conflict}
                   for p in a.people],
        "unassigned_ppe": [_det(d) for d in a.unassigned_ppe],
        "zone_incursions": [_det(d) for d in a.incursions],
        "rules": list(a.rules),
    }


def to_json(a: FrameAnalysis) -> str:
    return json.dumps(to_dict(a), sort_keys=True)
