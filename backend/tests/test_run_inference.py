import json
import numpy as np
from scripts import run_inference as ri

LABELS = {0: "person", 1: "helmet", 2: "no_helmet", 3: "safety_vest", 4: "no_safety_vest"}
INDEX = {v: k for k, v in LABELS.items()}

def test_records_are_normalised_and_unknown_ids_are_dropped():
    recs = ri.detections_to_records([[100, 50, 300, 250], [0, 0, 10, 10]], [0.9, 0.8], [4, 99], LABELS, 400, 500)
    assert len(recs) == 1 and recs[0]["class"] == "no_safety_vest" and recs[0]["confidence"] == 0.9
    assert recs[0]["yolo"] == [0.5, 0.3, 0.5, 0.4] and recs[0]["xyxy"] == [100.0, 50.0, 300.0, 250.0]

def test_yolo_lines_use_the_five_class_ids_with_confidence():
    recs = ri.detections_to_records([[0, 0, 200, 100]], [0.5], [2], LABELS, 200, 100)
    assert ri.yolo_lines(recs, INDEX) == "2 0.5 0.5 1.0 1.0 0.5\n"

def test_draw_returns_same_shape_and_does_not_modify_input():
    img = np.zeros((100, 100, 3), np.uint8); before = img.copy()
    recs = ri.detections_to_records([[10, 10, 60, 60]], [0.7], [1], LABELS, 100, 100)
    out = ri.draw(img, recs)
    assert out.shape == img.shape and (img == before).all() and out.any()

def test_registered_checkpoint_must_be_known(tmp_path):
    import pytest, torch
    from ppe.class_map import CheckpointMismatchError
    p = tmp_path / "x.pt"; torch.save({"w": 1}, p)
    with pytest.raises(CheckpointMismatchError):
        ri.load_model(p, ri.REPO / "config" / "classes.yaml")      # unregistered hash is refused before any load
