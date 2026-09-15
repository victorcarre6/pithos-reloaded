"""Le verrou arbitre réellement entre processus, y compris lors d'une reprise."""

import json
import multiprocessing
import os

import pytest

from lifecycle.lock import LockState, RunLock


def contender(path, trace, start, finish, result):
    lock = RunLock(path, max_seconds=60, trace=trace)
    start.wait(timeout=5)
    result.send(lock.acquire().value)
    finish.wait(timeout=5)
    lock.release()
    result.close()


def test_two_real_forks_have_one_winner(tmp_path, trace):
    context = multiprocessing.get_context("fork")
    start = context.Event()
    finish = context.Event()
    children = []
    readers = []
    for _ in range(2):
        reader, writer = context.Pipe(duplex=False)
        child = context.Process(target=contender, args=(tmp_path / "run", trace, start, finish, writer))
        children.append(child)
        readers.append(reader)
        child.start()
        writer.close()
    try:
        start.set()
        states = []
        for reader in readers:
            assert reader.poll(5)
            states.append(reader.recv())
        assert sorted(states) == ["held", "unavailable"]
    finally:
        finish.set()
        for child in children:
            child.join(timeout=5)
            if child.is_alive():
                child.kill()
                child.join(timeout=5)
            assert child.exitcode == 0
        for reader in readers:
            reader.close()


def test_expiry_cannot_reclaim_a_living_owner(tmp_path, trace):
    now = [10.0]
    first = RunLock(tmp_path / "run", max_seconds=5, trace=trace, clock=lambda: now[0])
    assert first.acquire() == LockState.held
    original = (first.path / "owner.json").read_bytes()
    now[0] = 16.0
    second = RunLock(first.path, max_seconds=5, trace=trace, clock=lambda: now[0])
    assert second.acquire() == LockState.unavailable
    assert (first.path / "owner.json").read_bytes() == original
    assert trace.events == []
    second.release()
    assert first.path.exists()
    first.release()


def test_recycled_pid_does_not_authorize_old_release(tmp_path, trace):
    first = RunLock(tmp_path / "run", max_seconds=60, trace=trace, identity=lambda pid: "old")
    assert first.acquire() == LockState.held
    second = RunLock(first.path, max_seconds=60, trace=trace, identity=lambda pid: "new")
    assert second.acquire() == LockState.stale_reclaimed
    first.release()
    owner = json.loads((second.path / "owner.json").read_text())
    assert owner["pid"] == os.getpid()
    assert owner["start_time"] == "new"
    second.release()


@pytest.mark.parametrize("content", ["", "{", "{}", '[]', '{"pid":true}', '{"token":"../elsewhere"}'])
def test_unreadable_state_is_unavailable(tmp_path, trace, content):
    path = tmp_path / "run"
    path.mkdir()
    (path / "owner.json").write_text(content)
    lock = RunLock(path, max_seconds=60, trace=trace)
    assert lock.acquire() == LockState.unavailable
    lock.release()
    assert (path / "owner.json").read_text() == content


def test_unknown_start_identity_never_reclaims(tmp_path, trace):
    first = RunLock(tmp_path / "run", max_seconds=60, trace=trace)
    assert first.acquire() == LockState.held
    second = RunLock(first.path, max_seconds=60, trace=trace, identity=lambda pid: None)
    assert second.acquire() == LockState.unavailable
    first.release()


def test_failed_reclaim_journal_never_grants_lock(tmp_path, trace):
    first = RunLock(tmp_path / "run", max_seconds=1, trace=trace, identity=lambda pid: "old")
    assert first.acquire() == LockState.held
    trace.disk_full = True
    second = RunLock(first.path, max_seconds=1, trace=trace, identity=lambda pid: "new")
    assert second.acquire() == LockState.unavailable


def test_delayed_retirement_cannot_rename_new_owner(tmp_path, trace, monkeypatch):
    from pathlib import Path

    first = RunLock(tmp_path / "run", max_seconds=1, trace=trace, identity=lambda pid: "old")
    assert first.acquire() == LockState.held
    second = RunLock(first.path, max_seconds=1, trace=trace, identity=lambda pid: "new")
    third = RunLock(first.path, max_seconds=1, trace=trace, identity=lambda pid: "new")
    rename = Path.rename
    intervened = []

    def race(path, target):
        if path == first.path and not intervened:
            intervened.append(True)
            assert second.acquire() == LockState.stale_reclaimed

        return rename(path, target)

    monkeypatch.setattr(Path, "rename", race)
    assert third.acquire() == LockState.unavailable
    first.release()
    assert json.loads((first.path / "owner.json").read_text())["token"] == second.token
    second.release()


@pytest.mark.parametrize("seconds", [0, -1, float("inf"), float("nan")])
def test_invalid_duration_is_refused(tmp_path, trace, seconds):
    with pytest.raises(ValueError):
        RunLock(tmp_path / "run", max_seconds=seconds, trace=trace)
