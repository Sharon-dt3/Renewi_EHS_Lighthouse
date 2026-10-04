# Renewi EHS Lighthouse — PPE PoC

## S13 inference API

The bounded multipart `/infer` API and readiness endpoint wrap the same S11
pipeline as the CLI. See [S13 setup and safety limits](docs/s13-inference-api.md)
and the published [G1 OpenAPI contract](docs/openapi.json).
S14 security is implemented (named users with hashed passwords, IP/CIDR allow-list, supervisor/read-only roles,
lockout, audit trail, HTTPS serving); see [S14 security](docs/s14-security.md). G3 sign-off pending
([review package](docs/g3-security-review.md)); keep it on localhost until HTTPS and G3 are in place.

## S12 zone integration

Both local CLI runners support per-clip source-pixel zones and frame-local
combined PPE/zone observations. See [S12 usage and validation](docs/s12-zone-validation.md)
for commands, schema 1.2, the focused synthetic test set (run the full suite with `pytest` for the current count), and the
**blocked real VAL-04 fixture gate**. Older foundation-status sections below
are historical and do not describe the current CLI implementation.

Local Python backend foundation for PEOPLE/PPE worker safety. STEP-01 provides
an isolated runtime and provenance-gated model download tooling. The sections
below describe the historical foundation; see S12/S13 above for current behavior.
Pipeline scaffolding under
`ppe/` exists but has only been tested on synthetic data (see below). No frontend, forklift logic, face recognition, identity tracking, database,
or cloud infrastructure is included.

## Local environment

Run commands from this application Git root (`Renewi_EHS_Lighthouse/`, nested
inside the workspace). Python 3.11 is required for the tested baseline.

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install --disable-pip-version-check --no-input -r backend/requirements.lock
.venv/bin/python -m pip check
.venv/bin/python -m pytest backend/tests/test_download_model.py
```

`backend/requirements.txt` pins direct runtime dependencies;
`backend/requirements-dev.txt` adds pytest and HTTPX. The complete lock records
the tested macOS ARM64 Python 3.11 runtime/test resolution. Other platforms
require separate validation, not an assumption of equivalent wheel support.
Do not rely on globally installed Torch. CPU execution is the baseline;
accelerator availability is not evidence of model capability.

## Model approval is blocked

Read [model-selection evidence](docs/model-selection.md) before any checkpoint
download or load. Neither named candidate has verified acceptable weights
licensing. The preferred training taxonomy lacks a negative vest class;
the fallback card lists neither Person nor vest classes. No model was silently
substituted and no weights were executed.

```sh
.venv/bin/python scripts/download_model.py --config config/model.yaml
```

This command **must currently refuse with exit code 1**. Approval fields remain
false/null until documented rights and model capability review are complete.
After review, the same command verifies the expected size and SHA-256 and
installs atomically to the configured project-relative path. It does not run
inference and never deserializes weights.

Downloader tests use synthetic byte streams; they do not prove real-model
accuracy, class availability, or licensing.

## Security and privacy boundaries

`.gitignore` excludes `.env`, virtual environments, downloaded weights, private
media, generated outputs, and metrics artifacts. Never commit worker footage
or credentials. The HTTP service requires Basic credentials and an allow-listed peer (S14).
Credentials must be requested from the user through the orchestrator and supplied only in the
process environment, never hardcoded or written into a file in Git.

Ultralytics licensing requires separate rights review; installing it is not
approval for redistribution or deployment. Dataset rights and the authoritative
100-clip dataset are unresolved. No metrics have been computed.

## Implementation sequence

The approved saved plan lives at the workspace level under
`kavia-docs/CodeWiki/Artifacts/Plans/ppe-core-implementation-plan.md`.
Complete STEP-01's model approval before STEP-02 inference work. FR-2 remains
blocked until STEP-03 records an explicit real-model FR-1 pass. A mocked
downloader test or training notebook class list cannot satisfy that gate.

## Pipeline scaffolding status

`ppe/` contains model-independent building blocks:

- `class_map.py`, `checkpoint.py`, `config/classes.yaml`: map a checkpoint's class IDs to
  internal labels, keyed by the checkpoint's SHA-256. An unlisted hash raises an error.
- `pipeline.py`: drops unmapped classes and low-confidence results.
- `zone.py`, `zone_config.py`: bottom-center point-in-polygon check (edges count as inside).
  `config/zones.example.yaml` holds placeholder coordinates only.
- `schema.py`: one JSON shape for a frame result.
- `detector.py`, `frame_pipeline.py`: the `Detector` interface and the frame pipeline.

Run the tests from the repository root:

```sh
.venv/bin/python -m pytest backend/tests
```

### Not verified

- No model has been loaded and no inference has run. All tests use synthetic detections.
- `config/model.yaml` keeps `approved: false`. Rights, loading approval and the actual
  checkpoint class check are unresolved (see `docs/model-selection.md`).
- The pinned Hafizqaim checkpoint has no explicit NO-Safety Vest class. The pipeline never
  infers it from a missing vest detection; the class must come from the model.
- No authorized Renewi images, zone polygons or evaluation dataset are available.
