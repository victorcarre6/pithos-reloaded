"""`emit` et `update_json_locked` — durabilité, atomicité, et jamais d'exception."""

import errno
import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from journal import write
from journal.write import bind, emit, update_json_locked


def test_emit_writes_the_jsonl_line_and_its_live_projection(bound, an_event):
    events_path, live_path = bound

    assert emit(an_event(k=1)) is True

    row = json.loads(events_path.read_bytes())
    assert row["payload"] == {"k": 1}
    assert row["event_id"] == 1
    assert live_path.read_text(encoding="utf-8") == (
        "2026-09-06T00:00:00Z #1 validation [durable] (payload omitted: 1 keys)\n"
    )


def test_the_projection_declares_that_it_omits_the_payload(bound, an_event):
    _, live_path = bound

    emit(an_event(a=1, b=2, c=3))

    assert "(payload omitted: 3 keys)" in live_path.read_text(encoding="utf-8")


def test_each_line_is_written_in_a_single_write_syscall(bound, an_event, monkeypatch):
    events_path, live_path = bound
    real_write = os.write
    sizes = []

    def counting_write(fd, data):
        sizes.append(len(data))

        return real_write(fd, data)

    monkeypatch.setattr(write.os, "write", counting_write)
    emit(an_event(k=1))
    monkeypatch.undo()

    expected = [len(events_path.read_bytes()), len(live_path.read_bytes())]
    assert sorted(sizes) == sorted(expected)


def test_an_unavailable_projection_leaves_no_jsonl_line(tmp_path, an_event):
    events_path = tmp_path / "events.jsonl"
    live_path = tmp_path / "live.log"
    live_path.mkdir()
    bind(events_path, live_path)

    assert emit(an_event(k=1)) is False
    assert not events_path.exists()


def test_emit_returns_false_instead_of_raising_when_the_disk_is_full(bound, an_event, monkeypatch):
    events_path, _ = bound

    def no_space(fd, data):
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(write.os, "write", no_space)

    assert emit(an_event(k=1)) is False
    assert events_path.read_bytes() == b""


def test_emit_returns_false_instead_of_raising_on_a_read_only_directory(tmp_path, an_event):
    mission = tmp_path / "missions"
    mission.mkdir()
    bind(mission / "events.jsonl", tmp_path / "live.log")
    mission.chmod(0o500)

    try:
        assert emit(an_event(k=1)) is False
    finally:
        mission.chmod(0o700)


def test_a_failed_emit_does_not_consume_an_event_id(bound, an_event, monkeypatch):
    events_path, _ = bound
    monkeypatch.setattr(write.os, "write", lambda fd, data: (_ for _ in ()).throw(OSError(errno.ENOSPC, "full")))
    emit(an_event(k=1))
    monkeypatch.undo()

    assert emit(an_event(k=2)) is True
    assert json.loads(events_path.read_bytes())["event_id"] == 1


def test_event_ids_resume_across_two_bindings(bound, an_event):
    events_path, live_path = bound
    emit(an_event(k=1))
    emit(an_event(k=2))

    bind(events_path, live_path)
    emit(an_event(k=3))

    written_ids = [json.loads(line)["event_id"] for line in events_path.read_bytes().splitlines()]
    assert written_ids == [1, 2, 3]


def test_a_torn_tail_opens_a_linked_segment_and_is_never_repaired(tmp_path, an_event):
    events_path = tmp_path / "events.jsonl"
    complete = b'{"ts": "t", "v": 1, "type": "status", "durable": true, "payload": {}, "event_id": 1}\n'
    events_path.write_bytes(complete + b'{"ts": "t", "v": 1, "type": "sta')
    original = events_path.read_bytes()

    bind(events_path, tmp_path / "live.log")
    emit(an_event(k=1))

    segment = tmp_path / "events.1.jsonl"
    assert events_path.read_bytes() == original
    link, following = [json.loads(line) for line in segment.read_bytes().splitlines()]
    assert link["payload"]["segment_from"] == "events.jsonl"
    assert link["payload"]["torn_offset"] == len(complete)
    assert link["payload"]["torn_bytes"] == len(original) - len(complete)
    assert [link["event_id"], following["event_id"]] == [2, 3]


def test_a_new_binding_appends_to_the_last_open_segment(tmp_path, an_event):
    events_path = tmp_path / "events.jsonl"
    events_path.write_bytes(b'{"ts": "t", "v": 1, "type": "status", "durable": true, "payload": {}, "event_id": 1}\n{"torn')
    bind(events_path, tmp_path / "live.log")

    bind(events_path, tmp_path / "live.log")
    emit(an_event(k=1))

    assert not (tmp_path / "events.2.jsonl").exists()
    assert len((tmp_path / "events.1.jsonl").read_bytes().splitlines()) == 2


def test_update_json_locked_rereads_the_disk_inside_the_lock(bound, tmp_path):
    target = tmp_path / "tree.json"
    target.write_text(json.dumps({"n": 0}), encoding="utf-8")

    def slow_increment(current):
        time.sleep(0.3)

        return {"n": current["n"] + 1}

    holder = threading.Thread(target=update_json_locked, args=(target, slow_increment))
    holder.start()
    time.sleep(0.05)
    update_json_locked(target, lambda current: {"n": current["n"] + 10})
    holder.join()

    assert json.loads(target.read_text(encoding="utf-8")) == {"n": 11}


def test_update_json_locked_preserves_the_permission_bits(bound, tmp_path):
    target = tmp_path / "tree.json"
    target.write_text("{}", encoding="utf-8")
    target.chmod(0o640)

    update_json_locked(target, lambda current: {"n": 1})

    assert target.stat().st_mode & 0o777 == 0o640


def test_a_sigkill_before_the_rename_leaves_the_original_file_intact(tmp_path):
    target = tmp_path / "tree.json"
    target.write_text(json.dumps({"n": 0}), encoding="utf-8")
    original = target.read_bytes()
    script = (
        "import os, signal, sys\n"
        "from pathlib import Path\n"
        f"sys.path.insert(0, {str(Path(__file__).resolve().parents[1])!r})\n"
        "from journal import write\n"
        f"write.bind(Path({str(tmp_path / 'events.jsonl')!r}), Path({str(tmp_path / 'live.log')!r}))\n"
        "os.replace = lambda src, dst: os.kill(os.getpid(), signal.SIGKILL)\n"
        f"write.update_json_locked(Path({str(target)!r}), lambda current: {{'n': 99}})\n"
    )

    killed = subprocess.run([sys.executable, "-c", script], capture_output=True)

    assert killed.returncode == -signal.SIGKILL
    assert target.read_bytes() == original


def test_update_json_locked_leaves_no_temporary_behind_on_a_write_failure(bound, tmp_path, monkeypatch):
    target = tmp_path / "tree.json"
    target.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(write.os, "write", lambda fd, data: (_ for _ in ()).throw(OSError(errno.ENOSPC, "full")))

    with pytest.raises(OSError):
        update_json_locked(target, lambda current: {"n": 1})
    monkeypatch.undo()

    assert [entry.name for entry in tmp_path.iterdir() if ".tmp." in entry.name] == []


def test_a_failed_projection_does_not_retract_a_proof_already_written(bound, an_event, monkeypatch):
    events_path, live_path = bound
    real_write = os.write
    calls = []

    def failing_projection(fd, data):
        calls.append(fd)
        if len(calls) == 2:
            raise OSError(errno.ENOSPC, "No space left on device")

        return real_write(fd, data)

    monkeypatch.setattr(write.os, "write", failing_projection)
    written = emit(an_event(k=1))
    monkeypatch.undo()

    assert written is True
    assert json.loads(events_path.read_bytes())["event_id"] == 1
    assert live_path.read_bytes() == b""
    assert emit(an_event(k=2)) is True
    assert [json.loads(line)["event_id"] for line in events_path.read_bytes().splitlines()] == [1, 2]


def test_a_partial_proof_write_is_a_failure_and_is_never_projected(bound, an_event, monkeypatch):
    events_path, live_path = bound
    real_write = os.write
    monkeypatch.setattr(write.os, "write", lambda fd, data: real_write(fd, data[:10]))

    written = emit(an_event(k=1))
    monkeypatch.undo()

    assert written is False
    assert live_path.read_bytes() == b""


def test_emit_returns_false_when_the_lock_cannot_be_opened(bound, an_event, monkeypatch):
    monkeypatch.setattr(write, "_lock_path", write._lock_path.parent / "absent" / "x.lock")

    assert emit(an_event(k=1)) is False
