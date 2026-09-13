"""Contrat partagé entre implémentation et double."""

import inspect
from pathlib import Path

import pytest

import observatory
from observatory import Observatory
from tests.support import load_double as _load_double


@pytest.fixture
def memory(node_event, validation_event, moment):
    "Double chargé et scripté avec une mission : deux nœuds et une validation verte."

    module = _load_double("observatory")
    module.reset()
    module.missions["m1"] = [
        node_event("root", at=moment(1)),
        node_event("a", at=moment(2), parent_id="root", depth=1),
        validation_event(at=moment(3)),
    ]
    module.anomalies["m1"] = ("torn_tail:events.jsonl:120:9",)

    return module


def test_the_double_satisfies_the_same_protocol(memory):
    assert isinstance(observatory, Observatory)
    assert isinstance(memory, Observatory)
    for method in ("build_index", "build_run_index", "refresh", "mission_events", "flatten_tree"):
        real = inspect.signature(getattr(observatory, method))
        fake = inspect.signature(getattr(memory, method))
        assert list(real.parameters) == list(fake.parameters)


def test_the_double_serves_the_same_catalogue_and_the_same_tree(memory, logs_root, write_events):
    write_events("m1", memory.missions["m1"])
    real_index = observatory.build_index(logs_root)
    memory_index = memory.build_index(logs_root)
    real_events, _ = observatory.mission_events(real_index, "m1")
    memory_events, memory_anomalies = memory.mission_events(memory_index, "m1")
    real_row = real_index.rows["m1"]
    memory_row = memory_index.rows["m1"]
    assert real_events == memory_events
    assert memory_anomalies == ("torn_tail:events.jsonl:120:9",)
    assert real_row.model_dump(exclude={"anomalies"}) == memory_row.model_dump(exclude={"anomalies"})
    assert observatory.flatten_tree(real_events) == memory.flatten_tree(memory_events)
    assert observatory.status_text(real_row, []) == memory.status_text(real_row, [])


def test_the_double_touches_no_file(memory, monkeypatch, tmp_path):
    def forbidden(*args, **kwargs):
        raise AssertionError("double performed I/O")

    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(Path, "stat", forbidden)
    monkeypatch.setattr(Path, "iterdir", forbidden)
    monkeypatch.setattr(Path, "exists", forbidden)
    index = memory.build_index(tmp_path / "jamais-lu")
    memory.refresh(index)
    events, anomalies = memory.mission_events(index, "m1")
    assert index.rows["m1"].n_events == 3
    assert len(events) == 3
    assert anomalies == ("torn_tail:events.jsonl:120:9",)


def test_the_double_reports_an_unknown_mission_as_empty(memory, tmp_path):
    index = memory.build_index(tmp_path)
    assert memory.mission_events(index, "absente") == ([], ())


def test_signature_mutation_reaches_the_contract(memory, monkeypatch):
    test_the_double_satisfies_the_same_protocol(memory)
    monkeypatch.setattr(memory, "build_index", lambda wrong: None)
    with pytest.raises(AssertionError):
        test_the_double_satisfies_the_same_protocol(memory)
