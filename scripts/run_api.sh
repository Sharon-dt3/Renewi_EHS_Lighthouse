#!/bin/sh
# Start the PPE API (S13 + S14). Run from the application root:  scripts/run_api.sh
#
# Required in the process environment (never in a file in Git; request values from the project owner):
#   PPE_API_CONFIG          path to the server YAML (see config/api.example.yaml)
#   PPE_ALLOWED_NETWORKS    comma-separated IP/CIDR allow-list, e.g. 127.0.0.1/32 (a /0 network is refused)
#   At least one supervisor account, from either source (or both):
#     PPE_SUPERVISOR_USER / PPE_SUPERVISOR_PASSWORD   bootstrap pair (password of 12+ characters)
#     PPE_USERS_FILE        YAML of named users with scrypt hashes (see scripts/make_user.py)
#   Optional: PPE_READONLY_USER / PPE_READONLY_PASSWORD, PPE_AUTH_MAX_FAILURES, PPE_AUTH_FAILURE_WINDOW_SECONDS, PPE_AUDIT_LOG
# Missing or weak security settings make the server refuse to start (fail closed).
#
# HTTPS: set PPE_TLS_CERT and PPE_TLS_KEY (PEM files) to serve TLS directly. Binding to any address other than loopback
# WITHOUT TLS is refused, because Basic credentials are plaintext on the wire. (A TLS-terminating reverse proxy in front of a
# loopback bind is the other supported layout; that is deployment, step S21.)
#
# --no-proxy-headers is REQUIRED: without it uvicorn trusts X-Forwarded-For from 127.0.0.1 and rewrites the peer address,
# which would let a caller spoof the allow-list.
set -e
cd "$(dirname "$0")/.."
HOST="${PPE_BIND_HOST:-127.0.0.1}"
PORT="${PPE_PORT:-8000}"
TLS_ARGS=""
if [ -n "${PPE_TLS_CERT:-}" ] || [ -n "${PPE_TLS_KEY:-}" ]; then
  if [ -z "${PPE_TLS_CERT:-}" ] || [ -z "${PPE_TLS_KEY:-}" ]; then
    echo "refusing to start: set both PPE_TLS_CERT and PPE_TLS_KEY, or neither" >&2; exit 2
  fi
  for f in "$PPE_TLS_CERT" "$PPE_TLS_KEY"; do
    [ -r "$f" ] || { echo "refusing to start: cannot read TLS file $f" >&2; exit 2; }
  done
  TLS_ARGS="--ssl-certfile $PPE_TLS_CERT --ssl-keyfile $PPE_TLS_KEY"
  export PPE_TLS_ENABLED=1
else
  case "$HOST" in
    127.*|localhost|::1) ;;
    *) echo "refusing to start: binding to $HOST without TLS would send Basic credentials in plaintext (set PPE_TLS_CERT and PPE_TLS_KEY, or bind to loopback behind a TLS proxy)" >&2; exit 2 ;;
  esac
fi
# shellcheck disable=SC2086
exec .venv/bin/python -m uvicorn backend.app:app --host "$HOST" --port "$PORT" --no-proxy-headers --no-server-header $TLS_ARGS
