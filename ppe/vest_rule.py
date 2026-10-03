from typing import Iterable

from ppe.detections import Detection


class NoVestDeriver:
    """Compatibility shim: missing vest detections never establish no_safety_vest.

    An explicit negative-vest class must be learned and emitted by the model.
    The legacy overlap argument is validated for API compatibility only.
    """

    def __init__(self, min_vest_overlap: float = 0.5) -> None:
        if not 0.0 < min_vest_overlap <= 1.0:
            raise ValueError("min_vest_overlap must be in (0, 1]")

    def derive(self, detections: Iterable[Detection]) -> list[Detection]:
        return []
