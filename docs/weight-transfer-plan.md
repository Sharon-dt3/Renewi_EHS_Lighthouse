# S7: Architecture and weight-transfer plan (DRAFT, not approved)

Status: draft for owner review, written 2026-10-04. **Nothing here authorizes loading the checkpoint or training.**
Training (S8) needs separate, explicit user authorization after the gates in section 9.
Related: `docs/implementation-plan.md` (S7, S8, S9, ADR-002, ADR-009), `docs/model-selection.md`,
`docs/evaluation-set-guidelines.md`, `derived_ppe5/` (the derived dataset, outside Git).

## 1. Goal and starting point
- Goal: a YOLOv8n detector for five classes with a real NO-Safety Vest class:
  `person 0, helmet 1, no_helmet 2, safety_vest 3, no_safety_vest 4`.
- Starting checkpoint: Hafizqaim `models/best.pt`, 6,249,635 bytes, SHA-256
  `5464f555f1b9831e6f1f9adcab11063f9a081d62e6650c2f2154bd4c01720836` (never loaded to date).
- Its serialized taxonomy has 17 names. Four map to our classes:

| Source id | Source name | Target id | Target name |
| --- | --- | --- | --- |
| 14 | person | 0 | person |
| 12 | head_helmet | 1 | helmet |
| 13 | head_nohelmet | 2 | no_helmet |
| 16 | vest | 3 | safety_vest |
| none | none | 4 | no_safety_vest (new, no source) |

  The other 13 names (Barefoots, Ear-protection, Harness, No_Ear-Protection, No_Glasses, Sandals, boots,
  face_mask, face_nomask, glasses, hand_glove, hand_noglove, shoes) are dropped.
- Important caveat: the source names are **static label evidence only**. Whether the checkpoint actually detects
  these four classes well is unverified (no inference has been run).
- Pinned software (from `backend/requirements.lock`): ultralytics 8.3.70, torch 2.6.0, torchvision 0.21.0,
  numpy 1.26.4, opencv-python 4.11.0.86.

## 2. How the weights are carried over
Ultralytics YOLOv8 has a backbone, a neck, and a detection head. In the head, the box branch (`cv2`) outputs
box distribution values and the class branch (`cv3`) ends in a convolution whose output channels equal the
number of classes. Only that last class convolution depends on class count.

| Part | Treatment | Reason |
| --- | --- | --- |
| Backbone, neck | Copy unchanged | General visual features |
| Box branch (`cv2`) | Copy unchanged | Box geometry does not depend on class |
| Class branch (`cv3`), all layers except the last conv | Copy unchanged | Same shapes for any `nc` |
| Class branch last conv (17 to 5 outputs) | **Re-built, see options** | Output size changes |

Options for the last class convolution (`cv3` final conv, one per detection scale; weight and bias):
- **Option A (recommended): seeded initialisation.** Copy the source rows for classes 14, 12, 13 and 16 into
  target rows 0, 1, 2 and 3. Initialise row 4 (no_safety_vest) with Ultralytics' default class-bias
  initialisation (small prior) and random weights. Keeps what the model knows for four classes.
- **Option B (control): full reinitialisation** of the last conv (Ultralytics' normal behaviour when `nc`
  differs). Learns all five from scratch on top of transferred features.
- **Option C (control): COCO-pretrained YOLOv8n** (see section 5), same data and schedule.

Hard rules:
- Never initialise row 4 from the `vest` row, or derive no_safety_vest from absence of a vest detection.
- The new checkpoint gets its own file name, its own SHA-256 and its **own class map** in `config/classes.yaml`.
  Never reuse the Hafizqaim map (ids 12/13/14/16).
- Verify after building: the transferred rows are bit-identical to the source rows (an automated check, not a visual one).

## 3. Training schedule (proposed; all values are recorded per run)
| Setting | Proposal | Note |
| --- | --- | --- |
| Data | `derived_ppe5/data.yaml` (2,539 train; 35 valid; 26 test) | See caveats on valid/test in section 6 |
| Image size | 640; ablation at 960 | Many objects are small |
| Stage 1 | Freeze backbone and neck, train head, about 10 epochs | Settles the new class layer |
| Stage 2 | Unfreeze all, lower learning rate, about 90 epochs | Fine-tuning |
| Classes | All five trained together | Avoids forgetting the four known classes |
| Augmentation | Reduce Ultralytics mosaic (data already contains mosaics and Roboflow augmentations); keep flip, HSV, scale | Avoid compounding artefacts |
| Imbalance | Person 8,511 vs helmet 2,757 boxes: consider class weighting; document if used | |
| Seed, determinism | Fixed seed; record `deterministic` setting | Reproducibility |
| Batch, optimiser, LR, weight decay | Decide at run time; record the final values | Hardware dependent |
| Model selection | **Fixed epoch budget; keep the final-epoch weights** | 35 validation images (partly overlapping) are too few to pick a best epoch honestly |
| Early stopping | Off | Same reason |

## 4. Safety around the checkpoint
Risk: `best.pt` is a Python pickle. Loading it executes code paths named inside it. `docs/model-selection.md`
verified eight Ultralytics `GLOBAL` references inside the file (`DetectionModel`, `Conv`, `C2f`, `Bottleneck`,
`SPPF`, `Concat`, `Detect`, `DFL`). Only `DetectionModel` has a recorded exception, conditional on the specified
dependencies and an approved container; the other seven have no approval established, and that document records
that no blanket safe-global exception is justified. **Owner authorization is required before any load.**

Requirements before the first load:
1. Security/runtime owner authorizes a digest-bound loading harness (OPEN-08).
2. Run in an isolated environment: separate virtual environment from the lock file, no network, CPU only for the loading step,
   checkpoint mounted read-only, output only to a new run directory.
3. Load restricted: no `weights_only=False`, no unrestricted YOLO object loader, no blanket allow-list.
   Stop on any unapproved global. Extract tensors only; build the new model from `yolov8n.yaml` with `nc=5`
   and copy tensors in by name and shape.
4. Verify the SHA-256 of `models/best.pt` before and after every run.
5. Never overwrite or rename `models/best.pt`.

## 5. Fallback and control: COCO-pretrained YOLOv8n
If the Hafizqaim weights cannot be approved (licence, OPEN-01, or loading, OPEN-08), train all five classes from
an official COCO-pretrained YOLOv8n instead. Even if Hafizqaim is approved, run this as a control:
it shows whether the transfer actually helps. Licence caveat: Ultralytics software and its weights carry their own
terms (AGPL-3.0 or enterprise); a rights review is required before any deployment or redistribution.

## 6. Evaluation and acceptance
- Final evaluation: the independent set (ADR-009, `docs/evaluation-set-guidelines.md`). Report overall mAP50 and per-class
  AP50, precision and recall; record confidence and IoU thresholds, image size, dataset hash, checkpoint hash,
  Git commit and UTC date. No placeholder numbers.
- CSS valid and test (35 and 26 images) are **sanity checks only**: a SIFT check found 357 held-out/train pairs
  with 30 or more matching points, so they are not independent of training.
- Acceptance thresholds are **OPEN-07 and are not decided**. Proposed starting points for discussion only
  (not agreed): person and helmet AP50 at least 0.80; safety_vest at least 0.75; no_helmet and no_safety_vest at least 0.60.
  The owner sets the real values before S9 runs, because they must not be tuned after seeing results.
- Failure-case review: inspect false positives and misses, especially NO-Safety Vest versus safety_vest confusions,
  occlusion, distance and night views. Absence of a vest detection must remain `UNKNOWN` downstream.

## 7. Reproducibility record (one folder per run)
Run directory (separate from `models/`) contains: config and seed, package versions (lock hash), dataset
`manifest.json` hash, transfer-check output, training logs, per-epoch metrics, final checkpoint, its SHA-256,
and the new class map entry. Record the original checkpoint hash before and after.

## 8. Decisions and compute
| ID | Decision | Recommendation | Owner |
| --- | --- | --- | --- |
| D1 | Option A (seeded) as the main path, Option B and C as controls | Yes | Model owner |
| D2 | Compute: AWS GPU (g5/g6) versus the Mac | GPU for the real runs. The Mac (CPU or MPS) only for smoke tests | Infrastructure |
| D3 | Image size 640 versus 960 | Start at 640, test 960 as an ablation | Model owner |
| D4 | Acceptance thresholds (OPEN-07) | Owner to set before S9 | Model owner |
| D5 | Selfie and off-domain images in training | Decide, then re-run the derived-dataset builder | Dataset owner |
| D6 | Apply the AI first-pass audit decisions | Only after human confirmation | Reviewer |

Smoke test before any real run (after authorization): 1 epoch on a tiny subset, to confirm the pipeline runs end to end,
the transfer check passes and the checkpoint hash is unchanged.

## 9. Gates (all required before S8)
1. Owner approval of this document.
2. Weights licence resolved for fine-tuning and intended use (OPEN-01).
3. Security authorization of the loading and training harness (OPEN-08).
4. Acceptance thresholds agreed (OPEN-07).
5. Explicit user authorization to start training (S8).

## 10. Not covered here
Temporal smoothing, the API, the database and the UI (plan phases B to D), and the independent evaluation set
itself (OPEN-02), which still needs an owner to source and annotate.
