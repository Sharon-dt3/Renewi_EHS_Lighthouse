from abc import ABC, abstractmethod
from typing import Any, Sequence

from ppe.pipeline import RawDetection


class Detector(ABC):
    """Produces raw detections for one frame, in original frame pixel coordinates.

    Implementations return (class_id, confidence, x1, y1, x2, y2) tuples. IDs are
    checkpoint-specific and are mapped to labels elsewhere, never here.
    """

    @abstractmethod
    def detect(self, frame: Any) -> Sequence[RawDetection]:
        raise NotImplementedError
