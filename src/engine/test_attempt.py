"""Une nano-étape sur doubles officiels, sans processus ni accès au modèle."""

from difflib import unified_diff
from hashlib import sha256
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from engine.attempt import Deps, run_attempt
from engine.budget import Budget
from engine.tree import Tree
from engine.walk import StateNotWrittenError
from kernel.facts import RecordKey
from kernel.contracts import NodeStatus, Relation
from verifier.models import ExecutionResult, KillReport, MutationAttempt, Verdict


BEFORE = b"def clamp_level(level):\n    return level + 0.1\n"
AFTER = b"def clamp_level(level):\n    return min(1.0, max(0.0, level))\n"


@pytest.fixture
def scenario(kernel_double, journal_double, double, monkeypatch):
    root = Path("/campaign")
    target = root / "audio_visualizer.py"
    criterion = kernel_double.criterion(relation="idempotent", symbols=["clamp_level"], domain="floats_finite")
    node = kernel_double.node(target=target, criterion=criterion)
    tree = Tree(mission_id="audio", nodes=(node,), cap_children=2)
    workspace = double("workspace").MemoryWorkspace(root, {target: BEFORE})
    bridge = double("bridge")
    bridge.script(bridge.conformant({"function_name": "clamp_level", "new_source": AFTER.decode()}))
    file = kernel_double.file_fact(path=target, sha_before=sha256(BEFORE).hexdigest(),
                                   sha_after=sha256(AFTER).hexdigest(), spliced_range=(1, 2))
    sources = kernel_double.source_fact(path=target, before=BEFORE, after=AFTER)
    lines = unified_diff(BEFORE.decode().splitlines(keepends=True), AFTER.decode().splitlines(keepends=True),
                         fromfile="a/audio_visualizer.py", tofile="b/audio_visualizer.py")
    diff = "diff --git a/audio_visualizer.py b/audio_visualizer.py\n" + "".join(lines)
    dirty = kernel_double.repo_fact(complete=True, diff=diff,
                                   changes=[kernel_double.repo_change(path=Path("audio_visualizer.py"))])
    clean = kernel_double.repo_fact(complete=True)
    facts = [file, sources, dirty]
    red = ExecutionResult(execution="completed", check="failed", returncode=20,
                          artifact_path=Path("/evidence/before.py"), diagnostic="red", duration=0)
    green = ExecutionResult(execution="completed", check="passed", returncode=0,
                            artifact_path=Path("/evidence/after.py"), diagnostic="green", duration=0)
    killed = KillReport(status="killed", reason="killed", baseline=green,
                        attempts=(MutationAttempt(operator="return_none", result=red),))
    verdict = Verdict(criterion=criterion, verification="passed", reason="verified", before=red,
                      after=green, mutation=killed, effect="confirmed", facts=facts,
                      source_hashes=(file.sha_before, file.sha_after))
    key = RecordKey(kind="verification", value=(tree.mission_id, node.id, 1, criterion.relation))
    receipt = kernel_double.receipt(node_id=node.id, facts=facts, artifact_path=green.artifact_path, returncode=0)
    verifier = double("verifier").MemoryVerifier([(criterion, verdict)], [(key, receipt)])
    observations = iter([clean, dirty, dirty])
    deps = Deps(workspace=workspace, bridge=bridge, verifier=verifier, journal=journal_double,
                observe_repo=lambda: next(observations), capability=bridge.capability)

    def forbidden(*args, **kwargs):
        raise AssertionError("engine performed I/O outside its ports")

    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)

    return SimpleNamespace(tree=tree, deps=deps, target=target, key=key, verdict=verdict, receipt=receipt)


def launch(scenario, **changes):
    arguments = {
        "tree_path": Path("/evidence/tree.json"),
        "artifact_root": Path("/evidence"),
        "system": "candidate contract",
        "instruction": "Project a finite audio level to [0, 1].",
        "attempt": 1,
    }
    arguments.update(changes)

    return run_attempt(scenario.tree, "node-1", Budget(60), scenario.deps, **arguments)


def test_green_is_published_only_after_the_receipt(scenario):
    result = launch(scenario)
    assert result.nodes[0].status == "passed"
    assert scenario.deps.workspace.files[scenario.target] == AFTER
    assert scenario.deps.journal.json_files[Path("/evidence/tree.json")] == result.model_dump(mode="json")
    operations = [event.payload["operation"] for event in scenario.deps.journal.events]
    assert operations == ["running", "candidate_response", "verification_report", "passed"]
    assert len(scenario.deps.bridge.calls) == 1


@pytest.mark.parametrize("failure", ["receipt_absent", "red", "foreign_receipt", "gate_error"])
def test_every_non_green_path_restores_bytes(scenario, failure, monkeypatch):
    if failure == "receipt_absent":
        scenario.deps.verifier.receipts[scenario.key] = None
    elif failure == "foreign_receipt":
        scenario.deps.verifier.receipts[scenario.key] = scenario.receipt.model_copy(update={"facts": []})
    elif failure == "red":
        rejected = scenario.verdict.model_copy(update={"verification": "rejected", "reason": "after_red"})
        monkeypatch.setattr(scenario.deps.verifier, "run", lambda *args, **kwargs: rejected)
    else:
        def broken(*args, **kwargs):
            raise RuntimeError("gate crashed")

        monkeypatch.setattr(scenario.deps.verifier, "run", broken)
    if failure == "gate_error":
        with pytest.raises(RuntimeError, match="gate crashed"):
            launch(scenario)
    else:
        result = launch(scenario)
        assert result.nodes[0].status != "passed"
        if failure == "receipt_absent":
            assert result.nodes[0].blocked_cause == "receipt_not_written"
    assert scenario.deps.workspace.files[scenario.target] == BEFORE


def test_failed_tree_publication_rolls_back_even_after_receipt(scenario, monkeypatch):
    original = scenario.deps.journal.update_json_locked

    def publish(path, fn):
        current = scenario.deps.journal.json_files.get(path, {})
        updated = fn(current)
        if updated["nodes"][0]["status"] == "passed":
            raise StateNotWrittenError("publication failed")
        original(path, fn)

    monkeypatch.setattr(scenario.deps.journal, "update_json_locked", publish)
    with pytest.raises(StateNotWrittenError):
        launch(scenario)
    assert scenario.deps.workspace.files[scenario.target] == BEFORE


@pytest.mark.parametrize("payload", ["invalid-json", {"function_name": "other", "new_source": "def other(x): return x"}])
def test_bad_response_never_changes_the_target(scenario, payload):
    bridge = scenario.deps.bridge
    bridge.queue.clear()
    response = bridge.malformed(payload) if isinstance(payload, str) else bridge.conformant(payload)
    bridge.script(response)
    result = launch(scenario)
    assert result.nodes[0].blocked_cause == "invalid_schema"
    assert scenario.deps.workspace.files[scenario.target] == BEFORE


def test_no_criterion_means_no_model_or_mutation(scenario):
    node = scenario.tree.nodes[0].model_copy(update={"criterion": None})
    scenario.tree = scenario.tree.model_copy(update={"nodes": (node,)})
    result = launch(scenario)
    assert result.nodes[0].status == "blocked"
    assert scenario.deps.bridge.calls == []
    assert scenario.deps.workspace.files[scenario.target] == BEFORE


def test_no_effect_when_the_intention_is_not_durable(scenario):
    scenario.deps.journal.disk_full = True
    with pytest.raises(StateNotWrittenError):
        launch(scenario)
    assert scenario.deps.bridge.calls == []
    assert scenario.deps.workspace.files[scenario.target] == BEFORE


def test_already_running_is_not_reexecuted(scenario):
    node = scenario.tree.nodes[0].model_copy(update={"status": NodeStatus.running})
    scenario.tree = scenario.tree.model_copy(update={"nodes": (node,)})
    assert launch(scenario) == scenario.tree
    assert scenario.deps.bridge.calls == []


def test_an_unexecutable_relation_is_refused_before_the_model(scenario):
    node = scenario.tree.nodes[0]
    criterion = node.criterion.model_copy(update={"relation": Relation.schema_conform})
    node = node.model_copy(update={"criterion": type(criterion).model_validate(criterion.model_dump())})
    scenario.tree = scenario.tree.model_copy(update={"nodes": (node,)})
    result = launch(scenario)
    assert result.nodes[0].blocked_cause == "unverifiable"
    assert scenario.deps.bridge.calls == []
    assert scenario.deps.workspace.files[scenario.target] == BEFORE


def test_deadline_after_the_model_prevents_the_splice(scenario, monkeypatch):
    clock = [0]
    budget = Budget(60, clock=lambda: clock[0])
    original = scenario.deps.bridge.call

    def delayed(*args, **kwargs):
        response = original(*args, **kwargs)
        clock[0] = 56

        return response

    monkeypatch.setattr(scenario.deps.bridge, "call", delayed)
    result = run_attempt(scenario.tree, "node-1", budget, scenario.deps, tree_path=Path("/evidence/tree.json"),
                         artifact_root=Path("/evidence"), system="system", instruction="clamp", attempt=1)
    assert result.nodes[0].status == "budget_limited"
    assert scenario.deps.workspace.files[scenario.target] == BEFORE


def test_no_silent_replacement_of_a_concurrent_tree(scenario):
    concurrent = scenario.tree.model_copy(update={"cap_children": 3})
    scenario.deps.journal.json_files[Path("/evidence/tree.json")] = concurrent.model_dump(mode="json")
    with pytest.raises(StateNotWrittenError):
        launch(scenario)
    assert scenario.deps.bridge.calls == []
    assert scenario.deps.workspace.files[scenario.target] == BEFORE


def test_rejected_verification_is_durable_without_creating_a_receipt(scenario, monkeypatch):
    rejected = scenario.verdict.model_copy(update={"verification": "rejected", "reason": "after_red"})
    monkeypatch.setattr(scenario.deps.verifier, "run", lambda *args, **kwargs: rejected)
    result = launch(scenario)
    reports = [event for event in scenario.deps.journal.events if event.payload["operation"] == "verification_report"]
    assert len(reports) == 1
    event = reports[0]
    assert event.durable and event.type.value == "status"
    assert event.payload["verification"]["reason"] == "after_red"
    assert event.payload["key"] == scenario.key.model_dump(mode="json")
    assert "facts" not in event.payload["verification"]
    assert "receipt" not in event.payload
    assert result.nodes[0].status == "blocked"
    assert scenario.deps.workspace.files[scenario.target] == BEFORE


def test_missing_verification_trace_rolls_back_the_candidate(scenario, monkeypatch):
    emit = scenario.deps.journal.emit

    def refuse_report(event):
        return False if event.payload["operation"] == "verification_report" else emit(event)

    monkeypatch.setattr(scenario.deps.journal, "emit", refuse_report)
    with pytest.raises(StateNotWrittenError):
        launch(scenario)
    assert scenario.deps.workspace.files[scenario.target] == BEFORE
