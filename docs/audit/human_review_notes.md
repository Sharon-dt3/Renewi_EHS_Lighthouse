# Human review notes (derived five-class dataset)

These notes record informal human checks. They are **not** per-annotation decisions and are
not applied by `scripts/build_derived_dataset.py` (it only applies rows in `audit_log.csv`
signed by a human reviewer).

| Date | Reviewer | What was checked | Scope | Outcome |
| --- | --- | --- | --- | --- |
| 2026-10-04 | Project owner (name not recorded) | Derived dataset `derived_ppe5/` via `reports/dataset_viewer_derived/index.html` | Informal visual check; number of images and splits not specified | All five classes are visible in the viewer images. NO-Safety Vest labels looked correct. |

## Limits of this record
- The check was visual and informal. It does not give an error rate.
- The AI first-pass decisions in `audit_log.csv` (171 rows, signed "Claude (AI first pass...)") remain unconfirmed.
- The 61 held-out images (35 valid, 26 test) are not independent of training: a SIFT check found
  357 held-out/train pairs with 30 or more matching points. Use them for sanity checks only.
- Selfie and webcam images are still present in the training data (policy undecided).
- The final evaluation will use an independent set (plan ADR-009, OPEN-02).
