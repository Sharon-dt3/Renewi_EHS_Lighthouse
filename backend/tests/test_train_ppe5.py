import hashlib, json, pickle, zipfile
from pathlib import Path
import pytest, torch, yaml
from scripts import train_ppe5 as tr

FINAL = tr.FINAL
def sha(b): return hashlib.sha256(b).hexdigest()

@pytest.fixture
def world(tmp_path):
    root = tmp_path / "ws"; (root / "models").mkdir(parents=True); (root / "weights").mkdir()
    (root / "models" / "best.pt").write_bytes(b"protected")
    torch.save({"w": torch.zeros(2)}, root / "weights" / "yolov8n.pt")
    coco = (root / "weights" / "yolov8n.pt").read_bytes()
    for s, n in (("train", 3), ("valid", 1), ("test", 1)):
        (root / "derived" / "images" / s).mkdir(parents=True); (root / "derived" / "labels" / s).mkdir(parents=True)
        for k in range(n):
            (root / "derived" / "images" / s / f"{s}{k}.jpg").write_bytes(b"x")
            (root / "derived" / "labels" / s / f"{s}{k}.txt").write_text("0 .5 .5 .1 .1\n")
    (root / "derived" / "data.yaml").write_text(yaml.safe_dump({"nc": 5, "names": FINAL}))
    cfg = {"seed": 0, "data": "derived/data.yaml", "out_root": "runs",
           "init": {"kind": "coco_yolov8n", "weights_path": "weights/yolov8n.pt", "weights_sha256": sha(coco)},
           "protected_checkpoint": {"path": "models/best.pt", "sha256": sha(b"protected")},
           "train": {}, "smoke": {}}
    auth = tmp_path / "auth.yaml"
    auth.write_text(yaml.safe_dump({"rights_approved_for_poc": True, "security_isolation_approved": True, "training_go_ahead": True}))
    return root, cfg, auth

def test_all_good_passes_preflight(world):
    root, cfg, auth = world
    ev = tr.preflight(cfg, root, auth, "smoke", "r1")
    assert ev["blockers"] == [] and ev["dataset"][0] == {"train": 3, "valid": 1, "test": 1}

@pytest.mark.parametrize("flag", ["rights_approved_for_poc", "security_isolation_approved", "training_go_ahead"])
def test_each_gate_must_be_true(world, flag):
    root, cfg, auth = world
    d = yaml.safe_load(auth.read_text()); d[flag] = False; auth.write_text(yaml.safe_dump(d))
    with pytest.raises(tr.Refusal): tr.preflight(cfg, root, auth, "smoke", "r1")

def test_missing_authorization_file_refuses(world):
    root, cfg, auth = world; auth.unlink()
    with pytest.raises(tr.Refusal): tr.preflight(cfg, root, auth, "full", "r1")

def test_protected_checkpoint_change_always_refuses_even_in_dry_run(world):
    root, cfg, auth = world; (root / "models" / "best.pt").write_bytes(b"tampered")
    with pytest.raises(tr.Refusal): tr.preflight(cfg, root, auth, "dry-run", "r1")

def test_unpinned_or_wrong_init_weights(world):
    root, cfg, auth = world
    cfg["init"]["weights_sha256"] = None
    with pytest.raises(tr.Refusal): tr.preflight(cfg, root, auth, "smoke", "r1")
    assert tr.preflight(cfg, root, auth, "dry-run", "r1")["blockers"]            # dry run reports instead of failing
    cfg["init"]["weights_sha256"] = "0" * 64
    with pytest.raises(tr.Refusal): tr.preflight(cfg, root, auth, "smoke", "r1")
    cfg["init"]["weights_sha256"] = sha((root / "weights" / "yolov8n.pt").read_bytes()); (root / "weights" / "yolov8n.pt").unlink()
    with pytest.raises(tr.Refusal): tr.preflight(cfg, root, auth, "smoke", "r1")

def test_only_coco_init_kind_supported(world):
    root, cfg, auth = world; cfg["init"]["kind"] = "hafizqaim"
    with pytest.raises(tr.Refusal): tr.preflight(cfg, root, auth, "smoke", "r1")

def test_dataset_structure_checks(world):
    root, cfg, auth = world
    (root / "derived" / "labels" / "train" / "train0.txt").write_text("9 .5 .5 .1 .1\n")
    with pytest.raises(tr.Refusal): tr.preflight(cfg, root, auth, "dry-run", "r1")
    (root / "derived" / "labels" / "train" / "train0.txt").write_text("0 .5 .5 .1 .1\n")
    (root / "derived" / "labels" / "train" / "train1.txt").unlink()
    with pytest.raises(tr.Refusal): tr.preflight(cfg, root, auth, "dry-run", "r1")
    (root / "derived" / "images" / "train" / "train1.jpg").unlink()
    (root / "derived" / "data.yaml").write_text(yaml.safe_dump({"nc": 4, "names": FINAL[:4]}))
    with pytest.raises(tr.Refusal): tr.preflight(cfg, root, auth, "dry-run", "r1")

def test_run_dir_must_be_new_and_outside_protected_folders(world):
    root, cfg, auth = world
    (root / "runs" / "r1").mkdir(parents=True)
    with pytest.raises(tr.Refusal): tr.preflight(cfg, root, auth, "smoke", "r1")
    cfg["out_root"] = "models"
    with pytest.raises(tr.Refusal): tr.preflight(cfg, root, auth, "smoke", "x")
    (root / "raw_css_dataset").mkdir(); cfg["out_root"] = "raw_css_dataset"
    with pytest.raises(tr.Refusal): tr.preflight(cfg, root, auth, "smoke", "x")

def test_thresholds_must_match_locked_hash(monkeypatch, tmp_path):
    fake = tmp_path / "repo"; (fake / "config").mkdir(parents=True); (fake / "docs").mkdir()
    (fake / "config" / "acceptance_thresholds.yaml").write_text("a: 1\n")
    (fake / "docs" / "acceptance-thresholds.md").write_text("SHA-256 of that file at lock time: `" + "1" * 64 + "`\n")
    monkeypatch.setattr(tr, "REPO", fake)
    with pytest.raises(tr.Refusal): tr.check_thresholds()
    (fake / "docs" / "acceptance-thresholds.md").write_text("SHA-256 of that file at lock time: `" + sha(b"a: 1\n") + "`\n")
    assert tr.check_thresholds() == sha(b"a: 1\n")

def test_real_locked_thresholds_file_matches_its_recorded_hash():
    assert len(tr.check_thresholds()) == 64            # the repo's own lock is intact

def test_main_refuses_real_run_without_gates_and_writes_nothing(world, monkeypatch, capsys):
    root, cfg, auth = world
    d = yaml.safe_load(auth.read_text()); d["training_go_ahead"] = False; auth.write_text(yaml.safe_dump(d))
    cfgp = root.parent / "cfg.yaml"; cfgp.write_text(yaml.safe_dump(cfg))
    monkeypatch.setattr(tr, "find_root", lambda: root)
    code = tr.main(["--smoke", "--config", str(cfgp), "--authorization", str(auth), "--run-name", "r1"])
    assert code == 2 and "REFUSED" in capsys.readouterr().out and not (root / "runs").exists()

def test_main_dry_run_loads_nothing_and_writes_nothing(world, monkeypatch, capsys):
    root, cfg, auth = world
    cfgp = root.parent / "cfg.yaml"; cfgp.write_text(yaml.safe_dump(cfg))
    monkeypatch.setattr(tr, "find_root", lambda: root)
    code = tr.main(["--dry-run", "--config", str(cfgp), "--authorization", str(auth), "--run-name", "r1"])
    assert code == 0 and not (root / "runs").exists() and (root / "models" / "best.pt").read_bytes() == b"protected"

class _Evil:
    def __reduce__(self):
        import os
        return (os.system, ("true",))

def test_init_weights_with_unsafe_pickle_are_refused_at_preflight(world):
    root, cfg, auth = world
    p = root / "weights" / "yolov8n.pt"
    with zipfile.ZipFile(p, "w") as z: z.writestr("m/data.pkl", pickle.dumps({"x": _Evil()}, protocol=2))
    cfg["init"]["weights_sha256"] = sha(p.read_bytes())            # hash matches, so only the scan can stop it
    with pytest.raises(tr.Refusal, match="static pickle scan"): tr.preflight(cfg, root, auth, "smoke", "r1")

def test_protected_checkpoint_can_be_absent_only_when_config_says_so(world):
    root, cfg, auth = world
    (root / "models" / "best.pt").unlink()
    with pytest.raises(tr.Refusal): tr.check_protected(cfg, root)
    cfg["protected_checkpoint"]["required_on_host"] = False
    assert tr.check_protected(cfg, root).startswith("absent-on-this-host")

def test_present_protected_checkpoint_is_still_hash_checked_when_optional(world):
    root, cfg, auth = world
    cfg["protected_checkpoint"]["required_on_host"] = False
    (root / "models" / "best.pt").write_bytes(b"tampered")
    with pytest.raises(tr.Refusal): tr.check_protected(cfg, root)

def test_network_isolation_rules():
    assert tr.check_network_isolation({}, reachable=lambda: False).startswith("isolated")
    with pytest.raises(tr.Refusal): tr.check_network_isolation({}, reachable=lambda: True)
    with pytest.raises(tr.Refusal): tr.check_network_isolation({"network_isolation_waived": False}, reachable=lambda: True)
    with pytest.raises(tr.Refusal): tr.check_network_isolation({"network_isolation_waived": "yes"}, reachable=lambda: True)  # must be literal true
    out = tr.check_network_isolation({"network_isolation_waived": True, "network_isolation_waived_by": "A", "network_isolation_waived_on": "d"}, reachable=lambda: True)
    assert out.startswith("NOT isolated; waived by A")

def test_real_authorization_file_does_not_waive_isolation():
    import yaml as _y
    a = _y.safe_load((tr.REPO / "config" / "training_authorization.yaml").read_text())
    assert a["network_isolation_waived"] is False

def test_real_runs_use_an_absolute_path_data_yaml_and_leave_the_dataset_alone(world):
    root, cfg, auth = world
    src = root / "derived" / "data.yaml"
    src.write_text(yaml.safe_dump({"path": ".", "train": "images/train", "val": "images/valid", "test": "images/test", "nc": 5, "names": FINAL}))
    before = src.read_bytes(); out = root / "runs" / "r"; out.mkdir(parents=True)
    dst = tr.write_abs_data_yaml(cfg, root, out)
    y = yaml.safe_load(dst.read_text())
    assert Path(y["path"]).is_absolute() and Path(y["path"]) == (root / "derived").resolve()
    assert (Path(y["path"]) / y["train"]).is_dir() and y["nc"] == 5 and y["names"] == FINAL
    assert src.read_bytes() == before and dst.parent == out            # dataset file untouched, copy lives in the run folder

def test_abs_yaml_refuses_missing_split_directory(world):
    root, cfg, auth = world
    src = root / "derived" / "data.yaml"
    src.write_text(yaml.safe_dump({"path": ".", "train": "images/nope", "val": "images/valid", "nc": 5, "names": FINAL}))
    out = root / "runs" / "r"; out.mkdir(parents=True)
    with pytest.raises(tr.Refusal): tr.write_abs_data_yaml(cfg, root, out)
