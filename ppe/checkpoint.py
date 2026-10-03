import hashlib
from pathlib import Path

_CHUNK_BYTES = 1024 * 1024


def sha256_of(path) -> str:
    """Stream the file through SHA-256. Reads bytes only; never unpickles."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()
