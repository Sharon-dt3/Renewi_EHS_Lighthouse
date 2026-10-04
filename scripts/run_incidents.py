#!/usr/bin/env python3
"""End-to-end local run: video -> model -> per-worker compliance -> sustained incidents (no API, no database).

Shows what the real system will do with a clip: frame timestamps drive the 1.5 s smoothing in config/rules.yaml.
Also reports a NAIVE count (any negative-class box is a violation) so the effect of the confidence floor, the
UNKNOWN-on-conflict rule and the smoothing is visible. Run inside scripts/run_isolated.sh (no network).

Usage: scripts/run_isolated.sh .venv/bin/python scripts/run_incidents.py --checkpoint ../models/last.pt \
         --video data/input/clips/<clip>.mp4 --out ../reports/incidents/<name>
"""
import argparse, collections, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(HERE))

import yaml


def load_rules(path):
    r = yaml.safe_load(Path(path).read_text())
    if r["sample_fps"] * r["max_gap_seconds"] < 1:
        raise SystemExit("sample_fps must be at least 1 / max_gap_seconds, otherwise nothing can ever be sustained")
    return r


def timed_frames(video, fps_out):
    import cv2
    cap = cv2.VideoCapture(str(video)); fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    step = 1.0 / fps_out; next_t = 0.0; i = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        t = i / fps
        if t + 1e-9 >= next_t:
            yield t, frame
            next_t += step
        i += 1
    cap.release()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", type=Path, required=True); ap.add_argument("--video", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True); ap.add_argument("--rules", type=Path, default=REPO / "config" / "rules.yaml")
    ap.add_argument("--config", type=Path, default=REPO / "config" / "classes.yaml"); ap.add_argument("--device", default="cpu")
    a = ap.parse_args(argv)
    rules = load_rules(a.rules)
    import cv2
    import run_inference as ri
    from ppe import compliance as comp
    from ppe.detections import Box, Detection
    from ppe.smoothing import SustainedDetector
    model, cmap = ri.load_model(a.checkpoint, a.config)
    labels = dict(cmap.labels)
    det = SustainedDetector(rules["hold_seconds"], rules["max_gap_seconds"])
    out = a.out.resolve(); (out / "annotated").mkdir(parents=True, exist_ok=True)
    rows, incidents, naive_frames, pipe_frames = [], [], 0, 0
    states = collections.Counter()
    for t, frame in timed_frames(a.video, rules["sample_fps"]):
        h, w = frame.shape[:2]
        res = model.predict(frame, conf=rules["min_positive_confidence"], imgsz=640, device=a.device, verbose=False)[0]
        b = res.boxes
        recs = ri.detections_to_records(b.xyxy.cpu().numpy().tolist(), b.conf.cpu().numpy().tolist(), b.cls.cpu().numpy().astype(int).tolist(), labels, w, h)
        dets = [Detection(r["class"], r["confidence"], Box(*r["xyxy"])) for r in recs]
        people, unassigned = comp.evaluate(dets, rules["min_negative_confidence"])
        active = comp.active_rules(people)
        naive = any(d.label in ("no_helmet", "no_safety_vest") for d in dets)
        naive_frames += naive; pipe_frames += bool(active)
        for p in people:
            states[p.state] += 1
        fid = f"t{t:06.2f}s"
        new = det.update(t, active, fid); incidents += new
        rows.append({"t": round(t, 2), "people": len(people), "states": [p.state for p in people], "naive_violation": naive, "active_rules": sorted(active), "incidents_raised": [i.rule for i in new]})
        if naive or active or new:
            cv2.imwrite(str(out / "annotated" / f"{fid}.jpg"), ri.draw(frame, recs))
    n = len(rows)
    summary = {"video": a.video.name, "checkpoint_sha256": cmap.checkpoint_sha256, "rules": rules, "frames_sampled": n,
               "frames_flagged_naive": naive_frames, "frames_flagged_by_pipeline": pipe_frames,
               "person_states": dict(states), "incidents": [i.__dict__ for i in incidents], "timeline": rows}
    (out / "incidents.json").write_text(json.dumps(summary, indent=1))
    print(f"{n} frames at {rules['sample_fps']} fps | naive reading flags {naive_frames} frames | pipeline flags {pipe_frames} frames | incidents raised: {len(incidents)}")
    print("per-worker states over all frames:", dict(states))
    for i in incidents:
        print(f"  INCIDENT {i.rule}: started {i.started_at:.2f}s, raised {i.detected_at:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
