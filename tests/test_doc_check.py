"""Les interfaces annoncées comme livrées existent ; les interfaces prévues restent informatives."""

from pathlib import Path

import pytest

from tests.doc_check import check, rows

ARCHITECTURE = Path(__file__).resolve().parents[1] / "docs" / "ARCHITECTURE.md"


def test_published_inventory_covers_every_module_and_matches_the_code():
    entries = rows(ARCHITECTURE.read_text())
    delivered = [entry for entry in entries if entry[0] == "livré"]
    assert len(delivered) >= 18
    assert {entry[1].split(".")[0] for entry in delivered} == {
        "kernel", "journal", "verifier", "bridge", "workspace", "engine", "campaign",
        "lifecycle", "broker", "observatory", "refinery",
    }
    assert check(entries) == []


def test_an_absent_planned_interface_is_not_a_failed_delivery():
    assert check([("prévu", "engine.walk", "walk(tree, budget, deps)")]) == []


@pytest.mark.parametrize("signature", ["absent(path)", "read(wrong)", "read(*, path)", "read(path=None)"])
def test_a_missing_or_divergent_delivered_signature_is_detected(signature):
    assert check([("livré", "journal", signature)])


def test_document_parser_cannot_silently_cover_nothing():
    with pytest.raises(ValueError):
        rows("# Empty architecture")


def test_runtime_signature_mutation_reaches_the_document_check(monkeypatch):
    import journal

    entries = [("livré", "journal", "read(path)")]
    assert check(entries) == []
    monkeypatch.setattr(journal, "read", lambda wrong: None)
    assert check(entries)
