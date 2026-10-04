#!/usr/bin/env python3
"""Create the S4 audit decision-log template from the viewer data (read-only inputs).
Queues: Q1 empty-label, Q2 cross-split families, Q3 NO-Safety Vest sample (seed 0),
Q4 tiny-box sample (seed 0). Decision columns are left blank on purpose."""
import csv, json, random
from pathlib import Path

def _find_root():
    for p in Path(__file__).resolve().parents:
        if (p / 'raw_css_dataset').is_dir():
            return p
    raise SystemExit('raw_css_dataset/ not found in any parent directory')
R = _find_root() / "reports"
if (R / "audit/audit_log.csv").exists():
    raise SystemExit("audit_log.csv already exists; refusing to overwrite recorded decisions "
                     "(move or rename it first if you really want a fresh template)")
d = json.loads((R / "dataset_viewer/data.js").read_text().split("=", 1)[1].rstrip().rstrip(";"))
names, ims = d["names"], d["images"]
nv = names.index("NO-Safety Vest")
rng = random.Random(0)
rows = []
def add(q, im, issue):
    rows.append([q, im["split"], im["name"], im["fam"], issue, "", "", "", "", ""])
for im in ims:
    if "empty-label" in im["flags"]: add("Q1-empty-label", im, "Is anyone/anything visible that should be labelled?")
for im in sorted((i for i in ims if "family-crosses-splits" in i["flags"]), key=lambda i: (i["fam"], i["split"])):
    add("Q2-cross-split", im, f"Family appears in {','.join(im['fam_splits'])}: confirm same source image")
q3 = [i for i in ims if any(b[0] == nv for b in i["boxes"])]
for im in sorted(rng.sample(q3, 60), key=lambda i: (i["split"], i["name"])):
    add("Q3-NO-Safety-Vest-sample", im, "Torso visible and clearly without vest? Box fits?")
q4 = [i for i in ims if "tiny-box" in i["flags"]]
for im in sorted(rng.sample(q4, 40), key=lambda i: (i["split"], i["name"])):
    add("Q4-tiny-box-sample", im, "Is the tiny box a real, assessable object?")
hdr = ["queue","split","filename","source_family","question","decision","annotation_or_class","reviewer","date","notes"]
with open(R / "audit/audit_log.csv", "w", newline="") as f:
    csv.writer(f).writerows([hdr] + rows)
import collections; print(collections.Counter(r[0] for r in rows))
