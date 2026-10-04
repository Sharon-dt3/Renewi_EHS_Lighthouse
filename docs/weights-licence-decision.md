# Weights licence decision (OPEN-01)

Decision recorded **2026-10-04** by the project owner: **ask the Hafizqaim maintainer for a licence, and use a
COCO-pretrained YOLOv8n as the main training path meanwhile.** Hafizqaim becomes a comparison run only if a licence arrives.

## Why this route
- The exact Hafizqaim weights (`models/best.pt`, SHA-256 `5464f555f1b9831e6f1f9adcab11063f9a081d62e6650c2f2154bd4c01720836`,
  release asset 273300310) have **no licence**: the GitHub repository licence is null, the release tag and Hugging Face Space grant no rights, and the
  only existing request (GitHub issue #1 on `hafizqaim/Workspace-Safety-Detection-using-YOLOv8`) is open with zero replies
  (public-evidence check recorded in `docs/model-selection.md`, 2026-10-03). Public availability is not permission.
- Waiting on an unanswered request could block the project indefinitely, so the main path must not depend on it.

## What changes in the plan
| Item | Before | After |
| --- | --- | --- |
| Main training start | Hafizqaim, seeded head (Option A) | **COCO-pretrained YOLOv8n (Option C)** |
| Hafizqaim | Main path | Comparison/control only, **after** a licence is granted and OPEN-08 authorizes loading |
| `best.pt` | Read for seeding | **Not loaded** on the main path. Stays preserved and untouched |
| OPEN-08 (loading harness) | Required for the main path | Required only if Hafizqaim is later used. Training from COCO weights still needs a safe-loading review of those weights |

## What is NOT resolved by this decision
This does not make the licence question disappear. It moves it:
1. **Ultralytics terms.** The Ultralytics YOLOv8 software and its pretrained weights are published under AGPL-3.0 with an enterprise-licence option.
   Training and using them for a PoC demo, and any later deployment or redistribution, need a rights review by the rights reviewer, who must
   check the **current** terms. Installing the package is not approval. **Gate status: open until the rights reviewer signs off.**
2. **COCO data and weights lineage.** Confirm what obligations apply to COCO-pretrained weights as published by Ultralytics.
3. **Dataset.** CSS v27 is CC BY 4.0 (attribution and change notice are in `derived_ppe5/ATTRIBUTION.md`); the uploader's rights to every image are not established (OPEN-05).
4. **Loading any `.pt` file** is still a pickle risk. The restricted-loading requirements in `docs/weight-transfer-plan.md` section 4 apply to the COCO weights too.

## Actions
| Action | Owner | Status |
| --- | --- | --- |
| Send the rights request (`docs/rights-request-hafizqaim.md`, a draft, **not sent**) | Project owner | To do |
| Review Ultralytics (AGPL-3.0 / enterprise) and COCO-weights terms for this PoC use | Rights reviewer | To do |
| Decide whether the PoC may use AGPL software or needs an enterprise licence | Project owner / rights reviewer | To do |
| If a Hafizqaim licence is granted: record it (document, date, scope, asset hash) and re-open Option A as a comparison | Rights reviewer | Waiting |

## Gate wording for S8
Gate 2 (weights rights) is satisfied only when the rights reviewer records written approval of the weights that will actually be
used for training. Until then S8 stays blocked.
