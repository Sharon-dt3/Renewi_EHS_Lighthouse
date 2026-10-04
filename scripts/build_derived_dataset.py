#!/usr/bin/env python3
"""Build the derived five-class PPE dataset from CSS v27 (raw data is never modified).

Default is a DRY RUN: prints what would be kept/dropped and writes nothing.
Use --write to create the dataset at --out (default: <workspace>/derived_ppe5).

Inputs : raw CSS v27 (YOLOv8), reports/split/split_manifest.csv, optional audit log.
Classes: person 0, helmet 1, no_helmet 2, safety_vest 3, no_safety_vest 4
         (raw Person5, Hardhat0, NO-Hardhat2, Safety Vest7, NO-Safety Vest4).
         Mask, NO-Mask, Safety Cone, machinery, vehicle are dropped.
Rules  : boxes smaller than a per-class minimum side (px at 640x640) are dropped.
         A dropped box leaves that object unlabelled, so the effect is reported.
Audit  : only decisions from a HUMAN reviewer are applied (rows signed by the AI
         first pass are ignored). 'drop-image' removes the image, 'drop-annotation'
         removes the annotation only when --apply-audit is given and the row names
         a specific class/box; otherwise those rows are reported, not applied.
Never  : create no_safety_vest from missing detections.
"""
import argparse, collections, csv, hashlib, json, shutil, sys
from pathlib import Path

def _find_root():
    for p in Path(__file__).resolve().parents:
        if (p / "raw_css_dataset").is_dir():
            return p
    raise SystemExit("raw_css_dataset/ not found in any parent directory")
ROOT = _find_root()
DS = ROOT / "raw_css_dataset" / "Construction Site Safety.v27-yolov8.yolov8"
RAW = ['Hardhat','Mask','NO-Hardhat','NO-Mask','NO-Safety Vest','Person','Safety Cone','Safety Vest','machinery','vehicle']
FINAL = ["person", "helmet", "no_helmet", "safety_vest", "no_safety_vest"]
MAP = {"Person": 0, "Hardhat": 1, "NO-Hardhat": 2, "Safety Vest": 3, "NO-Safety Vest": 4}
# defaults come from the audit: real NO-Safety Vest boxes were torso-sized; bad ones were 8-15 px
MIN_SIDE = {"person": 12, "helmet": 8, "no_helmet": 8, "safety_vest": 12, "no_safety_vest": 24}
AI_REVIEWER = "Claude (AI first pass"

def human_decisions(path):
    out = {}
    if path and Path(path).exists():
        for r in csv.DictReader(open(path)):
            if r["decision"] and r["reviewer"] and not r["reviewer"].startswith(AI_REVIEWER):
                out.setdefault(r["filename"], []).append(r)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, default=ROOT / "reports/split/split_manifest.csv")
    ap.add_argument("--audit", type=Path, default=ROOT / "reports/audit/audit_log.csv")
    ap.add_argument("--out", type=Path, default=ROOT / "derived_ppe5")
    ap.add_argument("--min-no-vest", type=int, default=MIN_SIDE["no_safety_vest"])
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    MIN_SIDE["no_safety_vest"] = a.min_no_vest
    out = a.out.resolve()
    if DS in out.parents or out == DS:
        sys.exit("Refusing to write inside the raw dataset directory.")
    if a.write and out.exists() and any(out.iterdir()):
        sys.exit(f"{out} exists and is not empty; refusing to overwrite.")

    hd = human_decisions(a.audit)
    dropped_by_human = {n for n, rs in hd.items() if any(r["decision"] == "drop-image" for r in rs)}
    rows = [r for r in csv.DictReader(open(a.manifest)) if r["role"] in ("train", "eval")]
    kept = collections.defaultdict(list)                  # split -> [(row, labels)]
    stat = collections.defaultdict(collections.Counter)   # split -> counters
    cls_ct = collections.defaultdict(collections.Counter)
    removed = collections.Counter()
    for r in rows:
        if r["image"] in dropped_by_human:
            removed["images_dropped_by_human_audit"] += 1; continue
        split = "train" if r["role"] == "train" else r["new_split"]
        stem = r["image"].rsplit(".", 1)[0]
        lab = DS / r["old_split"] / "labels" / f"{stem}.txt"
        new = []
        for l in (lab.read_text().splitlines() if lab.exists() else []):
            p = l.split()
            if len(p) != 5: removed["malformed_lines"] += 1; continue
            name = RAW[int(p[0])]
            if name not in MAP: removed[f"other_class:{name}"] += 1; continue
            c = MAP[name]; w, h = float(p[3]) * 640, float(p[4]) * 640
            if min(w, h) < MIN_SIDE[FINAL[c]]:
                removed[f"too_small:{FINAL[c]}"] += 1; continue
            new.append(f"{c} {p[1]} {p[2]} {p[3]} {p[4]}"); cls_ct[split][FINAL[c]] += 1
        kept[split].append((r, new))
        stat[split]["images"] += 1
        if not new: stat[split]["images_without_target_boxes"] += 1

    print("DRY RUN" if not a.write else "WRITING", "->", out)
    for s in ("train", "valid", "test"):
        print(f"{s:6s} images={stat[s]['images']:5d} background-only={stat[s]['images_without_target_boxes']:4d}",
              {c: cls_ct[s][c] for c in FINAL})
    print("removed:", dict(removed))
    print("human audit decisions available:", sum(len(v) for v in hd.values()),
          "(AI first-pass rows are not applied)")
    if not a.write:
        return 0

    files = {}
    for s, items in kept.items():
        (out / "images" / s).mkdir(parents=True, exist_ok=True); (out / "labels" / s).mkdir(parents=True, exist_ok=True)
        for r, lines in items:
            src = DS / r["old_split"] / "images" / r["image"]
            dst = out / "images" / s / r["image"]
            shutil.copy2(src, dst)
            (out / "labels" / s / (r["image"].rsplit(".", 1)[0] + ".txt")).write_text("\n".join(lines) + ("\n" if lines else ""))
            files[f"images/{s}/{r['image']}"] = hashlib.sha256(dst.read_bytes()).hexdigest()
    (out / "data.yaml").write_text("path: .\ntrain: images/train\nval: images/valid\ntest: images/test\n"
                                   f"nc: {len(FINAL)}\nnames: {FINAL}\n")
    (out / "ATTRIBUTION.md").write_text(
        "# Attribution and changes\n\nSource: Construction Site Safety Dataset (v27), Roboflow Universe Projects.\n"
        "URL: https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety\n"
        "License: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)\n\n"
        "## Changes made (CC BY 4.0 requires indicating changes)\n"
        "- Kept only Person, Hardhat, NO-Hardhat, Safety Vest, NO-Safety Vest; remapped to 5 classes.\n"
        "- Dropped Mask, NO-Mask, Safety Cone, machinery and vehicle annotations.\n"
        f"- Dropped annotations below minimum box size (px at 640): {MIN_SIDE}.\n"
        "- Re-split by source photo; held-out splits keep one image per source photo.\n"
        "- No endorsement by the original author is implied.\n")
    (out / "manifest.json").write_text(json.dumps(dict(
        source=str(DS), split_manifest=str(a.manifest), min_side_px=MIN_SIDE, removed=dict(removed),
        images={s: stat[s]["images"] for s in stat}, classes={s: dict(cls_ct[s]) for s in cls_ct},
        sha256=files), indent=2))
    print("wrote", len(files), "images")
    return 0

if __name__ == "__main__":
    sys.exit(main())
