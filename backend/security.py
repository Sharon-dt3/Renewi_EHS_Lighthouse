"""S14 application-level security (ADR-005 / DEC-07).

Order of checks for every HTTP request, including /health, /docs and /openapi.json:
  1. Socket-peer IP/CIDR allow-list        -> 403 (before any credential is read, so denied peers learn nothing)
  2. Failed-login throttle for that peer    -> 429 with Retry-After (even valid credentials are refused while locked)
  3. HTTP Basic authentication              -> 401 with a Basic challenge
  4. Role check (supervisor or read-only)   -> 403
Every authenticated request is written to the audit log (user, role, peer, method, path, status; never a password or an image).

The peer is the TCP socket address from the ASGI scope. Forwarding headers (X-Forwarded-For, Forwarded, X-Real-IP) are never
consulted. Start uvicorn with --no-proxy-headers (scripts/run_api.sh does), because uvicorn otherwise rewrites the peer from
X-Forwarded-For when the connection comes from 127.0.0.1.

Accounts: named users from a hashed users file (PPE_USERS_FILE, scrypt hashes, see scripts/make_user.py) and/or the two
bootstrap credentials in the environment. Accounts are verified only against scrypt hashes. The bootstrap passwords' plaintext
survives in memory only in the log-redaction list (so it can be scrubbed from log text) and in the process environment. Configuration comes only from
the process environment and fails closed: missing, malformed or weak settings stop startup, and a request that arrives while no
security settings are loaded gets 503, never a pass-through.
"""
import base64
import binascii
import collections
import hashlib
import hmac
import ipaddress
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Mapping, Optional, Sequence, Tuple

import yaml
from starlette.responses import JSONResponse

LOGGER = logging.getLogger("ppe.security")
AUDIT = logging.getLogger("ppe.audit")

ENV_ALLOWED = "PPE_ALLOWED_NETWORKS"
ENV_SUPERVISOR_USER, ENV_SUPERVISOR_PASSWORD = "PPE_SUPERVISOR_USER", "PPE_SUPERVISOR_PASSWORD"
ENV_READONLY_USER, ENV_READONLY_PASSWORD = "PPE_READONLY_USER", "PPE_READONLY_PASSWORD"
ENV_USERS_FILE = "PPE_USERS_FILE"
ENV_MAX_FAILURES, ENV_FAILURE_WINDOW = "PPE_AUTH_MAX_FAILURES", "PPE_AUTH_FAILURE_WINDOW_SECONDS"
ENV_TLS_ENABLED, ENV_AUDIT_LOG = "PPE_TLS_ENABLED", "PPE_AUDIT_LOG"
SUPERVISOR, READONLY = "supervisor", "readonly"
ROLES = (SUPERVISOR, READONLY)
MIN_PASSWORD_LENGTH = 12
MAX_USERNAME_LENGTH = 64
MAX_AUTH_HEADER_BYTES = 1024
REALM = "Renewi PPE"
DEFAULT_MAX_FAILURES, DEFAULT_FAILURE_WINDOW = 10, 300
SCRYPT_COST = (2 ** 14, 8, 1)             # n, r, p for newly created hashes; each stored hash carries its own cost
AUTH_CACHE_TTL, AUTH_CACHE_MAX = 30.0, 256


# PUBLIC_INTERFACE
class SecurityConfigError(Exception):
    """Security settings are missing, malformed or too weak. The service must not start."""


# ---------------- password hashing ----------------
# PUBLIC_INTERFACE
def hash_password(password: str, *, salt: Optional[bytes] = None, cost: Optional[Tuple[int, int, int]] = None) -> str:
    """Return 'scrypt$n$r$p$salt_b64$hash_b64' for a password. A fresh random salt is used unless given."""
    n, r, p = cost or SCRYPT_COST
    salt = salt if salt is not None else os.urandom(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=32, maxmem=128 * 1024 * 1024)
    return "scrypt${}${}${}${}${}".format(n, r, p, base64.b64encode(salt).decode(), base64.b64encode(digest).decode())


@dataclass(frozen=True)
class Credential:
    username: str
    role: str
    salt: bytes = field(repr=False)
    digest: bytes = field(repr=False)
    n: int
    r: int
    p: int


def _parse_hash(username: str, role: str, text: str) -> Credential:
    try:
        scheme, n, r, p, salt, digest = text.split("$")
        if scheme != "scrypt":
            raise ValueError
        n, r, p = int(n), int(r), int(p)
        salt, digest = base64.b64decode(salt, validate=True), base64.b64decode(digest, validate=True)
        if not (2 ** 4 <= n <= 2 ** 20 and n & (n - 1) == 0 and 1 <= r <= 32 and 1 <= p <= 16 and len(salt) >= 8 and len(digest) == 32):
            raise ValueError
    except (ValueError, binascii.Error) as error:
        raise SecurityConfigError(f"The password hash for user '{username}' is not a valid scrypt hash") from error
    return Credential(username, role, salt, digest, n, r, p)


def _verify(password: bytes, credential: Credential) -> bool:
    derived = hashlib.scrypt(password, salt=credential.salt, n=credential.n, r=credential.r, p=credential.p,
                             dklen=32, maxmem=128 * 1024 * 1024)
    return hmac.compare_digest(derived, credential.digest)              # exactly one constant-time comparison per attempt


# PUBLIC_INTERFACE
@dataclass(frozen=True)
class SecuritySettings:
    """Validated allow-list, accounts and limits. Passwords exist only as scrypt hashes."""

    networks: Tuple[object, ...]
    users: Mapping[str, Credential]
    dummy: Credential                      # verified against for unknown usernames, so they cost the same as real ones
    max_failures: int = DEFAULT_MAX_FAILURES
    failure_window: int = DEFAULT_FAILURE_WINDOW
    hsts: bool = False
    env_secrets: Tuple[str, ...] = field(default=(), repr=False)    # for log redaction only; never shown in repr

    @property
    def credentials(self) -> Tuple[Credential, ...]:
        return tuple(self.users.values())

    def secrets(self) -> list:
        """Strings that must never reach a log: bootstrap passwords and their Basic tokens."""
        return list(self.env_secrets)


def _valid_username(name: str) -> bool:
    return bool(name) and name == name.strip() and ":" not in name and len(name) <= MAX_USERNAME_LENGTH and all(32 <= ord(ch) != 127 for ch in name)


def _env_credential(role: str, user_env: str, password_env: str, environ: Mapping[str, str]):
    user, password = environ.get(user_env), environ.get(password_env)
    if user is None and password is None:
        return None
    if not user or not password:
        raise SecurityConfigError(f"{user_env} and {password_env} must both be set")
    if not _valid_username(user):
        raise SecurityConfigError(f"{user_env} must be 1-{MAX_USERNAME_LENGTH} printable characters, no colon, no surrounding spaces")
    if len(password) < MIN_PASSWORD_LENGTH or not password.strip():
        raise SecurityConfigError(f"{password_env} must be at least {MIN_PASSWORD_LENGTH} characters")
    return user, password, _parse_hash(user, role, hash_password(password))


def _int_env(environ, name, default, low, high):
    raw = environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError as error:
        raise SecurityConfigError(f"{name} must be an integer") from error
    if not low <= value <= high:
        raise SecurityConfigError(f"{name} must be between {low} and {high}")
    return value


def _load_users_file(path: str) -> list:
    try:
        with open(path, encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as error:
        raise SecurityConfigError(f"{ENV_USERS_FILE} cannot be read as YAML") from error
    entries = data.get("users") if isinstance(data, dict) else None
    if not isinstance(entries, list) or not entries:
        raise SecurityConfigError(f"{ENV_USERS_FILE} must contain a non-empty 'users' list")
    out = []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"username", "role", "hash"}:
            raise SecurityConfigError("Each user needs exactly username, role and hash")
        name, role, text = entry["username"], entry["role"], entry["hash"]
        if not isinstance(name, str) or not _valid_username(name):
            raise SecurityConfigError("A username in the users file is invalid")
        if role not in ROLES:
            raise SecurityConfigError(f"User '{name}' has an unknown role")
        if not isinstance(text, str):
            raise SecurityConfigError(f"The password hash for user '{name}' must be a string")
        out.append(_parse_hash(name, role, text))
    return out


# PUBLIC_INTERFACE
def load_security(environ: Optional[Mapping[str, str]] = None) -> SecuritySettings:
    """Read and validate security settings from the environment, or raise SecurityConfigError (fail closed)."""
    env = os.environ if environ is None else environ
    raw = (env.get(ENV_ALLOWED) or "").strip()
    if not raw:
        raise SecurityConfigError(f"{ENV_ALLOWED} is required (comma-separated IP/CIDR list)")
    networks = []
    for item in (part.strip() for part in raw.split(",")):
        if not item:
            raise SecurityConfigError(f"{ENV_ALLOWED} contains an empty entry")
        try:
            network = ipaddress.ip_network(item, strict=False)
        except ValueError as error:
            raise SecurityConfigError(f"{ENV_ALLOWED} entry is not a valid IP or CIDR") from error
        if network.prefixlen == 0:
            raise SecurityConfigError(f"{ENV_ALLOWED} must not allow every address (a /0 network)")
        networks.append(network)

    users: Dict[str, Credential] = {}
    secrets_list: list = []
    sup = _env_credential(SUPERVISOR, ENV_SUPERVISOR_USER, ENV_SUPERVISOR_PASSWORD, env)
    ro = _env_credential(READONLY, ENV_READONLY_USER, ENV_READONLY_PASSWORD, env)
    if sup and ro and (sup[0] == ro[0] or sup[1] == ro[1]):
        raise SecurityConfigError("The read-only and supervisor credentials must differ in both username and password")
    for item in (sup, ro):
        if item:
            users[item[0]] = item[2]
            secrets_list += [item[1], base64.b64encode(f"{item[0]}:{item[1]}".encode()).decode()]
    users_file = (env.get(ENV_USERS_FILE) or "").strip()
    if users_file:
        for credential in _load_users_file(users_file):
            if credential.username in users:
                raise SecurityConfigError("A username appears more than once across the environment and the users file")
            users[credential.username] = credential
    if not any(c.role == SUPERVISOR for c in users.values()):
        raise SecurityConfigError(f"At least one supervisor is required ({ENV_SUPERVISOR_USER}/{ENV_SUPERVISOR_PASSWORD} or a supervisor in {ENV_USERS_FILE})")
    dummy = _parse_hash("dummy", READONLY, hash_password(base64.b64encode(os.urandom(18)).decode()))
    return SecuritySettings(
        tuple(networks), users, dummy,
        _int_env(env, ENV_MAX_FAILURES, DEFAULT_MAX_FAILURES, 3, 1000),
        _int_env(env, ENV_FAILURE_WINDOW, DEFAULT_FAILURE_WINDOW, 30, 86400),
        (env.get(ENV_TLS_ENABLED) or "").strip() == "1", tuple(secrets_list))


# PUBLIC_INTERFACE
def peer_allowed(peer: Optional[str], networks: Sequence) -> bool:
    """True only for a parseable socket peer inside an allowed network. IPv4-mapped IPv6 is treated as IPv4."""
    if not peer:
        return False
    try:
        ip = ipaddress.ip_address(peer)
    except ValueError:
        return False
    mapped = getattr(ip, "ipv4_mapped", None)
    if mapped is not None:
        ip = mapped
    return any(ip.version == n.version and ip in n for n in networks)


# PUBLIC_INTERFACE
def parse_basic(header: Optional[str]) -> Optional[Tuple[bytes, bytes]]:
    """Strictly parse 'Authorization: Basic <base64(user:password)>'. Anything else is None."""
    if not header or len(header.encode("utf-8", "ignore")) > MAX_AUTH_HEADER_BYTES:
        return None
    scheme, _, token = header.partition(" ")
    token = token.strip()
    if scheme.lower() != "basic" or not token:
        return None
    try:
        raw = base64.b64decode(token, validate=True)
    except (binascii.Error, ValueError):
        return None
    user, separator, password = raw.partition(b":")
    return (user, password) if separator else None


# PUBLIC_INTERFACE
def authenticate(settings: SecuritySettings, header: Optional[str]) -> Optional[Credential]:
    """Look the user up, then run exactly one scrypt verification. Unknown users are verified against a dummy hash,
    so a wrong username, a wrong password and a malformed header all cost the same."""
    parsed = parse_basic(header)
    user_bytes, password = parsed if parsed else (b"", b"")
    try:
        username = user_bytes.decode("utf-8")
    except UnicodeDecodeError:
        username = ""
    credential = settings.users.get(username)
    ok = _verify(password, credential if credential is not None else settings.dummy)
    return credential if (ok and credential is not None and parsed is not None) else None


# PUBLIC_INTERFACE
def roles_allowed(method: str, path: str) -> frozenset:
    """Uploads are supervisor-only (owner decision). Every other authenticated route is open to both roles."""
    if method == "POST" and path == "/infer":
        return frozenset({SUPERVISOR})
    return frozenset(ROLES)


# ---------------- failed-login throttle ----------------
# PUBLIC_INTERFACE
class FailureThrottle:
    """Per-peer failed-login limiter: max_failures inside window seconds locks that peer until the oldest failure ages out."""

    def __init__(self, max_failures: int, window_seconds: int, clock: Callable[[], float] = time.monotonic, max_peers: int = 10000):
        self.max_failures, self.window, self._clock, self._max_peers = max_failures, window_seconds, clock, max_peers
        self._failures: "collections.OrderedDict[str, collections.deque]" = collections.OrderedDict()

    def _prune(self, peer: str) -> collections.deque:
        queue, now = self._failures.setdefault(peer, collections.deque()), self._clock()
        while queue and now - queue[0] >= self.window:
            queue.popleft()
        return queue

    def retry_after(self, peer: str) -> int:
        """Seconds until the peer may try again; 0 when not locked."""
        queue = self._prune(peer)
        if len(queue) < self.max_failures:
            return 0
        return max(1, int(self.window - (self._clock() - queue[0])) + 1)

    def record_failure(self, peer: str) -> None:
        self._prune(peer).append(self._clock())
        self._failures.move_to_end(peer)
        while len(self._failures) > self._max_peers:                  # bounded memory under address churn
            self._failures.popitem(last=False)

    def reset(self, peer: str) -> None:
        self._failures.pop(peer, None)


# ---------------- log redaction ----------------
_AUTH_PATTERN = re.compile(r"(?i)\b(basic|bearer)\s+[A-Za-z0-9+/=._~-]{6,}")
_SECRETS: set = set()
_factory_installed = False


def redact(text: str) -> str:
    """Remove Authorization tokens and any registered secret value from a log message."""
    for secret in sorted(_SECRETS, key=len, reverse=True):
        text = text.replace(secret, "[REDACTED]")
    return _AUTH_PATTERN.sub(lambda m: m.group(1) + " [REDACTED]", text)


# PUBLIC_INTERFACE
def install_redaction(secrets: Sequence[str]) -> None:
    """Redact credentials from every log record process-wide (idempotent; secrets accumulate)."""
    global _factory_installed
    _SECRETS.update(s for s in secrets if s)
    if _factory_installed:
        return
    previous = logging.getLogRecordFactory()

    def factory(*args, **kwargs):
        record = previous(*args, **kwargs)
        try:
            record.msg = redact(record.getMessage())
            record.args = None
        except Exception:                                   # never let logging break a request
            record.msg, record.args = "[log message withheld]", None
        return record

    logging.setLogRecordFactory(factory)
    _factory_installed = True


# PUBLIC_INTERFACE
def configure_audit_file(path: Optional[str]) -> None:
    """Append the audit log to a private file (mode 0600) when PPE_AUDIT_LOG is set. Idempotent per path."""
    if not path:
        return
    for handler in AUDIT.handlers:
        if getattr(handler, "_ppe_path", None) == path:
            return
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    os.close(fd)
    handler = logging.FileHandler(path, encoding="utf-8")
    handler._ppe_path = path
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    AUDIT.addHandler(handler)
    AUDIT.setLevel(logging.INFO)


# ---------------- ASGI middleware ----------------
def _json(status: int, detail: str, headers: Optional[list] = None) -> JSONResponse:
    return JSONResponse({"detail": detail}, status_code=status, headers=dict(headers or []))


# PUBLIC_INTERFACE
class SecurityMiddleware:
    """Outermost ASGI layer: allow-list, throttle, Basic auth, role, audit. Fails closed when settings are absent."""

    def __init__(self, app, settings: Callable[[], Optional[SecuritySettings]]):
        self.app, self._settings = app, settings
        self._throttle: Optional[FailureThrottle] = None
        self._cache: "collections.OrderedDict[bytes, Tuple[Credential, float]]" = collections.OrderedDict()

    def _cached(self, header: Optional[str]) -> Optional[Credential]:
        if not header:
            return None
        key = hashlib.sha256(header.encode("utf-8", "ignore")).digest()
        hit = self._cache.get(key)
        if hit and time.monotonic() < hit[1]:
            return hit[0]
        self._cache.pop(key, None)
        return None

    def _remember(self, header: str, credential: Credential) -> None:
        self._cache[hashlib.sha256(header.encode("utf-8", "ignore")).digest()] = (credential, time.monotonic() + AUTH_CACHE_TTL)
        while len(self._cache) > AUTH_CACHE_MAX:
            self._cache.popitem(last=False)

    async def __call__(self, scope, receive, send):
        kind = scope["type"]
        if kind == "lifespan":
            await self.app(scope, receive, send)
            return
        if kind != "http":                                   # no websockets in this service
            if kind == "websocket":
                await send({"type": "websocket.close", "code": 1008})
            return
        settings = self._settings()
        method, path = scope.get("method", ""), scope.get("path", "")
        hardening = [(b"cache-control", b"no-store"), (b"x-content-type-options", b"nosniff")]
        if settings is not None and settings.hsts:
            hardening.append((b"strict-transport-security", b"max-age=31536000"))
        state = {"status": None}

        async def guarded_send(message):
            if message["type"] == "http.response.start":
                state["status"] = message["status"]
                names = {k.lower() for k, _ in message.get("headers", [])}
                message = {**message, "headers": list(message.get("headers", [])) + [h for h in hardening if h[0] not in names]}
            await send(message)

        if settings is None:
            LOGGER.error("security event=not_configured method=%s path=%s", method, path)
            await _json(503, "Security is not configured")(scope, receive, guarded_send)
            return
        if self._throttle is None:
            self._throttle = FailureThrottle(settings.max_failures, settings.failure_window)
        client = scope.get("client")
        peer = client[0] if client else None
        if not peer_allowed(peer, settings.networks):
            LOGGER.warning("security event=peer_denied peer=%s method=%s path=%s", peer, method, path)
            await _json(403, "Forbidden")(scope, receive, guarded_send)
            return
        wait = self._throttle.retry_after(peer)
        if wait:
            LOGGER.warning("security event=rate_limited peer=%s method=%s path=%s retry_after=%s", peer, method, path, wait)
            await _json(429, "Too many failed attempts", [("Retry-After", str(wait))])(scope, receive, guarded_send)
            return
        header = next((v.decode("latin-1") for k, v in scope.get("headers", []) if k.lower() == b"authorization"), None)
        credential = self._cached(header) or authenticate(settings, header)
        if credential is None:
            self._throttle.record_failure(peer)
            LOGGER.warning("security event=auth_failed peer=%s method=%s path=%s", peer, method, path)
            await _json(401, "Authentication required",
                        [("WWW-Authenticate", f'Basic realm="{REALM}", charset="UTF-8"')])(scope, receive, guarded_send)
            return
        self._throttle.reset(peer)
        self._remember(header, credential)
        if credential.role not in roles_allowed(method, path):
            LOGGER.warning("security event=role_denied peer=%s role=%s method=%s path=%s", peer, credential.role, method, path)
            AUDIT.info("audit user=%s role=%s peer=%s method=%s path=%s status=403", credential.username, credential.role, peer, method, path)
            await _json(403, "Insufficient role for this operation")(scope, receive, guarded_send)
            return
        scope["ppe_role"], scope["ppe_user"] = credential.role, credential.username
        try:
            await self.app(scope, receive, guarded_send)
        finally:
            AUDIT.info("audit user=%s role=%s peer=%s method=%s path=%s status=%s", credential.username, credential.role, peer, method, path, state["status"])
