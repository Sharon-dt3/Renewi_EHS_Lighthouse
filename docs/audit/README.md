# S4 annotation audit protocol

Tool: `reports/dataset_viewer/index.html` (open in Safari/Chrome). Log: `audit_log.csv`.
Review at zoom 3x or more. Search a filename with the box at the top left of the viewer.

## Queues
- **Q1 empty-label (23):** every image, no sampling. Is a person or PPE visible that should be labelled?
- **Q2 cross-split (48 images, 8 families):** every image. Confirm the copies share a source image; this decides the re-split.
- **Q3 NO-Safety Vest sample (60 of the NO-Safety Vest images, seed 0):** a sample only.
- **Q4 tiny-box sample (40, seed 0):** a sample only.
Samples do not prove the whole class is clean. If a sample shows a high error rate, widen it.

## Rules for labels (from the plan)
- NO-Safety Vest needs a visibly assessable torso without a vest. Occlusion, cut-off or distance is not a label.
- A missing detection is never evidence.

## `decision` values
`keep` · `fix-box` · `fix-class` · `add-annotation` · `drop-annotation` · `drop-image` · `unclear` (needs a second opinion).
Put the box or class in `annotation_or_class`, your name in `reviewer`, the date, and any reason in `notes`.

## Outputs
Fix decisions are applied only to the *derived* dataset (S6). The raw dataset is never edited.
Decision gate S5: use as-is, clean, or reject, based on the error rate in these queues.
