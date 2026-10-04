# S13 inference API and G1 contract

## Contract and integration

ADR-003 is recorded in [implementation-plan.md](implementation-plan.md), section 4.
`POST /infer` accepts exactly two multipart fields: `image` (one JPEG or PNG)
and `clip_id` (a key in the server's clip registry). It never accepts URLs,
paths, checkpoint choices, thresholds, or polygons from clients.

The entrypoint is `backend.app:app`. Startup loads server configuration,
reviewed zones, and the same registered/restricted checkpoint adapter
(`ppe.yolo_detector.load_yolo_detector`) used by the CLI. Inference calls
`ppe.analysis.FrameAnalyzer` and its `to_dict` serializer, exactly as
`scripts/run_inference.py` does. The response wraps unchanged schema 1.2
analysis with `clip_id` and `checkpoint_sha256`. Frame IDs are server-generated;
timestamps are null for independent image uploads. Coordinates are original
source pixels, with no EXIF rotation or zone rescaling.

Events are immediate observations, not S15 sustained incidents or S16
persisted events. Person indices remain frame-local. No raw images are retained
as application artifacts. Multipart parsing may spool temporarily to disk;
its context manager closes/removes those temporary files on success or error.

## Server setup and local operation

Use only footage and checkpoints explicitly approved for the PoC. This
template is not an approval and does not resolve S10/VAL-04 model, fixture,
licensing, or privacy gates.

1. Install `backend/requirements-dev.txt` (or the aligned lock).
2. Create a server-controlled configuration using
   [api.example.yaml](../config/api.example.yaml) as the template.
   Paths resolve relative to the nested application root.
3. Request `PPE_API_CONFIG` through the orchestrator, pointing at that configuration.
   The application reads process environment, not `.env` directly.
   Missing/invalid configuration or checkpoint loading leaves readiness false.
4. Start locally from the nested application root:

```sh
.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

With the process running and `approved_demo` configured:

```sh
curl --fail http://127.0.0.1:8000/health
curl --fail -F clip_id=approved_demo -F image=@approved-frame.jpg http://127.0.0.1:8000/infer
```

Swagger UI is `/docs`; the live contract is `/openapi.json`.
**S14 authentication/IP filtering is not implemented. Do not expose this
service publicly.** C-01 remains approved-public-only until the owner decides
otherwise. A clip key selects configuration; it cannot establish that uploaded
image content actually belongs to, or is licensed for, that clip.

## Bounds and errors

Default limits: 5 MiB encoded image, 4096 pixels per dimension, 12 million
decoded pixels. Server configuration may change these within hard caps of
20 MiB, 8192 pixels, and 32 million pixels. The full HTTP body is capped at
the file limit plus 64 KiB multipart overhead, counting actual streamed
bytes even without a trustworthy Content-Length.

Headers/dimensions are validated before pixel decoding. Animated images,
unsupported formats, corrupt content, unknown clip IDs, duplicate/extra
fields, and zone calibration mismatches are rejected before model execution.
Filenames are ignored. A single nonblocking model lock prevents concurrent
decoder/model execution; busy callers receive 503, not an unbounded model queue.

| Status | Meaning |
| --- | --- |
| 200 | Inference result; health is ready |
| 400 | Malformed multipart or invalid Content-Length |
| 413 | Request/file/dimension/pixel limit exceeded |
| 415 | Unsupported request, media type, or animated image |
| 422 | Invalid fields, image, clip ID, or clip dimensions |
| 500 | Sanitized inference failure |
| 503 | Not ready or model execution busy |

`GET /health` returns `{"status":"ready","ready":true}` with 200, or
`{"status":"not_ready","ready":false}` with 503. An unavailable model does
not prevent health and OpenAPI from being served.

## G1 publication and validation

The published machine-readable G1 contract is [openapi.json](openapi.json).
It is derived from the real FastAPI application, including schema 1.2 nested
response models, multipart requirements, response codes, operation IDs,
metadata, and tags. It requires no weight loading to generate or compare.

```sh
.venv/bin/python scripts/export_openapi.py --check docs/openapi.json
.venv/bin/python -m pytest backend/tests/test_api.py backend/tests/test_analysis.py backend/tests/test_run_inference.py
```

`export_openapi.py` without `--check` prints the complete contract to stdout.
API tests use deterministic detectors to verify pipeline parity and bounds;
they do not establish real-model accuracy, GPU latency, or full VAL-04 acceptance.
