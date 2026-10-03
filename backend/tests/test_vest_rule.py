import unittest

from ppe.detections import Box, Detection, Label
from ppe.vest_rule import NoVestDeriver

PERSON_A = Detection(Label.PERSON, 0.9, Box(0, 0, 100, 200))
PERSON_B = Detection(Label.PERSON, 0.8, Box(200, 0, 300, 200))
VEST_ON_A = Detection(Label.SAFETY_VEST, 0.7, Box(20, 50, 80, 120))
VEST_FAR = Detection(Label.SAFETY_VEST, 0.7, Box(500, 50, 560, 120))
VEST_BARELY_ON_A = Detection(Label.SAFETY_VEST, 0.7, Box(90, 50, 150, 120))


class NoVestDeriverTest(unittest.TestCase):
    def setUp(self):
        self.deriver = NoVestDeriver()

    def test_person_with_vest_gets_nothing(self):
        self.assertEqual(self.deriver.derive([PERSON_A, VEST_ON_A]), [])

    def test_person_without_vest_gets_one_derived_detection(self):
        result = self.deriver.derive([PERSON_B])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].label, Label.NO_SAFETY_VEST)
        self.assertTrue(result[0].derived)
        self.assertEqual(result[0].box, PERSON_B.box)
        self.assertEqual(result[0].confidence, PERSON_B.confidence)

    def test_vest_elsewhere_does_not_cover_person(self):
        self.assertEqual(len(self.deriver.derive([PERSON_A, VEST_FAR])), 1)

    def test_barely_overlapping_vest_is_below_threshold(self):
        self.assertEqual(len(self.deriver.derive([PERSON_A, VEST_BARELY_ON_A])), 1)

    def test_two_persons_only_one_vested(self):
        result = self.deriver.derive([PERSON_A, VEST_ON_A, PERSON_B])
        self.assertEqual([d.box for d in result], [PERSON_B.box])

    def test_non_person_labels_are_ignored(self):
        helmet = Detection(Label.HELMET, 0.9, Box(0, 0, 10, 10))
        self.assertEqual(self.deriver.derive([helmet]), [])

    def test_invalid_threshold_is_rejected(self):
        with self.assertRaises(ValueError):
            NoVestDeriver(min_vest_overlap=0)


if __name__ == "__main__":
    unittest.main()
