from pathlib import Path

import yaml

from ppe.zone import Polygon


class ZoneConfigError(Exception):
    """The zone config is missing a clip or has a malformed polygon."""


def load_zone(config_path, clip_id: str) -> Polygon:
    with Path(config_path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    entry = (data.get("clips") or {}).get(clip_id)
    if entry is None:
        raise ZoneConfigError(f"No zone for clip '{clip_id}' in {config_path}")
    points = entry.get("polygon") if isinstance(entry, dict) else None
    try:
        return Polygon(tuple((float(x), float(y)) for x, y in points))
    except (TypeError, ValueError) as error:
        raise ZoneConfigError(f"Malformed polygon for clip '{clip_id}'") from error
