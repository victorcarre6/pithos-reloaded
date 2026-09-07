"""Persistance du reçu sur le double journal ; aucune attestation d'effet externe implicite."""

import pytest

from kernel.facts import RecordKey
from verifier.gates import check_sources
from verifier.receipt import emit_receipt


@pytest.fixture(scope="module")
def verified(kernel_double, tmp_path_factory):
    criterion = kernel_double.criterion(relation="round_trip", symbols=["f", "g"])
    before = "def f(x): return x + 2\ndef g(x): return x - 1\n"
    after = "def f(x): return x + 1\ndef g(x): return x - 1\n"

    return check_sources(criterion, before, after, artifact_root=tmp_path_factory.mktemp("receipt"), timeout=10)


@pytest.fixture
def key():
    return RecordKey(kind="verification", value=("mission-1", "node-1", 1, "round_trip"))


def test_receipt_only_returned_after_ack(kernel_double, journal_double, verified, key):
    receipt = emit_receipt("node-1", 1, [kernel_double.file_fact()], verified.after.artifact_path,
                           key=key, verdict=verified, journal=journal_double)
    assert receipt is not None
    assert receipt.returncode == 0
    assert len(journal_double.events) == 1
    event = journal_double.events[0]
    assert event.durable is True
    assert event.type == "validation"
    assert event.payload["receipt"] == receipt.model_dump(mode="json")
    assert event.payload["key"] == key.model_dump(mode="json")
    assert event.payload["scope"] == "source_verification"
    assert event.payload["effect"] == "unproven"


def test_absent_receipt_when_journal_refuses(kernel_double, journal_double, verified, key):
    journal_double.disk_full = True
    receipt = emit_receipt("node-1", 1, [kernel_double.file_fact()], verified.after.artifact_path,
                           key=key, verdict=verified, journal=journal_double)
    assert receipt is None
    assert journal_double.events == []


@pytest.mark.parametrize("value", [
    ("mission-1", "other-node", 1, "round_trip"),
    ("mission-1", "node-1", 2, "round_trip"),
    ("mission-1", "node-1", 1, "total"),
])
def test_mismatched_identity_never_attempts_write(kernel_double, journal_double, verified, value):
    key = RecordKey(kind="verification", value=value)
    with pytest.raises(ValueError, match="identity"):
        emit_receipt("node-1", 1, [kernel_double.file_fact()], verified.after.artifact_path,
                     key=key, verdict=verified, journal=journal_double)
    assert journal_double.events == []


def test_no_fallback_from_raw_string_identity(kernel_double, journal_double, verified):
    with pytest.raises(ValueError, match="typed"):
        emit_receipt("node-1", 1, [kernel_double.file_fact()], verified.after.artifact_path,
                     key="node-1", verdict=verified, journal=journal_double)
    assert journal_double.events == []


def test_no_receipt_for_another_artifact(kernel_double, journal_double, verified, key, tmp_path):
    with pytest.raises(ValueError, match="artifact"):
        emit_receipt("node-1", 1, [kernel_double.file_fact()], tmp_path / "foreign.py",
                     key=key, verdict=verified, journal=journal_double)
    assert journal_double.events == []


def test_no_receipt_for_rejected_gate(kernel_double, journal_double, verified, key):
    values = verified.model_dump()
    values.update(verification="rejected", reason="after_red")
    rejected = type(verified)(**values)
    with pytest.raises(ValueError, match="verified"):
        emit_receipt("node-1", 1, [kernel_double.file_fact()], verified.after.artifact_path,
                     key=key, verdict=rejected, journal=journal_double)
    assert journal_double.events == []
