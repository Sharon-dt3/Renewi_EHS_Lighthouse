import unittest

from ppe.class_map import ClassMap
from ppe.detections import Label
from ppe.detector import Detector
from ppe.frame_pipeline import FramePipeline
from ppe.pipeline import DetectionNormalizer, PpeAnalyzer
from ppe.vest_rule import NoVestDeriver
from ppe.zone import Polygon, ZoneIncursionDetector

CLASS_MAP = ClassMap("test", "test", {14: "person", 16: "safety_vest"})
ZONE = Polygon(((0, 0), (400, 0), (400, 400), (0, 400)))
PERSON_IN_ZONE = (14, 0.9, 100, 100, 200, 300)
PERSON_OUTSIDE = (14, 0.9, 500, 100, 600, 300)
UNMAPPED = (0, 0.95, 0, 0, 10, 10)


class FakeDetector(Detector):
    def __init__(self, raw):
        self._raw = raw
        self.frames_seen = []

    def detect(self, frame):
        self.frames_seen.append(frame)
        return self._raw


def build_pipeline(raw):
    detector = FakeDetector(raw)
    pipeline = FramePipeline(
        detector,
        PpeAnalyzer(DetectionNormalizer(CLASS_MAP), NoVestDeriver()),
        ZoneIncursionDetector(ZONE),
    )
    return pipeline, detector


class FramePipelineTest(unittest.TestCase):
    def test_detector_is_abstract(self):
        with self.assertRaises(TypeError):
            Detector()

    def test_frame_id_is_passed_through(self):
        pipeline, _ = build_pipeline([])
        self.assertEqual(pipeline.process("clip1:7", object()).frame_id, "clip1:7")

    def test_detector_called_once_with_the_frame(self):
        pipeline, detector = build_pipeline([])
        frame = object()
        pipeline.process("f", frame)
        self.assertEqual(detector.frames_seen, [frame])

    def test_person_in_zone_does_not_imply_no_vest(self):
        pipeline, _ = build_pipeline([PERSON_IN_ZONE])
        result = pipeline.process("f", None)
        self.assertEqual(
            [d.label for d in result.detections],
            [Label.PERSON],
        )
        self.assertEqual([d.label for d in result.incursions], [Label.PERSON])

    def test_person_outside_zone_has_no_incursion(self):
        pipeline, _ = build_pipeline([PERSON_OUTSIDE])
        self.assertEqual(pipeline.process("f", None).incursions, ())

    def test_unmapped_classes_never_reach_the_result(self):
        pipeline, _ = build_pipeline([UNMAPPED])
        self.assertEqual(pipeline.process("f", None).detections, ())


if __name__ == "__main__":
    unittest.main()
