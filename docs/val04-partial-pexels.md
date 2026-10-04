# VAL-04 partial result: Pexels clip, approved test zone (2026-10-04)

**Verdict: PARTIAL. The zone-geometry cases passed. VAL-04 as a whole is NOT closed** (combined PPE-plus-zone case, evaluation-use licence and a reviewed table are still open; see the end).

## What was run
| Item | Value |
| --- | --- |
| Command | `scripts/run_isolated.sh .venv/bin/python scripts/run_incidents.py --checkpoint ../models/last.pt --video data/input/clips/pexels_10294766_1080p.mp4 --zones config/zones.reviewed.yaml --out ../reports/val04/pexels_partial_20261004` then `scripts/val04_zone_cases.py` |
| Clip | `pexels_10294766_1080p.mp4`, SHA-256 `53734aaf05d235e72e44bdac3c7164c9906e8cd2305a804b07f0e1f646a1af6c` (matches the cases file: True) |
| Checkpoint | `colab-full-1` `last.pt`, SHA-256 `899d48d685404a2aba794233da8990ac8478e841d5e5713557dc2d99ca8d6463` |
| Zone file | `config/zones.reviewed.yaml`, SHA-256 `fd6688a1783ef9a0760f4662639b6d58713623e376e7ea33aaf2bf47facff6f3` |
| Cases file | `config/val04_cases.pexels_10294766.yaml`, SHA-256 `41a77888a51d7a4c44a0d5dd32c43c01e8777d33f017d2dd83139baadaaaa1cd` |
| Raw outputs | `reports/val04/pexels_partial_20261004/` (outside Git): `incidents.json`, `val04_result.json`, annotated frames |
| Environment | local sandbox, no network, Python 3.11, 4 fps sampling, rules from `config/rules.yaml` |

## Approvals recorded
- **Zone approved by the project owner on 2026-10-04 as a test fixture** (a stand-in, not a real restricted area). Name not recorded.
- The **expected-cases table** was drafted by the assistant by eye, without model output, and the owner approved proceeding with it. It has **not been independently reviewed row by row** by a named reviewer.
- **Evaluation use of the clip is NOT approved** (licence reviewer has not confirmed).

## Results (scored on the system's own `zone_incursion` flag)
| Case | Frame (s) | Expected | System | Distance to expected position | Outcome |
| --- | --- | --- | --- | --- | --- |
| O1 | 2.0 | outside | outside | 119 px | **MATCH** |
| O2 | 10.01 | outside | - | - | **NOT_DETECTED** |
| O2b | 10.28 | outside | outside | 21 px | **MATCH** |
| O3 | 12.01 | outside | outside | 58 px | **MATCH** |
| I1 | 10.01 | inside | inside | 3 px | **MATCH** |
| I2 | 8.01 | inside | inside | 45 px | **MATCH** |
| I3 | 14.01 | inside | inside | 43 px | **MATCH** |

Counts: {'MATCH': 6, 'MISMATCH': 0, 'NOT_DETECTED': 1, 'NO_FRAME': 0}.
- **O2 NOT_DETECTED** is a detection limitation, not a zone failure: at 10.0 s the model produced no person box for the navy-jacket worker (only a weak helmet 0.34 and vest 0.29). The same worker is detected one sample later (O2b) and is correctly outside. This is reported, not hidden.

## Constructed boundary case (real foot point, polygon edge placed through it)
Measured foot point from the real run: `[1430.8234252929688, 666.7547607421875]` (case I1).
| Construction | Foot counted inside? | Expected |
| --- | --- | --- |
| Edge passes exactly through the foot point | True | True |
| Edge 0.001 px beyond the foot point | False | False |
| Edge 0.001 px on the other side | True | True |
| Foot point is exactly a polygon corner | True | True |
Outcome: **MATCH**. This case is **constructed**, not natural footage.

## Not covered (why VAL-04 is still open)
1. **Combined PPE-plus-zone case (C1):** the clip has no PPE violator. Needs another approved clip.
2. **Evaluation-use licence** for the clip: licence reviewer.
3. **Independent review** of the expected-cases table by a named reviewer (reviewer and date).
4. The zone is a stand-in; it says nothing about where a real restricted area should be.
5. One case (O2) was NOT_DETECTED, so the zone check cannot catch a worker the model never sees.

Re-run command for the scoring step: `.venv/bin/python scripts/val04_zone_cases.py --cases config/val04_cases.pexels_10294766.yaml --run ../reports/val04/pexels_partial_20261004/incidents.json --out <result.json>`
