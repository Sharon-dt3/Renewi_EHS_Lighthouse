#!/usr/bin/env python3
"""Print the G1 OpenAPI contract or check a published JSON artifact without loading weights."""
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from backend.app import create_app  # noqa: E402


# PUBLIC_INTERFACE
def main(argv=None):
    """Print OpenAPI to stdout; --check returns nonzero when the artifact has drifted."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", type=Path, help="Compare a committed JSON contract with the live schema.")
    args = parser.parse_args(argv)
    schema = create_app().openapi()
    if args.check:
        if json.loads(args.check.read_text(encoding="utf-8")) != schema:
            print("OpenAPI contract has drifted", file=sys.stderr)
            return 1
        print("G1 OpenAPI contract matches the application")
    else:
        print(json.dumps(schema, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
