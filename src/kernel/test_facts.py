"""Contrats de preuves : forme fermée, octets intacts, aucune décision de vérité."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from kernel.codeview import MAX_SOURCE_BYTES
from kernel.facts import FileFact, Receipt, RepoChange, RepoFact, SourceFact


def test_source_bytes_survive_a_heterogeneous_receipt(kernel_double):
    raw = b"\xef\xbb\xbf# caf\xc3\xa9\r\n# \xff\x00\r\n"
    sources = SourceFact(path=Path("tool.py"), before=raw, after=raw + b"# end")
    repo = kernel_double.repo_fact(changes=[kernel_double.repo_change()])
    receipt = kernel_double.receipt(facts=[kernel_double.file_fact(), sources, repo])
    restored = Receipt.model_validate_json(receipt.model_dump_json())

    assert restored == receipt
    assert restored.facts[1].before == raw
    assert [type(fact) for fact in restored.facts] == [FileFact, SourceFact, RepoFact]
    assert not repo.complete


@pytest.mark.parametrize("field,value", [
    ("before", "def f(): pass"), ("after", bytearray(b"mutable")),
    ("before", b"x" * (MAX_SOURCE_BYTES + 1)),
    ("after", b"x" * (MAX_SOURCE_BYTES + 1)),
    ("path", ["a.py", "b.py"]), ("authority", "verifier"),
])
def test_source_fact_rejects_coercion_and_oversized_snapshots(field, value):
    data = {"path": Path("tool.py"), "before": b"", "after": b"x"}
    data[field] = value
    with pytest.raises(ValidationError):
        SourceFact(**data)


@pytest.mark.parametrize("changes", [
    {"status": ""}, {"status": "M"}, {"status": "ZZ"}, {"status": "  "},
    {"status": "R ", "origin": None}, {"origin": Path("old.py")},
    {"path": Path("../escape.py")}, {"path": Path("/absolute.py")},
    {"path": Path(".")}, {"status": "R ", "origin": Path("../escape.py")},
])
def test_repo_changes_refuse_ambiguous_status_and_unscoped_paths(changes):
    data = {"status": " M", "path": Path("tool.py"), "origin": None}
    data.update(changes)
    with pytest.raises(ValidationError):
        RepoChange(**data)


def test_rename_keeps_both_paths():
    change = RepoChange(status="R ", path=Path("new.py"), origin=Path("old.py"))
    assert RepoChange.model_validate_json(change.model_dump_json()) == change


@pytest.mark.parametrize("changes", [
    {"head": None}, {"diff": 1}, {"complete": "true"}, {"complete": 1},
    {"changes": [{}]}, {"authority": "verifier"},
])
def test_repo_fact_rejects_invalid_observations(kernel_double, changes):
    with pytest.raises(ValidationError):
        kernel_double.repo_fact(**changes)


def test_empty_or_incomplete_observations_remain_representable(kernel_double):
    repo = kernel_double.repo_fact(head="", diff="", changes=[], complete=False)
    assert repo.head == ""
    assert repo.changes == []
    assert repo.complete is False


@pytest.mark.parametrize("factory,model", [
    ("source_fact", SourceFact), ("repo_change", RepoChange), ("repo_fact", RepoFact),
])
def test_new_double_constructors_validate_and_serialize(kernel_double, factory, model, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("a fact constructor performed I/O")

    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(Path, "resolve", forbidden)
    value = getattr(kernel_double, factory)()
    assert isinstance(value, model)
    assert model.model_validate_json(value.model_dump_json()) == value
