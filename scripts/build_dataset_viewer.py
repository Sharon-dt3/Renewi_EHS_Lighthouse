#!/usr/bin/env python3
"""Build a static, read-only original-resolution viewer for a YOLOv8 dataset.

Reads images/labels/data.yaml from the dataset directory and writes only
reports/dataset_viewer/{index.html,data.js,summary.json}. Images are NOT copied
or re-encoded: the page loads the original files by relative path and draws the
boxes on a canvas at native pixel size (zoom is nearest-neighbour).

Usage:
    .venv/bin/python utils/build_dataset_viewer.py [--dataset DIR] [--out DIR]
Open reports/dataset_viewer/index.html in Safari or Chrome.
"""
import argparse
import collections
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import quote

import yaml
from PIL import Image

def _find_root():
    # workspace root = the nearest parent that contains the raw dataset (it sits outside this repo)
    for p in Path(__file__).resolve().parents:
        if (p / "raw_css_dataset").is_dir():
            return p
    raise SystemExit("raw_css_dataset/ not found in any parent directory")
ROOT = _find_root()
DEFAULT_DATASET = ROOT / "raw_css_dataset" / "Construction Site Safety.v27-yolov8.yolov8"
DEFAULT_OUT = ROOT / "reports" / "dataset_viewer"
SPLITS = ["train", "valid", "test"]
IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp"}
TINY_PX = 16          # a box with either side under this many pixels
TINY_AREA = 0.001     # or under this fraction of image area is flagged tiny
FAMILY_RE = re.compile(r"^(?P<fam>.+?)[._]rf[._][0-9a-f]{32}$")


def family_of(stem: str) -> str:
    """Roboflow names augmented copies <source>_jpg.rf.<hash>; group by <source>."""
    m = FAMILY_RE.match(stem)
    return m.group("fam") if m else stem


def read_labels(path: Path, n_classes: int, w: int, h: int):
    boxes, problems = [], []
    if not path.exists():
        return None, ["missing label file"]
    for i, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split()
        try:
            cls = int(parts[0])
            vals = [float(v) for v in parts[1:]]
        except ValueError:
            problems.append(f"line {i}: not numeric")
            continue
        if len(vals) != 4:
            problems.append(f"line {i}: {len(vals)} coords (polygon/segment?)")
            continue
        if not 0 <= cls < n_classes:
            problems.append(f"line {i}: class {cls} out of range")
            continue
        xc, yc, bw, bh = vals
        if not (0 <= xc <= 1 and 0 <= yc <= 1 and 0 < bw <= 1 and 0 < bh <= 1):
            problems.append(f"line {i}: box outside 0..1")
        x1, y1 = (xc - bw / 2) * w, (yc - bh / 2) * h
        boxes.append([cls, round(x1, 1), round(y1, 1), round(bw * w, 1), round(bh * h, 1)])
    return boxes, problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    ds, out = args.dataset.resolve(), args.out.resolve()

    if out == ds or ds in out.parents:
        sys.exit("Refusing to write inside the dataset directory (read-only viewer).")
    cfg = yaml.safe_load((ds / "data.yaml").read_text())
    names = cfg["names"]

    images, fam_splits = [], collections.defaultdict(set)
    fam_count = collections.Counter()
    for split in SPLITS:
        # two layouts: <split>/images (Roboflow) or images/<split> (derived dataset)
        flat = (ds / "images" / split).is_dir()
        img_dir = ds / "images" / split if flat else ds / split / "images"
        lab_dir = ds / "labels" / split if flat else ds / split / "labels"
        if not img_dir.is_dir():
            continue
        for p in sorted(img_dir.iterdir()):
            if p.name.startswith("._") or p.suffix.lower() not in IMG_EXT:
                continue
            with Image.open(p) as im:
                w, h = im.size
            boxes, problems = read_labels(lab_dir / (p.stem + ".txt"), len(names), w, h)
            fam = family_of(p.stem)
            fam_splits[fam].add(split)
            fam_count[fam] += 1
            rel = os.path.relpath(p, out)
            images.append({
                "id": len(images), "split": split, "name": p.name, "fam": fam,
                "src": quote(rel.replace(os.sep, "/")), "w": w, "h": h,
                "boxes": boxes or [], "problems": problems, "nolabel": boxes is None,
            })

    # flags (computed from geometry only; a flag is a prompt to look, not a verdict)
    for im in images:
        tiny = [b for b in im["boxes"]
                if b[3] < TINY_PX or b[4] < TINY_PX or (b[3] * b[4]) / (im["w"] * im["h"]) < TINY_AREA]
        flags = []
        if im["nolabel"]:
            flags.append("missing-label-file")
        elif not im["boxes"]:
            flags.append("empty-label")
        if tiny:
            flags.append("tiny-box")
        if im["problems"]:
            flags.append("format-problem")
        if fam_count[im["fam"]] > 1:
            flags.append("augmented-family")
        if len(fam_splits[im["fam"]]) > 1:
            flags.append("family-crosses-splits")
        im["flags"] = flags
        im["fam_n"] = fam_count[im["fam"]]
        im["fam_splits"] = sorted(fam_splits[im["fam"]])

    per_class = collections.Counter(b[0] for im in images for b in im["boxes"])
    leak = {f: sorted(s) for f, s in fam_splits.items() if len(s) > 1}
    summary = {
        "dataset": str(ds), "images": {s: sum(i["split"] == s for i in images) for s in SPLITS},
        "total_images": len(images), "classes": {names[k]: v for k, v in sorted(per_class.items())},
        "flag_counts": dict(collections.Counter(f for i in images for f in i["flags"])),
        "source_families": len(fam_count),
        "families_with_multiple_copies": sum(1 for c in fam_count.values() if c > 1),
        "families_crossing_splits": len(leak),
        "images_in_cross_split_families": sum(i["fam"] in leak for i in images),
        "image_sizes": [list(k) for k in {(i["w"], i["h"]) for i in images}],
    }

    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    (out / "data.js").write_text(
        "window.VIEWER_DATA = " + json.dumps({"names": names, "images": images, "tiny_px": TINY_PX}) + ";\n")
    (out / "index.html").write_text(HTML)
    print(json.dumps(summary, indent=2))
    print(f"\nWrote {out}/index.html")
    return 0


HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Dataset viewer (read-only)</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--bg:#fff;--fg:#1a1a1a;--mut:#666;--bd:#d0d0d0;--pn:#f5f5f5;--hl:#e8f0fe}
@media(prefers-color-scheme:dark){:root{--bg:#161616;--fg:#e8e8e8;--mut:#999;--bd:#3a3a3a;--pn:#202020;--hl:#26324a}}
*{box-sizing:border-box}body{margin:0;font:13px system-ui,sans-serif;background:var(--bg);color:var(--fg);display:flex;height:100vh}
#side{width:340px;border-right:1px solid var(--bd);display:flex;flex-direction:column;background:var(--pn)}
#ctl{padding:8px;border-bottom:1px solid var(--bd);display:flex;flex-direction:column;gap:6px}
#ctl select,#ctl input{width:100%;padding:4px}
#list{overflow:auto;flex:1}
.row{padding:4px 8px;border-bottom:1px solid var(--bd);cursor:pointer;font-size:12px;word-break:break-all}
.row:hover{background:var(--hl)}.row.sel{background:var(--hl);font-weight:600}
.fl{display:inline-block;background:var(--bd);border-radius:3px;padding:0 4px;margin:1px;font-size:10px}
#main{flex:1;display:flex;flex-direction:column;min-width:0}
#bar{padding:8px;border-bottom:1px solid var(--bd);display:flex;flex-wrap:wrap;gap:10px;align-items:center}
#wrap{flex:1;overflow:auto;background:#444;display:flex}
canvas{image-rendering:pixelated;margin:auto;display:block}
#info{width:300px;border-left:1px solid var(--bd);padding:8px;overflow:auto;background:var(--pn)}
#body{flex:1;display:flex;min-height:0}
.ann{padding:3px 4px;cursor:pointer;border-bottom:1px solid var(--bd)}.ann:hover{background:var(--hl)}
.sw{display:inline-block;width:10px;height:10px;margin-right:4px;vertical-align:middle}
h4{margin:8px 0 4px}small{color:var(--mut)}
</style></head><body>
<div id="side"><div id="ctl">
 <b>Read-only dataset viewer</b>
 <select id="split"><option value="">All splits</option></select>
 <select id="flag"><option value="">All images</option></select>
 <select id="cls"><option value="">Any class</option></select>
 <input id="q" placeholder="filename contains…">
 <small id="count"></small>
</div><div id="list"></div></div>
<div id="main"><div id="bar">
 <label>Zoom <input id="zoom" type="range" min="1" max="8" step="0.5" value="1.5"> <span id="zv">1.5x</span></label>
 <label><input type="checkbox" id="lbl" checked> labels</label>
 <label><input type="checkbox" id="raw"> hide boxes</label>
 <span id="cls-toggles"></span>
 <small>←/→ previous/next · click an annotation to zoom to it</small>
</div><div id="body"><div id="wrap"><canvas id="cv"></canvas></div><div id="info"></div></div></div>
<script src="data.js"></script>
<script>
const D=window.VIEWER_DATA,N=D.names,IM=D.images;
const COL=['#e6194b','#3cb44b','#ffe119','#4363d8','#f58231','#911eb4','#46f0f0','#f032e6','#bcf60c','#fabebe'];
const $=id=>document.getElementById(id);
let view=[],cur=-1,img=new Image(),hidden=new Set(),focus=null;
const splits=[...new Set(IM.map(i=>i.split))];splits.forEach(s=>$('split').add(new Option(s,s)));
[...new Set(IM.flatMap(i=>i.flags))].sort().forEach(f=>$('flag').add(new Option(f,f)));
N.forEach((n,i)=>{$('cls').add(new Option(n,i));
 const l=document.createElement('label');l.innerHTML=`<span class="sw" style="background:${COL[i%10]}"></span><input type="checkbox" checked data-c="${i}">${n} `;
 l.querySelector('input').onchange=e=>{e.target.checked?hidden.delete(i):hidden.add(i);draw()};$('cls-toggles').append(l)});
function filt(){const s=$('split').value,f=$('flag').value,c=$('cls').value,q=$('q').value.toLowerCase();
 view=IM.filter(i=>(!s||i.split===s)&&(!f||i.flags.includes(f))&&(c===''||i.boxes.some(b=>b[0]==c))&&(!q||i.name.toLowerCase().includes(q)));
 $('count').textContent=view.length+' of '+IM.length+' images';
 $('list').innerHTML='';view.slice(0,1500).forEach((i,k)=>{const d=document.createElement('div');d.className='row';d.dataset.k=k;
  d.innerHTML=`${i.split}/${i.name.slice(0,40)} `+i.flags.map(f=>`<span class="fl">${f}</span>`).join('');d.onclick=()=>show(k);$('list').append(d)});
 if(view.length>1500)$('list').append(Object.assign(document.createElement('div'),{className:'row',textContent:'… list truncated at 1500; narrow filters'}));
 cur=-1;if(view.length)show(0)}
function show(k){cur=k;focus=null;document.querySelectorAll('.row').forEach(r=>r.classList.toggle('sel',r.dataset.k==k));
 const i=view[k];img=new Image();img.onload=()=>{draw();info()};img.src=i.src;}
function draw(){if(cur<0)return;const i=view[cur],z=+$('zoom').value;$('zv').textContent=z+'x';
 const cv=$('cv'),x=cv.getContext('2d');cv.width=i.w*z;cv.height=i.h*z;x.imageSmoothingEnabled=false;
 x.drawImage(img,0,0,i.w*z,i.h*z);if($('raw').checked)return;x.lineWidth=2;x.font='12px sans-serif';
 i.boxes.forEach((b,n)=>{if(hidden.has(b[0]))return;const c=COL[b[0]%10];x.strokeStyle=c;x.lineWidth=focus===n?4:2;
  x.strokeRect(b[1]*z,b[2]*z,b[3]*z,b[4]*z);
  if($('lbl').checked){const t=N[b[0]];x.fillStyle=c;const w=x.measureText(t).width+4;
   const ty=b[2]*z>14?b[2]*z-14:b[2]*z;x.fillRect(b[1]*z,ty,w,14);x.fillStyle='#000';x.fillText(t,b[1]*z+2,ty+11)}})}
function info(){const i=view[cur];let h=`<b>${i.split}/${i.name}</b><br><small>${i.w}×${i.h}px</small>`;
 h+=`<h4>Flags</h4>`+(i.flags.map(f=>`<span class="fl">${f}</span>`).join('')||'<small>none</small>');
 h+=`<h4>Source family</h4><small>${i.fam}<br>${i.fam_n} cop${i.fam_n==1?'y':'ies'} · splits: ${i.fam_splits.join(', ')}</small>`;
 if(i.problems.length)h+=`<h4>Format problems</h4><small>${i.problems.join('<br>')}</small>`;
 h+=`<h4>Annotations (${i.boxes.length})</h4>`;
 i.boxes.forEach((b,n)=>{h+=`<div class="ann" data-n="${n}"><span class="sw" style="background:${COL[b[0]%10]}"></span>${N[b[0]]} <small>${Math.round(b[3])}×${Math.round(b[4])}px @ ${Math.round(b[1])},${Math.round(b[2])}${(b[3]<D.tiny_px||b[4]<D.tiny_px)?' · tiny':''}</small></div>`});
 $('info').innerHTML=h;$('info').querySelectorAll('.ann').forEach(a=>a.onclick=()=>zoomTo(+a.dataset.n))}
function zoomTo(n){const i=view[cur],b=i.boxes[n];focus=n;
 const z=Math.max(1,Math.min(8,Math.floor(300/Math.max(b[3],b[4],20)*2)/2));$('zoom').value=z;draw();
 const w=$('wrap');w.scrollLeft=(b[1]+b[3]/2)*z-w.clientWidth/2;w.scrollTop=(b[2]+b[4]/2)*z-w.clientHeight/2}
['split','flag','cls'].forEach(id=>$(id).onchange=filt);$('q').oninput=filt;
['zoom','lbl','raw'].forEach(id=>$(id).oninput=draw);
document.addEventListener('keydown',e=>{if(e.target.tagName==='INPUT'&&e.target.type==='text')return;
 if(e.key==='ArrowRight'&&cur<view.length-1)show(cur+1);if(e.key==='ArrowLeft'&&cur>0)show(cur-1)});
filt();
</script></body></html>
"""

if __name__ == "__main__":
    raise SystemExit(main())
