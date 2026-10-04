# Independent evaluation set: selection and annotation guidelines

Status: DRAFT for owner review. Decision recorded 2026-10-04 (plan ADR-009): evaluate the fine-tuned
model on a fresh, independent set, because CSS v27 only yields about 61 cleanly held-out images
(35 valid, 26 test) and about 20 NO-Safety Vest boxes per split.

## 1. Purpose and rules of use
- Measure per-class AP50 and overall mAP50 of the fine-tuned model on data it has never seen.
- **Never** use these images for training, augmentation, threshold tuning or model selection.
  Use a separate *dev* subset (10-20% of clips) for any tuning, and keep the rest as the final *test* set.
- Report the CSS v27 held-out numbers as secondary evidence only.

## 2. Selection criteria
| Requirement | Rule |
| --- | --- |
| Rights | Licence permits this use (e.g. CC BY, CC0, Apache-2.0 for datasets). Record URL, licence, date, author for every source. No Renewi footage (C-01). |
| Privacy | Public, non-identifiable people only. No face recognition or identification. Exclude children and close-up faces. |
| Domain | Real work sites or industrial sites, CCTV-like views preferred: elevated or distant camera, 360p-1080p, motion blur, mixed lighting. |
| Exclude | Selfies and webcam shots, posters, screens, mannequins and cardboard cut-outs, cartoons, stock-studio portraits, images already in CSS v27. |
| Independence | Split by **clip or site**, never by frame. One source clip contributes to one split only. Sample video at most one frame per 2 s. No near-duplicates. |
| Diversity | Mix of viewpoints, distances, lighting (day, dusk, indoor), occlusion, vest styles/colours, helmet colours, crowds and single workers. |

## 3. Size and composition targets (to be agreed, OPEN-07)
- At least 100 images from at least 20 distinct clips or sites.
- At least 150 person, and **at least 50 instances each** of helmet, no_helmet, safety_vest and no_safety_vest.
- At least 30% of images containing a worker without a vest or without a helmet (hard negatives for the model).
- Include some background-only frames (no workers), to measure false positives.

## 4. Classes and labelling rules (YOLO txt, class ids)
`0 person  1 helmet  2 no_helmet  3 safety_vest  4 no_safety_vest`

Draw tight boxes. Label only what is clearly assessable at the image's own resolution.

| Class | Label when | Do NOT label when |
| --- | --- | --- |
| person | A person is visible and at least about half the body or head and torso are in frame. Box covers the visible person. | Reflections, posters, screens, statues, a few pixels of a limb at the edge. |
| helmet | A hard hat is worn on the head. Box covers the hard hat. | Held in hand, on the ground, or bump caps and baseball caps. |
| no_helmet | The head is clearly visible (hair, bare head or non-hard-hat headwear) and there is no hard hat. Box covers the head. | Head cut off, turned away so it is not assessable, too small (under 12 px), or covered by something that could be a helmet. |
| safety_vest | A high-visibility vest or jacket is worn. Box covers the visible torso with the vest. | Plain clothing in a bright colour with no reflective strips or hi-vis material. |
| no_safety_vest | The **torso is clearly visible** (at least 24 px on its shorter side) and the person is **not** wearing a hi-vis vest. Box covers the torso. | Torso hidden, cut off, in a cab, behind an object, seen only from far away, or a neck/collar sliver. **Absence of a vest detection is never a label.** |

Edge cases:
- If you cannot tell, leave the object **unlabelled** and note the image in `unclear.csv`. Do not guess.
- Hi-vis worn over a coat counts as vest. A bib with only a logo does not.
- People partly occluded by others: label the visible part only if it meets the rules above.
- One box per object. No duplicate boxes.

## 5. Annotation workflow and quality control
1. Two annotators label every image independently, or 20-30% of images if effort is limited. Resolve disagreements by discussion and record the rule that decided it.
2. Compute box agreement (IoU >= 0.5 and same class) on the double-labelled subset and record it.
3. Run `scripts/check_eval_labels.py` (format, size rules, counts, provenance).
4. Independent audit: a third person reviews a random sample of 30 images at full resolution. **Proposed gate: error rate under 5% of boxes** (to be agreed, OPEN-07).
5. Independence check against training images (ORB/SIFT region match, as in `utils/build_group_split.py`). Any match removes the image from the evaluation set.
6. Freeze: write the manifest with SHA-256 for every file, then lock the set (read-only).

## 6. Provenance record (one row per source clip or image)
Use `docs/eval-set-provenance-template.csv`. Required columns: `source_id, source_url, licence, licence_url, author, retrieved_date, media_type, split_group, notes`. Each image maps to a `source_id`.

## 7. Open questions for the owner
- Who sources and annotates (OPEN-02, OPEN-03)? Which public clips or datasets are acceptable?
- Acceptance thresholds per class for AP50 (OPEN-07) and the error-rate gate above.
- Whether any Renewi-approved material is later allowed (currently not, C-01).
