#!/usr/bin/env python3
"""Create one entry for the users file (PPE_USERS_FILE): a named user with a salted scrypt hash.

The password is read from a hidden prompt (or the PPE_NEW_PASSWORD environment variable for automation); it is never
accepted as a command-line argument, so it cannot end up in shell history or a process list. Only the hash is printed.

Usage:  .venv/bin/python scripts/make_user.py --username alice --role supervisor >> users.yaml   (add a 'users:' header once)
"""
import argparse
import getpass
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from backend import security as sec  # noqa: E402


# PUBLIC_INTERFACE
def build_entry(username: str, role: str, password: str) -> str:
    """Return the YAML list item for a user after applying the same rules the server applies at startup."""
    if role not in sec.ROLES:
        raise SystemExit(f"role must be one of {sec.ROLES}")
    if not sec._valid_username(username):
        raise SystemExit(f"username must be 1-{sec.MAX_USERNAME_LENGTH} printable characters, no colon, no surrounding spaces")
    if len(password) < sec.MIN_PASSWORD_LENGTH or not password.strip():
        raise SystemExit(f"password must be at least {sec.MIN_PASSWORD_LENGTH} characters")
    return f'  - {{username: "{username}", role: {role}, hash: "{sec.hash_password(password)}"}}'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--username", required=True); ap.add_argument("--role", required=True, choices=sec.ROLES)
    a = ap.parse_args(argv)
    password = os.environ.get("PPE_NEW_PASSWORD")
    if password is None:
        password = getpass.getpass("Password: ")
        if getpass.getpass("Repeat password: ") != password:
            raise SystemExit("passwords differ")
    print(build_entry(a.username, a.role, password))
    return 0


if __name__ == "__main__":
    sys.exit(main())
