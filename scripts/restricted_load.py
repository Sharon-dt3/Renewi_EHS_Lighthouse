"""Compatibility shim. The implementation moved to `ppe/restricted_load.py` so library code does not depend on `scripts/`.
Existing imports (`from scripts import restricted_load`, `import restricted_load`) keep working."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ppe.restricted_load import *  # noqa: F401,F403,E402
from ppe.restricted_load import _resolve  # noqa: F401,E402
