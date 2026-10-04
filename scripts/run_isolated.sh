#!/bin/sh
# Run a command with no network and no write access to the protected folders (macOS sandbox-exec).
# Usage: scripts/run_isolated.sh <command> [args...]
# Part of the isolated environment required by docs/weight-transfer-plan.md section 4.
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
[ -d "$ROOT/raw_css_dataset" ] || { echo "workspace root not found" >&2; exit 2; }
PROFILE="(version 1)
(allow default)
(deny network*)
(deny file-write* (subpath \"$ROOT/models\") (subpath \"$ROOT/raw_css_dataset\") (subpath \"$ROOT/derived_ppe5\") (subpath \"$ROOT/weights\"))"
exec /usr/bin/sandbox-exec -p "$PROFILE" "$@"
