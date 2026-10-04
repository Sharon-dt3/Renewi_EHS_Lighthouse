"""YOLO adapter: the only place Ultralytics objects exist. Everything downstream sees plain tuples and Detections.

Safety (same rules as training): the checkpoint's SHA-256 must be registered in the class-map config, the file is
scanned and loaded only through `ppe.restricted_load`, and nothing is downloaded.
"""
from pathlib import Path
from typing import Any, Sequence, Tuple

from ppe.class_map import ClassMap, load_class_map
from ppe.detector import Detector
from ppe.pipeline import RawDetection
from ppe import restricted_load as rl


def load_model(checkpoint, class_config) -> Tuple[Any, ClassMap]:
    """Return (Ultralytics YOLO object, ClassMap). Raises CheckpointMismatchError for an unregistered hash."""
    cmap = load_class_map(class_config, checkpoint)                 # trust class ids only for this exact file
    src = rl.pick_model(rl.load_restricted(checkpoint))             # static scan + allow-list, weights_only
    names = {int(k): v for k, v in dict(getattr(src, "names", {})).items()}
    if names and names != dict(cmap.labels):
        raise ValueError(f"class names inside the checkpoint {names} do not match the registered map {dict(cmap.labels)}")
    from ultralytics import YOLO
    yolo = YOLO("yolov8n.yaml")
    yolo.load(src)
    yolo.model = src.float().eval()
    yolo.model.names = dict(cmap.labels)
    return yolo, cmap


class YoloDetector(Detector):
    """Detector for one registered checkpoint. Returns (class_id, confidence, x1, y1, x2, y2) in original-frame pixels."""

    def __init__(self, model: Any, device: str = "cpu", imgsz: int = 640, min_confidence: float = 0.25) -> None:
        self._model, self._device, self._imgsz, self._conf = model, device, imgsz, min_confidence

    def detect(self, frame: Any) -> Sequence[RawDetection]:
        result = self._model.predict(frame, conf=self._conf, imgsz=self._imgsz, device=self._device, verbose=False)[0]
        boxes = result.boxes                                         # Ultralytics maps boxes back to the original frame size
        xyxy = boxes.xyxy.cpu().numpy().tolist()
        conf = boxes.conf.cpu().numpy().tolist()
        cls = boxes.cls.cpu().numpy().astype(int).tolist()
        return [(int(c), float(p), x1, y1, x2, y2) for c, p, (x1, y1, x2, y2) in zip(cls, conf, xyxy)]


def load_yolo_detector(checkpoint, class_config, device: str = "cpu", imgsz: int = 640, min_confidence: float = 0.25):
    """Convenience: registered checkpoint -> (YoloDetector, ClassMap)."""
    model, cmap = load_model(Path(checkpoint), Path(class_config))
    return YoloDetector(model, device, imgsz, min_confidence), cmap
