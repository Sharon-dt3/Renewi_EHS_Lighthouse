from typing import Iterable, Tuple

from ppe.class_map import ClassMap
from ppe.detections import Box, Detection
from ppe.vest_rule import NoVestDeriver

# (class_id, confidence, x1, y1, x2, y2) as produced by the model
RawDetection = Tuple[int, float, float, float, float, float]


class DetectionNormalizer:
    """Maps raw model output to Detections. Unmapped classes and low-confidence
    results are dropped, so the 12 classes outside the BRD never leave this layer."""

    def __init__(self, class_map: ClassMap, min_confidence: float = 0.25) -> None:
        if not 0.0 <= min_confidence <= 1.0:
            raise ValueError("min_confidence must be in [0, 1]")
        self._class_map = class_map
        self._min_confidence = min_confidence

    def normalize(self, raw: Iterable[RawDetection]) -> list[Detection]:
        detections = []
        for class_id, confidence, x1, y1, x2, y2 in raw:
            label = self._class_map.label_for(int(class_id))
            if label is None or confidence < self._min_confidence:
                continue
            detections.append(Detection(label, float(confidence), Box(x1, y1, x2, y2)))
        return detections


class PpeAnalyzer:
    """Normalizes explicit model output without inferring missing PPE."""

    def __init__(
        self, normalizer: DetectionNormalizer, deriver: NoVestDeriver | None = None
    ) -> None:
        # The legacy argument is accepted for compatibility but never invoked.
        self._normalizer = normalizer

    def analyze(self, raw: Iterable[RawDetection]) -> list[Detection]:
        return self._normalizer.normalize(raw)
