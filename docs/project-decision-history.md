# Project history and decisions (to 2026-10-04)

A readable record of how the PPE detection work got from the BRD to a smoke-tested training pipeline, and why.
**No trained model exists yet.** The only checkpoint is a 1-epoch smoke test (`runs/smoke-20261004`, outside Git); its numbers are meaningless.

## 1. Starting problem
- Goal (BRD, Use Case 1): detect people and PPE in CCTV video using five classes: `person, helmet, no_helmet, safety_vest, no_safety_vest`.
- Preferred starting model (BRD): Hafizqaim YOLOv8. Its checkpoint (`models/best.pt`, SHA-256 `5464f555…20836`) has 17 serialized class names and **no NO-Safety Vest**.
- **Decision:** never infer NO-Safety Vest from a missing vest detection (conflicts or missing evidence give `UNKNOWN`). The class has to be learned from labelled examples (ADR-002).

## 2. Plan
- The original plan (rev 1) was stale and covered only the model and rules layers. **Decision:** rewrite as revision 2 covering model, backend, persistence, UI and deployment, with requirement traceability (`docs/implementation-plan.md`). Nine ADRs are recorded there. Revision 2 has the owner's approval for S7 only.

## 3. Dataset audit (CSS v27)
- Built a read-only original-resolution viewer (`scripts/build_dataset_viewer.py`), because 256 px thumbnails could not support label judgement.
- Audit log (171 rows) filled as an **AI first pass**: unconfirmed, and never applied automatically.
- Findings: many NO-Safety Vest boxes were poor (tiny, cropped, cab operators); only 700 source photos sit behind 2,799 files (augmented copies and 4-photo mosaics).

## 4. Leakage
- Attempt 1 (merge all matches into groups) chained false matches into one giant group: discarded.
- Attempt 2 (disqualify a held-out candidate that matches anything) left 61 held-out images (35 valid, 26 test). A second detector (SIFT) still found 357 held-out/train pairs, so even those are **not independent**.
- **Decision (ADR-009):** final evaluation uses a fresh, licensed, independent set (`docs/evaluation-set-guidelines.md`). CSS held-out images are sanity checks only.

## 5. Derived dataset
- `derived_ppe5/` (outside Git): five classes, boxes below a minimum size removed (24 px for no_safety_vest; 8-12 px for the rest), CC BY 4.0 attribution and change notice, hashes in `manifest.json`.
- 2,539 train, 35 valid, 26 test images. Raw data untouched. Only human-confirmed audit decisions are applied (none so far).
- Owner's informal check: all five classes visible, NO-Safety Vest labels looked correct (`docs/audit/human_review_notes.md`).
- Undecided: whether to remove selfie and off-domain images (D5).

## 6. Approvals and locked decisions
- **S7 weight-transfer plan** approved as a document (`docs/weight-transfer-plan.md`).
- **Acceptance thresholds locked before any results** (`config/acceptance_thresholds.yaml`, `docs/acceptance-thresholds.md`): AP50 person 0.80, helmet 0.80, safety_vest 0.75, no_helmet 0.60, no_safety_vest 0.60; overall mAP50 0.70; recall at least 0.60 for the two negative classes.
- **Weights route:** Hafizqaim has no licence, so the main path is a COCO-pretrained YOLOv8n; the rights request is drafted and **not sent** (`docs/weights-licence-decision.md`).
- **Gates for this PoC** (rights, security isolation, go-ahead) approved by the owner, scope PoC only (`config/training_authorization.yaml`). Not recorded: approver name; AGPL-3.0 vs enterprise licence route; a separate rights-reviewer document.

## 7. Training harness
- `scripts/train_ppe5.py`: refuses to run unless authorization, hashes, dataset and thresholds check out; never downloads; never loads `models/best.pt`; checks its hash before and after.
- `scripts/restricted_load.py`: static pickle scan plus an allow-list before `torch.load(weights_only=True)`. Added after noticing the first harness used Ultralytics' unrestricted loader, contrary to the approved plan. Tested against a malicious pickle.
- `scripts/run_isolated.sh`: macOS sandbox, no network, no writes to `models/`, `weights/`, the raw dataset or `derived_ppe5/`. Verified.
- `scripts/evaluate_ppe5.py`: AP50 and recall against the locked thresholds. Verdicts: PASS/FAIL only on a valid independent set, SANITY_ONLY for CSS held-out, NOT_EVALUATED otherwise.
- COCO `yolov8n.pt` downloaded (6,549,796 bytes, `ultralytics/assets` release v8.3.0). GitHub publishes no checksum, so the SHA-256 (`f59b3d83…`) was recorded on first download (trust on first use).
- Smoke test passed in the sandbox: 355/355 tensors loaded, head swapped to 5 classes (319/355 transferred), `best.pt` unchanged.

## 8. Known gaps and limits
- No trained model and no accuracy numbers. The independent evaluation set (OPEN-02) does not exist yet.
- Full CPU training on the Mac is impractical (about 25 min per epoch, roughly 40 hours for 100 epochs). A GPU is needed (`docs/gpu-training-runbook.md`).
- Ultralytics re-loads its own run outputs with its normal loader at the end of a run (low risk, but an exception to the restricted-loader rule).
- 31 `._*.mplstyle` macOS metadata files were removed from the venv because matplotlib crashed on them.
- Backend, temporal smoothing, database, UI and deployment (plan phases B to D) are not started.

## 9. First Colab run (2026-10-04)
- Colab (T4 GPU, Python 3.13, torch 2.6.0+cu124) passed: bundle hash verification (5,259 files), 52 tests, dry run with no blockers, network-namespace isolation, and the smoke test.
- **Bug found by the first full run:** it stopped at once with "Dataset ... images not found". The derived `data.yaml` has `path: .`, and Ultralytics resolves a relative `path` against its own datasets directory, not the yaml's folder. The smoke test had worked only because it uses a generated absolute-path file. Nothing had trained.
- **Fix in the repo:** `scripts/train_ppe5.py` now writes `data_abs.yaml` (absolute `path`) into the run folder for real runs, never touching the dataset (`write_abs_data_yaml`, with tests; 119 tests pass).
- **Workaround used on Colab for the live run:** the Colab copy of the bundle still had the old script, so its copy of `derived_ppe5/data.yaml` had its `path` line changed to `/content/ws/derived_ppe5` (path line only; the manifest and images are unchanged) and the failed run folder was removed. The run then used the old harness with the corrected path. The bundle was rebuilt afterwards with the fixed harness.
- Colab showed a generative-AI privacy notice when text was typed in an empty cell; it was **declined** (Cancel).
- The training run is `colab-full-1` (stage 1: 10 epochs, backbone frozen; stage 2: 90 epochs). Early log: about 20 to 30 seconds per epoch.

## 10. Decision to proceed (2026-10-04)
After the first look at footage (`reports/inference/pexels_clip1`, 8 frames), the project owner decided to **proceed on the assumption that the model is acceptable for the PoC** and move on to the application layers.
Recorded risk acceptance, so it is not forgotten:
- **Known weakness:** the `no_safety_vest` class. Lowest validation result (mAP50 0.76, precision 0.75, on 23 objects) and, on the Pexels clip, three false "no vest" detections on vested workers (two at confidence 0.65 to 0.71) in 2 of 8 frames. Likely causes: noisy original labels and bent or occluded postures.
- **Not measured:** recall for real missing-PPE cases (the clip had no violators), behaviour on CCTV-quality footage, and any figure from an independent evaluation set (OPEN-02 still open).
- **Mitigations planned in the pipeline:** a higher confidence floor for negative classes, an UNKNOWN verdict whenever evidence conflicts, and 1.5-second sustained-detection smoothing (S15).
- Accuracy claims remain forbidden until the independent set exists (`docs/acceptance-thresholds.md`).

## 11. S11 closed (2026-10-04)
- One shared pipeline: `ppe/yolo_detector.py` (the only Ultralytics-aware code) -> `ppe/analysis.py` `FrameAnalyzer` -> `ppe/compliance.py` -> JSON schema 1.1. The CLIs (`scripts/run_inference.py`, `scripts/run_incidents.py`) and the future API use it.
- `restricted_load` moved to `ppe/restricted_load.py`; `scripts/restricted_load.py` is a compatibility shim.
- Behaviour unchanged by the refactor: the Pexels clip (63 frames at 4 fps) still gives 17 naive flags, 4 pipeline flags, 0 incidents; the 26 test photos give the same detection counts.
- **Open design question found while closing S11:** rule flags are derived from the combined five-state verdict, so a worker with an explicit strong `no_safety_vest` but no helmet detection is `UNKNOWN` and raises no rule. That follows the plan's text (incomplete combinations are UNKNOWN) but under-reports. Option: derive rule flags from per-item verdicts (a vest violation is flagged whenever the vest evidence is explicitly negative, whatever the helmet status) while keeping the five-state label for display. Awaiting the owner's decision.

## 12. S12 partial validation (2026-10-04)
- Owner approved a **stand-in test zone** for the Pexels clip (`config/zones.reviewed.yaml`) and the draft expected-cases table as the basis for a partial check.
- Partial VAL-04 run: 6 MATCH, 0 MISMATCH, 1 NOT_DETECTED, constructed boundary MATCH. Record: `docs/val04-partial-pexels.md`.
- New outcome category **NOT_DETECTED** keeps model misses separate from zone-logic errors.
- S12 is **implemented, partially validated**. Still open: the combined PPE-plus-zone case (needs a violator clip), evaluation-use licence, independent table review.

## 13. S13 reviewed, S14 implemented (2026-10-04)
- S13 (`/infer`, `/health`, G1 contract) reviewed: shared pipeline verified identical to the CLI on a real 1080p frame; bounds and error handling tested live. Open question: whether ADR-003's "clip_id pointer" should also allow analysing a server-held clip with no upload.
- S14 implemented per ADR-005 / DEC-07: socket-peer IP/CIDR allow-list, constant-time Basic auth, 401 with challenge, 403 for peers and roles, fail-closed configuration, log redaction, supervisor-only upload. 77 new tests, mutation-checked; live checks with `scripts/run_api.sh`.
- Hazard found and handled: uvicorn's default proxy-header handling lets `X-Forwarded-For` rewrite the peer from 127.0.0.1; the launcher passes `--no-proxy-headers` and a test proves both sides.
- S15 closed as a library (acceptance criteria met). Wiring to the API and ledger is S16/S17.
- Not done and recorded: G3 review, HTTPS, rate limiting, named users (SSO).

## 14. S14 close-out (2026-10-04)
Gaps listed after the first S14 build were closed in code: named users with scrypt hashes and an audit trail (`PPE_USERS_FILE`, `scripts/make_user.py`), a per-peer failed-login lockout (429), TLS serving with the launcher refusing unencrypted non-loopback binds, and response hardening headers.
A test (no plaintext password in the settings repr) caught a real flaw during this work: bootstrap passwords were reachable from the settings object; they are now hidden from repr and held only in the redaction list.
Left to people: **G3 sign-off** (review package: `docs/g3-security-review.md`) and a production certificate or reverse proxy (S21).
