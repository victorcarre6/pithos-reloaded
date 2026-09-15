"""Verrou et worker scriptés, sans processus ni accès disque."""

from collections.abc import Callable

from lifecycle.lock import LockState


class MemoryLock:
    def __init__(self, state=LockState.held):
        self.state = state
        self.owned = False

    def acquire(self) -> LockState:
        if self.owned:
            return LockState.unavailable
        self.owned = self.state in {LockState.held, LockState.stale_reclaimed}

        return self.state

    def release(self) -> None:
        self.owned = False


class MemoryMissionProcess:
    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def run(self, task: Callable[[], None], deadline: float) -> None:
        self.calls.append((task, deadline))
        if self.error is not None:
            raise self.error
