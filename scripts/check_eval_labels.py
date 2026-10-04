#!/usr/bin/env python3
"""Validate a candidate evaluation set (read-only).

Expected layout:  <dir>/images/*.jpg|png   <dir>/labels/*.txt   <dir>/provenance.csv
Optional:         <dir>/image_sources.csv  with columns image,source_id

Checks: image/label pairing, YOLO format, class ids 0-4, normalised boxes, minimum box
sizes (px, from the guidelines), duplicate boxes, per-class counts vs targets, image size
spread, and provenance coverage. Exit code 1 if any hard error is found.
Does not run the independence check against training images (see build_group_split.py).

Usage: python scripts/check_eval_labels.py EVAL_DIR [--min-images 100]
"""
import argparse, collections, csv, sys
from pathlib import Path
from PIL import Image

CLASSES = ["person", "helmet", "no_helmet", "safety_vest", "no_safety_vest"]
MIN_SIDE = {"person": 12, "helmet": 8, "no_helmet": 12, "safety_vest": 12, "no_safety_vest": 24}
TARGET = {"person": 150, "helmet": 50, "no_helmet": 50, "safety_vest": 50, "no_safety_vest": 50}
PROV_COLS = ["source_id", "source_url", "licence", "licence_url", "author", "retrieved_date", "media_type", "split_group", "notes"]

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("eval_dir", type=Path)
    ap.add_argument("--min-images", type=int, default=100)
    a = ap.parse_args(argv)
    d = a.eval_dir
    errors, warns = [], []
    imgs = {p.stem: p for p in sorted((d / "images").glob("*")) if p.suffix.lower() in {".jpg", ".jpeg", ".png"} and not p.name.startswith("._")}
    labs = {p.stem: p for p in sorted((d / "labels").glob("*.txt")) if not p.name.startswith("._")}
    for s in sorted(set(imgs) - set(labs)): errors.append(f"{s}: image without label file")
    for s in sorted(set(labs) - set(imgs)): errors.append(f"{s}: label file without image")

    counts, sizes, empty = collections.Counter(), collections.Counter(), 0
    for s in sorted(set(imgs) & set(labs)):
        with Image.open(imgs[s]) as im: w, h = im.size
        sizes[(w, h)] += 1
        seen, n = set(), 0
        for i, line in enumerate(labs[s].read_text().splitlines(), 1):
            if not line.strip(): continue
            p = line.split()
            if len(p) != 5: errors.append(f"{s}:{i}: expected 5 fields, got {len(p)}"); continue
            try: c = int(p[0]); xc, yc, bw, bh = map(float, p[1:])
            except ValueError: errors.append(f"{s}:{i}: non-numeric"); continue
            if not 0 <= c < len(CLASSES): errors.append(f"{s}:{i}: class {c} not in 0-4"); continue
            if not (0 <= xc <= 1 and 0 <= yc <= 1 and 0 < bw <= 1 and 0 < bh <= 1): errors.append(f"{s}:{i}: box outside 0..1"); continue
            if xc - bw / 2 < -1e-6 or xc + bw / 2 > 1 + 1e-6 or yc - bh / 2 < -1e-6 or yc + bh / 2 > 1 + 1e-6:
                warns.append(f"{s}:{i}: box extends past image edge")
            name = CLASSES[c]
            if min(bw * w, bh * h) < MIN_SIDE[name]:
                errors.append(f"{s}:{i}: {name} box {bw*w:.0f}x{bh*h:.0f}px below minimum {MIN_SIDE[name]}px (unassessable; remove the label)")
            key = (c, round(xc, 3), round(yc, 3), round(bw, 3), round(bh, 3))
            if key in seen: errors.append(f"{s}:{i}: duplicate box")
            seen.add(key); counts[name] += 1; n += 1
        if n == 0: empty += 1

    n_img = len(set(imgs) & set(labs))
    if n_img < a.min_images: errors.append(f"only {n_img} images; target is at least {a.min_images}")
    for c in CLASSES:
        if counts[c] < TARGET[c]: errors.append(f"{c}: {counts[c]} instances; target is at least {TARGET[c]}")
    prov = d / "provenance.csv"
    if not prov.exists(): errors.append("provenance.csv missing")
    else:
        rows = list(csv.DictReader(open(prov)))
        miss = [c for c in PROV_COLS if rows and c not in rows[0]]
        if miss or not rows: errors.append(f"provenance.csv missing columns {miss} or empty")
        bad = [r["source_id"] for r in rows if r.get("source_id", "").startswith("EXAMPLE") or not r.get("licence")]
        if bad: errors.append(f"provenance rows with example/blank licence: {bad[:5]}")
        src = d / "image_sources.csv"
        if src.exists():
            known = {r["source_id"] for r in rows}
            for r in csv.DictReader(open(src)):
                if r["source_id"] not in known: errors.append(f"{r['image']}: source_id {r['source_id']} not in provenance.csv")
        else: warns.append("image_sources.csv missing: cannot confirm every image has a source")

    print(f"images={n_img}  background-only={empty}  image sizes={dict(sizes.most_common(3))}")
    print("instances:", {c: counts[c] for c in CLASSES})
    for w in warns[:20]: print("WARN ", w)
    for e in errors[:50]: print("ERROR", e)
    print(f"{len(errors)} errors, {len(warns)} warnings")
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
