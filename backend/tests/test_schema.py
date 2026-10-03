import json
import unittest

from ppe.detections import Box, Detection, Label
from ppe.schema import SCHEMA_VERSION, FrameResult, to_dict, to_json

PERSON = Detection(Label.PERSON, 0.9, Box(0, 0, 100, 200))
NO_VEST = Detection(Label.NO_SAFETY_VEST, 0.9, Box(0, 0, 100, 200), derived=True)


class SchemaTest(unittest.TestCase):
    def setUp(self):
        self.result = FrameResult("clip1:0042", (PERSON, NO_VEST), (PERSON,))

    def test_top_level_keys(self):
        self.assertEqual(
            set(to_dict(self.result)),
            {"schema_version", "frame_id", "detections", "incursions"},
        )
        self.assertEqual(to_dict(self.result)["schema_version"], SCHEMA_VERSION)

    def test_detection_entry_shape(self):
        entry = to_dict(self.result)["detections"][0]
        self.assertEqual(set(entry), {"label", "confidence", "box", "derived"})
        self.assertEqual(entry["box"], [0, 0, 100, 200])

    def test_derived_flag_is_preserved(self):
        flags = [d["derived"] for d in to_dict(self.result)["detections"]]
        self.assertEqual(flags, [False, True])

    def test_incursions_are_serialized(self):
        incursions = to_dict(self.result)["incursions"]
        self.assertEqual(len(incursions), 1)
        self.assertEqual(incursions[0]["label"], Label.PERSON)

    def test_json_round_trip(self):
        self.assertEqual(json.loads(to_json(self.result)), to_dict(self.result))

    def test_label_outside_internal_set_is_rejected(self):
        bad = Detection("NO-Hardhat", 0.9, Box(0, 0, 1, 1))
        with self.assertRaises(ValueError):
            to_dict(FrameResult("f", (bad,), ()))


if __name__ == "__main__":
    unittest.main()
