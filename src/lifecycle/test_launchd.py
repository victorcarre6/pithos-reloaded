"""Les ticks sont consommés avant livraison, sans file d'attente implicite."""

from lifecycle.launchd import claim_tick
from lifecycle.lock import LockState, RunLock


def test_close_ticks_are_coalesced_and_never_replayed(tmp_path, trace):
    path = tmp_path / "run"
    first = RunLock(path, max_seconds=60, trace=trace, identity=lambda pid: "current")
    second = RunLock(path, max_seconds=60, trace=trace, identity=lambda pid: "current")
    events = tmp_path / "events.jsonl"
    assert claim_tick("tick1", lock=first, events_path=events, trace=trace)
    assert trace.events[-1].payload["operation"] == "tick_claimed"
    assert not claim_tick("tick2", lock=second, events_path=events, trace=trace)
    assert path.exists()
    first.release()
    assert not claim_tick("tick2", lock=second, events_path=events, trace=trace)
    assert not claim_tick("tick1", lock=second, events_path=events, trace=trace)
    assert claim_tick("tick3", lock=second, events_path=events, trace=trace)
    second.release()


def test_failed_persistence_never_delivers(tmp_path, trace):
    trace.disk_full = True
    lock = RunLock(tmp_path / "run", max_seconds=60, trace=trace, identity=lambda pid: "current")
    assert not claim_tick("tick1", lock=lock, events_path=tmp_path / "events.jsonl", trace=trace)
    assert lock.acquire() == LockState.held
    lock.release()


def test_unreadable_lock_blocks_caller(tmp_path, trace):
    path = tmp_path / "run"
    path.mkdir()
    lock = RunLock(path, max_seconds=60, trace=trace, identity=lambda pid: "current")
    assert not claim_tick("tick1", lock=lock, events_path=tmp_path / "events.jsonl", trace=trace)
    assert list(path.iterdir()) == []


def test_failed_replay_releases_lock_without_delivery(tmp_path, trace, monkeypatch):
    def fail(path):
        raise OSError("unreadable ledger")

    monkeypatch.setattr(trace, "read", fail)
    lock = RunLock(tmp_path / "run", max_seconds=60, trace=trace, identity=lambda pid: "current")
    assert not claim_tick("tick1", lock=lock, events_path=tmp_path / "events.jsonl", trace=trace)
    assert lock.acquire() == LockState.held
    lock.release()
