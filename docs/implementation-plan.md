---
artifact_type: implementation_plan
plan_id: renewi-ppe-core
title: Core PPE Computer-Vision Implementation Plan
status: revision_2_pending_approval
revision: 2
approved_revision: 1
approval:
  state: revision_2_awaiting_user_approval   # revision 1 was approved; revision 2 changes scope and needs a fresh approval
execution:
  state: blocked
  blocking_gates: [OPEN-01, S3-viewer, S4-audit]
risk_level: high
plan_depth: standard
revision_1_backup: ppe-core-implementation-plan.rev1-backup.md
drafted: 2026-10-04
primary_references:
  - BRD summary (FR-1, FR-2, metrics and security gaps)
  - Architecture document (TOGAF/42010; sections 2-15)
  - Renewi_EHS_Lighthouse/docs/model-selection.md
  - Renewi_EHS_Lighthouse/docs/dataset-license.md
---

[CodeWiki](../../index.md) / [Artifacts](../index.md) / [Plans](index.md)

# Core PPE Computer-Vision Implementation Plan — Revision 2

> **Revision 2 is not approved.** Revision 1 (approved) is preserved unchanged in `ppe-core-implementation-plan.rev1-backup.md`. Nothing here authorizes checkpoint loading, training or inference. Fine-tuning needs its own explicit user authorization (step S8).

## 1. Purpose and scope

Use Case 1 (PEOPLE: PPE and worker safety) of the Renewi EHS Lighthouse CCTV Analytics PoC. The system analyses a **single video feed**, detects people and PPE, flags PPE non-compliance and restricted-zone incursions, persists validated incidents, and lets a supervisor acknowledge them. Positioning is "safety, not surveillance": public non-identifiable clips only, no Renewi footage (C-01), no face recognition, no per-person tracking, no raw-frame storage.

### Delivery phases

| Phase | Scope | Covered by |
| --- | --- | --- |
| **A. Model and perception** | Dataset audit, five-class dataset, fine-tune, evaluate | S3-S10 |
| **B. Rules and backend** | Compliance, zone incursion, temporal smoothing, `/infer` API, security | S11-S15 |
| **C. Persistence and UI** | Postgres incident ledger, acknowledgement workflow, event transport, React single-feed UI, mAP50 card | S16-S19 |
| **D. Demo hardening** | Performance validation, deployment, end-to-end verification | S20-S22 |

Phase A gates everything else, because no usable five-class model exists yet. Phases B-D are architecture scope that revision 1 omitted; they are now planned but remain `blocked` behind their dependencies.

## 2. Why revision 2

1. **Revision 1 was stale against the repo** (pipeline scaffolding, fingerprint, dataset audit and fine-tuning direction were not reflected).
2. **Verified model fact:** `models/best.pt` (6,249,635 bytes, SHA-256 `5464f555f1b9831e6f1f9adcab11063f9a081d62e6650c2f2154bd4c01720836`) has a 17-name serialized taxonomy. Of the five targets it contains `person` (14), `head_helmet` (12), `head_nohelmet` (13) and `vest` (16). It has **no NO-Safety Vest**. Runtime behaviour of these classes is unverified (no checkpoint loaded, no inference run). The architecture's assumption A-02 does not hold for this checkpoint.
3. **Therefore fine-tuning on a five-class dataset is required** (ADR-002). Revision 1 had no such steps.
4. **Revision 1 covered only the model and rules layers.** The architecture also requires temporal smoothing, Postgres persistence, event broadcast and a UI. These are now in the plan.

## 3. Requirements traceability

### 3.1 Functional requirements

| Requirement | Source | Plan coverage |
| --- | --- | --- |
| FR-1: ingest frames, detect person, helmet, vest and explicit negatives | BRD | S6-S10 (model), S11 (rules), S13 (API) |
| FR-1: open weights, permissive licences | BRD | OPEN-01 (weights), OPEN-05 (dataset rights), ADR-002 |
| FR-1: consistent internal taxonomy (BRD mixes `no_helmet` / `NO-Hardhat`) | BRD note | ADR-001: canonical names `person`, `helmet`, `no_helmet`, `safety_vest`, `no_safety_vest`; display names Person, Hardhat, NO-Hardhat, Safety Vest, NO-Safety Vest |
| FR-2: bottom-centre `(x_c, y_max)` ray-casting against static per-clip polygon | BRD | S12 (code exists in `ppe/zone.py`, synthetic-tested) |
| FR-2 needs Person boxes | BRD note | Person is one of the five classes in the fine-tuned model; no second detector |
| FR-2 is dropped first if time is short | BRD, RAID | S12 and S19 overlays are marked optional/drop-first |
| BC-03 incident lifecycle UNRESOLVED -> ACKNOWLEDGED | Architecture | S16-S17 |
| BC-04 single-feed UI with overlays and timeline | Architecture | S18-S19 |
| BC-05 precomputed mAP50 shown in UI | Architecture | S9 (compute), S19 (display) |
| Metrics provenance (dataset, location, reproducibility, overall vs per-class) | BRD gap | S9: both overall mAP50 and per-class AP50, JSON with provenance, one reproducible command |
| Security: Basic auth + IP allow-list; which components | BRD gap | S14: backend app-level; reverse proxy at deployment boundary covers frontend (ADR-005) |
| Forklift/vehicle detection | BRD note | Out of scope; COCO is not assumed to include a forklift class |

### 3.2 Non-functional requirements

| NFR | Target | Plan coverage |
| --- | --- | --- |
| NFR-01 inference | <= 40 ms/frame (p95) | S20: measure on the target GPU host at representative resolution. CPU runs are functional only, not evidence for this target |
| NFR-02 backend + DB insert | <= 10 ms per validated incident | S20: benchmark the persistence path |
| NFR-03 security | Basic auth + IP allow-list enforced | S14 (app), S21 (deployment boundary), tests in VAL-06 |
| NFR-04 temporal smoothing | No event until 1.5 s sustained | S15, with timestamp-based synthetic tests |
| NFR-05 usability | Operator sees incident, time, rule, can acknowledge | S18-S19 |
| NFR-06 compliance | No Renewi footage; non-identifiable people | Dataset/clip audit (S4, S6, S21) |

### 3.3 Architecture constraints

C-01 zero Renewi footage; C-02 single builder, five-day budget (see risk R-07); C-03 40 ms inference; C-04 10 ms persistence; C-05 basic auth + IP allow-list. No message broker; in-process handling with direct Postgres persistence.

## 4. Decisions

| ID | Decision | Status |
| --- | --- | --- |
| ADR-001 | Canonical five-class taxonomy and naming (above) | Proposed |
| ADR-002 | **Fine-tune Hafizqaim for five classes** rather than infer NO-Safety Vest from absence or substitute another model. A missing vest detection is never negative evidence; conflicts or insufficient evidence give `UNKNOWN` | Proposed. Needs approval | **Update 2026-10-04:** the main path is a COCO-pretrained start because the Hafizqaim weights are unlicensed; Hafizqaim stays a comparison run if licensed.
| ADR-003 | `/infer` contract: image upload (multipart) for the PoC, plus a server-side `clip_id` pointer for demo clips. No client-supplied file paths or URLs | Proposed. Architecture lists this as undecided **Update 2026-10-04:** the operator/supervisor is the persona that uploads feeds once the system is built (owner statement); the upload rules and the C-01 question are in `docs/access-control.md`. |
| ADR-004 | Event transport to UI: **SSE** (one-directional, simple, no extra dependency) with polling fallback. Alternatives: WebSocket, polling | Proposed. Architecture ADR-001 is undecided |
| ADR-005 | Security: app-level Basic auth and socket-peer IP allow-list on the backend; HTTPS and a reverse proxy covering the frontend at the deployment boundary; forwarding headers ignored unless a trusted-proxy policy is added | Proposed |
| ADR-006 | Metrics: store as static JSON (`data/metrics/latest.json`) with provenance, served to the UI | Proposed. Architecture lists as pending |
| ADR-007 | Temporal smoothing: time-based (1.5 s on frame timestamps), not frame-count based, to tolerate frame-rate variability (A-03) | Proposed |
| ADR-008 | Person bounding box source: the fine-tuned five-class model's Person class | Proposed |
| ADR-009 | **Independent evaluation set.** CSS v27 can yield only about 61 cleanly held-out photos (35 valid, 26 test; about 20 NO-Safety Vest boxes per split), because 209 of 270 candidate photos also appear inside other images (mosaics). Final evaluation therefore uses a fresh, licensed, clip-split set (guidelines: `docs/evaluation-set-guidelines.md`). CSS held-out numbers are secondary | Proposed. Needs an owner to source and annotate |

## 5. Current state (verified 2026-10-04)

| Item | State | Evidence |
| --- | --- | --- |
| Environment and downloader | Done: Python 3.11 venv, pinned lock, checksum-gated downloader | `backend/requirements.lock`, `scripts/download_model.py` |
| Pipeline scaffolding | Exists, **synthetic tests only**: `ppe/{class_map,checkpoint,pipeline,frame_pipeline,schema,zone,zone_config,detector}.py` | `pytest`: 65 passed |
| Absence-based NO-vest inference | Removed deliberately | commits 7df0cab, 040b8ba |
| Checkpoint | Fingerprint recorded; never loaded | `docs/model-selection.md` |
| Weights licence | **Unresolved (OPEN-01)**; all approval flags false in `config/model.yaml` | `config/model.yaml` |
| Dataset | CSS v27 in `raw_css_dataset/`: 2,799 images (2,603 / 114 / 82), CC BY 4.0 recorded | `docs/dataset-license.md` |
| Dataset audit | Phases 1-2C done; **blocked at 2D (no original-resolution viewer)** | session record |
| Backend `/infer`, smoothing, DB, UI, metrics, deployment | **Not started** | n/a |
| Training, inference, metrics | **None** | n/a |

### Housekeeping (decide before building more)

- **Duplicate trees:** workspace-level `ppe/` and `config/` duplicate the nested application repo and already differ (`vest_rule.py` only in the outer copy; `pipeline.py` differs). One canonical tree is needed (OPEN-06).
- **Layout drift:** revision 1 specified `backend/app/...`; the code is in `ppe/`. Adopt `ppe/` as the package (or migrate) and keep this plan in step.
- **Stale class map:** `config/classes.yaml` maps old Hafizqaim IDs (12/13/14/16). A fine-tuned checkpoint has a new hash and its own map; never reuse this one.
- **Git scope:** only the nested repo is tracked. `raw_css_dataset/`, `models/`, `utils/`, `reports/` and `kavia-docs/` are outside it.

## 6. Steps

Statuses: `done`, `partial`, `to_do`, `blocked`. Each step lists the validation that proves it. Steps S3 onward are new in revision 2.

### Phase A: model and perception

| ID | Step | Owner | Status | Depends on | Gate and output |
| --- | --- | --- | --- | --- | --- |
| S1 | Environment and checksum-gated downloader | Code | done | none | 25 downloader tests; 65 total pass |
| S2 | Model provenance: fingerprint, serialized taxonomy, licence | Model and rights owner | **partial** | S1 | Fingerprint and taxonomy done; weights licence open (OPEN-01) |
| S3 | **Phase 2D read-only original-resolution viewer** in `utils/`: static HTML/PNG to `reports/`; full-resolution boxes with class colours, zoomable crops, filters (empty labels, tiny boxes, NO-Safety Vest, the known Safety Vest and tiny Hardhat examples) | Code | to_do | none | Reviewer can open the output. Writes nothing to dataset, labels or checkpoint |
| S4 | **Original-resolution annotation audit** with a decision log; train/val/test source-family overlap check; resolve 2,799 vs 2,801 | Reviewer and Code | blocked | S3 | Signed decision log in `reports/` |
| S5 | **Dataset readiness decision** (use as is, clean, or reject) | Dataset owner | blocked | S4 | Written decision |
| S6 | **Derived five-class dataset**: Person, Hardhat, NO-Hardhat, Safety Vest, NO-Safety Vest; drop Mask, NO-Mask, Safety Cone, machinery, vehicle; raw data untouched; CC BY 4.0 attribution and change notice; re-split by source family if the audit finds leakage | Code | blocked | S5 | New dataset directory with manifest, hashes and class counts |
| S7 | **Architecture and weight-transfer plan**: 17-class head to 5-class head, layers transferred or frozen, seed, hyperparameters, per-class acceptance thresholds (OPEN-07), restricted-loading harness (read-only source mount, no unsafe globals, digest verified before and after, output-only write boundary) | Model and security owners | **approved 2026-10-04** (`docs/weight-transfer-plan.md`); gates for S8 still open | S6 | Written plan approved by the user |
| S8 | **Fine-tuning** | Training | blocked | S7, OPEN-01, OPEN-08 | Needs **separate explicit user authorization**. New versioned checkpoint with its own hash. Original `best.pt` unchanged **Status 2026-10-04:** gates approved for this PoC; COCO weights downloaded and pinned; guarded harness and restricted loader built; CPU smoke test passed in a sandbox. Full run waits for a GPU host (`docs/gpu-training-runbook.md`). |
| S9 | **Evaluation**: overall mAP50 and per-class AP50, precision, recall on the independent evaluation set (ADR-009), with CSS v27 held-out results as secondary; provenance (dataset version and hash, checkpoint hash and revision, thresholds, UTC date, Git commit); failure-case review; no placeholder values | Test | blocked | S8, OPEN-02 | Evaluation JSON in `reports/` and `data/metrics/latest.json`, one reproducible command |
| S10 | Register the new checkpoint's class map under its own hash; **FR-1 real-model gate** on reviewed fixtures (Person and positive and negative PPE across the fixture set, image and video) | Code and Test | blocked | S9, OPEN-03 | `docs/fr1-verification.md` with explicit pass or fail. FR-2 and the API stay blocked on failure |

### Phase B: rules and backend

| ID | Step | Owner | Status | Depends on | Gate and output |
| --- | --- | --- | --- | --- | --- |
| S11 | FR-1 inference and compliance on the real model: association (PPE centre to smallest containing person box, stable ties), five states (`COMPLIANT`, `HELMET_MISSING`, `VEST_MISSING`, `HELMET_AND_VEST_MISSING`, `UNKNOWN`), original-frame coordinates, JSON and annotated output, CLI. Scaffolding exists; complete and test on real detections | Code | blocked | S10 | VAL-02 tests plus real CLI runs |
| S12 | FR-2 zones: per-clip polygons in source-frame pixels, validated, bottom-centre, boundary-inclusive ray casting, `ZONE_INCURSION` and combined events. **Optional, drop first** | Code and Test | blocked | S10, OPEN-03 | VAL-04 on real zone fixtures. Logic already synthetic-tested |
| S13 | `/infer` endpoint and health check per ADR-003 (multipart image, server-side `clip_id` for demo clips), bounded input, shared pipeline with the CLI | Code | blocked | S11 | OpenAPI contract published (architecture gate G1) |
| S14 | Security per ADR-005: environment-backed Basic auth, application-level IP/CIDR allow-list on the socket peer, constant-time comparison, 401 with challenge, 403 for disallowed peers, fail closed on missing config, log redaction | Code | blocked | S13 | VAL-06; architecture gate G3 **Roles (proposed):** supervisor credential may upload and acknowledge; read-only credential may not (`docs/access-control.md`). |
| S15 | **Temporal smoothing** per ADR-007: timestamp-based, incident only after 1.5 s sustained, per-rule state, one incident per sustained episode, tolerance for frame-rate variability | Code | blocked | S11 | Synthetic intermittent-detection tests (NFR-04) |

### Phase C: persistence and UI

| ID | Step | Owner | Status | Depends on | Gate and output |
| --- | --- | --- | --- | --- | --- |
| S16 | **Postgres incident ledger**: `incidents` table (id, timestamp, clip_id, rule, JSONB bounding boxes with a stable shape, status UNRESOLVED / ACKNOWLEDGED, acknowledged_at), indexes on timestamp and clip_id, only validated incidents stored, no raw frames, short retention with manual cleanup | Code | blocked | S15 | Schema and persistence tests; architecture gate G2 |
| S17 | **Event API**: list incidents, `POST /events/{id}/acknowledge` idempotent (status check on update), event stream per ADR-004 | Code | blocked | S16, S14 | API tests including duplicate acknowledgement |
| S18 | **React single-feed UI**: video, overlay rendering, incident timeline, acknowledge action, mAP50 card (overall and per-class). No multi-camera grid, no per-person tracking features | Code | blocked | S17, S9 | NFR-05 walkthrough |
| S19 | Zone polygon overlay in the UI (optional, with S12) | Code | blocked | S12, S18 | Visual check |

### Phase D: demo hardening

| ID | Step | Owner | Status | Depends on | Gate and output |
| --- | --- | --- | --- | --- | --- |
| S20 | **Performance validation**: p95 inference latency (<= 40 ms) on the GPU host, backend plus DB insert (<= 10 ms), event delivery latency; pre-warm model; adjust resolution or model size if missed | Test | blocked | S17 | Measurements report (NFR-01, NFR-02; architecture gate G4) |
| S21 | **Deployment**: AWS GPU instance (g5/g6, >= 32 GB RAM), reverse proxy with basic auth and IP allow-list covering frontend and backend, simulated RTSP (ffmpeg loop plus mediamtx), manual deployment script, recorded local video backup; clip audit (public, non-identifiable, no Renewi footage) | Infra and Delivery | blocked | S20, OPEN-03 | Deployment checklist; architecture gate G3 |
| S22 | **End-to-end verification**: full test suite, FR-1 regression fixtures, configured demo clip with zone, authenticated API checks (valid and invalid credentials, disallowed peers, spoofed forwarding headers), incident through to acknowledgement in the UI, remaining limitations recorded | Test | blocked | S21 | `docs/poc-verification.md` |

## 7. Validation matrix

| ID | Validates | Method |
| --- | --- | --- |
| VAL-01 | AC-01 provenance | Inspect `docs/model-selection.md`, SHA-256, `pip check`, licence evidence |
| VAL-02 | FR-1 logic | Mapping, schema, association and compliance tests; real image and video CLI runs |
| VAL-03 | FR-1 real model | Real weights on reviewed fixtures; saved detections, annotations, config, provenance, explicit gate decision |
| VAL-04 | FR-2 | Boundary, corner and concave polygon tests; configuration tests; event combinations |
| VAL-05 | Metrics | Schema and reproducibility tests; real evaluation on an identified, licensed, annotated dataset |
| VAL-06 | Security | Credential, peer-IP, missing-config, spoofed-header and log-redaction tests |
| VAL-07 | End to end | Full suite, authenticated API integration, CLI demo, UI walkthrough |
| VAL-08 | Smoothing | Synthetic stream with intermittent detections; no event before 1.5 s |
| VAL-09 | Persistence | Schema, insert, acknowledge, idempotency; insert latency benchmark |
| VAL-10 | Performance | p95 inference and persistence latency on the target host |

Acceptance criteria AC-01 to AC-07 from revision 1 are unchanged. New: **AC-08** smoothing (VAL-08), **AC-09** persistence and acknowledgement (VAL-09), **AC-10** UI (NFR-05 walkthrough), **AC-11** performance targets (VAL-10), **AC-12** fine-tuned model meets agreed per-class thresholds (S9).

## 8. Open items

| ID | Item | Owner | Required before |
| --- | --- | --- | --- |
| OPEN-01 | **Approved for this PoC 2026-10-04** by the project owner (`config/training_authorization.yaml`, scope: this PoC only). Route: train from COCO-pretrained YOLOv8n (`docs/weights-licence-decision.md`); Hafizqaim stays unlicensed and unused (rights request draft not sent). Not recorded: approver name, AGPL-3.0 vs enterprise route, a separate rights-reviewer document | PoC/model owner and rights reviewer | S8 (approved; record gaps remain) |
| OPEN-02 | Source, license and annotate an independent evaluation set (at least 100 images from at least 20 clips or sites, at least 50 instances per target class); CSS v27's 61 clean held-out photos are not enough. See `docs/evaluation-set-guidelines.md` | Dataset owner | S9 and any "100-clip" claim |
| OPEN-03 | Licensed demo clips and per-clip zone polygons | PoC owner | S10 fixtures, S12, S21 |
| OPEN-04 | Plans-location resolver | Documentation platform owner | Canonical publication |
| OPEN-05 | Rights to every CSS v27 image (uploader rights not established); suitability for Renewi sites | Dataset owner | S6 |
| OPEN-06 | Canonical code tree and layout; Git scope | Engineering | S3 |
| OPEN-07 | **Resolved 2026-10-04:** thresholds set by the owner (Balanced profile plus recall floor) and locked before any results; see `docs/acceptance-thresholds.md` and `config/acceptance_thresholds.yaml` | Model owner | done |
| OPEN-08 | **Approved 2026-10-04** by the project owner for isolated training (`config/training_authorization.yaml`). The harness is `scripts/train_ppe5.py`, built to `docs/weight-transfer-plan.md` section 4 | Security owner | S8 (approved) |
| OPEN-09 | Whether the five-day single-builder budget (C-02) still applies given Phase A | Sponsor | Planning |
| OPEN-10 | Approve ADR-001 to ADR-008, including the architecture ADRs left undecided (transport, `/infer` contract, metrics storage) | Architect | S13, S17, S18 |
| OPEN-11 | C-01 (zero Renewi footage) versus operators uploading their own feeds: choose approved-public-only for the PoC, or relax C-01 in writing with privacy sign-off. Assume approved-public-only until decided. Also decide the role mechanism (shared credential, two credentials, or SSO) | Sponsor / compliance | S13, S14 |

## 9. Risks

| ID | Risk | Mitigation |
| --- | --- | --- |
| R-01 | Weights licence not obtainable | Keep approval disabled; owner decision on a replacement model, which needs plan reapproval. Do not invent Person boxes |
| R-02 | CSS v27 annotation quality (suspect NO-Safety Vest, missing Person, tiny objects, split leakage) | S3-S5 audit before any derived dataset |
| R-03 | Fine-tuned model underperforms on NO-Safety Vest or Renewi-like views | Per-class thresholds set before evaluation; failure-case review; keep `UNKNOWN` conservative |
| R-04 | Latency targets missed | GPU host, smaller input size, pre-warmed model (S20) |
| R-05 | Occlusion causes false violations | Deterministic association, `UNKNOWN` on conflict, temporal smoothing |
| R-06 | Zone polygons mismatch frame resolution | Validate dimensions and source-pixel coordinates |
| R-07 | **Schedule:** the BRD assumes five days; Phase A alone is a multi-stage effort | Resolve OPEN-09; phases B-D can be reduced (drop FR-2 first) |
| R-08 | Dataset rights or privacy posture violated by public clips | Provenance record and pre-demo clip audit |
| R-09 | Basic credentials sent in plaintext | HTTPS and deployment-boundary controls; local bind by default |
| R-10 | Accidental commit of weights, dataset or secrets | `.gitignore` coverage; keep `best.pt`, `raw_css_dataset/` and `.env` out of Git |

## 10. Rules carried over unchanged

- A missing detection is never negative evidence; conflicts or insufficient evidence give `UNKNOWN`. Uncertain PPE fields are null, not false.
- Never create NO-Safety Vest by subtracting vest detections from persons. Labels need a visibly assessable torso without a vest.
- The original `models/best.pt` is immutable. Trained output goes to a separate run directory with its own hash and class map.
- No facial recognition, worker identification or persistent person tracking. Person indices are frame-local.
- No unsupported accuracy claims and no placeholder metrics.

## 11. History

Revision 1 (approved 2026-10-03): STEP-01 environment and provenance (failed on model approval), STEP-02 to STEP-05 not started. Its full text, tracker and execution record are in `ppe-core-implementation-plan.rev1-backup.md`. Revision 2 drafted 2026-10-04: adds the dataset audit and fine-tuning path, the architecture layers that revision 1 omitted (smoothing, persistence, event API, UI, performance, deployment), decisions ADR-001 to ADR-008, and requirement traceability.
