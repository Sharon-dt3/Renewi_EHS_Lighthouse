import json
from dataclasses import dataclass
from typing import Tuple

from ppe.detections import ALL_LABELS, Detection

SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class FrameResult:
    frame_id: str
    detections: Tuple[Detection, ...]
    incursions: Tuple[Detection, ...]


def _detection_to_dict(detection: Detection) -> dict:
    if detection.label not in ALL_LABELS:
        raise ValueError(f"Label '{detection.label}' is not in the internal label set")
    box = detection.box
    return {
        "label": detection.label,
        "confidence": detection.confidence,
        "box": [box.x1, box.y1, box.x2, box.y2],
        "derived": detection.derived,
    }


def to_dict(result: FrameResult) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "frame_id": result.frame_id,
        "detections": [_detection_to_dict(d) for d in result.detections],
        "incursions": [_detection_to_dict(d) for d in result.incursions],
    }


def to_json(result: FrameResult) -> str:
    return json.dumps(to_dict(result), sort_keys=True)
