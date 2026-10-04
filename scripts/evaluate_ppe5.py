#!/usr/bin/env python3
"""Evaluate five-class detections against ground truth and the LOCKED acceptance thresholds.

Model-independent: it reads prediction files, so it can be tested without any checkpoint.
Predictions: one YOLO txt per image in --pred-dir, lines "cls xc yc w h conf" (normalised).
Ground truth: one YOLO txt per image in --gt-dir, lines "cls xc yc w h".

Verdicts
  PASS / FAIL    only when --eval-set-kind independent, the set passes scripts/check_eval_labels.py
                 and every class has ground truth. Compared with config/acceptance_thresholds.yaml.
  SANITY_ONLY    --eval-set-kind css-heldout: numbers are reported, never pass/fail.
  NOT_EVALUATED  independent set missing or invalid, or a class has no ground truth.
Nothing is ever reported as passed without a real independent evaluation set.
"""
import argparse, collections, datetime, hashlib, json, subprocess, sys
from pathlib import Path
import yaml

CLASSES = ["person", "helmet", "no_helmet", "safety_vest", "no_safety_vest"]
HERE = Path(__file__).resolve().parent
REPO = HERE.parent
THRESH = REPO / "config" / "acceptance_thresholds.yaml"

def read_boxes(path, with_conf):
    out = []
    if Path(path).exists():
        for line in Path(path).read_text().splitlines():
            p = line.split()
            if not p: continue
            need = 6 if with_conf else 5
            if len(p) != need: raise ValueError(f"{path}: expected {need} fields, got {len(p)}")
            c = int(p[0]); xc, yc, w, h = map(float, p[1:5]); conf = float(p[5]) if with_conf else 1.0
            out.append((c, xc - w / 2, yc - h / 2, xc + w / 2, yc + h / 2, conf))
    return out

def iou(a, b):
    ix = max(0.0, min(a[3], b[3]) - max(a[1], b[1])); iy = max(0.0, min(a[4], b[4]) - max(a[2], b[2]))
    inter = ix * iy
    union = (a[3] - a[1]) * (a[4] - a[2]) + (b[3] - b[1]) * (b[4] - b[2]) - inter
    return inter / union if union > 0 else 0.0

def match(gt_by_img, pr_by_img, cls, iou_thr):
    """Greedy match per image in descending confidence. Returns (list of (conf, is_tp), n_gt)."""
    recs, n_gt = [], 0
    for img in set(gt_by_img) | set(pr_by_img):
        gts = [g for g in gt_by_img.get(img, []) if g[0] == cls]; n_gt += len(gts)
        used = [False] * len(gts)
        for p in sorted((q for q in pr_by_img.get(img, []) if q[0] == cls), key=lambda q: -q[5]):
            best, bi = 0.0, -1
            for i, g in enumerate(gts):
                if not used[i]:
                    v = iou(p, g)
                    if v > best: best, bi = v, i
            if bi >= 0 and best >= iou_thr: used[bi] = True; recs.append((p[5], True))
            else: recs.append((p[5], False))
    return recs, n_gt

def average_precision(recs, n_gt):
    """All-point interpolated AP (area under the monotone precision envelope)."""
    if n_gt == 0: return None
    recs = sorted(recs, key=lambda r: -r[0]); tp = fp = 0; rec, prec = [0.0], [1.0]
    for _, ok in recs:
        tp += ok; fp += (not ok); rec.append(tp / n_gt); prec.append(tp / (tp + fp))
    rec.append(rec[-1]); prec.append(0.0)
    for i in range(len(prec) - 2, -1, -1): prec[i] = max(prec[i], prec[i + 1])
    return sum((rec[i + 1] - rec[i]) * prec[i + 1] for i in range(len(rec) - 1))

def metrics(gt_by_img, pr_by_img, iou_thr=0.5, conf_thr=0.25):
    res = {}
    for c, name in enumerate(CLASSES):
        recs, n_gt = match(gt_by_img, pr_by_img, c, iou_thr)
        ap = average_precision(recs, n_gt)
        kept = [r for r in recs if r[0] >= conf_thr]
        tp = sum(ok for _, ok in kept); fp = len(kept) - tp
        res[name] = dict(n_gt=n_gt, n_pred=len(recs), ap50=ap,
                         precision=(tp / (tp + fp)) if kept else None, recall=(tp / n_gt) if n_gt else None)
    aps = [v["ap50"] for v in res.values() if v["ap50"] is not None]
    return res, (sum(aps) / len(aps) if aps else None)

def judge(res, overall, th):
    """Return (verdict_if_complete, failures). Any class without ground truth => NOT_EVALUATED."""
    if any(v["n_gt"] == 0 for v in res.values()): return "NOT_EVALUATED", ["a class has no ground truth"]
    fails = []
    for c, mn in th["per_class_ap50_min"].items():
        if res[c]["ap50"] < mn: fails.append(f"{c} AP50 {res[c]['ap50']:.3f} < {mn}")
    if overall < th["overall_map50_min"]: fails.append(f"overall mAP50 {overall:.3f} < {th['overall_map50_min']}")
    rf = th["recall_floor"]
    for c in rf["classes"]:
        r = res[c]["recall"]
        if r is None or r < rf["min_recall"]: fails.append(f"{c} recall {r if r is None else round(r,3)} < {rf['min_recall']} at conf {rf['at_confidence']}")
    return ("FAIL" if fails else "PASS"), fails

def sha256(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def tree_hash(d):
    h = hashlib.sha256()
    for p in sorted(Path(d).rglob("*")):
        if p.is_file() and not p.name.startswith("._"): h.update(p.relative_to(d).as_posix().encode()); h.update(sha256(p).encode())
    return h.hexdigest()

def git_commit():
    try: return subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10).stdout.strip() or None
    except Exception: return None

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--gt-dir", type=Path, required=True); ap.add_argument("--pred-dir", type=Path, required=True)
    ap.add_argument("--eval-set-kind", choices=["independent", "css-heldout"], required=True)
    ap.add_argument("--eval-root", type=Path, help="independent set root (images/, labels/, provenance.csv) for validation")
    ap.add_argument("--checkpoint-sha256", required=True); ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--conf", type=float); ap.add_argument("--iou", type=float, default=0.5)
    a = ap.parse_args(argv)
    th = yaml.safe_load(THRESH.read_text())
    conf = a.conf if a.conf is not None else th["recall_floor"]["at_confidence"]

    gt = {p.stem: read_boxes(p, False) for p in sorted(a.gt_dir.glob("*.txt")) if not p.name.startswith("._")}
    pr = {s: read_boxes(a.pred_dir / f"{s}.txt", True) for s in gt}
    res, overall = metrics(gt, pr, a.iou, conf)

    notes, verdict, fails = [], None, []
    if a.eval_set_kind == "css-heldout":
        verdict = "SANITY_ONLY"; notes.append("CSS held-out images are not independent of training; never pass/fail")
    else:
        sys.path.insert(0, str(HERE))
        import check_eval_labels
        if not a.eval_root or not a.eval_root.is_dir(): verdict = "NOT_EVALUATED"; notes.append("independent set root not given or missing")
        elif check_eval_labels.main([str(a.eval_root)]) != 0: verdict = "NOT_EVALUATED"; notes.append("independent set failed scripts/check_eval_labels.py")
        else: verdict, fails = judge(res, overall, th)
        if verdict == "NOT_EVALUATED" and not notes: notes.extend(fails)
    report = dict(
        verdict=verdict, failures=fails, notes=notes, overall_map50=overall, per_class=res,
        provenance=dict(date_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), git_commit=git_commit(),
                        checkpoint_sha256=a.checkpoint_sha256, thresholds_file_sha256=sha256(THRESH), thresholds_used=th,
                        iou=a.iou, conf=conf, eval_set_kind=a.eval_set_kind, n_images=len(gt),
                        gt_tree_sha256=tree_hash(a.gt_dir), pred_tree_sha256=tree_hash(a.pred_dir)))
    a.out.parent.mkdir(parents=True, exist_ok=True); a.out.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ("verdict", "failures", "notes", "overall_map50")}, indent=2))
    for c, v in res.items(): print(f"{c:15s} n_gt={v['n_gt']:4d} AP50={v['ap50'] if v['ap50'] is None else round(v['ap50'],3)} recall={v['recall'] if v['recall'] is None else round(v['recall'],3)}")
    return 0 if verdict in ("PASS", "SANITY_ONLY") else 1

if __name__ == "__main__":
    sys.exit(main())
