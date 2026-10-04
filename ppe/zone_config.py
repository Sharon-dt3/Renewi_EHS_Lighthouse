"""Load per-clip source-pixel zones without silently falling back to a default."""
from pathlib import Path

import yaml

from ppe.zone import Polygon


# PUBLIC_INTERFACE
class ZoneConfigError(Exception):
    """The zone config is unreadable, missing a clip, or has a malformed polygon."""


# PUBLIC_INTERFACE
def load_zone(config_path, clip_id: str) -> Polygon:
    """Return the validated polygon for clip_id, or raise ZoneConfigError.

    YAML entries contain polygon: [[x, y], ...] in source pixels and may specify
    source_size: [width, height] to reject a differently sized video.
    """
    try:
        with Path(config_path).open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        if not isinstance(data, dict) or not isinstance(data.get("clips"), dict):
            raise ValueError("Expected a clips mapping")
        entry = data["clips"].get(clip_id)
        if entry is None:
            raise ZoneConfigError(f"No zone for clip '{clip_id}' in {config_path}")
        if not isinstance(entry, dict):
            raise ValueError("Expected a clip mapping")
        points = entry.get("polygon")
        size = entry.get("source_size")
        return Polygon(points, tuple(size) if size is not None else None)
    except (OSError, yaml.YAMLError, TypeError, ValueError, OverflowError) as error:
        raise ZoneConfigError(f"Invalid zone for clip '{clip_id}' in {config_path}: {error}") from error
