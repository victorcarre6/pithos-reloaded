"""Deadline monotone unique ; réserve fixe, sans estimation de coût ni borne de tours.

Adapté de unsloth/unsloth/dataprep/synthetic.py:172-177 et du principe de réserve
de ouroboros/ouroboros/task_pacing.py:199-224. Aucun calibrage EWMA repris.
"""

import math
import time


FINALIZATION_RESERVE_SECONDS = 5.0


class Budget:
    """Ferme l'admission avant la deadline pour laisser la réserve à la finalisation."""

    def __init__(self, seconds: float, *, clock=time.monotonic):
        if isinstance(seconds, bool) or not math.isfinite(seconds) or seconds <= 0:
            raise ValueError("budget must be finite and positive")
        self.clock = clock
        self.started = clock()
        self.deadline = self.started + seconds

    @property
    def elapsed(self) -> float:
        return max(0.0, self.clock() - self.started)

    @property
    def remaining(self) -> float:
        return max(0.0, self.deadline - self.clock())

    @property
    def spendable(self) -> float:
        return max(0.0, self.remaining - FINALIZATION_RESERVE_SECONDS)

    @property
    def can_start(self) -> bool:
        return self.spendable > 0
