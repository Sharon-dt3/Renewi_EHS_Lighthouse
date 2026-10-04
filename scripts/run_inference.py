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


def draw(image_bgr, records):
    import cv2
    img = image_bgr.copy()
    for r in records:
        x1, y1, x2, y2 = (int(v) for v in r["xyxy"]); col = COLORS.get(r["class"], (255, 255, 255))[::-1]
        cv2.rectangle(img, (x1, y1), (x2, y2), col, 2)
        text = f"{r['class']} {r['confidence']:.2f}"
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(img, (x1, max(0, y1 - th - 6)), (x1 + tw + 4, max(th + 6, y1)), col, -1)
        cv2.putText(img, text, (x1 + 2, max(th + 2, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    return img


def load_model(checkpoint, config):
    from ppe.class_map import load_class_map
    import restricted_load as rl
    cmap = load_class_map(config, checkpoint)               # raises unless the exact SHA-256 is registered
    ck = rl.load_restricted(checkpoint)                      # static scan + allow-list, weights_only
    src = rl.pick_model(ck)
    names = dict(getattr(src, "names", {}))
    if names and {int(k): v for k, v in names.items()} != dict(cmap.labels):
        raise SystemExit(f"class names inside the checkpoint {names} do not match the registered map {dict(cmap.labels)}")
    from ultralytics import YOLO
    y = YOLO("yolov8n.yaml"); y.load(src)
    y.model = src.float().eval(); y.model.names = dict(cmap.labels)
    return y, cmap


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


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", type=Path, required=True); ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True); ap.add_argument("--config", type=Path, default=REPO / "config" / "classes.yaml")
    ap.add_argument("--conf", type=float, default=0.25); ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--device", default="cpu"); ap.add_argument("--every-seconds", type=float, default=2.0)
    ap.add_argument("--max-items", type=int, default=0, help="0 = no limit")
    a = ap.parse_args(argv)
    import cv2
    out = a.out.resolve()
    for bad in ("models", "raw_css_dataset", "derived_ppe5", "weights"):
        if bad in out.parts:
            sys.exit(f"refusing to write inside a protected folder ({bad})")
    model, cmap = load_model(a.checkpoint, a.config)
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
        res = model.predict(img, conf=a.conf, imgsz=a.imgsz, device=a.device, verbose=False)[0]
        b = res.boxes
        recs = detections_to_records(b.xyxy.cpu().numpy().tolist(), b.conf.cpu().numpy().tolist(), b.cls.cpu().numpy().astype(int).tolist(), dict(cmap.labels), w, h)
        cv2.imwrite(str(out / "annotated" / f"{name}.jpg"), draw(img, recs))
        (out / "pred_txt" / f"{name}.txt").write_text(yolo_lines(recs, index))
        summary.append({"image": name, "width": w, "height": h, "detections": recs}); n += 1
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
