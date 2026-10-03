import unittest

from ppe.detections import Box, Detection, Label
from ppe.zone import Polygon, ZoneIncursionDetector, foot_point

SQUARE = Polygon(((0, 0), (10, 0), (10, 10), (0, 10)))
L_SHAPE = Polygon(((0, 0), (10, 0), (10, 4), (4, 4), (4, 10), (0, 10)))


class PolygonTest(unittest.TestCase):
    def test_point_inside_square(self):
        self.assertTrue(SQUARE.contains((5, 5)))

    def test_point_outside_square(self):
        self.assertFalse(SQUARE.contains((15, 5)))

    def test_point_on_edge_counts_as_inside(self):
        self.assertTrue(SQUARE.contains((10, 5)))

    def test_vertex_counts_as_inside(self):
        self.assertTrue(SQUARE.contains((0, 0)))

    def test_concave_notch_is_outside(self):
        self.assertFalse(L_SHAPE.contains((7, 7)))

    def test_concave_arms_are_inside(self):
        self.assertTrue(L_SHAPE.contains((2, 7)))
        self.assertTrue(L_SHAPE.contains((7, 2)))

    def test_fewer_than_three_vertices_rejected(self):
        with self.assertRaises(ValueError):
            Polygon(((0, 0), (1, 1)))


class FootPointTest(unittest.TestCase):
    def test_foot_point_is_bottom_center(self):
        self.assertEqual(foot_point(Box(10, 20, 30, 100)), (20.0, 100))


class IncursionTest(unittest.TestCase):
    def setUp(self):
        self.detector = ZoneIncursionDetector(SQUARE)

    def test_person_with_foot_inside_is_reported(self):
        person = Detection(Label.PERSON, 0.9, Box(4, -20, 6, 8))
        self.assertEqual(self.detector.persons_inside([person]), [person])

    def test_person_standing_outside_is_not_reported(self):
        person = Detection(Label.PERSON, 0.9, Box(4, -30, 6, -1))
        self.assertEqual(self.detector.persons_inside([person]), [])

    def test_non_person_labels_are_ignored(self):
        vest = Detection(Label.SAFETY_VEST, 0.9, Box(4, 4, 6, 8))
        self.assertEqual(self.detector.persons_inside([vest]), [])


if __name__ == "__main__":
    unittest.main()
