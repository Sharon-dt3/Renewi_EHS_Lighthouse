#!/usr/bin/env python3
"""Run a registered five-class checkpoint on images (or sampled video frames) and draw the detections.

Safety: the checkpoint's SHA-256 must be registered in config/classes.yaml (so its class ids are trusted), the file is
statically scanned and loaded only through scripts/restricted_load.py, and nothing is downloaded. Intended to run inside
scripts/run_isolated.sh (no network). Writes only to --out.

Outputs in --out:  annotated/<name>.jpg   detections.json   pred_txt/<name>.txt (YOLO "cls xc yc w h conf", for evaluate_ppe5.py)

Usage:
  scripts/run_isolated.sh .venv/bin/python scripts/run_inference.py \
      --checkpoint ../models/last.pt --input ../derived_ppe5/images/test --out ../reports/inference/derived_test
"""
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(HERE))

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp"}
VID_EXT = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
COLORS = {"person": (60, 200, 60), "helmet": (255, 160, 0), "no_helmet": (255, 0, 0),
          "safety_vest": (0, 200, 255), "no_safety_vest": (255, 0, 200)}


def detections_to_records(boxes_xyxy, confs, class_ids, labels, width, height):
    """Plain-Python detection records (pixel and normalised coordinates). `labels` maps class id -> internal label."""
    out = []
    for (x1, y1, x2, y2), conf, cid in zip(boxes_xyxy, confs, class_ids):
        label = labels.get(int(cid))
        if label is None:
            continue                      # an id that is not in the registered map is never reported
        out.append({"class": label, "confidence": round(float(conf), 4),
                    "xyxy": [round(float(v), 1) for v in (x1, y1, x2, y2)],
                    "yolo": [round(((x1 + x2) / 2) / width, 6), round(((y1 + y2) / 2) / height, 6),
                             round((x2 - x1) / width, 6), round((y2 - y1) / height, 6)]})
    return out


def yolo_lines(records, class_index):
    return "".join(f"{class_index[r['class']]} {r['yolo'][0]} {r['yolo'][1]} {r['yolo'][2]} {r['yolo'][3]} {r['confidence']}\n"
                   for r in records)


STATE_COLORS = {"COMPLIANT": (60, 200, 60), "UNKNOWN": (160, 160, 160), "HELMET_MISSING": (255, 0, 0),
                "VEST_MISSING": (255, 0, 0), "HELMET_AND_VEST_MISSING": (255, 0, 0)}


def draw(image_bgr, records, people=None):
    """Draw detections; `people` (list of {"box","state"}) adds a state tag under each worker's box."""
    import cv2
    img = image_bgr.copy()
    for p in people or []:
        x1, y1, x2, y2 = (int(v) for v in p["box"]); col = STATE_COLORS.get(p["state"], (255, 255, 255))[::-1]
        text = p["state"] + (" + ZONE_INCURSION" if p.get("zone_incursion") else "")
        cv2.putText(img, text, (x1 + 3, min(img.shape[0] - 4, y2 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, col, 2, cv2.LINE_AA)
    for r in records:
        x1, y1, x2, y2 = (int(v) for v in r["xyxy"]); col = COLORS.get(r["class"], (255, 255, 255))[::-1]
        cv2.rectangle(img, (x1, y1), (x2, y2), col, 2)
        text = f"{r['class']} {r['confidence']:.2f}"
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(img, (x1, max(0, y1 - th - 6)), (x1 + tw + 4, max(th + 6, y1)), col, -1)
        cv2.putText(img, text, (x1 + 2, max(th + 2, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    return img


from ppe.yolo_detector import load_model  # noqa: E402,F401  (shared adapter; kept here under the same name)


def frames_from_video(path, every_seconds):
    import cv2
    cap = cv2.VideoCapture(str(path)); fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    step = max(1, int(round(fps * every_seconds))); i = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if i % step == 0:
            yield f"{Path(path).stem}_t{i / fps:06.2f}s", frame
        i += 1
    cap.release()


def load_zone_for_source(zones_path, clip_id, source_path):
    """Load the clip's zone and check it against the real source frame size BEFORE any model is loaded.
    Exits with one clear line instead of a traceback."""
    import cv2
    from ppe.zone import ZoneIncursionDetector
    from ppe.zone_config import ZoneConfigError, load_zone
    try:
        zone = load_zone(zones_path, clip_id)
        if Path(source_path).suffix.lower() in VID_EXT:
            cap = cv2.VideoCapture(str(source_path))
            w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
        else:
            img = cv2.imread(str(source_path))
            if img is None:
                raise ValueError(f"cannot read {source_path}")
            h, w = img.shape[:2]
        if not (w and h):
            raise ValueError(f"cannot determine the frame size of {source_path}")
        zone.validate_frame(w, h)
    except (ZoneConfigError, ValueError) as error:
        sys.exit(f"zone error for clip '{clip_id}': {error}")
    return ZoneIncursionDetector(zone)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", type=Path, required=True); ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True); ap.add_argument("--config", type=Path, default=REPO / "config" / "classes.yaml")
    ap.add_argument("--conf", type=float, default=0.25); ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--device", default="cpu"); ap.add_argument("--every-seconds", type=float, default=2.0)
    ap.add_argument("--max-items", type=int, default=0, help="0 = no limit")
    ap.add_argument("--zones", type=Path, help="Per-clip source-pixel polygon YAML; omitted = PPE only")
    ap.add_argument("--clip-id", help="Zone config key (default: input filename stem)")
    a = ap.parse_args(argv)
    if a.clip_id and not a.zones:
        ap.error("--clip-id requires --zones")
    if a.zones and a.input.is_dir():
        ap.error("--zones requires one clip or source image, not an image directory")
    zone = load_zone_for_source(a.zones, a.clip_id or a.input.stem, a.input) if a.zones else None
    import cv2
    out = a.out.resolve()
    for bad in ("models", "raw_css_dataset", "derived_ppe5", "weights"):
        if bad in out.parts:
            sys.exit(f"refusing to write inside a protected folder ({bad})")
    import yaml
    from ppe.analysis import FrameAnalyzer, to_dict
    from ppe.yolo_detector import load_yolo_detector
    rules = yaml.safe_load((REPO / "config" / "rules.yaml").read_text())
    detector, cmap = load_yolo_detector(a.checkpoint, a.config, a.device, a.imgsz, a.conf)
    analyzer = FrameAnalyzer(detector, cmap, min_confidence=a.conf, min_negative_confidence=max(a.conf, rules["min_negative_confidence"]),
                             zone_detector=zone)
    index = {v: k for k, v in cmap.labels.items()}
    (out / "annotated").mkdir(parents=True, exist_ok=True); (out / "pred_txt").mkdir(exist_ok=True)

    if a.input.is_dir():
        items = ((p.stem, cv2.imread(str(p))) for p in sorted(a.input.iterdir()) if p.suffix.lower() in IMG_EXT and not p.name.startswith("._"))
    elif a.input.suffix.lower() in VID_EXT:
        items = frames_from_video(a.input, a.every_seconds)
    else:
        items = [(a.input.stem, cv2.imread(str(a.input)))]
    summary, n = [], 0
    for name, img in items:
        if img is None:
            continue
        h, w = img.shape[:2]
        result = analyzer.analyze(name, img)
        recs = detections_to_records([[d.box.x1, d.box.y1, d.box.x2, d.box.y2] for d in result.detections], [d.confidence for d in result.detections],
                                     [index[d.label] for d in result.detections], dict(cmap.labels), w, h)
        analysis = to_dict(result)
        cv2.imwrite(str(out / "annotated" / f"{name}.jpg"), draw(img, recs, analysis["people"]))
        (out / "pred_txt" / f"{name}.txt").write_text(yolo_lines(recs, index))
        summary.append({"image": name, "width": w, "height": h, "detections": recs, "analysis": analysis}); n += 1
        if a.max_items and n >= a.max_items:
            break
    (out / "detections.json").write_text(json.dumps({"checkpoint_sha256": cmap.checkpoint_sha256, "conf": a.conf, "imgsz": a.imgsz, "items": summary}, indent=1))
    counts = {}
    for s in summary:
        for r in s["detections"]:
            counts[r["class"]] = counts.get(r["class"], 0) + 1
    print(f"{n} items -> {out}\ndetections by class: {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
