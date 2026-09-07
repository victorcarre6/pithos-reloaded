from pathlib import Path
from decimal import Decimal

import pytest
from pydantic import ValidationError

from kernel.contracts import Criterion, Event, Node, Relation
from kernel.facts import FileFact, Receipt


@pytest.fixture
def node_data():
    return {
        "id": "node-1",
        "parent_id": None,
        "depth": 0,
        "target": Path("tool.py"),
        "criterion": None,
        "status": "pending",
        "blocked_cause": None,
    }


def test_node_target_refuses_list(node_data):
    node_data["target"] = [Path("one.py"), Path("two.py")]
    with pytest.raises(ValidationError) as caught:
        Node(**node_data)
    assert caught.value.errors()[0]["loc"] == ("target",)


@pytest.mark.parametrize("field,value", [
    ("id", ""), ("id", 3), ("parent_id", ""),
    ("depth", -1), ("depth", 4), ("depth", True), ("depth", "1"),
    ("target", None), ("status", "greenish"), ("blocked_cause", "unknown"),
    ("extra", "ignored"),
])
def test_node_rejects_invalid_field(node_data, field, value):
    node_data[field] = value
    with pytest.raises(ValidationError):
        Node(**node_data)


@pytest.mark.parametrize("changes", [
    {"parent_id": "node-1", "depth": 1},
    {"parent_id": "parent"},
    {"depth": 1},
    {"status": "running"},
    {"status": "passed"},
    {"status": "blocked"},
    {"blocked_cause": "invalid_schema"},
])
def test_node_rejects_inconsistent_state(node_data, changes):
    node_data.update(changes)
    with pytest.raises(ValidationError):
        Node(**node_data)


def test_node_can_wait_without_criterion(node_data):
    node = Node(**node_data)
    assert node.criterion is None
    assert node.target == Path("tool.py")
    assert Node.model_validate_json(node.model_dump_json()) == node


@pytest.mark.parametrize("field,value", [
    ("relation", "equals_literal"), ("domain", "lists_of<exec>"),
    ("symbols", []), ("symbols", ["f", "g"]), ("symbols", ["f()"]),
    ("symbols", ["0.0"]), ("symbols", [3]), ("symbols", ("f",)),
    ("symbols", ["return"]), ("expected", 42),
])
def test_criterion_rejects_literals_and_unknown_choices(field, value):
    data = {"relation": "total", "symbols": ["f"], "domain": "json_values"}
    data[field] = value
    with pytest.raises(ValidationError):
        Criterion(**data)


@pytest.mark.parametrize("relation", list(Relation))
def test_all_relations_round_trip(relation):
    unary = {"idempotent", "monotone", "total", "schema_conform"}
    symbols = ["f"] if relation in unary else ["f", "g"]
    criterion = Criterion(relation=relation, symbols=symbols, domain="json_values")
    assert Criterion.model_validate_json(criterion.model_dump_json()) == criterion
    assert len(Relation) == 9


@pytest.fixture
def event_data():
    return {
        "ts": "2026-09-06T18:00:00Z",
        "v": 1,
        "type": "validation",
        "durable": True,
        "payload": {"nested": [{"value": 2}]},
    }


@pytest.mark.parametrize("field,value", [
    ("ts", ""), ("v", 2), ("v", True), ("v", "1"),
    ("type", "anything"), ("durable", "true"), ("extra", 1),
    ("payload", {"v": float("nan")}),
    ("payload", {"v": [float("inf")]}),
    ("payload", {"v": {"nested": float("-inf")}}),
    ("payload", {1: "value"}), ("payload", {"v": Path("a")}),
    ("payload", {"v": (1, 2)}), ("payload", {"v": {1, 2}}),
    ("payload", {"v": Decimal("1.5")}),
])
def test_event_rejects_invalid_values(event_data, field, value):
    event_data[field] = value
    with pytest.raises(ValidationError):
        Event(**event_data)


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_event_rejects_nonfinite_json(event_data, constant):
    raw = Event(**event_data).model_dump_json()
    raw = raw.replace('"value":2', '"value":' + constant)
    with pytest.raises(ValidationError):
        Event.model_validate_json(raw)


def test_event_detaches_payload(event_data):
    event = Event(**event_data)
    event_data["payload"]["nested"][0]["value"] = 99
    assert event.payload["nested"][0]["value"] == 2
    assert Event.model_validate_json(event.model_dump_json()) == event


def test_event_rejects_cyclic_payload(event_data):
    payload = {}
    payload["self"] = payload
    event_data["payload"] = payload
    with pytest.raises(ValidationError):
        Event(**event_data)


@pytest.fixture
def file_fact_data():
    return {
        "path": Path("tool.py"),
        "sha_before": "a" * 64,
        "sha_after": "b" * 64,
        "spliced_range": (1, 3),
        "n_replacements": 1,
    }


@pytest.mark.parametrize("field,value", [
    ("path", []), ("sha_before", ""), ("sha_after", "g" * 64),
    ("spliced_range", (0, 1)), ("spliced_range", (3, 1)),
    ("spliced_range", (1,)), ("spliced_range", (True, 2)),
    ("n_replacements", -1), ("n_replacements", True), ("extra", 1),
])
def test_file_fact_rejects_invalid_values(file_fact_data, field, value):
    file_fact_data[field] = value
    with pytest.raises(ValidationError):
        FileFact(**file_fact_data)


@pytest.mark.parametrize("returncode", [None, 0, 1, -9])
def test_receipt_keeps_returncode(file_fact_data, returncode):
    fact = FileFact(**file_fact_data)
    receipt = Receipt(
        node_id="node-1", attempt=1, returncode=returncode,
        artifact_path=Path("invariant.py"), facts=[fact],
    )
    restored = Receipt.model_validate_json(receipt.model_dump_json())
    assert restored == receipt
    assert restored.returncode == returncode


@pytest.mark.parametrize("field,value", [
    ("node_id", ""), ("attempt", 0), ("attempt", True),
    ("returncode", False), ("returncode", "0"),
    ("artifact_path", []), ("facts", [{}]), ("authority", "verifier"),
])
def test_receipt_rejects_invalid_values(field, value):
    data = {
        "node_id": "node-1",
        "attempt": 1,
        "returncode": None,
        "artifact_path": Path("invariant.py"),
        "facts": [],
    }
    data[field] = value
    with pytest.raises(ValidationError):
        Receipt(**data)
