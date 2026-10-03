from dataclasses import dataclass


class Label:
    """Internal class names, shared across the pipeline."""
    PERSON = "person"
    HELMET = "helmet"
    NO_HELMET = "no_helmet"
    SAFETY_VEST = "safety_vest"
    NO_SAFETY_VEST = "no_safety_vest"


@dataclass(frozen=True)
class Box:
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def area(self) -> float:
        return max(0.0, self.x2 - self.x1) * max(0.0, self.y2 - self.y1)

    def intersection_area(self, other: "Box") -> float:
        width = min(self.x2, other.x2) - max(self.x1, other.x1)
        height = min(self.y2, other.y2) - max(self.y1, other.y1)
        return max(0.0, width) * max(0.0, height)


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float
    box: Box
    derived: bool = False  # True when inferred by a rule, not detected by a model


ALL_LABELS = frozenset(v for k, v in vars(Label).items() if not k.startswith("_"))
