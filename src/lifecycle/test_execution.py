"""Un worker frais ne commence qu'après admission durable, puis son groupe est récolté."""

from functools import partial
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

from lifecycle.execution import MissionProcess, run_command
from lifecycle.lock import LockState, RunLock, record
from lifecycle.process import ProcessIdentity


def task(path, action):
    assert signal.getsignal(signal.SIGALRM) == signal.SIG_DFL
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    path.write_text(str(child.pid))
    if action == "hang":
        time.sleep(30)
    if action == "fail":
        raise ValueError("worker failed")


@pytest.mark.parametrize("action", ["finish", "hang", "fail"])
def test_worker_and_descendant_are_stopped_before_lock_release(tmp_path, trace, action):
    lock = RunLock(tmp_path / "lock", max_seconds=1, trace=trace)
    mission = MissionProcess(lock, events_path=tmp_path / "events", trace=trace)
    evidence = tmp_path / "grandchild"
    started = time.monotonic()
    callback = partial(task, evidence, action)
    if action == "finish":
        mission.run(callback, started + 2)
    else:
        error = TimeoutError if action == "hang" else RuntimeError
        with pytest.raises(error):
            mission.run(callback, started + 2)
    assert time.monotonic() - started < 6
    assert not lock.path.exists()
    assert evidence.exists()
    result = subprocess.run(["/bin/ps", "-p", evidence.read_text(), "-o", "stat="], capture_output=True, text=True)
    assert not result.stdout.strip() or result.stdout.strip().startswith("Z")
    operations = [event.payload["operation"] for event in trace.events]
    assert operations == ["process_started", "process_stopped"]
    expected = {"finish": "completed", "hang": "unknown", "fail": "failed"}
    assert trace.events[-1].payload["outcome"] == expected[action]


def test_command_never_starts_if_its_custody_cannot_be_written(tmp_path, trace, monkeypatch):
    emit = trace.emit

    def refused(event):
        if event.payload.get("process_scope") == "task":
            return False
        return emit(event)

    monkeypatch.setattr(trace, "emit", refused)
    lock = RunLock(tmp_path / "lock", max_seconds=2, trace=trace)
    mission = MissionProcess(lock, events_path=tmp_path / "events", trace=trace)
    with pytest.raises(RuntimeError, match="custody was not written"):
        mission.run(partial(command_task, tmp_path, 1), time.monotonic() + 2)
    assert not (tmp_path / "pids").exists()
    assert not (tmp_path / "stdout.txt").exists()
    assert not lock.path.exists()


def test_unavailable_lock_or_journal_prevents_task_admission(tmp_path, trace):
    path = tmp_path / "lock"
    first = RunLock(path, max_seconds=1, trace=trace)
    assert first.acquire() == LockState.held
    contender = RunLock(path, max_seconds=1, trace=trace)
    mission = MissionProcess(contender, events_path=tmp_path / "events", trace=trace)
    evidence = tmp_path / "forbidden"
    with pytest.raises(RuntimeError, match="lock"):
        mission.run(partial(task, evidence, "finish"), time.monotonic() + 2)
    first.release()
    trace.disk_full = True
    with pytest.raises(RuntimeError, match="custody"):
        mission.run(partial(task, evidence, "finish"), time.monotonic() + 2)
    assert not evidence.exists()
    assert not path.exists()


def test_unresolved_custody_prevents_a_new_worker(tmp_path, trace):
    identity = ProcessIdentity(pid=os.getpid(), start_time="unknown", cmd_sha256="a" * 64)
    record(trace, "process_started", process=identity.model_dump(), owner_pid=os.getpid(),
           owner_start="unknown", process_scope="session")
    lock = RunLock(tmp_path / "lock", max_seconds=2, trace=trace)
    mission = MissionProcess(lock, events_path=tmp_path / "events", trace=trace)
    evidence = tmp_path / "forbidden"
    with pytest.raises(RuntimeError, match="custody"):
        mission.run(partial(task, evidence, "finish"), time.monotonic() + 2)
    assert not evidence.exists()


@pytest.mark.parametrize("deadline", [float("nan"), float("inf"), 0])
def test_invalid_or_expired_deadline_never_acquires_lock(tmp_path, trace, deadline):
    lock = RunLock(tmp_path / "lock", max_seconds=2, trace=trace)
    mission = MissionProcess(lock, events_path=tmp_path / "events", trace=trace)
    with pytest.raises((ValueError, TimeoutError)):
        mission.run(partial(task, tmp_path / "forbidden", "finish"), deadline)
    assert not lock.path.exists()


def command_task(directory, timeout):
    source = (
        "import os, subprocess, sys, time\n"
        "from pathlib import Path\n"
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
        "Path('pids').write_text(f'{os.getpid()} {child.pid}')\n"
        "print('gate admitted', flush=True)\n"
        "time.sleep(30)\n"
    )
    run_command([sys.executable, "-c", source], directory=directory, environment={}, timeout=timeout)


@pytest.mark.parametrize("gate_timeout", [0.6, 30])
def test_command_group_is_admitted_and_stopped_with_its_worker(tmp_path, trace, gate_timeout):
    for name in ("stdout.txt", "stderr.txt"):
        (tmp_path / name).touch()
    lock = RunLock(tmp_path / "lock", max_seconds=2, trace=trace)
    mission = MissionProcess(lock, events_path=tmp_path / "events", trace=trace)
    with pytest.raises((TimeoutError, RuntimeError)):
        mission.run(partial(command_task, tmp_path, gate_timeout), time.monotonic() + 2)
    assert (tmp_path / "stdout.txt").read_text() == "gate admitted\n"
    for pid in (tmp_path / "pids").read_text().split():
        observed = subprocess.run(["/bin/ps", "-p", pid, "-o", "stat="], capture_output=True, text=True)
        assert not observed.stdout.strip() or observed.stdout.strip().startswith("Z")
    operations = [event.payload["operation"] for event in trace.events]
    assert operations == ["process_started", "process_started", "process_stopped", "process_stopped"]
    assert len({event.payload["owner_pid"] for event in trace.events[:2]}) == 1
    assert not lock.path.exists()
