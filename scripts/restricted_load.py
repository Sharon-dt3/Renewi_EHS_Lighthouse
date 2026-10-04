"""Restricted loading of PyTorch .pt checkpoints (docs/weight-transfer-plan.md section 4).

1. Statically list every GLOBAL the pickle would import (pickletools; nothing is executed or imported).
2. Refuse unless every global is on the allow-list of plain tensor/module classes.
3. Only then call torch.load(weights_only=True) with exactly those classes registered.
No blanket allow-list, no weights_only=False, no Ultralytics YOLO() loader.
"""
import collections, importlib, pickletools, zipfile
from pathlib import Path

ALLOWED_EXACT = {
    "__builtin__.set", "builtins.set", "collections.OrderedDict", "torch.Size",
    "torch._utils._rebuild_parameter", "torch._utils._rebuild_tensor_v2",
    "torch.FloatStorage", "torch.HalfStorage", "torch.LongStorage", "torch.IntStorage", "torch.DoubleStorage",
    "ultralytics.nn.tasks.DetectionModel",
}
ALLOWED_PREFIXES = ("torch.nn.modules.", "ultralytics.nn.modules.")
# never allowed, even if a prefix above would match
DENY_FRAGMENTS = ("os.", "posix.", "subprocess", "builtins.eval", "builtins.exec", "builtins.getattr", "__import__", "sys.", "shutil", "socket", "pty", "importlib")

class UnsafeCheckpoint(Exception): pass

def scan_globals(path):
    z = zipfile.ZipFile(path)
    pkls = [n for n in z.namelist() if n.endswith("data.pkl")]
    if len(pkls) != 1: raise UnsafeCheckpoint(f"expected exactly one data.pkl, found {pkls}")
    data = z.read(pkls[0]); found = collections.Counter(); strs = []
    for op, arg, _ in pickletools.genops(data):
        if op.name in ("SHORT_BINUNICODE", "BINUNICODE", "UNICODE"): strs.append(arg)
        if op.name == "GLOBAL": found[arg.replace(" ", ".", 1)] += 1
        elif op.name == "STACK_GLOBAL":
            if len(strs) < 2: raise UnsafeCheckpoint("STACK_GLOBAL without two strings")
            found[f"{strs[-2]}.{strs[-1]}"] += 1
        elif op.name in ("REDUCE", "BUILD", "OBJ", "NEWOBJ", "INST", "NEWOBJ_EX"): pass   # constructors of the globals above
    return found

def is_allowed(name):
    if any(f in name for f in DENY_FRAGMENTS): return False
    return name in ALLOWED_EXACT or name.startswith(ALLOWED_PREFIXES)

def verify(found):
    bad = sorted(n for n in found if not is_allowed(n))
    if bad: raise UnsafeCheckpoint(f"checkpoint references globals outside the allow-list: {bad}")

def _resolve(name):
    if name.startswith("__builtin__."): name = "builtins." + name.split(".", 1)[1]
    mod, _, attr = name.rpartition(".")
    return getattr(importlib.import_module(mod), attr)

def load_restricted(path):
    """Return the checkpoint object after the static scan passes. Raises UnsafeCheckpoint otherwise."""
    import torch
    found = scan_globals(path); verify(found)
    classes = []
    for n in found:
        if n.startswith(("torch.nn.modules.", "ultralytics.nn.", "builtins.", "__builtin__.", "collections.")):
            try: classes.append(_resolve(n))
            except (ImportError, AttributeError) as e: raise UnsafeCheckpoint(f"cannot resolve allowed global {n}: {e}")
    with torch.serialization.safe_globals(classes):
        return torch.load(path, map_location="cpu", weights_only=True)

def pick_model(ckpt):
    """Ultralytics checkpoints hold weights as ckpt['ema'] or ckpt['model']."""
    m = ckpt.get("ema") or ckpt.get("model")
    if m is None: raise UnsafeCheckpoint("checkpoint has neither 'ema' nor 'model'")
    return m.float()
