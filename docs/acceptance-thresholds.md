# Acceptance thresholds (OPEN-07): set, locked before results

Set by the project owner on **2026-10-04**, before any model has been trained or evaluated.
Machine-readable values: `config/acceptance_thresholds.yaml`.
SHA-256 of that file at lock time: `46f6919fb3145f27ca52d930145c1998b48642408c2d1c8da74a256f4ee53ec0`

| Class | Minimum AP50 (IoU 0.5) |
| --- | --- |
| person | 0.80 |
| helmet | 0.80 |
| safety_vest | 0.75 |
| no_helmet | 0.60 |
| no_safety_vest | 0.60 |
| overall mAP50 | 0.70 |

Recall floor: **no_helmet and no_safety_vest each need recall of at least 0.60** at confidence 0.25, IoU 0.5.

## Rules
- Measured on the **independent evaluation set** (ADR-009). The CSS v27 held-out images are sanity checks only and cannot satisfy this test.
- **All** thresholds must hold. If the independent set does not exist yet, the result is "not evaluated", not "passed".
- No retuning after results are seen. If the owner wants different values, add a dated entry below with the reason,
  and re-lock the file hash. Results produced under the old values stay reported against the old values.
- Report the numbers actually measured, with dataset hash, checkpoint hash, thresholds used, Git commit and UTC date.
- Reaching these numbers does not approve deployment. It is the gate for moving to the FR-1 real-model check (S10).

## Rationale (owner profile: Balanced)
The negative classes have lower targets because they are rarer in the data and visually harder. The recall floor guards the costly failure,
a missed violation, which AP50 alone can hide.

## Change log
| Date | Change | Reason | New file hash |
| --- | --- | --- | --- |
| 2026-10-04 | Initial thresholds, Balanced profile plus recall floor | Owner decision, set before any results | `46f6919fb3145f27ca52d930145c1998b48642408c2d1c8da74a256f4ee53ec0` |
