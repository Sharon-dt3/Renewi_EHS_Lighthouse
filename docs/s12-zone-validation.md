# S12 zone integration and validation

## Status

**Implementation integrated; synthetic validation passed; real VAL-04 BLOCKED.**

Both local CLI runners now accept a per-clip zone configuration. No approved
real zone fixture was available for this invocation, and no real-model zone
evaluation was performed. This does not close OPEN-03, the independent
model-evaluation gate, or S12's real-fixture acceptance gate.

## Configuration and usage

Run from the nested application repository root. Add `--zones` to enable zone
analysis; omitting it preserves PPE-only operation. The configuration key
defaults to the input video filename stem. Use `--clip-id` to select a different
key. Inference with zones accepts a single video or image, not an image directory.

```yaml
clips:
  reviewed_clip:
    source_size: [1920, 1080]
    polygon: [[100, 200], [400, 200], [400, 500], [100, 500]]
```

These coordinates are illustrative only, not an approved fixture. Replace them
with reviewed coordinates for the actual source video. `source_size` is optional
for compatibility but recommended: it rejects resolution mismatches. Vertices
must be finite numeric pairs, distinct, ordered around a simple polygon with
non-zero area. Do not repeat the first vertex to close the polygon. Concave
polygons and clockwise ordering are supported; self-intersections, non-adjacent
touches, and overlapping edges are rejected.

```sh
scripts/run_isolated.sh .venv/bin/python scripts/run_inference.py \
  --checkpoint ../models/last.pt --input data/input/clips/reviewed_clip.mp4 \
  --zones config/zones.reviewed.yaml \
  --out ../reports/inference/reviewed_clip_zones --every-seconds 0.25

scripts/run_isolated.sh .venv/bin/python scripts/run_incidents.py \
  --checkpoint ../models/last.pt --video data/input/clips/reviewed_clip.mp4 \
  --zones config/zones.reviewed.yaml \
  --out ../reports/incidents/reviewed_clip_zones
```

These commands require an approved clip/configuration and a registered
checkpoint; neither command downloads weights. Sampling can miss short
incursions between analyzed frames.

## Output and semantics

`ppe/analysis.py`, `FrameAnalyzer.analyze`, validates source dimensions before
detection with `self._zone.validate_frame(w, h)`. No polygon scaling or
normalization is performed. `ppe/yolo_detector.py`, `YoloDetector.detect`, reads
`boxes.xyxy` from Ultralytics, whose adapter contract is original-frame pixels.

`ppe/zone.py`, `foot_point`, computes
`((box.x1 + box.x2) / 2.0, max(box.y1, box.y2))`. `Polygon.contains` checks
`_on_segment(point, start, end)` before toggling the ray-casting result, so edges
and corners count as inside. Source bounds use continuous coordinates
`[0, width]` and `[0, height]`, including the outer bounding-box edge.

Analysis JSON schema **1.2** retains existing fields and adds:

- Per-person `foot_point`, `zone_incursion`, and `rules`.
- An immediate `events` array with `person_index`, S11 `state`, `foot_point`,
  `zone_incursion`, and combined `rules`.
- A same-person example: state `HELMET_MISSING`, rules
  `["PPE_HELMET_MISSING", "ZONE_INCURSION"]`.

PPE rules keep their existing `PPE_` prefix. S11's conservative five-state
verdict remains unchanged, including UNKNOWN on incomplete/conflicting evidence.
A compliant or UNKNOWN person can still produce a zone event.
`FrameAnalyzer.analyze` derives each event with
`comp.active_rules([p], [p.person] if zone_incursion else [])`; it does not attach
another person's frame-level PPE flags.

`run_inference.py` emits this analysis in `detections.json`.
`run_incidents.py` stores immediate `events` and `person_observations` in each
timeline row, along with source dimensions. Annotated labels include zone
incursion beside the PPE state.

Events are observations on every analyzed frame touching/inside the zone, not
tracked entry transitions. Person indices are frame-local, never identities.
The existing sustained incidents remain separate: `run_incidents.py` calls
`det.update(t, active, fid)` with frame-level rule flags. Its 1.5-second hold
can suppress short observations and is not proof of continuous occupancy by
one particular person.

## Completed validation

The following focused command passed **105 tests in 9.15 seconds** (the full suite had 204 tests at that point) after the
implementation was approved and materialized:

```sh
.venv/bin/python -m pytest -q \
  backend/tests/test_zone.py backend/tests/test_zone_config.py \
  backend/tests/test_analysis.py backend/tests/test_compliance.py \
  backend/tests/test_frame_pipeline.py backend/tests/test_yolo_detector.py \
  backend/tests/test_run_inference.py backend/tests/test_run_incidents.py \
  backend/tests/test_smoothing.py backend/tests/test_s12_zones.py
git diff --check
```

`git diff --check` reported no whitespace errors.

New synthetic regressions in `backend/tests/test_s12_zones.py` cover invalid
geometry/configuration, calibrated source-size rejection before detection,
1920×1080 source coordinates with a 640 inference-size adapter stub, exact
bottom-centre positions, inside/outside/edge/corner checks, no rounding into
the zone, stable per-person combinations, S11 states, and both CLI runners
decoding generated 320×240 video. A short generated clip verifies immediate
combined events while sustained incidents remain empty.

The YOLO adapter test uses a model stub, not real weights; generated video is
not a real VAL-04 fixture. These tests establish integration behavior, not
real-model accuracy, approved zone placement, or clip licensing.

## Blocked real VAL-04 evidence

The existing `config/zones.example.yaml` is explicitly placeholder-only.
`data/input/clips/provenance.csv` identifies the available Pexels clip as
“qualitative first look only, NOT an evaluation set” and says evaluation-use
licensing must be confirmed.

To resume real validation, the PoC owner and licence reviewer must supply:

1. Approved evaluation-use clip provenance and privacy eligibility.
2. Reviewed per-clip source resolution and polygon coordinates.
3. Reviewed frame/timestamp expectations for source-coordinate alignment,
   person boxes/foot points, inside, outside, boundary/corner contact, and
   same-person combined PPE/zone observations. If the available clip lacks
   negative PPE or boundary cases, additional approved clips are needed.
4. Expected distinctions between immediate observations and sustained incidents.

Run the registered checkpoint through both CLI paths and compare saved
observations with those expectations. Record fixture identifiers/hashes,
checkpoint hash, configuration, command, output, reviewer and explicit
pass/fail per case. Until that evidence exists, **real VAL-04 remains BLOCKED,
not passed**.
