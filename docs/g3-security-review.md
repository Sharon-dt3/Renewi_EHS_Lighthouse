# G3 security review package for S14 (READY FOR REVIEW, NOT SIGNED)

Prepared 2026-10-04 by the assistant. G3 is the architecture gate "Security/Privacy: basic auth + IP allow-list and data constraints,
before public demo exposure". **Only a named reviewer can sign it.** This package is meant to make that a single sitting.

## 1. Scope
The `/infer` and `/health` service (S13) with the S14 controls. Not in scope: the React frontend and the TLS proxy (S21), the Postgres ledger (S16/S17).

## 2. Requirements traced to controls
| Requirement | Control | Evidence |
| --- | --- | --- |
| NFR-03 / C-05: Basic auth + IP allow-list enforced | Allow-list on the socket peer, then Basic auth, on every route | `test_security.py`; live checks in `docs/s14-security.md` |
| ADR-005 / DEC-07: forwarding headers ignored | Peer from the TCP socket only; launcher passes `--no-proxy-headers` | Real-server tests prove both the hazard and the fix |
| DEC-07: constant-time comparison | scrypt hash, one `hmac.compare_digest` per attempt, dummy hash for unknown users | `test_exactly_one_scrypt_comparison_per_attempt_whatever_the_outcome` |
| DEC-07: 401 with challenge, 403 for peers | `WWW-Authenticate: Basic ...`; 403 before credentials are read | `test_no_credentials_gives_401_...`, `test_disallowed_peer_is_403_...` |
| DEC-07: fail closed on missing config | Startup refuses; 503 if settings absent at request time | `test_service_refuses_to_start_...`, real-uvicorn startup test |
| DEC-07: log redaction | Process-wide record factory; audit has no secrets | `test_credentials_never_appear_in_logs`, live log scan |
| Access control: supervisor-only upload (owner decision) | Role check on `POST /infer` | `test_supervisor_can_upload_and_read_only_cannot` |
| Risk R-09: plaintext Basic credentials | TLS served by the launcher; non-loopback bind without TLS refused; HSTS | launcher tests, real HTTPS test |
| Brute force (found as a gap) | Per-peer lockout with `Retry-After` | throttle tests, live check |
| Shared credentials (found as a gap) | Named users with scrypt hashes; audit trail by user | users-file tests, audit tests |
| OWASP A01 Broken access control | Allow-list, role matrix, unknown paths need auth | route-protection tests |
| OWASP A02 Cryptographic failures | scrypt hashes, TLS option, no plaintext passwords in settings repr | hashing tests |
| OWASP A05 Misconfiguration | Fail-closed settings; `--no-server-header`; no-store and nosniff headers | config and header tests |
| OWASP A07 Identification and authentication failures | Strict parsing, lockout, strong password minimum, no username hints | auth and throttle tests |
| OWASP A09 Logging and monitoring failures | Audit trail and security event log; secrets never logged | audit tests |

## 2b. Abuse cases tested
Wrong or empty credentials; credentials of another role; header tricks (bad base64, no colon, non-UTF-8, 2 KB header, Digest and Bearer schemes); spoofed `X-Forwarded-For`, `Forwarded`, `X-Real-IP` from a blocked peer; an oversize body from an unauthenticated caller (must be 401, not 413); route enumeration of unknown paths; read-only user uploading; a locked-out peer using the right password; a half-configured or `/0` allow-list; weak passwords; duplicate and malformed users-file entries; plain HTTP to the TLS port.

## 3. Residual risks (decisions for the reviewer)
| # | Risk | Mitigation in place | Reviewer decision needed |
| --- | --- | --- | --- |
| 1 | No production TLS certificate or proxy yet | Launcher refuses non-loopback without TLS | Accept until S21, **and confirm no exposure before then** |
| 2 | Throttle and cache are in memory, per process | Run a single worker | Accept for the PoC? |
| 3 | A shared NAT address can be locked out by one user | Lockout is per peer and short (default 5 min) | Accept, or shorten the window |
| 4 | No live revocation: removing a user needs a restart, a cached login lives up to 30 s | Short cache | Accept? |
| 5 | No MFA or SSO | Out of PoC scope | Accept for the demo |
| 6 | Audit log is a plain local file, no tamper evidence or rotation | File mode 0600 | Is a plain file enough for the demo? |
| 7 | The audit log records staff usernames and IPs: staff-activity data | Pseudonymous account names; no media stored | **Privacy/works-council view needed** (GDPR Article 88 framing) |
| 8 | scrypt cost 2^14 is a baseline | Cost is stored per hash and can be raised | Required cost for production? |
| 9 | Zone and clip registry keys are not secrets but reveal configuration names to authenticated users | Auth required for `/openapi.json` | Accept |

## 4. Review checklist (tick each; attach notes)
- [ ] Read `docs/s14-security.md` and `backend/security.py`.
- [ ] Run `.venv/bin/python -m pytest -q backend/tests/test_security.py` (expect all pass).
- [ ] Start with `scripts/run_api.sh` on loopback and try: no credentials, wrong credentials, read-only upload, three bad logins then a good one.
- [ ] Confirm the launcher refuses `PPE_BIND_HOST=0.0.0.0` without TLS.
- [ ] Confirm no credential appears in logs, code, tests, docs or Git history.
- [ ] Decide each residual risk above.
- [ ] Confirm the deployment precondition: nothing is exposed beyond localhost until HTTPS is configured (S21).

## 5. Sign-off (to be completed by the Security/Privacy owner)
| Field | Entry |
| --- | --- |
| Reviewer name and role | |
| Date | |
| Decision (Approved / Approved with conditions / Rejected) | |
| Conditions | |
| Residual risks accepted (numbers) | |
