"""Time-based sustained-incident smoothing (NFR-04, ADR-007).

An incident is raised only after a rule has been observed continuously for `hold_seconds`, measured on frame
timestamps (not frame counts), so it behaves the same at any frame rate. Observations further apart than
`max_gap_seconds` start a new run. One incident per sustained episode; a rule that disappears for longer than the gap
re-arms. State is per rule (for example "PPE_VEST_MISSING"), never per person: no identity or tracking is stored.
"""
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True)
class Incident:
    rule: str
    started_at: float      # first observation of the run (seconds)
    detected_at: float     # timestamp at which the hold time was reached
    frame_id: Optional[str] = None


class _Run:
    __slots__ = ("first", "last", "fired")

    def __init__(self, ts: float) -> None:
        self.first, self.last, self.fired = ts, ts, False


class SustainedDetector:
    def __init__(self, hold_seconds: float = 1.5, max_gap_seconds: float = 1.0) -> None:
        if hold_seconds < 0 or max_gap_seconds <= 0:
            raise ValueError("hold_seconds must be >= 0 and max_gap_seconds > 0")
        self.hold = float(hold_seconds)
        self.max_gap = float(max_gap_seconds)
        self._runs: Dict[str, _Run] = {}
        self._now: Optional[float] = None

    def update(self, timestamp: float, active_rules: Iterable[str], frame_id: Optional[str] = None) -> List[Incident]:
        """Feed one frame. `timestamp` is seconds and must not go backwards. Returns incidents raised by this frame."""
        if self._now is not None and timestamp < self._now:
            raise ValueError(f"timestamps must not decrease ({timestamp} < {self._now})")
        self._now = timestamp
        active = set(active_rules)
        for rule in list(self._runs):
            if rule not in active and timestamp - self._runs[rule].last > self.max_gap:
                del self._runs[rule]                      # run ended; the rule can fire again later
        raised = []
        for rule in sorted(active):
            run = self._runs.get(rule)
            if run is None or timestamp - run.last > self.max_gap:
                run = self._runs[rule] = _Run(timestamp)  # new run
            else:
                run.last = timestamp
            if not run.fired and run.last - run.first >= self.hold:
                run.fired = True
                raised.append(Incident(rule, run.first, timestamp, frame_id))
        return raised
