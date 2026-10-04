#!/usr/bin/env python3
"""Score a run_incidents output against reviewed VAL-04 zone cases.

Outcomes: MATCH, MISMATCH (detected, wrong side: a zone failure), NOT_DETECTED (no person near the expected
position: a detection limitation, reported separately). It reads the system's own `zone_incursion` flag from the run;
it never recomputes the answer. Also runs the CONSTRUCTED boundary check: a polygon edge is placed exactly through a
real measured foot point, and one placed 0.001 px beyond it, to confirm edge-inclusive behaviour on real data.

Usage: .venv/bin/python scripts/val04_zone_cases.py --cases config/val04_cases.pexels_10294766.yaml \
          --run ../reports/val04/<name>/incidents.json --out ../reports/val04/<name>/val04_result.json
"""
import argparse, hashlib, json, math, sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))


def score_case(case, rows, tolerance_px, time_tolerance_s):
    """Return a dict with the outcome for one case."""
    near = [r for r in rows if abs(r["t"] - case["t"]) <= time_tolerance_s]
    if not near:
        return {"id": case["id"], "outcome": "NO_FRAME", "detail": "no sampled frame within the time tolerance"}
    row = min(near, key=lambda r: abs(r["t"] - case["t"]))
    best, dist = None, None
    for p in row["person_observations"]:
        d = math.hypot(p["foot_point"][0] - case["feet"][0], p["foot_point"][1] - case["feet"][1])
        if dist is None or d < dist:
            best, dist = p, d
    if best is None or dist > tolerance_px:
        return {"id": case["id"], "t_sampled": row["t"], "outcome": "NOT_DETECTED", "expected": case["expected"],
                "nearest_px": None if dist is None else round(dist), "detail": "no person box near the expected position"}
    got = "inside" if best["zone_incursion"] else "outside"
    return {"id": case["id"], "t_sampled": row["t"], "expected": case["expected"], "system": got,
            "foot_point": [round(v, 1) for v in best["foot_point"]], "distance_px": round(dist),
            "person_confidence": best["confidence"], "outcome": "MATCH" if got == case["expected"] else "MISMATCH"}


def constructed_boundary(foot):
    """Edge placed exactly through a real foot point, and 0.001 px away from it."""
    from ppe.detections import Box, Detection, Label
    from ppe.zone import Polygon, ZoneIncursionDetector, foot_point
    fx, fy = foot
    person = Detection(Label.PERSON, 0.9, Box(fx - 40.0, fy - 200.0, fx + 40.0, fy))    # bottom-centre is exactly (fx, fy)
    assert foot_point(person.box) == (fx, fy)
    out = {}
    for name, top in (("edge_through_foot", fy), ("edge_0.001px_below_foot", fy + 0.001), ("edge_0.001px_above_foot", fy - 0.001)):
        poly = Polygon(((fx - 300.0, top), (fx + 300.0, top), (fx + 300.0, top + 300.0), (fx - 300.0, top + 300.0)))
        out[name] = bool(ZoneIncursionDetector(poly).persons_inside([person]))
    vertex = Polygon(((fx, fy), (fx + 300.0, fy), (fx + 300.0, fy + 300.0)))
    out["foot_exactly_on_a_corner"] = bool(ZoneIncursionDetector(vertex).persons_inside([person]))
    expected = {"edge_through_foot": True, "edge_0.001px_below_foot": False, "edge_0.001px_above_foot": True, "foot_exactly_on_a_corner": True}
    return {"foot_point": [fx, fy], "results": out, "expected": expected, "outcome": "MATCH" if out == expected else "MISMATCH"}


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", type=Path, required=True); ap.add_argument("--run", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    spec = yaml.safe_load(a.cases.read_text()); run = json.loads(a.run.read_text()); rows = run["timeline"]
    results = [score_case(c, rows, spec["tolerance_px"], spec["time_tolerance_s"]) for c in spec["cases"]]
    anchor = next((r for r in results if r["id"] == "I1" and "foot_point" in r), None)
    boundary = constructed_boundary(tuple(anchor["foot_point"])) if anchor else None
    if boundary is not None:     # use the unrounded foot point from the run for the exact-edge case
        raw = next(p for r in rows if abs(r["t"] - anchor["t_sampled"]) < 1e-9 for p in r["person_observations"] if [round(v, 1) for v in p["foot_point"]] == anchor["foot_point"])
        boundary = constructed_boundary(tuple(raw["foot_point"]))
    counts = {k: sum(1 for r in results if r["outcome"] == k) for k in ("MATCH", "MISMATCH", "NOT_DETECTED", "NO_FRAME")}
    record = {"video": run["video"], "checkpoint_sha256": run["checkpoint_sha256"], "cases_file_sha256": sha256(a.cases),
              "zones_file_sha256": sha256(REPO / spec["zones_file"]), "clip_sha256_expected": spec["clip_sha256"],
              "counts": counts, "cases": results, "constructed_boundary": boundary,
              "verdict": "PARTIAL: zone-geometry cases passed" if counts["MISMATCH"] == 0 and (boundary or {}).get("outcome") == "MATCH" else "FAIL"}
    a.out.write_text(json.dumps(record, indent=1))
    for r in results:
        print(f"{r['id']:4s} t={r.get('t_sampled', '-')!s:6s} expected {r.get('expected', '-'):8s} -> {r['outcome']:12s} {r.get('system', '')} {('(' + str(r['distance_px']) + ' px)') if 'distance_px' in r else ''}")
    print("counts:", counts)
    if boundary:
        print("constructed boundary:", boundary["results"], "->", boundary["outcome"])
    print("verdict:", record["verdict"])
    return 0 if record["verdict"].startswith("PARTIAL") else 1


if __name__ == "__main__":
    sys.exit(main())
