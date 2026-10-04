# S14 application security (ADR-005, DEC-07, NFR-03; gate G3)

Status: **implemented and tested 2026-10-04.** Gate G3 (Security/Privacy review) is still to be done by the security owner.
Code: `backend/security.py`, wired in `backend/app.py`. Tests: `backend/tests/test_security.py` (VAL-06) and the S13 tests, which now run with credentials.

## What every request goes through (all routes, including `/health`, `/docs`, `/redoc`, `/openapi.json` and unknown paths)
| Step | Check | Failure |
| --- | --- | --- |
| 1 | The **TCP socket peer** is inside the IP/CIDR allow-list | `403 {"detail":"Forbidden"}`, no `WWW-Authenticate`, credentials are not read |
| 2 | HTTP **Basic** credentials match a configured user | `401` with `WWW-Authenticate: Basic realm="Renewi PPE", charset="UTF-8"` and the same body for every failure |
| 3 | The credential's **role** may perform the operation | `403 {"detail":"Insufficient role for this operation"}` |
Security runs outermost, so an unauthenticated caller never reaches the body-size checks, the model or the routes.

## Roles (owner decision: the operator uploads feeds; read-only is a proposal)
| Operation | Supervisor | Read-only |
| --- | --- | --- |
| `POST /infer` (upload an image) | yes | **no (403)** |
| `GET /health`, `/docs`, `/openapi.json` | yes | yes |
The role matrix for other personas is in `docs/access-control.md`. Both roles are shared logins, not named users: the API cannot say who uploaded.

## Configuration (process environment only; fails closed)
| Variable | Meaning |
| --- | --- |
| `PPE_ALLOWED_NETWORKS` | Required. Comma-separated IPs or CIDRs. A `/0` network, an empty entry or a bad value stops startup |
| `PPE_SUPERVISOR_USER`, `PPE_SUPERVISOR_PASSWORD` | Required. Username 1 to 64 printable characters, no colon, no surrounding spaces. Password at least 12 characters |
| `PPE_READONLY_USER`, `PPE_READONLY_PASSWORD` | Optional pair. Must differ from the supervisor's in both fields |
Credentials are never read from a file in the repository and never appear in code, tests or documents. Request them from the project owner and supply them only in the process environment.
**Fail closed:** missing, malformed or weak settings stop the server at startup (uvicorn exits with a message naming the variable). A request that arrives while no settings are loaded gets `503`, never a pass-through.

## Design points
- **Peer address only.** `X-Forwarded-For`, `Forwarded`, `X-Real-IP` and similar headers are ignored, both to grant and to remove access. IPv4-mapped IPv6 (`::ffff:a.b.c.d`) is treated as IPv4. An unparseable or missing peer is denied.
- **uvicorn must run with `--no-proxy-headers`** (`scripts/run_api.sh` does). By default uvicorn trusts `X-Forwarded-For` from 127.0.0.1 and rewrites the peer, which would let a caller spoof the allow-list. `test_why_the_launcher_must_pass_no_proxy_headers` demonstrates the hazard on a real server; `test_real_server_with_no_proxy_headers_ignores_a_spoofed_x_forwarded_for` proves the fix.
- **Constant-time comparison.** Username and password are each hashed (SHA-256, so lengths match) and compared with `hmac.compare_digest`, against every configured credential on every request, with no short-circuit.
- **Strict parsing.** Only `Basic <valid base64 of user:password>`, header at most 1 KiB; the scheme is case-insensitive. Anything else is a 401.
- **Log redaction.** A process-wide log-record factory removes `Basic`/`Bearer` tokens and every configured password and its base64 token from every log message. Security events log `event`, peer, method, path and role only; never headers, usernames or passwords.
- **Contract.** `docs/openapi.json` declares the `basicAuth` scheme and the 401 and 403 responses on every operation (the G1 contract was republished).

## How to run
```sh
export PPE_API_CONFIG=<server yaml>  PPE_ALLOWED_NETWORKS=127.0.0.1/32
export PPE_SUPERVISOR_USER=<user> PPE_SUPERVISOR_PASSWORD=<password of 12+ characters>
scripts/run_api.sh
curl --user "<user>:<password>" http://127.0.0.1:8000/health
```
The Swagger page at `/docs` asks for the credential through the browser's login prompt, then offers the upload form.

## Validation (VAL-06)
`backend/tests/test_security.py` (77 cases) covers: valid and invalid credentials (wrong user, wrong password, empty, malformed, non-Basic, bad base64, non-UTF-8, oversized); disallowed peers with and without valid credentials; spoofed forwarding headers in both directions; missing or weak configuration (startup refused, and a real `uvicorn` process refusing to start); every route requiring credentials; authentication before body handling; supervisor-only upload; constant-time comparison calls; log redaction; and the published contract. A deliberate break of the role check, the allow-list, the password comparison and the log redaction each made a test fail.

## Limits and what remains
- **HTTPS is required beyond localhost.** Basic credentials are plaintext without TLS (risk R-09). TLS belongs at the reverse proxy (S21); this service does not terminate TLS.
- **No rate limiting or lockout.** A caller on an allow-listed network can guess passwords at full speed. Use long random passwords; add throttling if the allow-list is wide.
- **Shared credentials.** No named users, no per-user audit trail, no rotation mechanism beyond restarting with new values. Production needs SSO and per-user roles (outside the PoC).
- **Frontend and proxy.** The React app is protected at the deployment boundary (S21), not by this code.
- **G3** needs the Security/Privacy owner's review before any exposure beyond localhost.
