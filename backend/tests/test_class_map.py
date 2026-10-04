import hashlib
import tempfile
import unittest
from pathlib import Path

from ppe.class_map import CheckpointMismatchError, ConfigError, load_class_map

FAKE_BYTES = b"not a real checkpoint"
FAKE_SHA = hashlib.sha256(FAKE_BYTES).hexdigest()


def _config(sha: str, label: str = "person") -> str:
    return (
        "checkpoints:\n"
        f"  {sha}:\n"
        "    source: test\n"
        "    classes:\n"
        f"      14: {label}\n"
    )


class LoadClassMapTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.checkpoint = self.dir / "best.pt"
        self.checkpoint.write_bytes(FAKE_BYTES)
        self.config = self.dir / "classes.yaml"

    def test_matching_hash_returns_labels(self):
        self.config.write_text(_config(FAKE_SHA))
        class_map = load_class_map(self.config, self.checkpoint)
        self.assertEqual(class_map.label_for(14), "person")
        self.assertIsNone(class_map.label_for(99))
        self.assertEqual(class_map.checkpoint_sha256, FAKE_SHA)

    def test_unlisted_hash_raises(self):
        self.config.write_text(_config("0" * 64))
        with self.assertRaises(CheckpointMismatchError):
            load_class_map(self.config, self.checkpoint)

    def test_unknown_label_raises(self):
        self.config.write_text(_config(FAKE_SHA, label="persn"))
        with self.assertRaises(ConfigError):
            load_class_map(self.config, self.checkpoint)

    def test_missing_checkpoint_raises(self):
        self.config.write_text(_config(FAKE_SHA))
        with self.assertRaises(FileNotFoundError):
            load_class_map(self.config, self.dir / "absent.pt")


if __name__ == "__main__":
    unittest.main()


def test_colab_full_1_checkpoint_has_its_own_five_class_map():
    import yaml
    from pathlib import Path
    cfg = yaml.safe_load((Path(__file__).resolve().parents[2] / "config" / "classes.yaml").read_text())
    new = cfg["checkpoints"]["899d48d685404a2aba794233da8990ac8478e841d5e5713557dc2d99ca8d6463"]
    assert new["classes"] == {0: "person", 1: "helmet", 2: "no_helmet", 3: "safety_vest", 4: "no_safety_vest"}
    old = cfg["checkpoints"]["5464f555f1b9831e6f1f9adcab11063f9a081d62e6650c2f2154bd4c01720836"]
    assert 4 not in old["classes"] and "no_safety_vest" not in old["classes"].values()   # the old map is untouched and has no negative vest
