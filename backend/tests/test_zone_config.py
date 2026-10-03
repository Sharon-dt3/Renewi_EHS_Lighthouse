import tempfile
import unittest
from pathlib import Path

from ppe.zone_config import ZoneConfigError, load_zone


class LoadZoneTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "zones.yaml"

    def _write(self, polygon_yaml: str) -> None:
        self.path.write_text(f"clips:\n  clip_a:\n    polygon: {polygon_yaml}\n")

    def test_loads_polygon_for_clip(self):
        self._write("[[0, 0], [10, 0], [10, 10]]")
        zone = load_zone(self.path, "clip_a")
        self.assertEqual(zone.vertices, ((0.0, 0.0), (10.0, 0.0), (10.0, 10.0)))

    def test_unknown_clip_raises(self):
        self._write("[[0, 0], [10, 0], [10, 10]]")
        with self.assertRaises(ZoneConfigError):
            load_zone(self.path, "clip_b")

    def test_malformed_points_raise(self):
        self._write("[[0, 0, 5], [10, 0], [10, 10]]")
        with self.assertRaises(ZoneConfigError):
            load_zone(self.path, "clip_a")

    def test_too_few_points_raise(self):
        self._write("[[0, 0], [10, 0]]")
        with self.assertRaises(ZoneConfigError):
            load_zone(self.path, "clip_a")


if __name__ == "__main__":
    unittest.main()
