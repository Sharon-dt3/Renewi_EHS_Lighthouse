"""VAL-06 / S14: allow-list, Basic auth, roles, fail-closed configuration, spoofed forwarding headers, log redaction.

All credentials here are random per-run test values created by the tests; no real secret appears anywhere.
"""
import base64
import hmac
import logging
import secrets
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from backend import security as sec
from backend.app import create_app
from backend.security import SecurityConfigError, load_security
from backend.tests.test_api import CMAP, FakeDetector, image_bytes  # reuse the S13 model-free fixtures
from backend.service import ApiSettings, ClipSettings, InferenceService

REPO = Path(__file__).resolve().parents[2]
SUP_USER, SUP_PASS = "supervisor1", secrets.token_urlsafe(18)
RO_USER, RO_PASS = "viewer1", secrets.token_urlsafe(18)
ENV = {"PPE_ALLOWED_NETWORKS": "10.0.0.0/8, 127.0.0.1/32, ::1/128", "PPE_SUPERVISOR_USER": SUP_USER,
       "PPE_SUPERVISOR_PASSWORD": SUP_PASS, "PPE_READONLY_USER": RO_USER, "PPE_READONLY_PASSWORD": RO_PASS}


def basic(user, password):
    return {"Authorization": "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()}


@pytest.fixture
def service():
    return InferenceService(ApiSettings(checkpoint=Path("unused.pt"), clips={"demo": ClipSettings()}), FakeDetector(), CMAP)


def make_client(service, peer="127.0.0.1", headers=None, env=None, with_lifespan=True):
    application = create_app(service, load_security(env or ENV))
    client = TestClient(application, client=(peer, 50000), headers=headers or {})
    return client.__enter__() if with_lifespan else client


def upload(client, headers=None):
    return client.post("/infer", data={"clip_id": "demo"}, files={"image": ("x.png", image_bytes(), "image/png")}, headers=headers or {})


# ---------------- fail closed: configuration ----------------
@pytest.mark.parametrize("drop", ["PPE_ALLOWED_NETWORKS", "PPE_SUPERVISOR_USER", "PPE_SUPERVISOR_PASSWORD"])
def test_missing_required_settings_fail_closed(drop):
    env = {k: v for k, v in ENV.items() if k != drop}
    with pytest.raises(SecurityConfigError):
        load_security(env)


@pytest.mark.parametrize("override", [
    {"PPE_ALLOWED_NETWORKS": ""}, {"PPE_ALLOWED_NETWORKS": "   "}, {"PPE_ALLOWED_NETWORKS": "10.0.0.0/8,,127.0.0.1"},
    {"PPE_ALLOWED_NETWORKS": "not-an-ip"}, {"PPE_ALLOWED_NETWORKS": "0.0.0.0/0"}, {"PPE_ALLOWED_NETWORKS": "::/0"},
    {"PPE_SUPERVISOR_PASSWORD": "short"}, {"PPE_SUPERVISOR_PASSWORD": " " * 14}, {"PPE_SUPERVISOR_USER": "has:colon"},
    {"PPE_SUPERVISOR_USER": " padded "}, {"PPE_SUPERVISOR_USER": "x" * 65},
    {"PPE_READONLY_USER": SUP_USER}, {"PPE_READONLY_PASSWORD": SUP_PASS}, {"PPE_READONLY_PASSWORD": ""},
])
def test_malformed_or_weak_settings_fail_closed(override):
    with pytest.raises(SecurityConfigError):
        load_security({**ENV, **override})


def test_readonly_credential_is_optional_but_must_be_a_complete_pair():
    env = {k: v for k, v in ENV.items() if not k.startswith("PPE_READONLY")}
    assert len(load_security(env).credentials) == 1
    with pytest.raises(SecurityConfigError):
        load_security({**env, "PPE_READONLY_USER": "only-a-user"})


def test_service_refuses_to_start_without_security_config(service, monkeypatch):
    for key in ENV:
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(SecurityConfigError):
        with TestClient(create_app(service)):
            pass


def test_request_with_no_loaded_settings_is_refused_never_passed_through(service):
    application = create_app(service, load_security(ENV))
    client = TestClient(application, client=("127.0.0.1", 50000))          # no `with`: lifespan never runs, settings stay None
    assert client.get("/health", headers=basic(SUP_USER, SUP_PASS)).status_code == 503


# ---------------- IP allow-list on the socket peer ----------------
@pytest.mark.parametrize("peer, allowed", [
    ("127.0.0.1", True), ("10.200.1.9", True), ("::1", True), ("::ffff:10.1.2.3", True),
    ("192.168.1.5", False), ("203.0.113.9", False), ("2001:db8::1", False), ("::ffff:192.168.1.5", False),
    ("testclient", False), ("", False), (None, False), ("999.1.1.1", False),
])
def test_peer_allow_list(peer, allowed):
    assert sec.peer_allowed(peer, load_security(ENV).networks) is allowed


def test_disallowed_peer_is_403_even_with_valid_credentials_and_without(service):
    client = make_client(service, peer="203.0.113.9")
    ok, bad = client.get("/health", headers=basic(SUP_USER, SUP_PASS)), client.get("/health")
    assert ok.status_code == 403 and bad.status_code == 403            # denied before credentials are even considered
    assert "www-authenticate" not in {k.lower() for k in ok.headers} | {k.lower() for k in bad.headers}
    assert ok.json() == bad.json() == {"detail": "Forbidden"}


@pytest.mark.parametrize("spoof", [
    {"X-Forwarded-For": "127.0.0.1"}, {"X-Forwarded-For": "10.0.0.5, 127.0.0.1"}, {"Forwarded": "for=127.0.0.1"},
    {"X-Real-IP": "127.0.0.1"}, {"X-Forwarded-Host": "localhost"}, {"True-Client-IP": "127.0.0.1"},
])
def test_spoofed_forwarding_headers_cannot_grant_access(service, spoof):
    client = make_client(service, peer="203.0.113.9")
    assert client.get("/health", headers={**basic(SUP_USER, SUP_PASS), **spoof}).status_code == 403


def test_forwarding_headers_cannot_remove_access_from_an_allowed_peer_either(service):
    client = make_client(service, peer="127.0.0.1")
    assert client.get("/health", headers={**basic(SUP_USER, SUP_PASS), "X-Forwarded-For": "203.0.113.9"}).status_code == 200


# ---------------- Basic authentication ----------------
def test_no_credentials_gives_401_with_a_basic_challenge(service):
    r = make_client(service).get("/health")
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == 'Basic realm="Renewi PPE", charset="UTF-8"'
    assert r.json() == {"detail": "Authentication required"}


@pytest.mark.parametrize("headers", [
    basic(SUP_USER, "wrong-password-123"), basic("nobody", SUP_PASS), basic(SUP_USER, ""), basic("", ""), basic(SUP_USER, SUP_PASS + "x"),
    basic(SUP_USER, SUP_PASS.upper()), basic(RO_USER, SUP_PASS), basic(SUP_USER, RO_PASS),
    {"Authorization": "Bearer " + SUP_PASS}, {"Authorization": "Basic"}, {"Authorization": "Basic !!!not-base64!!!"},
    {"Authorization": "Basic " + base64.b64encode(b"nocolon").decode()},
    {"Authorization": "Basic " + base64.b64encode(SUP_USER.encode() + b":\xff\xfe\xfa").decode()},
    {"Authorization": "Basic " + base64.b64encode(b"u:" + b"p" * 2000).decode()},
    {"Authorization": "Digest username=x"}, {"Authorization": ""},
])
def test_invalid_credentials_are_401_and_identical(service, headers):
    r = make_client(service).get("/health", headers=headers)
    assert r.status_code == 401 and r.json() == {"detail": "Authentication required"}      # same body: no hint which part failed
    assert "www-authenticate" in {k.lower() for k in r.headers}


def test_valid_credentials_scheme_case_and_unicode_password(service):
    c = make_client(service)
    assert c.get("/health", headers={"Authorization": "basic " + basic(SUP_USER, SUP_PASS)["Authorization"][6:]}).status_code == 200
    env = {**ENV, "PPE_SUPERVISOR_PASSWORD": "pässwörd-ünïcode-123"}
    assert make_client(service, env=env).get("/health", headers=basic(SUP_USER, "pässwörd-ünïcode-123")).status_code == 200


@pytest.mark.parametrize("method, path", [
    ("GET", "/health"), ("GET", "/docs"), ("GET", "/redoc"), ("GET", "/openapi.json"), ("GET", "/does-not-exist"),
    ("POST", "/infer"), ("GET", "/infer"), ("DELETE", "/health"), ("OPTIONS", "/infer"),
])
def test_every_route_requires_credentials(service, method, path):
    r = make_client(service).request(method, path)
    assert r.status_code == 401                                   # unknown paths too: no route enumeration for strangers


def test_authentication_precedes_body_handling(service):
    big = b"\x89PNG\r\n\x1a\n" + secrets.token_bytes(6 * 1024 * 1024)
    r = make_client(service).post("/infer", data={"clip_id": "demo"}, files={"image": ("x.png", big, "image/png")})
    assert r.status_code == 401                                   # not 413: an unauthenticated caller never reaches body limits
    assert service._analyzers["demo"]._detector.calls == 0


def test_comparison_is_constant_time_style_every_credential_every_time(monkeypatch):
    settings, calls = load_security(ENV), []
    real = hmac.compare_digest
    monkeypatch.setattr(sec.hmac, "compare_digest", lambda a, b: calls.append(1) or real(a, b))
    for header in (basic(SUP_USER, SUP_PASS)["Authorization"], basic("nobody", "x" * 20)["Authorization"], None, "garbage"):
        calls.clear()
        sec.authenticate(settings, header)
        assert len(calls) == 2 * len(settings.credentials)        # never short-circuits on a match or a mismatch


# ---------------- roles ----------------
def test_supervisor_can_upload_and_read_only_cannot(service):
    sup = make_client(service)
    assert upload(sup, basic(SUP_USER, SUP_PASS)).status_code == 200
    ro_headers = basic(RO_USER, RO_PASS)
    ro = make_client(service)
    r = upload(ro, ro_headers)
    assert r.status_code == 403 and r.json() == {"detail": "Insufficient role for this operation"}
    assert service._analyzers["demo"]._detector.calls == 1        # the read-only attempt never reached the model
    assert ro.get("/health", headers=ro_headers).status_code == 200
    assert ro.get("/openapi.json", headers=ro_headers).status_code == 200


def test_roles_policy_function():
    assert sec.roles_allowed("POST", "/infer") == {"supervisor"}
    assert sec.roles_allowed("GET", "/health") == {"supervisor", "readonly"}


# ---------------- log redaction ----------------
def test_credentials_never_appear_in_logs(service, caplog):
    caplog.set_level(logging.DEBUG)
    client = make_client(service)
    token = basic(SUP_USER, SUP_PASS)["Authorization"][6:]
    client.get("/health", headers=basic(SUP_USER, "a-wrong-password-9"))                 # failed login
    client.get("/health", headers=basic(SUP_USER, SUP_PASS))                              # good login
    client.get("/health", headers={"Authorization": "Basic " + token[:-2] + "!!"})        # mangled token
    logging.getLogger("uvicorn.error").warning("debug dump headers: Authorization: Basic %s and password=%s", token, SUP_PASS)
    text = caplog.text
    assert "event=auth_failed" in text and "peer=127.0.0.1" in text
    for secret in (SUP_PASS, RO_PASS, token, "a-wrong-password-9"):
        assert secret not in text
    assert "[REDACTED]" in text


def test_redact_function_covers_tokens_and_registered_secrets():
    sec.install_redaction(["very-secret-value"])
    assert "very-secret-value" not in sec.redact("x very-secret-value y")
    assert "dXNlcjpwYXNz" not in sec.redact("Authorization: Basic dXNlcjpwYXNz")
    assert "Bearer [REDACTED]" in sec.redact("Authorization: Bearer abcdef.ghi-jkl")
    assert sec.redact("nothing sensitive here") == "nothing sensitive here"


# ---------------- OpenAPI declares the scheme ----------------
def test_contract_declares_basic_auth_and_401_403_everywhere():
    schema = create_app().openapi()
    assert schema["components"]["securitySchemes"]["basicAuth"] == {
        "type": "http", "scheme": "basic", "description": schema["components"]["securitySchemes"]["basicAuth"]["description"]}
    for operations in schema["paths"].values():
        for operation in operations.values():
            assert operation["security"] == [{"basicAuth": []}] and {"401", "403"} <= set(operation["responses"])
            assert "WWW-Authenticate" in operation["responses"]["401"]["headers"]


# ---------------- real server: uvicorn and proxy headers ----------------
def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_server(extra_args, allowed):
    port = free_port()
    env = {"PATH": "/usr/bin:/bin", "PPE_ALLOWED_NETWORKS": allowed, "PPE_SUPERVISOR_USER": SUP_USER, "PPE_SUPERVISOR_PASSWORD": SUP_PASS}
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.app:app", "--host", "127.0.0.1", "--port", str(port), *extra_args],
                            cwd=REPO, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for _ in range(80):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            return proc, port
        except OSError:
            if proc.poll() is not None:
                break
            time.sleep(0.1)
    proc.kill()
    pytest.skip("could not start a real uvicorn server in this environment")


def test_real_server_with_no_proxy_headers_ignores_a_spoofed_x_forwarded_for():
    proc, port = start_server(["--no-proxy-headers"], allowed="10.0.0.0/8")           # the real peer 127.0.0.1 is NOT allowed
    try:
        r = httpx.get(f"http://127.0.0.1:{port}/health", headers={**basic(SUP_USER, SUP_PASS), "X-Forwarded-For": "10.1.2.3"})
        assert r.status_code == 403
    finally:
        proc.terminate(); proc.wait(timeout=10)


def test_why_the_launcher_must_pass_no_proxy_headers():
    """Documents the hazard: uvicorn's default trusts X-Forwarded-For from 127.0.0.1 and rewrites the peer."""
    proc, port = start_server([], allowed="10.0.0.0/8")
    try:
        r = httpx.get(f"http://127.0.0.1:{port}/health", headers={**basic(SUP_USER, SUP_PASS), "X-Forwarded-For": "10.1.2.3"})
        assert r.status_code != 403                     # the spoof got through the IP check: uvicorn rewrote the peer
    finally:
        proc.terminate(); proc.wait(timeout=10)
    assert "--no-proxy-headers" in (REPO / "scripts" / "run_api.sh").read_text()


def test_real_server_without_security_environment_refuses_to_start():
    port = free_port()
    proc = subprocess.run([sys.executable, "-m", "uvicorn", "backend.app:app", "--host", "127.0.0.1", "--port", str(port)],
                          cwd=REPO, env={"PATH": "/usr/bin:/bin"}, capture_output=True, text=True, timeout=60)
    assert proc.returncode != 0 and "PPE_ALLOWED_NETWORKS" in (proc.stdout + proc.stderr)
