"""Reprise depuis les preuves durables, sans nouvelle inférence."""

from dataclasses import replace
from copy import deepcopy
from pathlib import Path

import pytest

from engine.recovery import reconcile
from engine.test_attempt import AFTER, BEFORE, launch, scenario
from engine.tree import Tree
from engine.walk import StateNotWrittenError
from kernel.contracts import NodeStatus


TREE_PATH = Path("/evidence/tree.json")
EVENTS_PATH = Path("/evidence/events.jsonl")


def interrupted(scenario, monkeypatch):
    original = scenario.deps.journal.update_json_locked

    def publish(path, fn):
        current = scenario.deps.journal.json_files.get(path, {})
        updated = fn(current)
        if updated["nodes"][0]["status"] == "passed":
            raise StateNotWrittenError("publication interrupted")
        original(path, fn)

    monkeypatch.setattr(scenario.deps.journal, "update_json_locked", publish)
    with pytest.raises(StateNotWrittenError):
        launch(scenario)
    monkeypatch.setattr(scenario.deps.journal, "update_json_locked", original)

    return Tree.model_validate(scenario.deps.journal.json_files[TREE_PATH])


@pytest.mark.parametrize("on_disk, expected", [(AFTER, "passed"), (BEFORE, "blocked")])
def test_running_reconciles_receipt_against_actual_bytes(scenario, monkeypatch, on_disk, expected):
    tree = interrupted(scenario, monkeypatch)
    scenario.deps.workspace.files[scenario.target] = on_disk
    repo = scenario.receipt.facts[-1]
    scenario.deps = replace(scenario.deps, observe_repo=lambda: repo)
    calls_before = len(scenario.deps.bridge.calls)
    result = reconcile(tree, "node-1", scenario.deps, tree_path=TREE_PATH, events_path=EVENTS_PATH)
    assert result.nodes[0].status == expected
    assert len(scenario.deps.bridge.calls) == calls_before
    assert scenario.deps.workspace.files[scenario.target] == on_disk
    if expected == "passed":
        assert result.receipts["node-1"] == scenario.receipt
    else:
        assert result.nodes[0].blocked_cause == "interrupted"


def test_candidate_without_receipt_is_restored_exactly(scenario, monkeypatch):
    tree = interrupted(scenario, monkeypatch)
    events = scenario.deps.journal.events
    events[:] = [event for event in events if event.payload.get("operation") != "passed"]
    scenario.deps.workspace.files[scenario.target] = AFTER
    result = reconcile(tree, "node-1", scenario.deps, tree_path=TREE_PATH, events_path=EVENTS_PATH)
    assert result.nodes[0].blocked_cause == "interrupted"
    assert scenario.deps.workspace.files[scenario.target] == BEFORE
    assert result.receipts == {}


def test_unrecognized_bytes_are_preserved_and_blocked(scenario, monkeypatch):
    tree = interrupted(scenario, monkeypatch)
    foreign = b"def clamp_level(level):\n    return 'external edit'\n"
    scenario.deps.workspace.files[scenario.target] = foreign
    result = reconcile(tree, "node-1", scenario.deps, tree_path=TREE_PATH, events_path=EVENTS_PATH)
    assert result.nodes[0].blocked_cause == "unverifiable"
    assert scenario.deps.workspace.files[scenario.target] == foreign


def test_stale_tree_cannot_restore_a_newer_attempt(scenario, monkeypatch):
    tree = interrupted(scenario, monkeypatch)
    scenario.deps.workspace.files[scenario.target] = AFTER
    newer = tree.model_copy(update={"cap_children": 3})
    scenario.deps.journal.json_files[TREE_PATH] = newer.model_dump(mode="json")
    with pytest.raises(StateNotWrittenError):
        reconcile(tree, "node-1", scenario.deps, tree_path=TREE_PATH, events_path=EVENTS_PATH)
    assert scenario.deps.workspace.files[scenario.target] == AFTER


def test_verifier_receipt_survives_loss_of_engine_acknowledgement(scenario, monkeypatch):
    tree = interrupted(scenario, monkeypatch)
    events = scenario.deps.journal.events
    acknowledged = events[-1]
    payload = deepcopy(acknowledged.payload)
    payload.pop("operation")
    payload["scope"] = "node_verification"
    events[-1] = acknowledged.model_copy(update={"type": "validation", "payload": payload})
    scenario.deps.workspace.files[scenario.target] = AFTER
    scenario.deps = replace(scenario.deps, observe_repo=lambda: scenario.receipt.facts[-1])
    result = reconcile(tree, "node-1", scenario.deps, tree_path=TREE_PATH, events_path=EVENTS_PATH)
    assert result.nodes[0].status == "passed"
    assert len(scenario.deps.bridge.calls) == 1


def test_invalid_receipt_cannot_prevent_restoration_of_known_candidate(scenario, monkeypatch):
    tree = interrupted(scenario, monkeypatch)
    events = scenario.deps.journal.events
    payload = deepcopy(events[-1].payload)
    payload["receipt"]["returncode"] = 20
    events[-1] = events[-1].model_copy(update={"payload": payload})
    scenario.deps.workspace.files[scenario.target] = AFTER
    result = reconcile(tree, "node-1", scenario.deps, tree_path=TREE_PATH, events_path=EVENTS_PATH)
    assert result.nodes[0].blocked_cause == "unverifiable"
    assert scenario.deps.workspace.files[scenario.target] == BEFORE


def test_legacy_running_without_snapshot_is_blocked_without_guessing(scenario):
    node = scenario.tree.nodes[0].model_copy(update={"status": NodeStatus.running})
    tree = scenario.tree.model_copy(update={"nodes": (node,)})
    result = reconcile(tree, node.id, scenario.deps, tree_path=TREE_PATH, events_path=EVENTS_PATH)
    assert result.nodes[0].blocked_cause == "unverifiable"
    assert scenario.deps.bridge.calls == []


def test_restoration_survives_an_interrupted_state_publication(scenario, monkeypatch):
    tree = interrupted(scenario, monkeypatch)
    events = scenario.deps.journal.events
    events[:] = [event for event in events if event.payload.get("operation") != "passed"]
    scenario.deps.workspace.files[scenario.target] = AFTER
    original = scenario.deps.journal.update_json_locked

    def fail_terminal(path, fn):
        updated = fn(scenario.deps.journal.json_files[path])
        if updated["nodes"][0]["status"] == "blocked":
            raise StateNotWrittenError("terminal publication interrupted")
        original(path, fn)

    monkeypatch.setattr(scenario.deps.journal, "update_json_locked", fail_terminal)
    with pytest.raises(StateNotWrittenError):
        reconcile(tree, "node-1", scenario.deps, tree_path=TREE_PATH, events_path=EVENTS_PATH)
    assert scenario.deps.workspace.files[scenario.target] == BEFORE


def test_repository_mismatch_restores_the_known_candidate(scenario, monkeypatch):
    tree = interrupted(scenario, monkeypatch)
    scenario.deps.workspace.files[scenario.target] = AFTER
    changed = scenario.receipt.facts[-1].model_copy(update={"head": "c" * 40})
    scenario.deps = replace(scenario.deps, observe_repo=lambda: changed)
    result = reconcile(tree, "node-1", scenario.deps, tree_path=TREE_PATH, events_path=EVENTS_PATH)
    assert result.nodes[0].blocked_cause == "unverifiable"
    assert scenario.deps.workspace.files[scenario.target] == BEFORE
