"""Server-owned inference configuration and bounded image processing.

PPE_API_CONFIG must be requested from the user through the orchestrator.
It names a server-controlled YAML file, not a client input.
"""
import io
import os
import re
import threading
import warnings
from pathlib import Path
from uuid import uuid4

import numpy as np
import yaml
from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ppe.analysis import FrameAnalyzer, to_dict
from ppe.zone import ZoneIncursionDetector
from ppe.zone_config import load_zone

REPO = Path(__file__).resolve().parents[1]


# PUBLIC_INTERFACE
class ClipSettings(BaseModel):
    """One server-controlled demo configuration; null zones means PPE only."""

    model_config = ConfigDict(extra="forbid")
    zones: Path | None = Field(default=None, description="Server-owned zone YAML path.")


# PUBLIC_INTERFACE
class ApiSettings(BaseModel):
    """Validated, bounded runtime settings loaded only from server YAML."""

    model_config = ConfigDict(extra="forbid")
    checkpoint: Path = Field(description="Registered server checkpoint path.")
    classes: Path = Field(default=Path("config/classes.yaml"), description="Class-map registry.")
    rules: Path = Field(default=Path("config/rules.yaml"), description="Shared CLI compliance rules.")
    clips: dict[str, ClipSettings] = Field(min_length=1, description="Allowed clip identifiers.")
    device: str = Field(default="cpu", description="Server-selected inference device.")
    imgsz: int = Field(default=640, ge=32, le=2048, description="Model inference resolution.")
    confidence: float = Field(default=0.25, ge=0, le=1, description="Same confidence floor as CLI.")
    max_file_bytes: int = Field(default=5 * 1024 * 1024, ge=1, le=20 * 1024 * 1024,
                                description="Maximum encoded image size.")
    max_dimension: int = Field(default=4096, ge=1, le=8192, description="Maximum width or height.")
    max_pixels: int = Field(default=12_000_000, ge=1, le=32_000_000,
                            description="Maximum decoded pixel count.")

    @model_validator(mode="after")
    def _validate_clip_keys(self):
        if any(not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", key) for key in self.clips):
            raise ValueError("Clip keys must be 1-64 alphanumeric, underscore or hyphen characters")
        return self


def _server_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO / path


# PUBLIC_INTERFACE
def load_settings() -> ApiSettings:
    """Load PPE_API_CONFIG; missing or invalid settings fail readiness closed."""
    value = os.environ.get("PPE_API_CONFIG")
    if not value:
        raise ValueError("PPE_API_CONFIG is required")
    with _server_path(Path(value)).open(encoding="utf-8") as handle:
        return ApiSettings.model_validate(yaml.safe_load(handle))


# PUBLIC_INTERFACE
def decode_image(data: bytes, settings: ApiSettings) -> np.ndarray:
    """Validate JPEG/PNG headers before decoding; return unresized OpenCV BGR pixels."""
    if not data:
        raise HTTPException(422, "Empty image")
    if len(data) > settings.max_file_bytes:
        raise HTTPException(413, "Image exceeds file-size limit")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as image:
                if image.format not in {"JPEG", "PNG"}:
                    raise HTTPException(415, "Only JPEG and PNG images are supported")
                width, height = image.size
                if (width > settings.max_dimension or height > settings.max_dimension
                        or width * height > settings.max_pixels):
                    raise HTTPException(413, "Image exceeds dimension or pixel limit")
                if getattr(image, "n_frames", 1) != 1:
                    raise HTTPException(415, "Animated images are not supported")
                image.verify()
            with Image.open(io.BytesIO(data)) as image:
                # Do not rotate EXIF or resize: zones and boxes use CLI source coordinates.
                return np.asarray(image.convert("RGB"))[:, :, ::-1].copy()
    except HTTPException:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
        raise HTTPException(413, "Image exceeds decoder safety limit") from error
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as error:
        raise HTTPException(422, "Invalid or corrupt image") from error


# PUBLIC_INTERFACE
class InferenceService:
    """Load one registered model and share CLI FrameAnalyzer across allowed clips."""

    def __init__(self, settings: ApiSettings, detector=None, class_map=None):
        """Load server rules/zones and the restricted checkpoint, or inject a test detector."""
        self.settings = settings
        with _server_path(settings.rules).open(encoding="utf-8") as handle:
            rules = yaml.safe_load(handle)
        negative_floor = max(settings.confidence, float(rules["min_negative_confidence"]))
        # Validate every zone before loading a checkpoint; never fall back to PPE-only.
        zones = {
            key: ZoneIncursionDetector(load_zone(_server_path(clip.zones), key))
            if clip.zones else None
            for key, clip in settings.clips.items()
        }
        if detector is None:
            from ppe.yolo_detector import load_yolo_detector
            detector, class_map = load_yolo_detector(
                _server_path(settings.checkpoint), _server_path(settings.classes),
                settings.device, settings.imgsz, settings.confidence,
            )
        if class_map is None:
            raise ValueError("A registered class map is required")
        self.checkpoint_sha256 = class_map.checkpoint_sha256
        self._analyzers = {
            key: FrameAnalyzer(detector, class_map, settings.confidence, negative_floor, zone)
            for key, zone in zones.items()
        }
        self._zones = zones
        self._lock = threading.Lock()

    # PUBLIC_INTERFACE
    def infer(self, clip_id: str, data: bytes) -> dict:
        """Analyze one bounded image with server configuration; reject parallel model use."""
        analyzer = self._analyzers.get(clip_id)
        if analyzer is None:
            raise HTTPException(422, "Unknown clip_id")
        if not self._lock.acquire(blocking=False):
            raise HTTPException(503, "Inference service is busy")
        try:
            frame = decode_image(data, self.settings)
            # Validate zone dimensions before model execution using the same zone validator.
            zone = self._zones[clip_id]
            if zone:
                try:
                    zone.validate_frame(frame.shape[1], frame.shape[0])
                except ValueError as error:
                    raise HTTPException(422, "Image dimensions do not match clip configuration") from error
            result = analyzer.analyze(uuid4().hex, frame)
            return {"clip_id": clip_id, "checkpoint_sha256": self.checkpoint_sha256,
                    "analysis": to_dict(result)}
        finally:
            self._lock.release()
