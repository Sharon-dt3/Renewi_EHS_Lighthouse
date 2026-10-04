#!/bin/sh
# Start the PPE API locally (S13 + S14). Run from the application root:  scripts/run_api.sh
#
# Requires, in the process environment (never in a file in Git; request values from the project owner):
#   PPE_API_CONFIG                path to the server YAML (see config/api.example.yaml)
#   PPE_ALLOWED_NETWORKS          comma-separated IP/CIDR allow-list, e.g. 127.0.0.1/32
#   PPE_SUPERVISOR_USER / PPE_SUPERVISOR_PASSWORD     (password at least 12 characters)
#   PPE_READONLY_USER / PPE_READONLY_PASSWORD         (optional pair; must differ from the supervisor's)
# Missing or weak security settings make the server refuse to start (fail closed).
#
# --no-proxy-headers is REQUIRED: without it uvicorn trusts X-Forwarded-For from 127.0.0.1 and rewrites the peer address,
# which would let a caller spoof the allow-list. Bind to 127.0.0.1 unless a TLS-terminating reverse proxy is in front.
set -e
cd "$(dirname "$0")/.."
exec .venv/bin/python -m uvicorn backend.app:app --host "${PPE_BIND_HOST:-127.0.0.1}" --port "${PPE_PORT:-8000}" --no-proxy-headers --no-server-header
