"""Écritures réelles sur cibles de test ; kernel injecté sous sa forme mémoire."""

from hashlib import sha256
from pathlib import Path

import pytest

from kernel.errors import PithosError
from workspace import StaleContentError, Transaction


BEFORE = b"\xef\xbb\xbf# keep\r\ndef f(x):\r\n    return x\r\n"


@pytest.fixture
def target(workspace):
    path = workspace.root / "tool.py"
    path.write_bytes(BEFORE)
    path.chmod(0o640)

    return path


def test_splice_writes_one_target_and_returns_measured_fact(workspace, target):
    fact = workspace.splice(target, "f", "def f(x):\n    return 7")
    after = target.read_bytes()
    assert after == BEFORE.replace(b"return x", b"return 7")
    assert fact.path == target
    assert fact.sha_before == sha256(BEFORE).hexdigest()
    assert fact.sha_after == sha256(after).hexdigest()
    assert fact.n_replacements == 1
    assert target.stat().st_mode & 0o777 == 0o640
    assert list(workspace.root.iterdir()) == [target]


@pytest.mark.parametrize("source", [
    '{}', 'def f(x): pass\ndef g(x): pass', 'def other(x): pass',
    'def f(x, y): pass', 'def f(x): break', 'def f(x):\n    return x',
])
def test_rejections_never_write(workspace, target, source, monkeypatch):
    import workspace.transaction as transactions

    def forbidden(*args, **kwargs):
        raise AssertionError("staging started before validation")

    monkeypatch.setattr(transactions.tempfile, "mkstemp", forbidden)
    with pytest.raises(PithosError):
        workspace.splice(target, "f", source)
    assert target.read_bytes() == BEFORE


def test_restore_is_exact_and_repeatable(workspace, target):
    with workspace.transaction(target) as transaction:
        assert transaction.before == BEFORE
        transaction.cas_write(b"def f(x): return 4\n")
        transaction.restore()
        transaction.restore()
    assert sha256(target.read_bytes()).digest() == sha256(BEFORE).digest()


@pytest.mark.parametrize("error", [RuntimeError("red"), KeyboardInterrupt(), TimeoutError("deadline")])
def test_exception_exit_restores_bytes(workspace, target, error):
    with pytest.raises(type(error)):
        with workspace.transaction(target) as transaction:
            transaction.cas_write(b"def f(x): return 4\n")
            raise error
    assert target.read_bytes() == BEFORE


def test_stale_write_does_not_restore_over_competing_writer(workspace, target):
    competing = b"def f(x): return 99\n"
    with pytest.raises(StaleContentError):
        with workspace.transaction(target) as transaction:
            target.write_bytes(competing)
            transaction.cas_write(b"def f(x): return 4\n")
    assert target.read_bytes() == competing


def test_stale_check_is_repeated_after_staging(workspace, target, monkeypatch):
    import workspace.transaction as transactions

    real_fsync = transactions.os.fsync
    competing = b"def f(x): return 99\n"

    def interleave(fd):
        real_fsync(fd)
        target.write_bytes(competing)

    monkeypatch.setattr(transactions.os, "fsync", interleave)
    with pytest.raises(StaleContentError):
        with workspace.transaction(target) as transaction:
            transaction.cas_write(b"def f(x): return 4\n")
    assert target.read_bytes() == competing


@pytest.mark.parametrize("failing_call", ["mkstemp", "replace", "fsync"])
def test_io_failure_retains_target(workspace, target, monkeypatch, failing_call):
    import workspace.transaction as transactions

    def failed(*args, **kwargs):
        raise OSError("injected disk error")

    owner = transactions.tempfile if failing_call == "mkstemp" else transactions.os
    monkeypatch.setattr(owner, failing_call, failed)
    with pytest.raises(OSError, match="injected disk error"):
        with workspace.transaction(target) as transaction:
            transaction.cas_write(b"def f(x): return 4\n")
    assert target.read_bytes() == BEFORE


def test_snapshot_is_taken_at_entry(workspace, target):
    transaction = workspace.transaction(target)
    target.write_bytes(b"new before")
    with transaction:
        assert transaction.before == b"new before"


def test_transaction_is_exported(workspace, target):
    assert isinstance(workspace.transaction(target), Transaction)


def test_failed_candidate_and_byte_snapshots_are_archived(workspace, target, journal_double):
    with pytest.raises(PithosError):
        workspace.splice(target, "f", "{}")
    assert journal_double.events[0].payload["new_source"] == "{}"
    workspace.splice(target, "f", "def f(x): return 7")
    event = journal_double.events[-1]
    assert event.durable is True
    assert bytes.fromhex(event.payload["before_hex"]) == BEFORE
    assert bytes.fromhex(event.payload["after_hex"]) == target.read_bytes()


def test_failed_journal_prevents_writing(workspace, target, journal_double):
    journal_double.disk_full = True
    with pytest.raises(PithosError, match="attempt_not_written"):
        workspace.splice(target, "f", "def f(x): return 7")
    assert target.read_bytes() == BEFORE


def test_journal_failure_after_mutation_does_not_prevent_restore(workspace, target, journal_double):
    with pytest.raises(RuntimeError, match="red"):
        with workspace.transaction(target) as transaction:
            transaction.splice("f", "def f(x): return 7")
            journal_double.disk_full = True
            raise RuntimeError("red")
    assert target.read_bytes() == BEFORE


def test_restore_failure_keeps_original_error(workspace, target, monkeypatch):
    with pytest.raises(ExceptionGroup) as caught:
        with workspace.transaction(target) as transaction:
            transaction.cas_write(b"def f(x): return 7\n")

            def failed():
                raise OSError("restore failed")

            monkeypatch.setattr(transaction, "restore", failed)
            raise ValueError("invariant failed")
    assert [str(error) for error in caught.value.exceptions] == ["invariant failed", "restore failed"]
    assert transaction.before == BEFORE


def test_two_competing_snapshots_cannot_both_write(workspace, target):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    barrier = Barrier(2)

    def run(number):
        try:
            with workspace.transaction(target) as transaction:
                barrier.wait(timeout=3)
                transaction.cas_write(f"def f(x): return {number}\n".encode())
        except StaleContentError:
            return "stale"

        return "written"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(run, [1, 2]))
    assert sorted(outcomes) == ["stale", "written"]


def test_symlink_change_during_staging_cannot_redirect_write(workspace, target, monkeypatch):
    import workspace.transaction as transactions

    other = workspace.root / "other.py"
    other.write_bytes(BEFORE)
    real_fsync = transactions.os.fsync

    def redirect(fd):
        real_fsync(fd)
        target.unlink()
        target.symlink_to(other)

    monkeypatch.setattr(transactions.os, "fsync", redirect)
    with pytest.raises(StaleContentError):
        workspace.splice(target, "f", "def f(x): return 7")
    assert other.read_bytes() == BEFORE


def test_transaction_requires_active_context(workspace, target):
    transaction = workspace.transaction(target)
    for action in (lambda: transaction.cas_write(b"x"), transaction.restore, lambda: transaction.splice("f", "def f(x): pass")):
        with pytest.raises(RuntimeError, match="not active"):
            action()
    with transaction:
        pass
    with pytest.raises(RuntimeError, match="single-use"):
        transaction.__enter__()


def test_raw_write_cannot_exceed_restorable_size(workspace, target):
    from kernel.codeview import MAX_SOURCE_BYTES

    with workspace.transaction(target) as transaction:
        with pytest.raises(PithosError, match="oversized"):
            transaction.cas_write(b"x" * (MAX_SOURCE_BYTES + 1))
    assert target.read_bytes() == BEFORE
