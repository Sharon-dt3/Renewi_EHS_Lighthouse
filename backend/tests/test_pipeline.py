import unittest

from ppe.class_map import ClassMap
from ppe.detections import Label
from ppe.pipeline import DetectionNormalizer, PpeAnalyzer
from ppe.vest_rule import NoVestDeriver

CLASS_MAP = ClassMap(
    checkpoint_sha256="test",
    source="test",
    labels={14: "person", 16: "safety_vest", 12: "helmet"},
)
PERSON = (14, 0.9, 0, 0, 100, 200)
VEST = (16, 0.7, 20, 50, 80, 120)
UNMAPPED = (0, 0.95, 0, 0, 10, 10)
LOW_CONFIDENCE = (12, 0.1, 0, 0, 10, 10)


class DetectionNormalizerTest(unittest.TestCase):
    def setUp(self):
        self.normalizer = DetectionNormalizer(CLASS_MAP)

    def test_maps_ids_to_labels(self):
        labels = [d.label for d in self.normalizer.normalize([PERSON, VEST])]
        self.assertEqual(labels, [Label.PERSON, Label.SAFETY_VEST])

    def test_drops_unmapped_class_ids(self):
        self.assertEqual(self.normalizer.normalize([UNMAPPED]), [])

    def test_drops_below_min_confidence(self):
        self.assertEqual(self.normalizer.normalize([LOW_CONFIDENCE]), [])

    def test_rejects_invalid_min_confidence(self):
        with self.assertRaises(ValueError):
            DetectionNormalizer(CLASS_MAP, min_confidence=1.5)


class PpeAnalyzerTest(unittest.TestCase):
    def setUp(self):
        self.analyzer = PpeAnalyzer(DetectionNormalizer(CLASS_MAP), NoVestDeriver())

    def test_missing_vest_detection_does_not_create_no_vest(self):
        result = self.analyzer.analyze([PERSON, UNMAPPED])
        self.assertEqual([d.label for d in result], [Label.PERSON])
        self.assertFalse(result[0].derived)

    def test_explicit_no_vest_model_output_is_preserved(self):
        # Synthetic future checkpoint mapping, not a claim about Hafizqaim.
        mapping = ClassMap("synthetic-five-class", "test", {0: "person", 4: "no_safety_vest"})
        analyzer = PpeAnalyzer(DetectionNormalizer(mapping))
        result = analyzer.analyze([(0, 0.9, 0, 0, 100, 200), (4, 0.8, 0, 0, 100, 200)])
        self.assertEqual([d.label for d in result], [Label.PERSON, Label.NO_SAFETY_VEST])
        self.assertTrue(all(not d.derived for d in result))

    def test_legacy_deriver_is_never_called(self):
        class ForbiddenDeriver:
            def derive(self, detections):
                raise AssertionError("absence-based derivation must not run")

        analyzer = PpeAnalyzer(DetectionNormalizer(CLASS_MAP), ForbiddenDeriver())
        self.assertEqual([d.label for d in analyzer.analyze([PERSON])], [Label.PERSON])

    def test_vested_person_gets_no_derived_detection(self):
        result = self.analyzer.analyze([PERSON, VEST])
        self.assertEqual([d.label for d in result], [Label.PERSON, Label.SAFETY_VEST])


if __name__ == "__main__":
    unittest.main()
