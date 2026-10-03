"""Regression checks for download safety; synthetic bytes are not model evidence."""

from copy import deepcopy
import hashlib
from pathlib import Path

import pytest
import requests
import yaml

from scripts.download_model import PROJECT_ROOT, download_model, load_source


@pytest.fixture
def approved_config(tmp_path):
    """Create reviewed synthetic metadata for isolated downloader tests."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/model-selection.md").write_text("Synthetic review", encoding="utf-8")
    model = {
        "name": "test/synthetic",
        "repository": "https://github.com/test/synthetic",
        "revision": "a" * 40,
        "architecture": "test-only",
        "weights_url": "https://api.github.com/repos/test/synthetic/releases/assets/1",
        "weights_sha256": hashlib.sha256(b"test-weights").hexdigest(),
        "weights_size_bytes": len(b"test-weights"),
        "local_path": "models/test.pt",
        "provenance_document": "docs/model-selection.md",
        "approval": {
            "approved": True,
            "reviewer": "synthetic-test-reviewer",
            "license_identifier": "synthetic-test-only",
            "license_evidence_url": "https://github.com/test/synthetic/blob/" + "a" * 40 + "/LICENSE",
            "actual_classes_verified": True,
            "required_classes_supported": True,
        },
    }
    return tmp_path, model


def _config(root, model):
    path = root / "model.yaml"
    path.write_text(yaml.safe_dump({"model": model}), encoding="utf-8")
    return path


class _Response:
    status_code = 200
    headers = {}

    def __init__(self, content=b"test-weights"):
        self.content = content

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size):
        yield self.content


def test_real_configuration_refuses_approval_before_io(monkeypatch, tmp_path):
    def forbidden(*args, **kwargs):
        pytest.fail("Unapproved model must not reach the network")

    monkeypatch.setattr(requests, "get", forbidden)
    with pytest.raises(ValueError, match="approval"):
        download_model(PROJECT_ROOT / "config/model.yaml", tmp_path)
    assert not (tmp_path / "models").exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("approved", False),
        ("approved", "true"),
        ("reviewer", ""),
        ("license_identifier", None),
        ("license_evidence_url", None),
        ("actual_classes_verified", False),
        ("required_classes_supported", False),
    ],
)
def test_incomplete_approval(approved_config, field, value):
    root, model = approved_config
    model["approval"][field] = value
    with pytest.raises(ValueError):
        load_source(_config(root, model), root)


@pytest.mark.parametrize(
    "field,value",
    [
        ("revision", "main"),
        ("weights_sha256", "invalid"),
        ("weights_size_bytes", 0),
        ("local_path", "../escaped.pt"),
        ("weights_url", "http://api.github.com/repos/test/synthetic/releases/assets/1"),
        ("weights_url", "https://evil.example/best.pt"),
        ("weights_url", "https://github.com/test/synthetic/releases/download/latest/best.pt"),
        ("weights_url", "https://huggingface.co/test/synthetic/resolve/main/best.pt"),
    ],
)
def test_invalid_sources(approved_config, field, value):
    root, model = approved_config
    model[field] = value
    with pytest.raises(ValueError):
        load_source(_config(root, model), root)


def test_verified_download_and_cache(approved_config, monkeypatch):
    root, model = approved_config
    config = _config(root, model)
    calls = []

    def get(*args, **kwargs):
        calls.append(args[0])
        assert kwargs["allow_redirects"] is False
        return _Response()

    monkeypatch.setattr(requests, "get", get)
    destination = download_model(config, root)
    assert destination.read_bytes() == b"test-weights"
    assert download_model(config, root) == destination
    assert len(calls) == 1
    assert not list(destination.parent.glob("*.part"))


@pytest.mark.parametrize("content", [b"wrong-weight", b"x", b"x" * 100])
def test_integrity_failure_preserves_existing(approved_config, monkeypatch, content):
    root, model = approved_config
    destination = root / model["local_path"]
    destination.parent.mkdir()
    destination.write_bytes(b"previous")
    monkeypatch.setattr(requests, "get", lambda *a, **k: _Response(content))
    with pytest.raises(ValueError):
        download_model(_config(root, model), root)
    assert destination.read_bytes() == b"previous"
    assert not list(destination.parent.glob("*.part"))


def test_network_failure_cleans_partial(approved_config, monkeypatch):
    root, model = approved_config

    class Interrupted(_Response):
        def iter_content(self, chunk_size):
            yield b"test"
            raise requests.ConnectionError("synthetic disconnect")

    monkeypatch.setattr(requests, "get", lambda *a, **k: Interrupted())
    with pytest.raises(requests.ConnectionError):
        download_model(_config(root, model), root)
    assert not (root / model["local_path"]).exists()
    assert not list((root / "models").glob("*.part"))


@pytest.mark.parametrize("url", ["http://github.com/best.pt", "https://evil.example/best.pt"])
def test_unsafe_redirect(approved_config, monkeypatch, url):
    root, model = approved_config
    response = _Response()
    response.status_code = 302
    response.headers = {"Location": url}
    monkeypatch.setattr(requests, "get", lambda *a, **k: response)
    with pytest.raises(ValueError, match="HTTPS"):
        download_model(_config(root, model), root)


def test_redirect_limit(approved_config, monkeypatch):
    root, model = approved_config
    response = _Response()
    response.status_code = 302
    response.headers = {"Location": model["weights_url"]}
    monkeypatch.setattr(requests, "get", lambda *a, **k: response)
    with pytest.raises(ValueError, match="redirect limit"):
        download_model(_config(root, model), root)


def test_unknown_configuration_fields(approved_config):
    root, model = approved_config
    modified = deepcopy(model)
    modified["implicit_model"] = "not-allowed"
    with pytest.raises(ValueError):
        load_source(_config(root, modified), root)
