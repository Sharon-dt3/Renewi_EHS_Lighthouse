from typing import Any

from ppe.detector import Detector
from ppe.pipeline import PpeAnalyzer
from ppe.schema import FrameResult
from ppe.zone import ZoneIncursionDetector


class FramePipeline:
    """Runs one frame through detection, analysis and zone checking."""

    def __init__(
        self,
        detector: Detector,
        analyzer: PpeAnalyzer,
        zone_detector: ZoneIncursionDetector,
    ) -> None:
        self._detector = detector
        self._analyzer = analyzer
        self._zone_detector = zone_detector

    def process(self, frame_id: str, frame: Any) -> FrameResult:
        raw = self._detector.detect(frame)
        detections = self._analyzer.analyze(raw)
        incursions = self._zone_detector.persons_inside(detections)
        return FrameResult(frame_id, tuple(detections), tuple(incursions))
