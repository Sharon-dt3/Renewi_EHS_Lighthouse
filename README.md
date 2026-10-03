# Renewi EHS Lighthouse — PPE PoC

Local Python backend foundation for PEOPLE/PPE worker safety. STEP-01 provides
an isolated runtime and provenance-gated model download tooling. Inference,
compliance, geometry, metrics evaluation, and HTTP endpoints are not implemented
yet. No frontend, forklift logic, face recognition, identity tracking, database,
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
or credentials. There is currently no HTTP service or authentication interface.
Later API credentials must be requested from the user through the orchestrator,
not hardcoded or written directly into `.env`.

Ultralytics licensing requires separate rights review; installing it is not
approval for redistribution or deployment. Dataset rights and the authoritative
100-clip dataset are unresolved. No metrics have been computed.

## Implementation sequence

The approved saved plan lives at the workspace level under
`kavia-docs/CodeWiki/Artifacts/Plans/ppe-core-implementation-plan.md`.
Complete STEP-01's model approval before STEP-02 inference work. FR-2 remains
blocked until STEP-03 records an explicit real-model FR-1 pass. A mocked
downloader test or training notebook class list cannot satisfy that gate.
