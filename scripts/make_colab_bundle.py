#!/usr/bin/env python3
"""Build the upload bundle for Google Colab (writes only <workspace>/colab/).

Contains: the Git-tracked repo files, config/train_ppe5.colab.yaml, derived_ppe5/, weights/yolov8n.pt,
an empty raw_css_dataset/ marker, and bundle_manifest.json with the SHA-256 of every file.
NOT included: models/best.pt (unlicensed, unused), the raw dataset, the venv, runs/, the Git history.
"""
import hashlib, json, subprocess, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent; REPO = HERE.parent
def root():
    for p in HERE.parents:
        if (p / "raw_css_dataset").is_dir(): return p
    raise SystemExit("workspace root not found")
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def main():
    ws = root(); out = ws / "colab"; out.mkdir(exist_ok=True)
    tracked = subprocess.run(["git", "-C", str(REPO), "ls-files"], capture_output=True, text=True, check=True).stdout.split()
    files = {f"ws/Renewi_EHS_Lighthouse/{f}": REPO / f for f in tracked if (REPO / f).is_file()}
    for extra in ("config/train_ppe5.colab.yaml", "config/training_authorization.yaml", "config/train_ppe5.yaml"):
        files[f"ws/Renewi_EHS_Lighthouse/{extra}"] = REPO / extra          # include even if the latest edit is uncommitted
    for p in sorted((ws / "derived_ppe5").rglob("*")):
        if p.is_file() and not p.name.startswith("._"): files[f"ws/derived_ppe5/{p.relative_to(ws / 'derived_ppe5').as_posix()}"] = p
    w = ws / "weights" / "yolov8n.pt"
    if not w.exists(): sys.exit("weights/yolov8n.pt missing")
    files["ws/weights/yolov8n.pt"] = w
    forbidden = [k for k in files if "best.pt" in k or "raw_css_dataset/" in k or "/.venv/" in k]
    if forbidden: sys.exit(f"refusing to bundle {forbidden[:3]}")
    manifest = {k: sha(v) for k, v in sorted(files.items())}
    zp = out / "ppe5_colab_bundle.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for k, v in sorted(files.items()): z.write(v, k)
        z.writestr("ws/raw_css_dataset/.keep", ""); z.writestr("ws/models/.keep", "")
        z.writestr("bundle_manifest.json", json.dumps(dict(files=manifest, note="models/best.pt intentionally absent"), indent=2))
    print(f"{zp}  {zp.stat().st_size/1e6:.1f} MB  {len(files)} files  sha256 {sha(zp)}")

if __name__ == "__main__":
    main()
