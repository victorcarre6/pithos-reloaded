"""Publication locale reconnue après perte d'acquittement, sans second commit."""

from hashlib import sha256
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from broker.finalize import GreenFinalizer
from broker.git import repo_fact
from broker.test_git import repo, run
from kernel.contracts import Event
from kernel.errors import PithosError
from kernel.facts import FileFact, Receipt, RecordKey, SourceFact


@pytest.fixture
def proof(repo, trace):
    target = repo / "kept.py"
    before = target.read_bytes()
    after = b"value = 2\n"
    target.write_bytes(after)
    source = SourceFact(path=target, before=before, after=after)
    file = FileFact(path=target, sha_before=sha256(before).hexdigest(), sha_after=sha256(after).hexdigest(),
                    spliced_range=(1, 1), n_replacements=1)
    receipt = Receipt(node_id="node", attempt=1, returncode=0, artifact_path=repo.parent / "gate.py",
                      facts=[file, source, repo_fact(repo)])
    key = RecordKey(kind="verification", value=("mission", "node", 1, "idempotent"))
    trace.emit(Event(ts="2026-09-14T00:00:00+00:00", v=1, type="validation", durable=True, payload={
        "scope": "node_verification",
        "effect": "confirmed",
        "key": key.model_dump(mode="json"),
        "receipt": receipt.model_dump(mode="json"),
    }))
    ledger = repo.parent / "effects.json"
    events = repo.parent / "events.jsonl"
    finalizer = GreenFinalizer(repo, ledger=ledger, events_path=events, trace=trace)

    return SimpleNamespace(repo=repo, target=target, receipt=receipt, key=key, trace=trace,
                           finalizer=finalizer, ledger=ledger, events=events)


def test_finalization_and_reconciliation_create_only_one_commit(proof):
    p = proof
    before = repo_fact(p.repo).head
    assert p.finalizer.reconcile(p.key, p.receipt, 5) is None
    result = p.finalizer.finalize(p.key, p.receipt, 5)
    assert result.head != before
    assert result.complete and not result.changes and not result.diff
    assert run(p.repo, "show", "--format=", "--name-only", "HEAD").stdout.strip() == "kept.py"
    resumed = GreenFinalizer(p.repo, ledger=p.ledger, events_path=p.events, trace=p.trace)
    assert resumed.reconcile(p.key, p.receipt, 5) == result
    assert resumed.finalize(p.key, p.receipt, 5) == result
    assert run(p.repo, "rev-list", "--count", "HEAD").stdout.strip() == "2"
    assert [event.payload.get("operation") for event in p.trace.events[1:]] == ["commit_intent", "commit_result"]


def test_lost_commit_acknowledgement_is_interrogated_before_replay(proof):
    p = proof

    def lost(command, **kwargs):
        result = subprocess.run(command, **kwargs)
        if "commit" in command:
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])

        return result

    p.finalizer.runner = lost
    with pytest.raises(PithosError):
        p.finalizer.finalize(p.key, p.receipt, 5)
    p.finalizer.runner = subprocess.run
    found = p.finalizer.reconcile(p.key, p.receipt, 5)
    assert found.head == repo_fact(p.repo).head
    assert run(p.repo, "rev-list", "--count", "HEAD").stdout.strip() == "2"


@pytest.mark.parametrize("fault", ["missing_receipt", "foreign_key", "source_changed", "extra_file", "attributes"])
def test_unattested_or_changed_effect_is_refused(proof, fault):
    p = proof
    head = repo_fact(p.repo).head
    if fault == "missing_receipt":
        p.trace.events.clear()
    elif fault == "foreign_key":
        p.key = RecordKey(kind="verification", value=("foreign", "node", 1, "idempotent"))
    elif fault == "source_changed":
        p.target.write_bytes(b"foreign edit\n")
    elif fault == "extra_file":
        (p.repo / "extra.py").write_bytes(b"unattested\n")
    else:
        (p.repo / ".git" / "info" / "attributes").write_text("*.py filter=untrusted\n")
    with pytest.raises((PithosError, ValueError)):
        p.finalizer.finalize(p.key, p.receipt, 5)
    assert repo_fact(p.repo).head == head


def test_foreign_commit_is_not_mistaken_for_our_publication(proof):
    p = proof
    run(p.repo, "commit", "-qm", "foreign", "--", "kept.py")
    with pytest.raises(PithosError):
        p.finalizer.reconcile(p.key, p.receipt, 5)
    assert run(p.repo, "rev-list", "--count", "HEAD").stdout.strip() == "2"


def test_a_durability_failure_prevents_the_commit(proof):
    p = proof
    head = repo_fact(p.repo).head
    p.trace.disk_full = True
    with pytest.raises(PithosError):
        p.finalizer.finalize(p.key, p.receipt, 5)
    assert repo_fact(p.repo).head == head


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan"), True])
def test_invalid_deadline_never_starts_git(proof, timeout):
    p = proof
    calls = []
    p.finalizer.runner = lambda *args, **kwargs: calls.append(args)
    with pytest.raises((PithosError, ValueError)):
        p.finalizer.finalize(p.key, p.receipt, timeout)
    assert calls == []


def test_all_commands_share_the_remaining_deadline(proof):
    p = proof
    now = [0.0]
    durations = []

    def delayed(command, **kwargs):
        durations.append(kwargs["timeout"])
        result = subprocess.run(command, **kwargs)
        now[0] += 0.4

        return result

    p.finalizer.clock = lambda: now[0]
    p.finalizer.runner = delayed
    head = repo_fact(p.repo).head
    with pytest.raises(PithosError):
        p.finalizer.finalize(p.key, p.receipt, 1)
    assert durations == pytest.approx([1, 0.6, 0.2])
    assert repo_fact(p.repo).head == head


def test_double_preserves_publication_when_acknowledgement_is_lost(proof, double):
    p = proof
    expected = repo_fact(p.repo)
    port = double("broker").MemoryGreenFinalizer(expected)
    port.lose_ack = True
    with pytest.raises(TimeoutError):
        port.finalize(p.key, p.receipt, 5)
    assert port.reconcile(p.key, p.receipt, 5) == expected
    assert port.finalize(p.key, p.receipt, 5) == expected
    assert sum(call[0] == "finalize" for call in port.calls) == 1


def test_git_hooks_cannot_modify_the_attested_effect(proof):
    p = proof
    hook = p.repo / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\nprintf changed > kept.py\nexit 1\n")
    hook.chmod(0o700)
    result = p.finalizer.finalize(p.key, p.receipt, 5)
    assert result.complete and not result.changes
    assert p.target.read_bytes() == b"value = 2\n"


def test_result_projection_failure_is_reconciled(proof, monkeypatch):
    import broker.finalize as publication

    p = proof
    original = publication.record_result
    monkeypatch.setattr(publication, "record_result", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("disk")))
    with pytest.raises(OSError):
        p.finalizer.finalize(p.key, p.receipt, 5)
    monkeypatch.setattr(publication, "record_result", original)
    assert p.finalizer.reconcile(p.key, p.receipt, 5).head == repo_fact(p.repo).head
    assert run(p.repo, "rev-list", "--count", "HEAD").stdout.strip() == "2"
