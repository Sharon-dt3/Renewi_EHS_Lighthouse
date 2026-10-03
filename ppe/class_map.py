from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Optional

import yaml

from ppe.checkpoint import sha256_of
from ppe.detections import Label

_KNOWN_LABELS = frozenset(v for k, v in vars(Label).items() if not k.startswith("_"))


class CheckpointMismatchError(Exception):
    """The checkpoint's SHA-256 is not listed in the class-map config."""


class ConfigError(Exception):
    """The class-map config is malformed."""


@dataclass(frozen=True)
class ClassMap:
    checkpoint_sha256: str
    source: str
    labels: Mapping[int, str]

    def label_for(self, class_id: int) -> Optional[str]:
        return self.labels.get(class_id)


def load_class_map(config_path, checkpoint_path) -> ClassMap:
    """Return the class map for this exact checkpoint, or raise.

    The checkpoint is identified by SHA-256 before any ID is trusted.
    """
    actual = sha256_of(checkpoint_path)
    with Path(config_path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    entry = (data.get("checkpoints") or {}).get(actual)
    if entry is None:
        raise CheckpointMismatchError(
            f"Checkpoint SHA-256 {actual} is not listed in {config_path}"
        )
    classes = entry.get("classes")
    if not isinstance(classes, dict) or not classes:
        raise ConfigError(f"No 'classes' mapping for checkpoint {actual}")
    labels = {int(k): str(v) for k, v in classes.items()}
    unknown = set(labels.values()) - _KNOWN_LABELS
    if unknown:
        raise ConfigError(f"Unknown labels in config: {sorted(unknown)}")
    return ClassMap(actual, str(entry.get("source", "unknown")), MappingProxyType(labels))
