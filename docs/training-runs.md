# Training runs

## colab-full-1 (2026-10-04)  -  trained, NOT independently evaluated

| Item | Value |
| --- | --- |
| Start | COCO-pretrained YOLOv8n (`weights/yolov8n.pt`, SHA-256 `f59b3d83…`), loaded through `scripts/restricted_load.py` |
| Data | `derived_ppe5/`: 2,539 train, 35 valid, 26 test images; 5 classes |
| Schedule | Stage 1: 10 epochs, backbone frozen (0.122 h). Stage 2: 90 epochs, unfrozen (1.252 h) |
| Host | Google Colab, Tesla T4, Python 3.13.15, torch 2.6.0+cu124, ultralytics 8.3.70 |
| Isolation | `network: isolated (no outbound connection)` (network namespace) |
| Final checkpoint | `runs/colab-full-1/stage2/weights/last.pt`, SHA-256 `899d48d685404a2aba794233da8990ac8478e841d5e5713557dc2d99ca8d6463` (Drive: `ppe5_runs/colab-full-1/`) |
| Class map | own entry in `config/classes.yaml`: ids 0-4 = person, helmet, no_helmet, safety_vest, no_safety_vest |
| Protected checkpoint | `models/best.pt` not present on the Colab host and never loaded |

### Validation printed at the end of training (CSS valid split, 35 images, 300 instances)
Ultralytics validates `best.pt` (chosen by fitness on this same split), **not** the `last.pt` recorded above.
| Class | Instances | Precision | Recall | mAP50 |
| --- | --- | --- | --- | --- |
| all | 300 | 0.930 | 0.827 | 0.894 |
| person | 135 | 0.982 | 0.810 | 0.909 |
| helmet | 55 | 0.972 | 0.818 | 0.920 |
| no_helmet | 17 | 0.987 | 0.882 | 0.967 |
| safety_vest | 70 | 0.960 | 0.843 | 0.912 |
| no_safety_vest | 23 | 0.750 | 0.783 | 0.760 |
Speed on the T4: 0.2 ms preprocess, 4.5 ms inference, 1.2 ms postprocess per image (mean, single images, not a p95).

### What this does NOT show
- **These numbers are not accuracy.** The 35 valid images are not independent of the training images (SIFT found 357 held-out/train overlaps), and `best.pt` was selected on them. The project's evaluation rules (`docs/acceptance-thresholds.md`) allow CSS held-out numbers as a sanity check only; the verdict for this run is **SANITY_ONLY**, never PASS.
- No independent evaluation set exists yet (OPEN-02). Until it does, the acceptance thresholds cannot be checked.
- no_safety_vest has the weakest result and the smallest support (23 instances in 12 images), so its figures are the least reliable.
- The model was trained on photos (many close-ups), not CCTV views; behaviour on distant, low-resolution footage is unmeasured.
- `last.pt` itself was not separately validated; re-run validation on `last.pt` for a like-for-like record.

### Deviations from the plan, for the record
- Colab copy of the old harness was used with a path-only edit to `data.yaml` (see `docs/project-decision-history.md` section 9); the repo harness has the permanent fix.
- Python 3.13 and torch 2.6.0+cu124 on Colab differ from the Mac environment (Python 3.11, CPU torch 2.6.0).
