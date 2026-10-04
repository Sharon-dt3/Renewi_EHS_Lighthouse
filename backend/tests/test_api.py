"""S13 contract and safety tests; no checkpoint loading or accuracy claims."""
import base64
import io
import json
import secrets
from pathlib import Path
from types import MappingProxyType

import numpy as np
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from PIL import Image

from backend.app import BoundedBodyMiddleware, create_app
from backend.security import load_security
from backend.service import ApiSettings, ClipSettings, InferenceService, decode_image
from ppe.analysis import FrameAnalyzer, to_dict
from ppe.class_map import ClassMap

CMAP = ClassMap("a" * 64, "test", MappingProxyType({
    0: "person", 1: "helmet", 2: "no_helmet", 3: "safety_vest", 4: "no_safety_vest",
}))
RAW = [(0, 0.95, 1, 1, 15, 15), (1, 0.9, 4, 2, 8, 5),
       (4, 0.8, 3, 6, 12, 10)]

# S14: every route needs an allow-listed peer and credentials. Random per-run test values, never real secrets.
SUP_USER, SUP_PASS = "supervisor1", secrets.token_urlsafe(18)
RO_USER, RO_PASS = "viewer1", secrets.token_urlsafe(18)
TEST_SECURITY = load_security({
    "PPE_ALLOWED_NETWORKS": "127.0.0.1/32", "PPE_SUPERVISOR_USER": SUP_USER, "PPE_SUPERVISOR_PASSWORD": SUP_PASS,
    "PPE_READONLY_USER": RO_USER, "PPE_READONLY_PASSWORD": RO_PASS})
SUP_HEADERS = {"Authorization": "Basic " + base64.b64encode(f"{SUP_USER}:{SUP_PASS}".encode()).decode()}


def api_client(application):
    """TestClient that connects from an allow-listed peer with the supervisor credential."""
    return TestClient(application, client=("127.0.0.1", 50000), headers=SUP_HEADERS)


class FakeDetector:
    """A deterministic detector for API/CLI integration checks."""

    def __init__(self):
        self.calls = 0

    def detect(self, frame):
        self.calls += 1
        assert frame.dtype == np.uint8 and frame.shape[2] == 3
        return RAW


def image_bytes(size=(16, 16), format="PNG"):
    buffer = io.BytesIO()
    Image.new("RGB", size, color=(12, 34, 56)).save(buffer, format=format)
    return buffer.getvalue()


@pytest.fixture
def service():
    settings = ApiSettings(checkpoint=Path("unused.pt"), clips={"demo": ClipSettings()})
    return InferenceService(settings, FakeDetector(), CMAP)


@pytest.fixture
def client(service):
    with api_client(create_app(service, TEST_SECURITY)) as connection:
        yield connection


def upload(client, data=None, clip="demo", mime="image/png", extra=None):
    fields = {"clip_id": clip}
    fields.update(extra or {})
    return client.post("/infer", data=fields,
                       files={"image": ("../../ignored.png", image_bytes() if data is None else data, mime)})


def test_shared_cli_api_analysis_parity(client, service):
    response = upload(client)
    assert response.status_code == 200
    body = response.json()
    actual = body["analysis"]
    frame = decode_image(image_bytes(), service.settings)
    expected = to_dict(FrameAnalyzer(FakeDetector(), CMAP).analyze(actual["frame_id"], frame))
    assert actual == expected
    assert actual["people"][0]["state"] == "VEST_MISSING"
    assert body["checkpoint_sha256"] == CMAP.checkpoint_sha256
    assert body["clip_id"] == "demo"
    assert service._analyzers["demo"]._detector.calls == 1


def test_health_ready(client):
    assert client.get("/health").json() == {"status": "ready", "ready": True}


def test_missing_environment_fails_readiness_closed(monkeypatch):
    monkeypatch.delenv("PPE_API_CONFIG", raising=False)
    with api_client(create_app(None, TEST_SECURITY)) as client:
        assert client.get("/health").status_code == 503
        assert client.get("/health").json()["ready"] is False
        assert upload(client).status_code == 503
        assert client.get("/openapi.json").status_code == 200


def test_bad_config_fails_readiness_closed(monkeypatch, tmp_path):
    config = tmp_path / "bad.yaml"
    config.write_text("checkpoint: unused.pt\nclips: {}\n")
    monkeypatch.setenv("PPE_API_CONFIG", str(config))
    with api_client(create_app(None, TEST_SECURITY)) as client:
        assert client.get("/health").status_code == 503


@pytest.mark.parametrize("clip", ["unknown", "../../config", "https://example.org", ""])
def test_unknown_clip_rejected_before_detector(client, service, clip):
    assert upload(client, clip=clip).status_code == 422
    assert service._analyzers["demo"]._detector.calls == 0


def test_no_client_configuration(client, service):
    assert upload(client, extra={"checkpoint": "/tmp/evil.pt"}).status_code in {400, 422}
    assert service._analyzers["demo"]._detector.calls == 0


def test_duplicate_and_missing_fields(client):
    response = client.post("/infer", files=[
        ("clip_id", (None, "demo")), ("clip_id", (None, "demo")),
        ("image", ("a.png", image_bytes(), "image/png")),
    ])
    assert response.status_code in {400, 422}
    assert client.post("/infer", data={"clip_id": "demo"}).status_code == 415


@pytest.mark.parametrize("data, mime, status", [
    (b"", "image/png", 422),
    (b"not-an-image", "image/png", 422),
    (b"not-an-image", "application/octet-stream", 415),
    (image_bytes(format="GIF"), "image/png", 415),
    (image_bytes()[:40], "image/png", 422),
])
def test_invalid_images(client, service, data, mime, status):
    assert upload(client, data=data, mime=mime).status_code == status
    assert service._analyzers["demo"]._detector.calls == 0


def test_file_size_limit(service):
    service.settings.max_file_bytes = 32
    with api_client(create_app(service, TEST_SECURITY)) as client:
        assert upload(client).status_code == 413


@pytest.mark.parametrize("setting, value", [("max_dimension", 15), ("max_pixels", 255)])
def test_decoded_size_limits_before_detector(service, setting, value):
    setattr(service.settings, setting, value)
    with api_client(create_app(service, TEST_SECURITY)) as client:
        assert upload(client).status_code == 413
    assert service._analyzers["demo"]._detector.calls == 0


def test_jpeg_accepted(client):
    assert upload(client, image_bytes(format="JPEG"), mime="image/jpeg").status_code == 200


def test_bgr_source_coordinates_unchanged(service):
    frame = decode_image(image_bytes(), service.settings)
    assert frame.shape == (16, 16, 3)
    assert frame[0, 0].tolist() == [56, 34, 12]


def test_animated_image_rejected(service):
    buffer = io.BytesIO()
    first = Image.new("RGB", (16, 16), "red")
    first.save(buffer, format="PNG", save_all=True,
               append_images=[Image.new("RGB", (16, 16), "blue")])
    with pytest.raises(HTTPException) as error:
        decode_image(buffer.getvalue(), service.settings)
    assert error.value.status_code == 415


def test_busy_and_failure_sanitized(client, service, monkeypatch):
    service._lock.acquire()
    try:
        assert upload(client).status_code == 503
    finally:
        service._lock.release()

    def fail(*args):
        raise RuntimeError("/private/checkpoint/secret")
    monkeypatch.setattr(service._analyzers["demo"], "analyze", fail)
    response = upload(client)
    assert response.status_code == 500
    assert response.json() == {"detail": "Inference failed"}
    assert service._lock.acquire(blocking=False)
    service._lock.release()


def test_zone_and_combined_events_and_resolution(tmp_path):
    zones = tmp_path / "zones.yaml"
    zones.write_text("clips:\n  demo:\n    source_size: [16, 16]\n"
                     "    polygon: [[0, 12], [16, 12], [16, 16], [0, 16]]\n")
    settings = ApiSettings(checkpoint=Path("unused.pt"), clips={"demo": ClipSettings(zones=zones)})
    service = InferenceService(settings, FakeDetector(), CMAP)
    with api_client(create_app(service, TEST_SECURITY)) as client:
        result = upload(client)
        assert result.status_code == 200
        assert result.json()["analysis"]["events"][0]["rules"] == ["PPE_VEST_MISSING", "ZONE_INCURSION"]
        assert upload(client, image_bytes(size=(17, 16))).status_code == 422
        assert service._analyzers["demo"]._detector.calls == 1


def test_malformed_multipart_is_client_error(client):
    response = client.post("/infer", content=b"invalid", headers={"content-type": "multipart/form-data"})
    assert response.status_code == 400


def test_declared_request_limit_and_invalid_length(client):
    assert client.post("/infer", content=b"x", headers={"content-length": "99999999"}).status_code == 413
    assert client.post("/infer", content=b"x", headers={"content-length": "bad"}).status_code == 400


@pytest.mark.anyio
async def test_chunked_body_limit_without_content_length():
    reached, sent = [], []
    messages = iter([
        {"type": "http.request", "body": b"123", "more_body": True},
        {"type": "http.request", "body": b"456", "more_body": False},
    ])

    async def downstream(scope, receive, send):
        reached.append(True)

    async def receive():
        return next(messages)

    async def send(message):
        sent.append(message)

    middleware = BoundedBodyMiddleware(downstream, lambda: 5)
    await middleware({"type": "http", "path": "/infer", "headers": []}, receive, send)
    assert not reached
    assert sent[0]["status"] == 413


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_openapi_contract(client):
    schema = client.get("/openapi.json").json()
    operation = schema["paths"]["/infer"]["post"]
    assert operation["operationId"] == "inferImage"
    body = operation["requestBody"]["content"]["multipart/form-data"]["schema"]
    assert body["required"] == ["clip_id", "image"]
    assert body["additionalProperties"] is False
    assert body["properties"]["image"]["format"] == "binary"
    assert set(operation["responses"]) >= {"200", "400", "413", "415", "422", "500", "503"}
    assert schema["paths"]["/health"]["get"]["operationId"] == "getHealth"


def test_published_g1_has_no_drift():
    published = Path(__file__).resolve().parents[2] / "docs" / "openapi.json"
    assert json.loads(published.read_text()) == create_app().openapi()
