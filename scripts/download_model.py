"""Download reviewed weights without importing or executing a model checkpoint."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, StrictBool
import requests
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SOURCE_HOSTS = {"api.github.com", "github.com", "huggingface.co"}
_REDIRECT_HOSTS = _SOURCE_HOSTS | {
    "release-assets.githubusercontent.com",
    "objects.githubusercontent.com",
    "cdn-lfs.huggingface.co",
    "cdn-lfs-us-1.huggingface.co",
    "cas-bridge.xethub.hf.co",
}


# PUBLIC_INTERFACE
class ModelApproval(BaseModel):
    """Recorded human rights/capability review; false or incomplete review blocks IO."""

    model_config = ConfigDict(extra="forbid")
    approved: StrictBool = False
    reviewer: str | None = None
    license_identifier: str | None = None
    license_evidence_url: str | None = None
    actual_classes_verified: StrictBool = False
    required_classes_supported: StrictBool = False


# PUBLIC_INTERFACE
class ModelSource(BaseModel):
    """Pinned source metadata and destination relative to the application root."""

    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1)
    repository: str = Field(min_length=1)
    revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    architecture: str = Field(min_length=1)
    weights_url: str
    weights_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    weights_size_bytes: int = Field(gt=0, le=2_000_000_000, strict=True)
    local_path: str
    provenance_document: str
    approval: ModelApproval


def _validate_url(url: str, hosts: set[str]) -> None:
    parts = urlsplit(url)
    if (
        parts.scheme != "https"
        or parts.hostname not in hosts
        or parts.username is not None
        or parts.password is not None
        or parts.port not in (None, 443)
        or parts.fragment
    ):
        raise ValueError("Model source must use HTTPS on an approved public host.")


def _project_path(value: str, root: Path) -> Path:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Model paths must stay within the project root.")
    destination = (root / relative).resolve()
    if not destination.is_relative_to(root.resolve()) or destination == root.resolve():
        raise ValueError("Model paths must stay within the project root.")
    return destination


# PUBLIC_INTERFACE
def load_source(config_path: Path, project_root: Path = PROJECT_ROOT) -> ModelSource:
    """Load and validate approved YAML provenance before any network or file writes."""
    with config_path.open(encoding="utf-8") as stream:
        document = yaml.safe_load(stream)
    if not isinstance(document, dict) or set(document) != {"model"}:
        raise ValueError("Configuration must contain exactly one 'model' mapping.")
    source = ModelSource.model_validate(document["model"])
    approval = source.approval
    if not (
        approval.approved
        and approval.actual_classes_verified
        and approval.required_classes_supported
        and approval.reviewer
        and approval.reviewer.strip()
        and approval.license_identifier
        and approval.license_identifier.strip()
        and approval.license_evidence_url
    ):
        raise ValueError("Model approval is incomplete; see docs/model-selection.md.")
    _validate_url(source.repository, _SOURCE_HOSTS)
    _validate_url(source.weights_url, _SOURCE_HOSTS)
    # Do not let mutable branch URLs masquerade as pinned Hub downloads.
    if urlsplit(source.weights_url).hostname == "huggingface.co":
        if f"/resolve/{source.revision}/" not in urlsplit(source.weights_url).path:
            raise ValueError("Hugging Face weights must use the pinned revision.")
    if urlsplit(source.weights_url).hostname in {"github.com", "api.github.com"}:
        path = urlsplit(source.weights_url).path
        if not re.fullmatch(r"/repos/[^/]+/[^/]+/releases/assets/[0-9]+", path):
            raise ValueError("GitHub weights must use a release asset API URL.")
        if urlsplit(source.weights_url).hostname != "api.github.com":
            raise ValueError("GitHub release assets must use api.github.com.")
    _validate_url(approval.license_evidence_url, _SOURCE_HOSTS)
    _project_path(source.local_path, project_root)
    evidence = _project_path(source.provenance_document, project_root)
    if not evidence.is_file():
        raise ValueError("The model provenance document is missing.")
    return source


def _matches(path: Path, source: ModelSource) -> bool:
    if path.stat().st_size != source.weights_size_bytes:
        return False
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == source.weights_sha256


# PUBLIC_INTERFACE
def download_model(config_path: Path, project_root: Path = PROJECT_ROOT) -> Path:
    """Download approved bytes, verify size/SHA-256, and atomically install weights.

    Accepts a YAML config path and project root. Returns the verified local path.
    Existing corrupt files are not overwritten unless the new download verifies.
    No checkpoint is deserialized. Network, integrity, and approval failures raise.
    """
    source = load_source(config_path, project_root)
    destination = _project_path(source.local_path, project_root)
    if destination.is_file() and _matches(destination, source):
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    url = source.weights_url
    temporary: Path | None = None
    try:
        # GitHub asset redirects are mutable; the expected content hash is binding.
        for _ in range(6):
            _validate_url(url, _REDIRECT_HOSTS)
            with requests.get(
                url,
                headers={"Accept": "application/octet-stream"},
                stream=True,
                allow_redirects=False,
                timeout=(10, 60),
            ) as response:
                if response.status_code in (301, 302, 303, 307, 308):
                    url = response.headers.get("Location", "")
                    continue
                response.raise_for_status()
                digest = hashlib.sha256()
                size = 0
                with tempfile.NamedTemporaryFile(
                    dir=destination.parent, prefix=".weights-", suffix=".part", delete=False
                ) as stream:
                    temporary = Path(stream.name)
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        size += len(chunk)
                        if size > source.weights_size_bytes:
                            raise ValueError("Weights exceed the approved size.")
                        digest.update(chunk)
                        stream.write(chunk)
                    stream.flush()
                    os.fsync(stream.fileno())
                if (
                    size != source.weights_size_bytes
                    or digest.hexdigest() != source.weights_sha256
                ):
                    raise ValueError("Weights size or SHA-256 does not match provenance.")
                os.replace(temporary, destination)
                return destination
        raise ValueError("Model download exceeded the redirect limit.")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


# PUBLIC_INTERFACE
def main() -> int:
    """Parse CLI options, install verified weights, and return a process exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=PROJECT_ROOT / "config/model.yaml"
    )
    arguments = parser.parse_args()
    try:
        destination = download_model(arguments.config)
    except (OSError, ValueError, requests.RequestException, yaml.YAMLError):
        # Never echo redirect URLs (which can carry signed tokens) or config secrets.
        parser.exit(1, "Model download refused or failed; review provenance/configuration.\n")
    print(f"Verified weights: {destination.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
