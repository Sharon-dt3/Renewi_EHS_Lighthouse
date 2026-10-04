import json
from pathlib import Path
import pytest
from scripts import evaluate_ppe5 as ev

TH = {"per_class_ap50_min": {"person": .8, "helmet": .8, "safety_vest": .75, "no_helmet": .6, "no_safety_vest": .6},
      "overall_map50_min": .7, "recall_floor": {"classes": ["no_helmet", "no_safety_vest"], "min_recall": .6, "at_confidence": .25, "iou": .5}}

def box(c, x=.5, y=.5, w=.2, h=.2, conf=None):
    b = (c, x - w / 2, y - h / 2, x + w / 2, y + h / 2, 1.0 if conf is None else conf)
    return b

def gt_all(n=3):
    return {f"i{k}": [box(c) for c in range(5)] for k in range(n)}

def test_perfect_predictions_give_ap_one():
    gt = gt_all(); pr = {k: [box(b[0], conf=.9) for b in v] for k, v in gt.items()}
    res, overall = ev.metrics(gt, pr)
    assert overall == pytest.approx(1.0) and all(v["ap50"] == pytest.approx(1.0) and v["recall"] == 1.0 for v in res.values())

def test_no_predictions_give_zero():
    res, overall = ev.metrics(gt_all(), {})
    assert overall == 0 and all(v["ap50"] == 0 and v["recall"] == 0 for v in res.values())

def test_false_positive_lowers_precision_not_recall():
    gt = {"a": [box(0, .3, .3)]}
    pr = {"a": [box(0, .3, .3, conf=.9), box(0, .8, .8, conf=.95)]}   # higher-confidence FP first
    res, _ = ev.metrics(gt, pr)
    assert res["person"]["recall"] == 1.0 and res["person"]["precision"] == .5 and res["person"]["ap50"] == pytest.approx(.5)

def test_iou_below_threshold_is_a_miss_and_duplicates_count_once():
    gt = {"a": [box(1, .5, .5, .2, .2)]}
    res, _ = ev.metrics(gt, {"a": [box(1, .6, .5, .2, .2, conf=.9)]})            # IoU = 1/3
    assert res["helmet"]["recall"] == 0
    res, _ = ev.metrics(gt, {"a": [box(1, conf=.9), box(1, conf=.8)]})           # second is a duplicate FP
    assert res["helmet"]["n_pred"] == 2 and res["helmet"]["precision"] == .5

def test_wrong_class_does_not_match():
    res, _ = ev.metrics({"a": [box(2)]}, {"a": [box(3, conf=.9)]})
    assert res["no_helmet"]["recall"] == 0 and res["safety_vest"]["n_gt"] == 0

def test_judge_pass_fail_and_not_evaluated():
    gt = gt_all(); pr = {k: [box(b[0], conf=.9) for b in v] for k, v in gt.items()}
    res, overall = ev.metrics(gt, pr)
    assert ev.judge(res, overall, TH) == ("PASS", [])
    pr2 = {k: [box(b[0], conf=.9) for b in v if b[0] != 4] for k, v in gt.items()}   # model never finds no_safety_vest
    v, fails = ev.judge(*ev.metrics(gt, pr2), TH)
    assert v == "FAIL" and any("no_safety_vest" in f for f in fails)
    gt_missing = {k: [b for b in v if b[0] != 4] for k, v in gt.items()}              # no GT for a class
    assert ev.judge(*ev.metrics(gt_missing, pr), TH)[0] == "NOT_EVALUATED"

def test_recall_floor_can_fail_even_with_good_ap():
    gt = {f"i{k}": [box(2, conf=1)] for k in range(10)}
    pr = {f"i{k}": [box(2, conf=.9 if k < 5 else .1)] for k in range(10)}            # half found at conf >= .25
    res, _ = ev.metrics(gt, pr)
    assert res["no_helmet"]["ap50"] == pytest.approx(1.0) and res["no_helmet"]["recall"] == .5

def write_set(root: Path, gt, pred, n=2):
    (root / "gt").mkdir(parents=True); (root / "pr").mkdir()
    for k, v in gt.items():
        (root / "gt" / f"{k}.txt").write_text("".join(f"{b[0]} {(b[1]+b[3])/2} {(b[2]+b[4])/2} {b[3]-b[1]} {b[4]-b[2]}\n" for b in v))
    for k, v in pred.items():
        (root / "pr" / f"{k}.txt").write_text("".join(f"{b[0]} {(b[1]+b[3])/2} {(b[2]+b[4])/2} {b[3]-b[1]} {b[4]-b[2]} {b[5]}\n" for b in v))

def run(tmp_path, kind, extra=()):
    gt = gt_all(); write_set(tmp_path, gt, {k: [box(b[0], conf=.9) for b in v] for k, v in gt.items()})
    out = tmp_path / "report.json"
    code = ev.main(["--gt-dir", str(tmp_path / "gt"), "--pred-dir", str(tmp_path / "pr"), "--eval-set-kind", kind,
                    "--checkpoint-sha256", "abc", "--out", str(out), *extra])
    return code, json.loads(out.read_text())

def test_css_heldout_is_sanity_only_never_pass(tmp_path):
    code, rep = run(tmp_path, "css-heldout")
    assert rep["verdict"] == "SANITY_ONLY" and code == 0 and rep["overall_map50"] == pytest.approx(1.0)

def test_independent_without_root_is_not_evaluated(tmp_path):
    code, rep = run(tmp_path, "independent")                 # no --eval-root
    assert rep["verdict"] == "NOT_EVALUATED" and code == 1

def test_independent_with_invalid_set_is_not_evaluated(tmp_path):
    bad = tmp_path / "bad_root"; (bad / "images").mkdir(parents=True); (bad / "labels").mkdir()   # empty, no provenance
    code, rep = run(tmp_path, "independent", ["--eval-root", str(bad)])
    assert rep["verdict"] == "NOT_EVALUATED" and code == 1 and "check_eval_labels" in " ".join(rep["notes"])

def test_report_records_provenance(tmp_path):
    _, rep = run(tmp_path, "css-heldout")
    p = rep["provenance"]
    assert p["checkpoint_sha256"] == "abc" and len(p["thresholds_file_sha256"]) == 64
    assert p["thresholds_used"]["overall_map50_min"] == 0.7
    assert len(p["gt_tree_sha256"]) == 64 and len(p["pred_tree_sha256"]) == 64 and p["iou"] == 0.5 and p["conf"] == 0.25
