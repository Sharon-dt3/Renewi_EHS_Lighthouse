"""S14 application-level security (ADR-005 / DEC-07).

Order of checks for every HTTP request, including /health, /docs and /openapi.json:
  1. Socket-peer IP/CIDR allow-list      -> 403 (before any credential is read, so denied peers learn nothing)
  2. HTTP Basic authentication            -> 401 with a Basic challenge
  3. Role check (supervisor or read-only) -> 403
The peer is the TCP socket address from the ASGI scope. Forwarding headers (X-Forwarded-For, Forwarded, X-Real-IP) are
never consulted. Start uvicorn with --no-proxy-headers (scripts/run_api.sh does), because uvicorn otherwise rewrites the
peer from X-Forwarded-For when the connection comes from 127.0.0.1.

Configuration comes only from the process environment and fails closed: missing, malformed or weak settings stop startup,
and a request that arrives while no security settings are loaded gets 503, never a pass-through.
"""
import base64
import binascii
import hashlib
import hmac
import ipaddress
import logging
import os
import re
from dataclasses import dataclass
from typing import Callable, Mapping, Optional, Sequence, Tuple

from starlette.responses import JSONResponse

LOGGER = logging.getLogger("ppe.security")

ENV_ALLOWED = "PPE_ALLOWED_NETWORKS"
ENV_SUPERVISOR_USER, ENV_SUPERVISOR_PASSWORD = "PPE_SUPERVISOR_USER", "PPE_SUPERVISOR_PASSWORD"
ENV_READONLY_USER, ENV_READONLY_PASSWORD = "PPE_READONLY_USER", "PPE_READONLY_PASSWORD"
SUPERVISOR, READONLY = "supervisor", "readonly"
MIN_PASSWORD_LENGTH = 12
MAX_USERNAME_LENGTH = 64
MAX_AUTH_HEADER_BYTES = 1024
REALM = "Renewi PPE"


# PUBLIC_INTERFACE
class SecurityConfigError(Exception):
    """Security settings are missing, malformed or too weak. The service must not start."""


@dataclass(frozen=True)
class Credential:
    role: str
    username: bytes
    password: bytes


# PUBLIC_INTERFACE
@dataclass(frozen=True)
class SecuritySettings:
    """Validated allow-list and credentials. Passwords are held only as bytes in memory."""

    networks: Tuple[object, ...]
    credentials: Tuple[Credential, ...]

    def secrets(self) -> list:
        """Every string that must never reach a log: passwords, usernames and their Basic tokens."""
        out = []
        for c in self.credentials:
            token = base64.b64encode(c.username + b":" + c.password).decode("ascii")
            out += [c.password.decode("utf-8"), token]
        return out


def _clean(value: Optional[str]) -> str:
    return (value or "").strip()


def _credential(role: str, user_env: str, password_env: str, environ: Mapping[str, str]) -> Optional[Credential]:
    user, password = environ.get(user_env), environ.get(password_env)
    if user is None and password is None:
        return None
    if not user or not password:
        raise SecurityConfigError(f"{user_env} and {password_env} must both be set")
    if not user.strip() or user != user.strip() or ":" in user or any(ord(ch) < 32 for ch in user) or len(user) > MAX_USERNAME_LENGTH:
        raise SecurityConfigError(f"{user_env} must be 1-{MAX_USERNAME_LENGTH} printable characters, no colon, no surrounding spaces")
    if len(password) < MIN_PASSWORD_LENGTH or not password.strip():
        raise SecurityConfigError(f"{password_env} must be at least {MIN_PASSWORD_LENGTH} characters")
    return Credential(role, user.encode("utf-8"), password.encode("utf-8"))


# PUBLIC_INTERFACE
def load_security(environ: Optional[Mapping[str, str]] = None) -> SecuritySettings:
    """Read and validate security settings from the environment, or raise SecurityConfigError (fail closed)."""
    env = os.environ if environ is None else environ
    raw = _clean(env.get(ENV_ALLOWED))
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
    supervisor = _credential(SUPERVISOR, ENV_SUPERVISOR_USER, ENV_SUPERVISOR_PASSWORD, env)
    readonly = _credential(READONLY, ENV_READONLY_USER, ENV_READONLY_PASSWORD, env)
    if supervisor is None:
        raise SecurityConfigError(f"{ENV_SUPERVISOR_USER} and {ENV_SUPERVISOR_PASSWORD} are required")
    creds = [supervisor] + ([readonly] if readonly else [])
    if readonly and (readonly.username == supervisor.username or readonly.password == supervisor.password):
        raise SecurityConfigError("The read-only and supervisor credentials must differ in both username and password")
    return SecuritySettings(tuple(networks), tuple(creds))


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


def _digest(value: bytes) -> bytes:
    return hashlib.sha256(value).digest()


# PUBLIC_INTERFACE
def authenticate(settings: SecuritySettings, header: Optional[str]) -> Optional[Credential]:
    """Constant-time credential check. Every configured credential is compared every time, on both fields."""
    parsed = parse_basic(header)
    user, password = parsed if parsed else (b"", b"")
    user_d, password_d = _digest(user), _digest(password)
    matched = None
    for credential in settings.credentials:
        same_user = hmac.compare_digest(user_d, _digest(credential.username))
        same_password = hmac.compare_digest(password_d, _digest(credential.password))
        if same_user & same_password and parsed is not None:     # bitwise &: no short-circuit
            matched = credential
    return matched


# PUBLIC_INTERFACE
def roles_allowed(method: str, path: str) -> frozenset:
    """Uploads are supervisor-only (owner decision). Every other authenticated route is open to both roles."""
    if method == "POST" and path == "/infer":
        return frozenset({SUPERVISOR})
    return frozenset({SUPERVISOR, READONLY})


# ---------- log redaction ----------
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


# ---------- ASGI middleware ----------
def _json(status: int, detail: str, headers: Optional[list] = None) -> JSONResponse:
    return JSONResponse({"detail": detail}, status_code=status, headers=dict(headers or []))


# PUBLIC_INTERFACE
class SecurityMiddleware:
    """Outermost ASGI layer: allow-list, then Basic auth, then role. Fails closed when settings are absent."""

    def __init__(self, app, settings: Callable[[], Optional[SecuritySettings]]):
        self.app, self._settings = app, settings

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
        if settings is None:
            LOGGER.error("security event=not_configured method=%s path=%s", method, path)
            await _json(503, "Security is not configured")(scope, receive, send)
            return
        client = scope.get("client")
        peer = client[0] if client else None
        if not peer_allowed(peer, settings.networks):
            LOGGER.warning("security event=peer_denied peer=%s method=%s path=%s", peer, method, path)
            await _json(403, "Forbidden")(scope, receive, send)
            return
        header = next((v.decode("latin-1") for k, v in scope.get("headers", []) if k.lower() == b"authorization"), None)
        credential = authenticate(settings, header)
        if credential is None:
            LOGGER.warning("security event=auth_failed peer=%s method=%s path=%s", peer, method, path)
            await _json(401, "Authentication required",
                        [("WWW-Authenticate", f'Basic realm="{REALM}", charset="UTF-8"')])(scope, receive, send)
            return
        if credential.role not in roles_allowed(method, path):
            LOGGER.warning("security event=role_denied peer=%s role=%s method=%s path=%s", peer, credential.role, method, path)
            await _json(403, "Insufficient role for this operation")(scope, receive, send)
            return
        scope["ppe_role"] = credential.role
        await self.app(scope, receive, send)
