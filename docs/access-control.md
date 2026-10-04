# Access control: personas and permissions (DRAFT)

Status: draft, written 2026-10-04. The supervisor/read-only split for the API is implemented in S14 (`docs/s14-security.md`). Items marked **[owner-confirmed]** come from the project owner's statements in chat;
items marked **[proposal]** are the assistant's suggestions and need the owner's decision. The architecture document
(SAD v0.1) defines only a shared Basic-auth credential plus an IP allow-list at the deployment boundary (C-05, section 10.1); it defines no
personas, roles or uploader.

## Owner clarification (2026-10-04)
After the system is built, **the operator / supervisor uploads the feeds** for detection; engineering does not. **[owner-confirmed]**
This replaces the earlier proposal that only engineering may upload.

## Personas (from the SAD stakeholder list)
| Persona | Concern |
| --- | --- |
| Site supervisor / operator | Speed of acknowledging incidents; supplies the feeds |
| EHS leadership (sponsor) | Safety outcomes, credibility of detection |
| Works council / workforce representatives | No employee monitoring |
| Security / privacy | Authentication, data minimisation |
| Engineering (DT3/Kavia) | Deploy and run the system |

## Permission matrix  (✔ allowed, – not allowed, ◐ read-only)
| Capability | Supervisor / operator | EHS leadership | Works council | Security / privacy | Engineering |
| --- | --- | --- | --- | --- | --- |
| **Upload a feed (image or clip) for detection** **[owner-confirmed]** | ✔ | – | – | – | ✔ (testing) |
| Watch the processed feed with overlays | ✔ | ◐ | – | – | ✔ |
| View incident timeline and details | ✔ | ✔ | ◐ aggregates only | ✔ | ✔ |
| **Acknowledge an incident** | ✔ | – | – | – | – |
| Filter, search, export the event log | ✔ | ✔ | – | ✔ | – |
| View the mAP50 metrics card | ✔ | ✔ | ✔ | ✔ | ✔ |
| Change credentials / IP allow-list | – | – | – | – | ✔ (deployment config) |
| Change zone polygons or model | – | – | – | – | ✔ (server config) |
| Read logs and audit trail | – | – | – | ✔ | ✔ |
Roles other than the uploader row are **[proposal]**.

## Rules that must apply to uploads
1. **Authenticated only**, behind the same Basic auth and IP allow-list as every route.
2. **Safe input:** accepted file types and a size cap; never a client-supplied server path or URL; decode and validate before use; reject anything else.
3. **No retention of frames:** the uploaded media is processed in memory (or a temporary file removed afterwards). Only validated incidents are stored, with no raw frames and no identities.
4. **No identity features:** no face recognition, no worker identification, no per-person tracking (the "safety, not surveillance" principle).
5. **Audit:** log who (which credential) uploaded, when, and the media type and size, without logging the media itself.

## Open decision that this clarification creates  (needs the owner, in writing)
- **Constraint C-01 ("zero Renewi footage") conflicts with operators uploading their own feeds.** Choose one:
  - (a) For the PoC, operators upload only approved public or stock material; real Renewi footage waits for a later phase; or
  - (b) C-01 is relaxed for operator uploads, which brings privacy duties (works council, retention, identifiable people) that the SAD does not cover.
  Until decided, assume **(a)**.
- A shared Basic-auth login cannot tell a supervisor from engineering. Options: (1) one shared credential, roles are documentation only; (2) two credentials, a read-only one and a supervisor one,
  where only the supervisor credential may upload and acknowledge **[proposal]**; (3) per-user accounts and roles via SSO (outside the five-day PoC).
