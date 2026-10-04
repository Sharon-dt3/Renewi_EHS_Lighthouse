# GPU training runbook (DRAFT, untested on a GPU host)

Purpose: run `scripts/train_ppe5.py --full` on a GPU machine. Written 2026-10-04. Nothing here has been run on a GPU yet.
The authorization in `config/training_authorization.yaml` applies (this PoC only). Do not start until the owner confirms the compute choice and says go.

## 1. What to copy to the GPU host
| Item | Source | Notes |
| --- | --- | --- |
| Code and configs | the Git repo (`scripts/`, `config/`, `docs/`, `backend/tests/`) | commit and push first |
| Derived dataset | `derived_ppe5/` | copy `manifest.json` too; compare the manifest hash with `reports`/the dry-run output |
| Init weights | `weights/yolov8n.pt` | SHA-256 must equal `f59b3d833e2ff32e194b5bb8e08d211dc7c5bdf144b90d2c8412c47ccfc83b36` |
| Protected checkpoint | `models/best.pt` | **Do not copy.** It is not used on the main path. If the host's config still lists it, keep a placeholder with the same name and hash only if the guard requires it |

The harness expects the workspace layout: a folder containing `raw_css_dataset/` (can be an empty placeholder), `derived_ppe5/`, `weights/`, `models/best.pt` and the repo.

## 2. Environment
- Python 3.11, a fresh virtual environment. **`backend/requirements.lock` is pinned for macOS ARM**: on Linux with CUDA install a CUDA build of torch 2.6.0 and torchvision 0.21.0 and keep `ultralytics==8.3.70`, `numpy==1.26.4`, `opencv-python==4.11.0.86`. Record the resulting versions (the run record does this).
- Run the tests (`pytest`) and `python scripts/train_ppe5.py --dry-run` first. The dry run must report no blockers.

## 3. Isolation on Linux (`run_isolated.sh` is macOS-only)
Options, strongest first. Pick one and record which:
1. Docker with `--network none` and read-only mounts for the dataset, weights and the repo; a writable mount only for the run folder, plus `--gpus all`.
2. `unshare -n` (no network namespace) plus read-only bind mounts.
3. Disable the host's outbound network for the duration of the run.
Example shape (adapt paths and image; untested): `docker run --rm --gpus all --network none -v $WS/derived_ppe5:/ws/derived_ppe5:ro -v $WS/weights:/ws/weights:ro -v $WS/repo:/ws/repo:ro -v $WS/runs:/ws/runs <image> python /ws/repo/scripts/train_ppe5.py --smoke`

## 4. Config changes for the GPU
Edit `config/train_ppe5.yaml` on the host (record the changes in the run record):
- `train.device`: the GPU id (for example `0`).
- `train.batch`: raise (for example 32 or 64) if memory allows; `workers`: 4 to 8.
- Keep `amp: false` unless the AMP check can run offline (Ultralytics downloads a model for it).
- Keep `seed`, schedule and thresholds as locked. Do not change `config/acceptance_thresholds.yaml`.

## 5. Order of runs
1. `--dry-run` (no blockers).
2. `--smoke` (1 epoch, tiny subset): confirm the GPU is used, `best.pt` hash unchanged, no network use.
3. `--full` (stage 1: 10 epochs with backbone frozen; stage 2: 90 epochs unfrozen). Fixed schedule, final-epoch weights kept.
4. Copy back only `runs/<name>/` (checkpoint, `run_record.json`, logs). Record the new checkpoint's SHA-256 and add its own class map (ids 0-4) to `config/classes.yaml`.

## 6. After training
- Do **not** report accuracy from the CSS valid/test images as a result. Run `scripts/evaluate_ppe5.py` on the independent evaluation set (OPEN-02) once it exists; until then the verdict is NOT_EVALUATED.
- Run controls from `docs/weight-transfer-plan.md` (full reinitialisation of the class layer is already the COCO path; image size 960 ablation) only if the owner asks.

## 7. Open before the run
- Which GPU host (D2), device id, and who runs it.
- Confirm the owner wants to start the 100-epoch run.

## 8. Google Colab route (decided as the proposed GPU host, 2026-10-04)
Files: `notebooks/train_colab.ipynb`, `config/train_ppe5.colab.yaml`, `scripts/make_colab_bundle.py`.
1. On the Mac: `.venv/bin/python scripts/make_colab_bundle.py`. It writes `colab/ppe5_colab_bundle.zip` (about 150 MB: tracked repo files, the derived dataset, the COCO weights, a hash manifest). **Not included:** `models/best.pt`, the raw dataset, the venv.
2. Upload the zip to Google Drive and open the notebook in Colab with a GPU runtime. The notebook verifies every file hash, pins ultralytics 8.3.70 and torch 2.6.0, runs the tests and a dry run, then a smoke test, then (only when the owner chooses) the full run.
3. **Isolation:** your approval required training with no network. Colab cannot guarantee that, so the harness now **refuses a real run when the network is reachable** unless (a) the notebook can run the job in a network namespace (`unshare -rn`) or (b) the owner records a waiver (name and date) in `config/training_authorization.yaml`. The waiver is a deviation from the approved condition and must be the owner's explicit choice. It is **not** set; the default is `network_isolation_waived: false`. The restricted pickle loader still applies.
4. Data handling: the dataset is public (CC BY 4.0) and the weights are the public COCO checkpoint, so nothing proprietary leaves your machine, but both go to a third-party service (Google). No Renewi footage is involved.
5. Limits: Colab sessions can disconnect (free tier is typically shorter and less predictable). The harness cannot resume stage 2 mid-run; the notebook syncs `runs/` to Drive every two minutes so partial results survive. A run that dies must be restarted under a new run name.
6. Not yet tried: nothing in this section has run on Colab. Library versions on Colab differ from the Mac, which is why the notebook pins them, and the GPU run may need adjustments.
