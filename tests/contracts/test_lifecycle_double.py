"""Les ports du verrou et du worker restent identiques sur leurs doubles sans I/O."""

import inspect

import pytest

from lifecycle.execution import MissionProcess, MissionProcessPort
from lifecycle.lock import LockPort, RunLock


def test_signatures(double):
    memory = double("lifecycle")
    for contract, real, fake, names in (
        (LockPort, RunLock, memory.MemoryLock, ("acquire", "release")),
        (MissionProcessPort, MissionProcess, memory.MemoryMissionProcess, ("run",)),
    ):
        assert isinstance(fake(), contract)
        for name in names:
            expected = inspect.signature(getattr(contract, name))
            assert inspect.signature(getattr(real, name)) == expected
            assert inspect.signature(getattr(fake, name)) == expected


def test_signature_mutation_is_detected(double, monkeypatch):
    memory = double("lifecycle")
    monkeypatch.setattr(memory.MemoryMissionProcess, "run", lambda self, wrong: None)
    with pytest.raises(AssertionError):
        test_signatures(lambda name: memory)


def test_worker_double_never_executes_the_callback(double):
    worker = double("lifecycle").MemoryMissionProcess()

    def forbidden():
        raise AssertionError("double executed the worker")

    worker.run(forbidden, 42)
    assert worker.calls == [(forbidden, 42)]
