from typing import Iterable

from ppe.detections import Detection, Label


class NoVestDeriver:
    """Derives no_safety_vest for each person box not covered by a safety_vest box.

    Absence of a vest detection is not evidence of no vest: a missed or occluded
    vest produces a false alarm. Output is flagged derived=True for that reason.
    """

    def __init__(self, min_vest_overlap: float = 0.5) -> None:
        if not 0.0 < min_vest_overlap <= 1.0:
            raise ValueError("min_vest_overlap must be in (0, 1]")
        self._min_vest_overlap = min_vest_overlap

    def derive(self, detections: Iterable[Detection]) -> list[Detection]:
        detections = list(detections)
        persons = [d for d in detections if d.label == Label.PERSON]
        vests = [d for d in detections if d.label == Label.SAFETY_VEST]
        return [
            Detection(Label.NO_SAFETY_VEST, p.confidence, p.box, derived=True)
            for p in persons
            if not self._has_vest(p, vests)
        ]

    def _has_vest(self, person: Detection, vests: list[Detection]) -> bool:
        return any(self._overlap(person, v) >= self._min_vest_overlap for v in vests)

    @staticmethod
    def _overlap(person: Detection, vest: Detection) -> float:
        vest_area = vest.box.area
        if vest_area == 0:
            return 0.0
        return person.box.intersection_area(vest.box) / vest_area
