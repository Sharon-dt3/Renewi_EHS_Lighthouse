"""Source-pixel polygon validation and boundary-inclusive zone detection."""
from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Optional, Tuple

from ppe.detections import Box, Detection, Label

Point = Tuple[float, float]
_EPSILON = 1e-9


# PUBLIC_INTERFACE
def foot_point(box: Box) -> Point:
    """Return the bottom-centre in source-frame pixels (image y grows downward)."""
    return ((box.x1 + box.x2) / 2.0, max(box.y1, box.y2))


def _cross(start: Point, end: Point, point: Point) -> float:
    return ((end[0] - start[0]) * (point[1] - start[1])
            - (end[1] - start[1]) * (point[0] - start[0]))


def _on_segment(point: Point, start: Point, end: Point) -> bool:
    return (
        abs(_cross(start, end, point)) <= _EPSILON
        and min(start[0], end[0]) - _EPSILON <= point[0] <= max(start[0], end[0]) + _EPSILON
        and min(start[1], end[1]) - _EPSILON <= point[1] <= max(start[1], end[1]) + _EPSILON
    )


def _intersects(a: Point, b: Point, c: Point, d: Point) -> bool:
    crosses = (_cross(a, b, c), _cross(a, b, d), _cross(c, d, a), _cross(c, d, b))
    if any((_on_segment(c, a, b), _on_segment(d, a, b),
            _on_segment(a, c, d), _on_segment(b, c, d))):
        return True
    return crosses[0] * crosses[1] < 0 and crosses[2] * crosses[3] < 0


def _self_intersects(vertices: Tuple[Point, ...]) -> bool:
    """True if any two non-adjacent edges cross or touch."""
    count = len(vertices)
    for i in range(count):
        a, b = vertices[i], vertices[(i + 1) % count]
        for j in range(i + 1, count):
            if j == i + 1 or (i == 0 and j == count - 1):
                continue                                 # adjacent edges share a vertex by definition
            if _intersects(a, b, vertices[j], vertices[(j + 1) % count]):
                return True
    return False


# PUBLIC_INTERFACE
@dataclass(frozen=True)
class Polygon:
    """A simple, non-degenerate polygon in source-frame pixel coordinates."""

    vertices: Tuple[Point, ...]
    source_size: Optional[Tuple[int, int]] = None  # (width, height), if calibrated

    def __post_init__(self) -> None:
        try:
            vertices = tuple((float(x), float(y)) for x, y in self.vertices)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError("Polygon vertices must be numeric [x, y] pairs") from error
        if len(vertices) < 3:
            raise ValueError("A polygon needs at least 3 vertices")
        if not all(isfinite(v) for point in vertices for v in point):
            raise ValueError("Polygon coordinates must be finite")
        if len(set(vertices)) != len(vertices):
            raise ValueError("Polygon vertices must be distinct; do not repeat the closing vertex")
        object.__setattr__(self, "vertices", vertices)
        count = len(vertices)
        # Check crossings first: a bow-tie's two halves cancel to zero signed area, and "zero area" would be a misleading message.
        if _self_intersects(vertices):
            raise ValueError("Polygon must not self-intersect")
        area2 = sum(_cross(vertices[0], vertices[i], vertices[(i + 1) % count])
                    for i in range(count))
        if abs(area2) <= _EPSILON:
            raise ValueError("Polygon must have non-zero area")
        for i in range(count):
            a, b = vertices[i], vertices[(i + 1) % count]
            previous = vertices[(i - 1) % count]
            # Adjacent edges may share a vertex, but cannot double back/overlap.
            if _on_segment(b, previous, a) or _on_segment(previous, a, b):
                raise ValueError("Polygon has overlapping adjacent edges")
        if self.source_size is not None:
            size = self.source_size
            if (len(size) != 2 or any(type(v) is not int or v <= 0 for v in size)):
                raise ValueError("source_size must be positive integer [width, height]")
            object.__setattr__(self, "source_size", tuple(size))
            self.validate_frame(*size)

    # PUBLIC_INTERFACE
    def validate_frame(self, width: int, height: int) -> None:
        """Reject calibration mismatches or coordinates outside the source frame.

        Continuous image coordinates span [0, width] and [0, height], including
        the outer bounding-box edge. No normalization or rescaling is performed.
        """
        if width <= 0 or height <= 0:
            raise ValueError("Source-frame dimensions must be positive")
        if self.source_size is not None and self.source_size != (width, height):
            raise ValueError(f"Zone source_size {self.source_size} does not match frame {(width, height)}")
        if any(not (0 <= x <= width and 0 <= y <= height) for x, y in self.vertices):
            raise ValueError("Zone polygon lies outside the source frame")

    # PUBLIC_INTERFACE
    def contains(self, point: Point) -> bool:
        """Use ray casting; points on any edge or vertex count as inside."""
        x, y = point
        if not isfinite(x) or not isfinite(y):
            return False
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


# PUBLIC_INTERFACE
class ZoneIncursionDetector:
    """Report person observations touching or inside one source-pixel zone."""

    def __init__(self, zone: Polygon) -> None:
        self._zone = zone

    # PUBLIC_INTERFACE
    def validate_frame(self, width: int, height: int) -> None:
        """Validate the configured polygon against a decoded source frame."""
        self._zone.validate_frame(width, height)

    # PUBLIC_INTERFACE
    def persons_inside(self, detections: Iterable[Detection]) -> list[Detection]:
        """Return only people whose bottom-centre is inside or on the boundary."""
        return [
            d for d in detections
            if d.label == Label.PERSON and self._zone.contains(foot_point(d.box))
        ]
