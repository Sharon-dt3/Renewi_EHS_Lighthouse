"""HTTP response contracts for the shared schema 1.2 frame analysis."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Label = Literal["person", "helmet", "no_helmet", "safety_vest", "no_safety_vest"]
State = Literal["COMPLIANT", "HELMET_MISSING", "VEST_MISSING",
                "HELMET_AND_VEST_MISSING", "UNKNOWN"]
Rule = Literal["PPE_HELMET_MISSING", "PPE_VEST_MISSING", "ZONE_INCURSION"]
Box = tuple[float, float, float, float]
Point = tuple[float, float]


# PUBLIC_INTERFACE
class DetectionResult(BaseModel):
    """A normalized model detection in original-frame coordinates."""

    label: Label = Field(description="Canonical five-class label.")
    confidence: float = Field(ge=0, le=1, description="Model confidence.")
    box: Box = Field(description="Source pixels [x1, y1, x2, y2].")


# PUBLIC_INTERFACE
class PersonResult(BaseModel):
    """Conservative frame-local PPE assessment, never a tracked identity."""

    index: int = Field(description="Frame-local person index.")
    box: Box = Field(description="Person box in source pixels.")
    confidence: float = Field(description="Person detection confidence.")
    state: State = Field(description="Conservative PPE compliance state.")
    helmet: bool | None = Field(description="Helmet evidence; null means unknown or conflict.")
    vest: bool | None = Field(description="Vest evidence; null means unknown or conflict.")
    helmet_conflict: bool = Field(description="Positive and negative helmet evidence conflict.")
    vest_conflict: bool = Field(description="Positive and negative vest evidence conflict.")
    foot_point: Point = Field(description="Exact source-pixel bottom-center point.")
    zone_incursion: bool = Field(description="Foot point is inside the configured zone.")
    rules: list[Rule] = Field(description="Immediate rules for this person, not sustained incidents.")


# PUBLIC_INTERFACE
class EventResult(BaseModel):
    """Immediate frame observation, not a persisted or smoothed incident."""

    person_index: int = Field(description="Frame-local person index.")
    state: State = Field(description="PPE state.")
    foot_point: Point = Field(description="Exact source-pixel bottom-center point.")
    zone_incursion: bool = Field(description="Configured zone membership.")
    rules: list[Rule] = Field(description="Combined immediate PPE and zone rules.")


# PUBLIC_INTERFACE
class AnalysisResult(BaseModel):
    """Exact schema 1.2 payload emitted by ppe.analysis.to_dict."""

    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.2"] = Field(description="Shared CLI/API analysis version.")
    frame_id: str = Field(description="Server-generated frame identifier.")
    timestamp: float | None = Field(description="Null for independent uploaded images.")
    width: int = Field(description="Original decoded width in pixels.")
    height: int = Field(description="Original decoded height in pixels.")
    detections: list[DetectionResult] = Field(description="Normalized five-class detections.")
    people: list[PersonResult] = Field(description="Frame-local compliance assessments.")
    unassigned_ppe: list[DetectionResult] = Field(description="PPE not associated with a person.")
    zone_incursions: list[DetectionResult] = Field(description="Person detections inside the zone.")
    events: list[EventResult] = Field(description="Immediate observations, without temporal smoothing.")
    rules: list[Rule] = Field(description="Sorted aggregate immediate rules.")


# PUBLIC_INTERFACE
class InferResult(BaseModel):
    """Inference response and server-selected model provenance."""

    clip_id: str = Field(description="Accepted server registry key.")
    checkpoint_sha256: str = Field(description="Registered checkpoint digest.")
    analysis: AnalysisResult = Field(description="Unmodified shared S11 analysis.")


# PUBLIC_INTERFACE
class HealthResult(BaseModel):
    """Liveness with explicit model/configuration readiness."""

    status: Literal["ready", "not_ready"] = Field(description="Whether inference is available.")
    ready: bool = Field(description="True only after configuration and model loading succeed.")


# PUBLIC_INTERFACE
class ErrorResult(BaseModel):
    """Stable, sanitized HTTP error response."""

    detail: str = Field(description="Error explanation without internal paths or media.")
