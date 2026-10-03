from dataclasses import dataclass
from typing import Iterable, Tuple

from ppe.detections import Box, Detection, Label

Point = Tuple[float, float]
_EPSILON = 1e-9


def foot_point(box: Box) -> Point:
    """Bottom-center of a box. Image y grows downward, so max y is the feet."""
    return ((box.x1 + box.x2) / 2.0, max(box.y1, box.y2))


def _on_segment(point: Point, start: Point, end: Point) -> bool:
    px, py = point
    (x1, y1), (x2, y2) = start, end
    cross = (px - x1) * (y2 - y1) - (py - y1) * (x2 - x1)
    if abs(cross) > _EPSILON:
        return False
    return (
        min(x1, x2) - _EPSILON <= px <= max(x1, x2) + _EPSILON
        and min(y1, y2) - _EPSILON <= py <= max(y1, y2) + _EPSILON
    )


@dataclass(frozen=True)
class Polygon:
    vertices: Tuple[Point, ...]

    def __post_init__(self) -> None:
        if len(self.vertices) < 3:
            raise ValueError("A polygon needs at least 3 vertices")

    def contains(self, point: Point) -> bool:
        """Ray casting. Points on an edge or vertex count as inside."""
        x, y = point
        inside = False
        count = len(self.vertices)
        for i in range(count):
            start = self.vertices[i]
            end = self.vertices[(i + 1) % count]
            if _on_segment(point, start, end):
                return True
            (x1, y1), (x2, y2) = start, end
            if (y1 > y) != (y2 > y):
                x_cross = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                if x < x_cross:
                    inside = not inside
        return inside


class ZoneIncursionDetector:
    """Reports person detections whose foot point is inside the zone."""

    def __init__(self, zone: Polygon) -> None:
        self._zone = zone

    def persons_inside(self, detections: Iterable[Detection]) -> list[Detection]:
        return [
            d for d in detections
            if d.label == Label.PERSON and self._zone.contains(foot_point(d.box))
        ]
