# S14 application security (ADR-005, DEC-07, NFR-03; gate G3)

Status: **implemented, tested and live-verified 2026-10-04.** The only open item is the human gate **G3** (Security/Privacy review);
a ready-to-sign package is in [g3-security-review.md](g3-security-review.md).
Code: `backend/security.py`, wired in `backend/app.py`; tools `scripts/make_user.py`, `scripts/run_api.sh`.
Tests: `backend/tests/test_security.py` (VAL-06, 120+ cases) and the S13 tests, which now run with credentials.

## What every request goes through (all routes, including `/health`, `/docs`, `/redoc`, `/openapi.json` and unknown paths)
| Step | Check | Failure |
| --- | --- | --- |
| 1 | The **TCP socket peer** is inside the IP/CIDR allow-list | `403 {"detail":"Forbidden"}`, no `WWW-Authenticate`, credentials never read, not counted by the throttle |
| 2 | The peer is not **locked out** (too many failed logins) | `429` with `Retry-After`, even for the correct password |
| 3 | HTTP **Basic** credentials match a named user | `401` with `WWW-Authenticate: Basic realm="Renewi PPE", charset="UTF-8"`; same body for every failure |
| 4 | The user's **role** may perform the operation | `403 {"detail":"Insufficient role for this operation"}` |
| 5 | Every authenticated request is **audited** | `audit user=... role=... peer=... method=... path=... status=...` |
Security runs outermost: an unauthenticated caller never reaches body-size checks, the model or the routes. Every response, including errors, carries
`Cache-Control: no-store` and `X-Content-Type-Options: nosniff`, plus `Strict-Transport-Security` when TLS is enabled.

## Accounts and roles
- **Named users** live in a YAML file named by `PPE_USERS_FILE`, one entry each: `username`, `role` (`supervisor` or `readonly`) and a salted **scrypt hash**
  (`scrypt$n$r$p$salt$hash`, created with `scripts/make_user.py`, which reads the password from a hidden prompt and never from a command-line argument).
  The audit trail therefore names a person, not a shared login.
- **Bootstrap credentials** in the environment (`PPE_SUPERVISOR_USER/PASSWORD`, optional `PPE_READONLY_USER/PASSWORD`) still work and are hashed at startup.
  At least one supervisor is required from one source or both; usernames must be unique across sources.
- Verification: look the user up, then run **exactly one** scrypt comparison (`hmac.compare_digest`). An unknown username, a wrong password and a malformed header
  all cost the same, because unknown users are verified against a dummy hash.
- A successful login is **cached for 30 s** (keyed by a hash of the Authorization header; failures are never cached), so a stream of frames does not pay the scrypt cost each time.
- Roles: `POST /infer` (upload) is supervisor-only (owner decision); every other authenticated route is open to both roles. Matrix: `docs/access-control.md`.

## Configuration (process environment; fails closed)
| Variable | Meaning |
| --- | --- |
| `PPE_ALLOWED_NETWORKS` | Required. Comma-separated IPs or CIDRs. A `/0` network, an empty entry or a bad value stops startup |
| `PPE_USERS_FILE` | Path to the hashed users file. Unreadable, malformed, duplicate or role-less entries stop startup |
| `PPE_SUPERVISOR_USER`, `PPE_SUPERVISOR_PASSWORD` | Bootstrap supervisor. Username 1 to 64 printable characters, no colon; password at least 12 characters |
| `PPE_READONLY_USER`, `PPE_READONLY_PASSWORD` | Optional bootstrap pair; must differ from the supervisor's in both fields |
| `PPE_AUTH_MAX_FAILURES` / `PPE_AUTH_FAILURE_WINDOW_SECONDS` | Lockout: failures per peer inside a window (defaults 10 and 300 s; limits 3 to 1000 and 30 to 86400) |
| `PPE_AUDIT_LOG` | Optional path; the audit log is appended there with file mode 0600 |
| `PPE_TLS_CERT`, `PPE_TLS_KEY` | PEM files; `scripts/run_api.sh` then serves HTTPS and enables HSTS |
Credentials are never read from a file in the repository and never appear in code, tests or documents. Request them from the project owner and supply them only in the process environment (or, for named users, as hashes in the users file).
**Fail closed:** missing, malformed or weak settings stop the server at startup. A request that arrives while no settings are loaded gets `503`, never a pass-through.

## Design points
- **Peer address only.** `X-Forwarded-For`, `Forwarded`, `X-Real-IP` and similar headers are ignored, both to grant and to remove access. IPv4-mapped IPv6 is treated as IPv4. An unparseable or missing peer is denied.
- **uvicorn must run with `--no-proxy-headers`** (`scripts/run_api.sh` does). By default uvicorn trusts `X-Forwarded-For` from 127.0.0.1 and rewrites the peer, which would let a caller spoof the allow-list. A test demonstrates the hazard on a real server and another proves the fix.
- **HTTPS.** `scripts/run_api.sh` serves TLS when `PPE_TLS_CERT` and `PPE_TLS_KEY` are set, and **refuses to start** on any non-loopback address without TLS (Basic credentials are plaintext otherwise), or with a half-set or unreadable pair. The other supported layout is a TLS-terminating reverse proxy in front of a loopback bind (step S21). Tested over a real HTTPS server with a self-signed test certificate.
- **Strict parsing.** Only `Basic <valid base64 of user:password>`, header at most 1 KiB; scheme case-insensitive. Anything else is a 401.
- **Throttle.** Failed logins are counted per peer in a sliding window; at the limit the peer gets 429 until the oldest failure ages out. A success resets the count. Memory is bounded (10,000 peers). Denied peers are never counted.
- **Log redaction.** A process-wide log-record factory removes `Basic`/`Bearer` tokens and the bootstrap passwords and their base64 tokens from every log message. Security events log event, peer, method, path and role; a failed login never logs the attempted username. Only authenticated requests appear in the audit log with a username.
- **Contract.** `docs/openapi.json` declares the `basicAuth` scheme and the 401, 403 and 429 responses on every operation.

## How to run
```sh
export PPE_API_CONFIG=<server yaml>  PPE_ALLOWED_NETWORKS=127.0.0.1/32
export PPE_USERS_FILE=<users.yaml>                       # or PPE_SUPERVISOR_USER / PPE_SUPERVISOR_PASSWORD
export PPE_TLS_CERT=<cert.pem> PPE_TLS_KEY=<key.pem>     # needed for any non-loopback bind
scripts/run_api.sh
curl --cacert <cert.pem> --user "<user>:<password>" https://127.0.0.1:8000/health

# add a named user (password typed at a hidden prompt; only the hash is printed):
.venv/bin/python scripts/make_user.py --username alice --role supervisor >> users.yaml     # keep one 'users:' header line at the top
```
The Swagger page at `/docs` asks for the credential through the browser's login prompt, then offers the upload form.

## Validation (VAL-06)
Covered, each with passing and failing cases: valid and invalid credentials (wrong user or password, empty, malformed, non-Basic, bad base64, non-UTF-8, oversized); disallowed peers with and without valid credentials; spoofed forwarding headers in both directions; missing or weak configuration, including a real `uvicorn` process refusing to start; every route requiring credentials; authentication before body handling; supervisor-only upload; one scrypt comparison per attempt; named users and every bad users-file case; hash format; the user-creation tool; lockout, reset, per-peer isolation and bounded memory; the success cache and its expiry; response hardening headers; the audit trail and its 0600 file; the launcher's refusals; real HTTPS with HSTS; log redaction; the published contract.
**Mutation checks:** deliberately breaking the role check, the allow-list, the password comparison, log redaction, the throttle, failure recording, the unknown-user dummy verification, cache expiry, the audit user field, the hardening headers and the launcher's TLS guard each made a test fail.
**Live checks** (real model, real HTTPS, named users, production scrypt cost): 401 and 403 where expected, supervisor upload returned a real analysis, read-only upload refused, the lockout returned 429 with `Retry-After`, the audit file was mode 0600 and listed who did what, and no password, token or hash reached the audit file or the server log.

## Limits (also in the G3 package)
- **TLS certificates:** the code serves HTTPS and refuses insecure binds; obtaining and rotating a production certificate (or the reverse proxy) is deployment, step S21.
- **Single process.** The throttle and cache are in memory and per process: run one worker, and a restart clears them. Behind shared NAT, one bad actor can lock out others on the same address (a deliberate trade-off).
- **No live revocation.** Users and hashes load at startup; removing or changing a user needs a restart, and a cached login can live up to 30 s.
- **No MFA, no SSO, no self-service password change.** Named users are managed by editing the users file.
- **The audit log** is a local file: no tamper evidence, no rotation. It records staff usernames and peer addresses, which makes it staff-activity data (GDPR Article 88, works-council awareness: see the G3 package).
- **scrypt cost** 2^14 is a PoC baseline; raise it for production.
- **G3** needs the Security/Privacy owner's review before any exposure beyond localhost.
