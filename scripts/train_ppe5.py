#!/usr/bin/env python3
"""Guarded training harness for the five-class PPE model (docs/weight-transfer-plan.md, option C).

Default is --dry-run: runs every pre-flight check, prints the plan, imports nothing heavy, loads no weights.
A real run (--smoke or --full) additionally needs ALL of:
  - config/training_authorization.yaml with rights, security and go-ahead all true
  - a local init-weights file whose SHA-256 matches the value pinned in config/train_ppe5.yaml (never downloaded here)
  - models/best.pt unchanged (SHA-256 checked before and after; it is never loaded)
  - the derived dataset passing structural checks, and a new empty run directory outside protected folders
  - the acceptance-threshold file matching its locked hash in docs/acceptance-thresholds.md
Ultralytics is imported only after every check passes.
"""
import argparse, datetime, hashlib, json, os, platform, random, re, shutil, subprocess, sys
from pathlib import Path
import yaml

FINAL = ["person", "helmet", "no_helmet", "safety_vest", "no_safety_vest"]
HERE = Path(__file__).resolve().parent
REPO = HERE.parent

def find_root():
    for p in HERE.resolve().parents:
        if (p / "raw_css_dataset").is_dir(): return p
    raise SystemExit("raw_css_dataset/ not found in any parent directory")

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

class Refusal(Exception): pass

def check_authorization(path):
    a = yaml.safe_load(Path(path).read_text()) if Path(path).exists() else None
    if not a: raise Refusal(f"{path} missing or empty")
    for k in ("rights_approved_for_poc", "security_isolation_approved", "training_go_ahead"):
        if a.get(k) is not True: raise Refusal(f"authorization '{k}' is not true")
    return a

def check_protected(cfg, root):
    pc = cfg["protected_checkpoint"]; p = root / pc["path"]
    if not p.exists():
        if pc.get("required_on_host", True) is False: return "absent-on-this-host (not required; main path never loads it)"
        raise Refusal(f"protected checkpoint {p} not found")
    got = sha256(p)
    if got != pc["sha256"]: raise Refusal(f"{pc['path']} SHA-256 changed: {got}")
    return got

def check_init(cfg, root):
    i = cfg["init"]
    if i.get("kind") != "coco_yolov8n": raise Refusal(f"unsupported init kind {i.get('kind')!r} (only coco_yolov8n)")
    if not i.get("weights_sha256"): raise Refusal("init.weights_sha256 is not pinned; obtain the weights (with permission) and record their SHA-256")
    p = root / i["weights_path"]
    if not p.is_file(): raise Refusal(f"init weights {p} not found (the harness never downloads)")
    got = sha256(p)
    if got != i["weights_sha256"]: raise Refusal(f"init weights SHA-256 mismatch: {got}")
    sys.path.insert(0, str(HERE)); import restricted_load as rl
    try: rl.verify(rl.scan_globals(p))
    except rl.UnsafeCheckpoint as e: raise Refusal(f"init weights failed the static pickle scan: {e}")
    return got

def check_dataset(cfg, root):
    d = (root / cfg["data"]).resolve(); y = yaml.safe_load(d.read_text())
    if y.get("nc") != 5 or list(y.get("names", [])) != FINAL: raise Refusal(f"data.yaml must have nc=5 and names {FINAL}")
    base = d.parent; counts = {}
    for s in ("train", "valid", "test"):
        imgs = {p.stem for p in (base / "images" / s).glob("*") if not p.name.startswith("._")}
        labs = {p.stem for p in (base / "labels" / s).glob("*.txt") if not p.name.startswith("._")}
        if imgs != labs: raise Refusal(f"{s}: image/label mismatch ({len(imgs ^ labs)} unpaired)")
        for lp in (base / "labels" / s).glob("*.txt"):
            if lp.name.startswith("._"): continue
            for line in lp.read_text().splitlines():
                p = line.split()
                if p and (len(p) != 5 or not 0 <= int(p[0]) < 5): raise Refusal(f"{lp.name}: bad label line {line!r}")
        counts[s] = len(imgs)
    if counts["train"] == 0: raise Refusal("no training images")
    m = base / "manifest.json"
    return counts, (sha256(m) if m.exists() else None)

def network_reachable(timeout=3.0):
    """True if an outbound connection succeeds (so the process is NOT network-isolated)."""
    import socket
    for host, port in (("1.1.1.1", 53), ("8.8.8.8", 53)):
        try:
            socket.create_connection((host, port), timeout=timeout).close(); return True
        except OSError: continue
    return False

def check_network_isolation(auth, reachable=network_reachable):
    """Approval condition: train only without network access. A host that cannot isolate needs an explicit waiver."""
    if not reachable(): return "isolated (no outbound connection)"
    if auth.get("network_isolation_waived") is True:
        return f"NOT isolated; waived by {auth.get('network_isolation_waived_by', 'owner')} on {auth.get('network_isolation_waived_on', '?')}"
    raise Refusal("network is reachable and network_isolation_waived is not true in the authorization file; "
                  "run inside scripts/run_isolated.sh or an equivalent, or have the owner record a waiver")

def check_thresholds():
    t = REPO / "config" / "acceptance_thresholds.yaml"; doc = (REPO / "docs" / "acceptance-thresholds.md").read_text()
    m = re.search(r"SHA-256 of that file at lock time: `([0-9a-f]{64})`", doc)
    if not m: raise Refusal("locked hash not found in docs/acceptance-thresholds.md")
    if sha256(t) != m.group(1): raise Refusal("acceptance_thresholds.yaml changed since it was locked")
    return m.group(1)

def check_out(cfg, root, name):
    out = (root / cfg["out_root"] / name).resolve()
    for bad in (root / "models", root / "raw_css_dataset"):
        if bad.resolve() == out or bad.resolve() in out.parents: raise Refusal(f"run directory may not be inside {bad}")
    if out.exists(): raise Refusal(f"run directory {out} already exists")
    return out

def preflight(cfg, root, auth_path, mode, run_name):
    """Return a dict of evidence. Real runs enforce everything; dry-run reports what blocks a real run."""
    ev, blockers = {}, []
    def step(key, fn, *a, hard=False):
        try: ev[key] = fn(*a)
        except Refusal as e:
            if hard or mode != "dry-run": raise
            blockers.append(f"{key}: {e}"); ev[key] = None
    step("authorization", check_authorization, auth_path)
    step("protected_checkpoint_sha256", check_protected, cfg, root, hard=True)   # always enforced
    step("init_weights_sha256", check_init, cfg, root)
    step("dataset", check_dataset, cfg, root, hard=True)
    step("thresholds_sha256", check_thresholds, hard=True)
    ev["run_dir"] = str(check_out(cfg, root, run_name))
    ev["blockers"] = blockers
    return ev

def versions():
    import importlib.metadata as m
    return {p: m.version(p) for p in ("ultralytics", "torch", "torchvision", "numpy", "opencv-python")}

def git_commit():
    try: return subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10).stdout.strip() or None
    except Exception: return None

def smoke_subset(cfg, root, out, fraction, seed):
    """Copy a small random subset of train (and valid) into the run dir; the real dataset is never touched."""
    base = (root / cfg["data"]).resolve().parent; rng = random.Random(seed)
    names = sorted(p.name for p in (base / "images" / "train").glob("*") if not p.name.startswith("._"))
    keep = rng.sample(names, max(8, int(len(names) * fraction)))
    d = out / "smoke_data"
    for split, items in (("train", keep), ("valid", sorted(p.name for p in (base / "images" / "valid").glob("*") if not p.name.startswith("._"))[:8])):
        (d / "images" / split).mkdir(parents=True); (d / "labels" / split).mkdir(parents=True)
        for n in items:
            shutil.copy2(base / "images" / split / n, d / "images" / split / n)
            shutil.copy2(base / "labels" / split / (Path(n).stem + ".txt"), d / "labels" / split / (Path(n).stem + ".txt"))
    (d / "data.yaml").write_text(f"path: {d}\ntrain: images/train\nval: images/valid\nnc: 5\nnames: {FINAL}\n")
    return d / "data.yaml"

def write_abs_data_yaml(cfg, root, out):
    """Real runs use a copy of data.yaml with an ABSOLUTE `path` inside the run folder.
    Ultralytics resolves a relative `path` (such as '.') against its own datasets directory, not the yaml's folder,
    which made the first Colab full run fail with 'images not found'. The dataset itself is never modified."""
    src = (root / cfg["data"]).resolve(); y = yaml.safe_load(src.read_text())
    y["path"] = str(src.parent)
    for k in ("train", "val", "test"):
        if k in y and not (src.parent / y[k]).is_dir(): raise Refusal(f"data.yaml {k} directory {src.parent / y[k]} not found")
    dst = out / "data_abs.yaml"; dst.write_text(yaml.safe_dump(y, sort_keys=False)); return dst

def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true"); g.add_argument("--smoke", action="store_true"); g.add_argument("--full", action="store_true")
    ap.add_argument("--config", type=Path, default=REPO / "config" / "train_ppe5.yaml")
    ap.add_argument("--authorization", type=Path, default=REPO / "config" / "training_authorization.yaml")
    ap.add_argument("--run-name")
    a = ap.parse_args(argv)
    mode = "smoke" if a.smoke else "full" if a.full else "dry-run"
    root = find_root(); cfg = yaml.safe_load(a.config.read_text())
    name = a.run_name or datetime.datetime.now(datetime.timezone.utc).strftime(f"{mode}-%Y%m%dT%H%M%SZ")
    try: ev = preflight(cfg, root, a.authorization, mode, name)
    except Refusal as e:
        print(f"REFUSED: {e}"); return 2
    print(json.dumps({k: v for k, v in ev.items() if k != "authorization"}, indent=2, default=str))
    if mode == "dry-run":
        try: print("network:", check_network_isolation(ev["authorization"] or {}))
        except Refusal as e: print("network: would REFUSE a real run:", e)
        print("DRY RUN: nothing loaded or written." + (f" A real run is blocked by {len(ev['blockers'])} item(s)." if ev["blockers"] else " Pre-flight would pass."))
        return 0 if not ev["blockers"] else 3

    try: ev["network"] = check_network_isolation(ev["authorization"])
    except Refusal as e:
        print(f"REFUSED: {e}"); return 2
    print("network:", ev["network"])
    out = Path(ev["run_dir"]); out.mkdir(parents=True)
    t = cfg["train"]; before = ev["protected_checkpoint_sha256"]
    record = dict(mode=mode, started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), git_commit=git_commit(),
                  python=platform.python_version(), platform=platform.platform(), versions=versions(), seed=cfg["seed"], config=cfg,
                  evidence=ev, authorization=ev["authorization"], protected_sha256_before=before)
    (out / "run_record.json").write_text(json.dumps(record, indent=2, default=str))
    os.environ.setdefault("YOLO_OFFLINE", "1")
    from ultralytics import YOLO, settings
    settings.update({"sync": False})
    data = str(smoke_subset(cfg, root, out, cfg["smoke"]["fraction"], cfg["seed"])) if mode == "smoke" else str(write_abs_data_yaml(cfg, root, out))
    common = dict(data=data, imgsz=t["imgsz"], batch=t["batch"], device=t["device"], workers=t["workers"], seed=cfg["seed"],
                  deterministic=t["deterministic"], amp=t["amp"], plots=t["plots"], patience=t["patience"], mosaic=t["mosaic"], project=str(out), exist_ok=False)
    import restricted_load as rl
    wpath = (root / cfg["init"]["weights_path"]).resolve()

    def model_from(path):
        """Build the architecture from the packaged yaml and copy tensors from a restricted-loaded checkpoint.
        Never uses Ultralytics' unrestricted .pt loader. Ultralytics copies only shape-matching tensors, so the
        80-class COCO head is dropped for our 5 classes."""
        src = rl.pick_model(rl.load_restricted(path))
        m = YOLO("yolov8n.yaml"); m.load(src)
        m.ckpt = {"loaded_by": "restricted_load", "source": str(path)}    # makes the trainer transfer these tensors into the nc=5 model
        return m

    s1 = dict(common, name="stage1", epochs=cfg["smoke"]["epochs"] if mode == "smoke" else t["stage1"]["epochs"], freeze=t["stage1"]["freeze"], lr0=t["stage1"]["lr0"])
    model_from(wpath).train(**s1)
    if mode == "full":
        s2 = dict(common, name="stage2", epochs=t["stage2"]["epochs"], lr0=t["stage2"]["lr0"])
        model_from(out / "stage1" / "weights" / "last.pt").train(**s2)
    last = sorted(out.glob("stage*/weights/last.pt"))[-1]
    after = check_protected(cfg, root)
    record.update(finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), protected_sha256_after=after,
                  final_checkpoint=str(last), final_checkpoint_sha256=sha256(last),
                  note="New checkpoint needs its own class map entry (ids 0-4 = person, helmet, no_helmet, safety_vest, no_safety_vest); never reuse the Hafizqaim map.")
    (out / "run_record.json").write_text(json.dumps(record, indent=2, default=str))
    print("done; final checkpoint", last, record["final_checkpoint_sha256"]); return 0

if __name__ == "__main__":
    sys.exit(main())
