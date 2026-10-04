import cv2
import numpy as np
import pytest
from pathlib import Path
from scripts import run_incidents as ri


def test_default_rules_file_is_valid_and_consistent():
    r = ri.load_rules(ri.REPO / "config" / "rules.yaml")
    assert r["hold_seconds"] == 1.5 and r["sample_fps"] * r["max_gap_seconds"] >= 1
    assert r["min_negative_confidence"] > r["min_positive_confidence"]     # negatives need stronger evidence than positives


def test_rules_with_too_sparse_sampling_are_refused(tmp_path):
    p = tmp_path / "r.yaml"
    p.write_text("min_positive_confidence: 0.25\nmin_negative_confidence: 0.5\nhold_seconds: 1.5\nmax_gap_seconds: 1.0\nsample_fps: 0.5\n")
    with pytest.raises(SystemExit):
        ri.load_rules(p)


def test_timed_frames_samples_by_timestamp(tmp_path):
    p = tmp_path / "v.mp4"
    w = cv2.VideoWriter(str(p), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (64, 48))
    for _ in range(20):                                                   # 2 s at 10 fps
        w.write(np.zeros((48, 64, 3), np.uint8))
    w.release()
    got = [t for t, _ in ri.timed_frames(p, 4)]
    assert len(got) == 8 and got == sorted(got) and abs(got[1] - got[0] - 0.3) < 0.11   # ~4 fps from a 10 fps source
    assert got[0] == 0.0
