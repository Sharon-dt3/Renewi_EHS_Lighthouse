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


def test_exactly_one_scrypt_comparison_per_attempt_whatever_the_outcome(monkeypatch):
    settings, calls = load_security(ENV), []
    real = hmac.compare_digest
    monkeypatch.setattr(sec.hmac, "compare_digest", lambda a, b: calls.append(1) or real(a, b))
    for header in (basic(SUP_USER, SUP_PASS)["Authorization"], basic(SUP_USER, "wrong-password-123")["Authorization"],
                   basic("nobody", "x" * 20)["Authorization"], None, "garbage", "Basic !!!"):
        calls.clear()
        sec.authenticate(settings, header)
        assert len(calls) == 1                 # unknown users and malformed headers are verified against a dummy hash: same cost


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


# =============== S14 close-out: named users, hashing, throttle, cache, headers, audit, TLS ===============
import json
import os
import shutil
import stat

import yaml

from backend.security import FailureThrottle
from scripts import make_user

USER_PASS = secrets.token_urlsafe(18)


def users_file(tmp_path, entries):
    path = tmp_path / "users.yaml"
    path.write_text(yaml.safe_dump({"users": entries}))
    return str(path)


def entry(name, role, password):
    return {"username": name, "role": role, "hash": sec.hash_password(password)}


# ---- hashing ----
def test_hashes_verify_and_use_unique_salts():
    a, b = sec.hash_password(USER_PASS), sec.hash_password(USER_PASS)
    assert a != b and a.startswith("scrypt$16$8$1$")                  # test cost; production default is 2**14
    cred = sec._parse_hash("u", "supervisor", a)
    assert sec._verify(USER_PASS.encode(), cred) and not sec._verify(b"wrong-password-xx", cred)
    assert USER_PASS not in a


def test_production_default_cost_is_not_weakened(monkeypatch):
    monkeypatch.undo()
    assert sec.SCRYPT_COST == (2 ** 14, 8, 1)


@pytest.mark.parametrize("bad", ["", "scrypt", "md5$16$8$1$AAAAAAAAAAA=$AAAA", "scrypt$15$8$1$" + "QUJDREVGR0g=" + "$" + "A" * 43 + "=",
                                 "scrypt$16$8$1$notbase64!$" + "A" * 43 + "=", "scrypt$16$8$1$QUJDREVGR0g=$AAAA"])
def test_malformed_hashes_are_refused(bad):
    with pytest.raises(SecurityConfigError):
        sec._parse_hash("u", "supervisor", bad)


# ---- named users file ----
def test_named_users_authenticate_and_merge_with_bootstrap_credentials(tmp_path, service):
    path = users_file(tmp_path, [entry("alice", "supervisor", USER_PASS), entry("bob", "readonly", USER_PASS + "x")])
    env = {**ENV, "PPE_USERS_FILE": path}
    settings = load_security(env)
    assert {c.username for c in settings.credentials} == {SUP_USER, RO_USER, "alice", "bob"}
    c = make_client(service, env=env)
    assert c.get("/health", headers=basic("alice", USER_PASS)).status_code == 200
    assert upload(c, basic("alice", USER_PASS)).status_code == 200
    assert upload(c, basic("bob", USER_PASS + "x")).status_code == 403          # role from the file
    assert c.get("/health", headers=basic("alice", "wrong-password-1")).status_code == 401


def test_users_file_alone_is_enough_when_it_has_a_supervisor(tmp_path):
    env = {"PPE_ALLOWED_NETWORKS": "127.0.0.1/32", "PPE_USERS_FILE": users_file(tmp_path, [entry("alice", "supervisor", USER_PASS)])}
    assert [c.username for c in load_security(env).credentials] == ["alice"]


@pytest.mark.parametrize("entries", [
    [entry("bob", "readonly", USER_PASS)],                                                   # no supervisor anywhere
    [entry("alice", "supervisor", USER_PASS), entry("alice", "readonly", USER_PASS)],        # duplicate name
    [{"username": "a:b", "role": "supervisor", "hash": sec.hash_password(USER_PASS)}],       # colon in name
    [{"username": "alice", "role": "admin", "hash": sec.hash_password(USER_PASS)}],          # unknown role
    [{"username": "alice", "role": "supervisor", "hash": "plaintext-password"}],             # not a hash
    [{"username": "alice", "role": "supervisor", "hash": sec.hash_password(USER_PASS), "extra": 1}],
    [],
])
def test_bad_users_files_fail_closed(tmp_path, entries):
    env = {"PPE_ALLOWED_NETWORKS": "127.0.0.1/32", "PPE_USERS_FILE": users_file(tmp_path, entries)}
    with pytest.raises(SecurityConfigError):
        load_security(env)


def test_username_clash_between_environment_and_file_is_refused(tmp_path):
    env = {**ENV, "PPE_USERS_FILE": users_file(tmp_path, [entry(SUP_USER, "supervisor", USER_PASS)])}
    with pytest.raises(SecurityConfigError):
        load_security(env)


def test_missing_or_unreadable_users_file_fails_closed(tmp_path):
    with pytest.raises(SecurityConfigError):
        load_security({**ENV, "PPE_USERS_FILE": str(tmp_path / "missing.yaml")})
    bad = tmp_path / "bad.yaml"; bad.write_text("users: [")
    with pytest.raises(SecurityConfigError):
        load_security({**ENV, "PPE_USERS_FILE": str(bad)})


def test_no_plaintext_password_is_kept_in_the_loaded_settings():
    blob = repr(load_security(ENV))
    assert SUP_PASS not in blob and RO_PASS not in blob


def test_make_user_tool_produces_a_verifying_entry_and_enforces_rules(capsys, monkeypatch):
    line = make_user.build_entry("carol", "supervisor", USER_PASS)
    parsed = yaml.safe_load("users:\n" + line)["users"][0]
    assert parsed["username"] == "carol" and parsed["role"] == "supervisor" and USER_PASS not in line
    assert sec._verify(USER_PASS.encode(), sec._parse_hash("carol", "supervisor", parsed["hash"]))
    for args in (("c:x", "supervisor", USER_PASS), ("carol", "admin", USER_PASS), ("carol", "supervisor", "short")):
        with pytest.raises(SystemExit):
            make_user.build_entry(*args)
    monkeypatch.setenv("PPE_NEW_PASSWORD", USER_PASS)
    assert make_user.main(["--username", "dave", "--role", "readonly"]) == 0
    assert USER_PASS not in capsys.readouterr().out
    assert "--password" not in (REPO / "scripts" / "make_user.py").read_text().split('"""')[2]    # never a command-line argument


# ---- throttle ----
def test_throttle_locks_after_max_failures_and_unlocks_when_they_age_out():
    now = [1000.0]
    t = FailureThrottle(3, 60, clock=lambda: now[0])
    assert t.retry_after("a") == 0
    for _ in range(3):
        t.record_failure("a")
    assert t.retry_after("a") >= 1 and t.retry_after("b") == 0              # per peer
    now[0] += 59
    assert t.retry_after("a") >= 1
    now[0] += 2
    assert t.retry_after("a") == 0


def test_throttle_reset_and_bounded_memory():
    t = FailureThrottle(3, 60, max_peers=5)
    for i in range(50):
        t.record_failure(f"10.0.0.{i}")
    assert len(t._failures) == 5
    for _ in range(3):
        t.record_failure("x")
    t.reset("x")
    assert t.retry_after("x") == 0


def test_repeated_bad_logins_lock_out_even_the_right_password(service):
    env = {**ENV, "PPE_AUTH_MAX_FAILURES": "3"}
    c = make_client(service, env=env)
    for _ in range(3):
        assert c.get("/health", headers=basic(SUP_USER, "wrong-password-123")).status_code == 401
    locked = c.get("/health", headers=basic(SUP_USER, SUP_PASS))
    assert locked.status_code == 429 and int(locked.headers["retry-after"]) >= 1 and locked.json() == {"detail": "Too many failed attempts"}
    assert upload(c, basic(SUP_USER, SUP_PASS)).status_code == 429
    other_peer = make_client(service, peer="10.9.9.9", env=env)                # another allowed peer is unaffected
    assert other_peer.get("/health", headers=basic(SUP_USER, SUP_PASS)).status_code == 200


def test_successful_login_resets_the_failure_count(service):
    c = make_client(service, env={**ENV, "PPE_AUTH_MAX_FAILURES": "3"})
    for _ in range(2):
        c.get("/health", headers=basic(SUP_USER, "wrong-password-123"))
    assert c.get("/health", headers=basic(SUP_USER, SUP_PASS)).status_code == 200
    for _ in range(2):
        assert c.get("/health", headers=basic(SUP_USER, "wrong-password-123")).status_code == 401      # counter started again


def test_denied_peers_are_not_counted_or_throttled_and_stay_403(service):
    c = make_client(service, peer="203.0.113.9", env={**ENV, "PPE_AUTH_MAX_FAILURES": "3"})
    assert [c.get("/health").status_code for _ in range(6)] == [403] * 6


@pytest.mark.parametrize("name, value", [("PPE_AUTH_MAX_FAILURES", "2"), ("PPE_AUTH_MAX_FAILURES", "x"), ("PPE_AUTH_MAX_FAILURES", "5000"),
                                         ("PPE_AUTH_FAILURE_WINDOW_SECONDS", "5"), ("PPE_AUTH_FAILURE_WINDOW_SECONDS", "999999")])
def test_throttle_settings_are_validated(name, value):
    with pytest.raises(SecurityConfigError):
        load_security({**ENV, name: value})


# ---- success cache ----
def test_successful_logins_are_cached_briefly_and_failures_never_are(service, monkeypatch):
    c = make_client(service)
    calls = []
    real = hashlib_scrypt = sec.hashlib.scrypt
    monkeypatch.setattr(sec.hashlib, "scrypt", lambda *a, **k: calls.append(1) or real(*a, **k))
    for _ in range(5):
        assert c.get("/health", headers=basic(SUP_USER, SUP_PASS)).status_code == 200
    assert len(calls) == 1                                                  # one verification, four cache hits
    calls.clear()
    for _ in range(3):
        c.get("/health", headers=basic(SUP_USER, "wrong-password-123"))
    assert len(calls) == 3                                                  # failures are verified every time


def test_cache_entries_expire(service, monkeypatch):
    c = make_client(service)
    now = [100.0]
    monkeypatch.setattr(sec.time, "monotonic", lambda: now[0])
    calls = []
    real = sec.hashlib.scrypt
    monkeypatch.setattr(sec.hashlib, "scrypt", lambda *a, **k: calls.append(1) or real(*a, **k))
    c.get("/health", headers=basic(SUP_USER, SUP_PASS)); c.get("/health", headers=basic(SUP_USER, SUP_PASS))
    assert len(calls) == 1
    now[0] += sec.AUTH_CACHE_TTL + 1
    c.get("/health", headers=basic(SUP_USER, SUP_PASS))
    assert len(calls) == 2


# ---- response hardening ----
@pytest.mark.parametrize("headers, status", [(basic(SUP_USER, SUP_PASS), 200), ({}, 401), (basic(SUP_USER, "wrong-password-123"), 401)])
def test_every_response_is_no_store_and_nosniff(service, headers, status):
    r = make_client(service).get("/health", headers=headers)
    assert r.status_code == status and r.headers["cache-control"] == "no-store" and r.headers["x-content-type-options"] == "nosniff"
    assert "strict-transport-security" not in r.headers


def test_denied_peer_responses_are_hardened_too(service):
    r = make_client(service, peer="203.0.113.9").get("/health")
    assert r.status_code == 403 and r.headers["cache-control"] == "no-store"


def test_hsts_only_when_tls_is_enabled(service):
    on = make_client(service, env={**ENV, "PPE_TLS_ENABLED": "1"}).get("/health", headers=basic(SUP_USER, SUP_PASS))
    assert on.headers["strict-transport-security"].startswith("max-age=")


# ---- audit trail ----
def test_audit_records_who_did_what_without_secrets(service, caplog):
    caplog.set_level(logging.INFO)
    c = make_client(service)
    upload(c, basic(SUP_USER, SUP_PASS)); upload(c, basic(RO_USER, RO_PASS)); c.get("/health", headers=basic(SUP_USER, "bad-password-12345"))
    lines = [r.getMessage() for r in caplog.records if r.name == "ppe.audit"]
    assert any(f"user={SUP_USER} role=supervisor peer=127.0.0.1 method=POST path=/infer status=200" in m for m in lines)
    assert any(f"user={RO_USER} role=readonly" in m and "status=403" in m for m in lines)
    assert not any("bad-password" in m for m in lines)
    failed = [r.getMessage() for r in caplog.records if "event=auth_failed" in r.getMessage()]
    assert failed and all(SUP_USER not in m for m in failed)                  # the attempted username is never logged
    for secret in (SUP_PASS, RO_PASS):
        assert secret not in caplog.text


def test_audit_file_is_private_and_appended(tmp_path, service):
    path = tmp_path / "audit.log"
    sec.configure_audit_file(str(path))
    try:
        make_client(service).get("/health", headers=basic(SUP_USER, SUP_PASS))
        for h in sec.AUDIT.handlers:
            h.flush()
        assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
        assert f"user={SUP_USER}" in path.read_text() and SUP_PASS not in path.read_text()
    finally:
        for h in list(sec.AUDIT.handlers):
            if getattr(h, "_ppe_path", None) == str(path):
                sec.AUDIT.removeHandler(h); h.close()


# ---- HTTPS and the launcher ----
def run_launcher(env, timeout=30):
    return subprocess.run(["sh", str(REPO / "scripts" / "run_api.sh")], cwd=REPO, env={"PATH": "/usr/bin:/bin", **env},
                          capture_output=True, text=True, timeout=timeout)


@pytest.mark.parametrize("env", [{"PPE_BIND_HOST": "0.0.0.0"}, {"PPE_BIND_HOST": "192.168.1.10"}, {"PPE_BIND_HOST": "::"}])
def test_launcher_refuses_a_non_loopback_bind_without_tls(env):
    r = run_launcher(env)
    assert r.returncode == 2 and "without TLS" in r.stderr


def test_launcher_refuses_half_or_unreadable_tls_configuration(tmp_path):
    assert run_launcher({"PPE_TLS_CERT": str(tmp_path / "c.pem")}).returncode == 2
    r = run_launcher({"PPE_TLS_CERT": str(tmp_path / "c.pem"), "PPE_TLS_KEY": str(tmp_path / "k.pem")})
    assert r.returncode == 2 and "cannot read TLS file" in r.stderr


@pytest.mark.skipif(shutil.which("openssl") is None, reason="openssl not available")
def test_real_https_server_with_hsts(tmp_path):
    cert, key = tmp_path / "c.pem", tmp_path / "k.pem"
    subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", str(key), "-out", str(cert), "-days", "1",
                    "-subj", "/CN=localhost", "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1"], check=True, capture_output=True)
    port = free_port()
    env = {"PATH": "/usr/bin:/bin", "PPE_ALLOWED_NETWORKS": "127.0.0.1/32", "PPE_SUPERVISOR_USER": SUP_USER, "PPE_SUPERVISOR_PASSWORD": SUP_PASS,
           "PPE_TLS_CERT": str(cert), "PPE_TLS_KEY": str(key), "PPE_PORT": str(port)}
    proc = subprocess.Popen(["sh", str(REPO / "scripts" / "run_api.sh")], cwd=REPO, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        for _ in range(100):
            try:
                socket.create_connection(("127.0.0.1", port), timeout=0.2).close(); break
            except OSError:
                time.sleep(0.1)
        r = httpx.get(f"https://127.0.0.1:{port}/health", auth=(SUP_USER, SUP_PASS), verify=str(cert))
        assert r.status_code in (200, 503) and r.headers["strict-transport-security"].startswith("max-age=")
        assert httpx.get(f"https://127.0.0.1:{port}/health", verify=str(cert)).status_code == 401
        with pytest.raises(httpx.HTTPError):                                       # plain HTTP to the TLS port does not work
            httpx.get(f"http://127.0.0.1:{port}/health", auth=(SUP_USER, SUP_PASS), timeout=3)
    finally:
        proc.terminate(); proc.wait(timeout=10)
