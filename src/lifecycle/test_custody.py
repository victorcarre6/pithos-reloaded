"""Arrêt d'un groupe réel et refus des empreintes qui ne correspondent plus."""

import os
import subprocess
import sys
import time

import pytest

from lifecycle.custody import IdentityMismatch, kill_group, sweep_orphans
from lifecycle.lock import record
from lifecycle.process import fingerprint, process_start


def test_microsecond_identity_is_stable():
    identity = process_start(os.getpid())
    assert identity is not None
    seconds, microseconds = identity.split(":")
    assert int(seconds) > 0
    assert len(microseconds) == 6
    assert 0 <= int(microseconds) < 1_000_000
    assert process_start(os.getpid()) == identity


def test_kill_group_stops_child_and_grandchild(tmp_path):
    source = (
        "import subprocess, sys, time\n"
        "from pathlib import Path\n"
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
        "Path(sys.argv[1]).write_text(str(child.pid))\n"
        "time.sleep(30)\n"
    )
    evidence = tmp_path / "grandchild"
    parent = subprocess.Popen([sys.executable, "-c", source, str(evidence)], start_new_session=True)
    try:
        deadline = time.monotonic() + 3
        while not evidence.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert evidence.exists()
        grandchild = int(evidence.read_text())
        expected = fingerprint(parent.pid)
        assert expected is not None
        assert os.getpgid(grandchild) == parent.pid
        kill_group(parent.pid, expected=expected)
        assert parent.wait(timeout=2) == -9
        result = subprocess.run(
            ["/bin/ps", "-p", str(grandchild), "-o", "stat="],
            capture_output=True, text=True, check=False,
        )
        assert not result.stdout.strip() or result.stdout.strip().startswith("Z")
        kill_group(parent.pid, expected=expected)
    finally:
        if parent.poll() is None:
            os.killpg(parent.pid, 9)
            parent.wait(timeout=2)


def test_recycled_identity_never_signals(monkeypatch, double):
    import lifecycle.custody as custody

    current = fingerprint(os.getpid())
    assert current is not None
    previous = current.model_copy(update={"start_time": "previous"})
    signalled = []
    monkeypatch.setattr(custody.os, "killpg", lambda *args: signalled.append(args))
    with pytest.raises(IdentityMismatch):
        kill_group(current.pid, expected=previous)
    assert signalled == []


def test_sweep_reconciles_a_zombie_group_without_signalling(tmp_path, trace, monkeypatch):
    import lifecycle.custody as custody

    # garder le leader sorti non récolté pour reproduire la fenêtre observée après sigkill
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True)
    try:
        identity = fingerprint(child.pid)
        assert identity is not None
        child.kill()
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            state = subprocess.run(["/bin/ps", "-p", str(child.pid), "-o", "stat="],
                                   capture_output=True, text=True, check=True)
            if state.stdout.strip().startswith("Z"):
                break
            time.sleep(0.01)
        assert state.stdout.strip().startswith("Z")
        assert process_start(child.pid) is None
        assert fingerprint(child.pid) != identity
        os.kill(child.pid, 0)

        # propriétaire d'une génération antérieure ; aucun signal sur un groupe déjà sorti
        record(trace, "process_started", process=identity.model_dump(), owner_pid=os.getpid(),
               owner_start="previous", process_scope="session")
        signals = []
        monkeypatch.setattr(custody.os, "killpg", lambda *args: signals.append(args))
        assert sweep_orphans(events_path=tmp_path / "events", trace=trace) == [child.pid]
        assert signals == []
        assert trace.events[-1].payload["operation"] == "process_stopped"
    finally:
        child.kill()
        child.wait(timeout=2)


def test_unreadable_live_group_never_signals(monkeypatch):
    import lifecycle.custody as custody

    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True)
    try:
        identity = fingerprint(child.pid)
        assert identity is not None
        signals = []
        monkeypatch.setattr(custody, "fingerprint", lambda pid: None)
        monkeypatch.setattr(custody.os, "killpg", lambda *args: signals.append(args))
        with pytest.raises(IdentityMismatch):
            kill_group(child.pid, expected=identity)
        assert signals == []
        assert child.poll() is None
    finally:
        child.kill()
        child.wait(timeout=2)


def test_sweep_only_reaps_matching_process_of_proven_dead_owner(tmp_path, trace, monkeypatch):
    import lifecycle.custody as custody
    from lifecycle.process import ProcessIdentity

    entries = [
        {"pid": 201, "owner_pid": 101, "scope": "session", "start_time": "old"},
        {"pid": 202, "owner_pid": 102, "scope": "session", "start_time": "old"},
        {"pid": 203, "owner_pid": 101, "scope": "daemon", "start_time": "old"},
        {"pid": 204, "owner_pid": 101, "scope": "task", "start_time": "old"},
    ]
    identities = {}
    for entry in entries:
        identity = ProcessIdentity(pid=entry["pid"], start_time=entry["start_time"], cmd_sha256="a" * 64)
        identities[identity.pid] = identity
        record(trace, "process_started", process=identity.model_dump(), owner_pid=entry["owner_pid"],
               owner_start="owner", process_scope=entry["scope"])
    identities[204] = identities[204].model_copy(update={"start_time": "recycled"})

    def alive(pid, signal):
        if pid == 101:
            raise ProcessLookupError

    stopped = []
    monkeypatch.setattr(custody.os, "kill", alive)
    monkeypatch.setattr(custody, "process_start", lambda pid: "owner")
    monkeypatch.setattr(custody, "fingerprint", identities.get)
    monkeypatch.setattr(custody, "kill_group", lambda pid, **kwargs: stopped.append(pid))
    events = tmp_path / "events.jsonl"
    assert sweep_orphans(events_path=events, trace=trace) == [201]
    assert stopped == [201]
    assert trace.events[-1].payload["operation"] == "process_stopped"
    assert sweep_orphans(events_path=events, trace=trace) == []


def test_unreadable_owner_never_authorizes_reaping(tmp_path, trace, monkeypatch):
    import lifecycle.custody as custody
    from lifecycle.process import ProcessIdentity

    identity = ProcessIdentity(pid=201, start_time="process", cmd_sha256="a" * 64)
    record(trace, "process_started", process=identity.model_dump(), owner_pid=101,
           owner_start="owner", process_scope="session")
    monkeypatch.setattr(custody.os, "kill", lambda *args: None)
    monkeypatch.setattr(custody, "process_start", lambda pid: None)
    assert sweep_orphans(events_path=tmp_path / "events", trace=trace) == []
