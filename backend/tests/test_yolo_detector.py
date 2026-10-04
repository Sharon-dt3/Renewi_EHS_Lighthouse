import numpy as np
import pytest

from ppe.yolo_detector import YoloDetector, load_model


class _T:
    def __init__(self, a): self.a = np.array(a)
    def cpu(self): return self
    def numpy(self): return self.a


class _Boxes:
    def __init__(self):
        self.xyxy = _T([[10, 20, 110, 220], [5, 5, 50, 60]])
        self.conf = _T([0.9, 0.4])
        self.cls = _T([0.0, 3.0])


class _Result:
    boxes = _Boxes()


class _Model:
    def __init__(self): self.kwargs = None
    def predict(self, frame, **kw):
        self.kwargs = kw
        return [_Result()]


def test_detector_returns_plain_tuples_in_frame_pixels_and_passes_settings():
    m = _Model()
    out = YoloDetector(m, device="cpu", imgsz=640, min_confidence=0.25).detect(np.zeros((100, 100, 3), np.uint8))
    assert out == [(0, 0.9, 10.0, 20.0, 110.0, 220.0), (3, 0.4, 5.0, 5.0, 50.0, 60.0)]
    assert m.kwargs == {"conf": 0.25, "imgsz": 640, "device": "cpu", "verbose": False}
    assert all(isinstance(t[0], int) for t in out)


def test_unregistered_checkpoint_is_refused_before_loading(tmp_path):
    import torch
    from ppe.class_map import CheckpointMismatchError
    p = tmp_path / "x.pt"; torch.save({"w": 1}, p)
    from pathlib import Path
    with pytest.raises(CheckpointMismatchError):
        load_model(p, Path(__file__).resolve().parents[2] / "config" / "classes.yaml")
