# S12 VAL-04 expected cases for the Pexels clip (DRAFT, not reviewed)

Status: **DRAFT written 2026-10-04 by the assistant. Not approved. A person must confirm each row against the video before this becomes a fixture.**
Zone under test: `config/zones.candidate.yaml`, clip `pexels_10294766_1080p` (1920x1080), polygon `[[1250,560],[1920,520],[1920,900],[1180,900]]`. Not approved either.
Clip file SHA-256: `53734aaf05d235e72e44bdac3c7164c9906e8cd2305a804b07f0e1f646a1af6c`.

## How these were chosen
- Read **by eye from the video frames, without looking at any model output**, so the expected answers are independent of the system being tested.
- Only workers whose **feet are clearly visible** and **at least about 150 px from every zone edge** are listed. A hand reading is only good to roughly +-60 px, so near-edge cases are not trustworthy by eye.
- Excluded as ambiguous: feet hidden by foreground rebar, bodies cut off by the bottom of the frame (their bottom-centre is the frame edge, not the feet), and anyone near a zone edge.
- Each row is a **worker description and an approximate foot position in source pixels**, not a model index. A passing check means the system's foot point for that worker lands on the expected side.

## Cases
| ID | Time (s) | Worker | Approx. feet (x, y) | Expected | Notes |
| --- | --- | --- | --- | --- | --- |
| O1 | 2.0 | Large bent-over worker, grey sweatshirt and yellow vest, centre | about (880 to 1000, 940 to 980) | **outside** | Below the zone's bottom edge (y=900) and left of it |
| O2 | 10.0 | Crouching worker, navy jacket with green logo vest, centre-left | about (1000 to 1100, 840 to 880) | **outside** | More than 80 px left of the left edge (about x=1190 at this height); treat as outside |
| O3 | 12.0 | Same navy-jacket worker, crouching | about (1000 to 1100, 800 to 860) | **outside** | As O2 |
| I1 | 10.0 | Crouching worker, yellow helmet and vest, right of centre | about (1380 to 1480, 650 to 690) | **inside** | Feet visible on the open floor; more than 150 px from the left edge |
| I2 | 8.0 | Standing man in white T-shirt, background | about (1450 to 1500, 690 to 720) | **inside** | Boots visible between the poles |
| I3 | 14.0 | Crouching worker, yellow helmet, right | about (1480 to 1560, 620 to 680) | **inside** | Same area as I1 |
| B1 | (constructed) | Any measured foot point | exactly on a polygon edge or corner | **inside** (edge counts as inside) | Cannot occur naturally. Construct it by placing a polygon vertex or edge exactly through a measured foot point, and label the record "constructed" |
| C1 | **none available** | Worker missing PPE while inside the zone | n/a | `PPE_*_MISSING` + `ZONE_INCURSION` on the same worker | The Pexels clip has no PPE violator. Needs another approved clip |

Frame-level expectations (also by eye): between about 2 s and 14 s at least one worker stands inside the zone in most frames; at 0.0 s and 4.0 s the only person near the zone is partly hidden behind rebar, so those frames are not used.

## What is still needed before this is a fixture
1. A named reviewer checks every row against the video and confirms, changes or removes it (reviewer, date, per-row decision).
2. The zone is approved (`config/zones.reviewed.yaml`).
3. The clip's use for evaluation is confirmed by the licence reviewer.
4. A second clip with a PPE violator standing in a zone, for C1.
5. A constructed boundary case is added and labelled as constructed.

## How each case will be scored
Three outcomes, so a model miss is never confused with a zone-logic error:
- **MATCH:** the system detected the worker and put the foot point on the expected side of the zone.
- **MISMATCH:** the worker was detected but the foot point is on the wrong side. This is a zone-logic or geometry failure and fails VAL-04.
- **NOT DETECTED:** the model produced no person box for that worker. The zone logic cannot act on a person it never saw. This is reported separately as a detection limitation; it is not a zone failure, but it is a real limit on what the zone check can catch.
A case passes when the outcome is MATCH. NOT DETECTED cases are listed with their frame and are not silently dropped.

## Dry comparison (2026-10-04, NOT VAL-04)
A one-off comparison of the by-eye positions above against the system's foot points from the same clip (same checkpoint, candidate zone, 4 fps). It shows the draft is sensible; it does not replace the reviewed run.
| ID | Result |
| --- | --- |
| O1 (2.0 s) | MATCH: outside |
| O2 (10.0 s) | **NOT DETECTED.** The model found only a low-confidence helmet (0.34) and vest (0.29) for this worker, no person box. At 10.25 s a person box appears (confidence 0.32, feet near (1064, 876)). Consider using 10.25 s for this worker, or keep 10.0 s as a recorded detection miss |
| O3 (12.0 s) | MATCH: outside (feet about (1010, 872), confidence 0.88) |
| I1 (10.0 s) | MATCH: inside |
| I2 (8.0 s) | MATCH: inside |
| I3 (14.0 s) | MATCH: inside |
Five of six matched; one was a detection miss. B1 and C1 were not run (no constructed boundary case yet; no violator clip).

## Sign-off
| Item | Value |
| --- | --- |
| Reviewer | |
| Date | |
| Row decisions | |
| Zone approved | |
| Evaluation use of clip approved by | |
