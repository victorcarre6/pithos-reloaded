"""Une nano-étape sur doubles officiels, sans processus ni accès au modèle."""

from difflib import unified_diff
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from engine.attempt import Deps, run_attempt
from engine.budget import Budget
from engine.context import assemble
from engine.dump import Handoff
from engine.test_context import item
from engine.tree import StateConflictError, Tree
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
                observe_repo=lambda: next(observations), capability=bridge.capability,
                archive=double("engine").MemoryContextArchive())

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
    assert operations == ["context", "running", "candidate_response", "mutation_intent", "verification_report", "passed"]
    assert len(scenario.deps.bridge.calls) == 1
    handoffs = scenario.deps.archive.read("audio", path=Path("/evidence/CONTEXT.md"))
    assert len(handoffs) == 1
    assert handoffs[0].fingerprints == {scenario.target: sha256(AFTER).hexdigest()}
    assert json.loads(handoffs[0].content)["status"] == "passed"
    raw = scenario.deps.archive.files[Path("/evidence/CONTEXT.md")]
    assert "return level + 0.1" in raw
    assert "return level + 0.1" not in handoffs[0].content


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
    handoffs = scenario.deps.archive.read("audio", path=Path("/evidence/CONTEXT.md"))
    assert handoffs[0].fingerprints == {scenario.target: sha256(BEFORE).hexdigest()}
    content = json.loads(handoffs[0].content)
    assert content["status"] != "passed"
    if failure == "gate_error":
        assert content["verification"] is None


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
    assert scenario.deps.archive.files == {}


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


def test_irreducible_context_is_blocked_before_model_admission(scenario):
    result = launch(scenario, instruction="long instruction " * 5000)
    assert result.nodes[0].blocked_cause == "context_overflow"
    assert scenario.deps.bridge.calls == []
    assert scenario.deps.workspace.files[scenario.target] == BEFORE
    event = scenario.deps.journal.events[0]
    assert event.payload["operation"] == "context"
    assert event.payload["packet"]["blocked_cause"] == "context_overflow"
    assert all(item["included_reason"] for item in event.payload["packet"]["items"])


def test_attempt_identity_cannot_be_reused(scenario):
    scenario.tree = scenario.tree.model_copy(update={"attempts": {"node-1": 1}})
    with pytest.raises(ValueError, match="new attempt identity"):
        launch(scenario)
    assert scenario.deps.bridge.calls == []


@pytest.mark.parametrize("digest,reason,count", [
    (sha256(BEFORE).hexdigest(), None, 1),
    ("a" * 64, "stale", 1),
    (sha256(BEFORE).hexdigest(), "budget_pressure", 300),
])
def test_handoff_selection_reaches_the_actual_model_prompt(scenario, digest, reason, count):
    node = scenario.tree.nodes[0]
    fingerprints = {node.target: digest}
    entries = [item(f"historical-item-{index}", 20, content="OLD CODE MUST STAY ARCHIVED") for index in range(count)]
    packet = assemble(node, 2000, items=entries, fingerprints=fingerprints)
    section = Handoff(key=scenario.key, packet=packet, status="blocked", verdict=None, fingerprints=fingerprints)
    scenario.deps.archive.dump(section, path=Path("/evidence/CONTEXT.md"))
    launch(scenario)
    prompt = scenario.deps.bridge.calls[0]["user"]
    assert "OLD CODE MUST STAY ARCHIVED" not in prompt
    assert ("historical-item" in prompt) == (reason is None)
    assert ("[omitted: stale=1]" in prompt) == (reason == "stale")
    assert ("[omitted: budget_pressure=1]" in prompt) == (reason == "budget_pressure")
    context = scenario.deps.journal.events[0].payload["packet"]
    assert context["items"][0]["excluded_reason"] == reason
    assert "return level + 0.1" in prompt
    assert "candidate contract" not in prompt


def test_unreadable_archive_blocks_before_model_and_preserves_raw(scenario):
    path = Path("/evidence/CONTEXT.md")
    scenario.deps.archive.files[path] = "incomplete history"
    result = launch(scenario)
    assert result.nodes[0].blocked_cause == "unverifiable"
    assert scenario.deps.bridge.calls == []
    assert scenario.deps.archive.files[path] == "incomplete history"


def test_archive_failure_after_green_does_not_roll_back_acknowledged_effect(scenario, monkeypatch):
    def broken(*args, **kwargs):
        raise OSError("archive unavailable")

    monkeypatch.setattr(scenario.deps.archive, "dump", broken)
    with pytest.raises(OSError, match="archive unavailable"):
        launch(scenario)
    assert scenario.deps.workspace.files[scenario.target] == AFTER
    durable = scenario.deps.journal.json_files[Path("/evidence/tree.json")]
    assert durable["nodes"][0]["status"] == "passed"


def test_foreign_verdict_is_traced_without_attaching_it_to_handoff(scenario, monkeypatch):
    criterion = scenario.verdict.criterion.model_copy(update={"symbols": ["other"]})
    foreign = scenario.verdict.model_copy(update={"criterion": criterion})
    monkeypatch.setattr(scenario.deps.verifier, "run", lambda *args, **kwargs: foreign)
    result = launch(scenario)
    assert result.nodes[0].blocked_cause == "unverifiable"
    assert scenario.deps.workspace.files[scenario.target] == BEFORE
    handoffs = scenario.deps.archive.read("audio", path=Path("/evidence/CONTEXT.md"))
    assert json.loads(handoffs[0].content)["verification"] is None
    reports = [event for event in scenario.deps.journal.events if event.payload["operation"] == "verification_report"]
    assert reports[0].payload["verification"]["criterion"]["symbols"] == ["other"]


def test_conflict_while_recording_failure_stops_handoff_writes(scenario, monkeypatch):
    publish = scenario.deps.journal.update_json_locked

    def conflict(path, fn):
        current = scenario.deps.journal.json_files.get(path, {})
        updated = fn(current)
        if updated["nodes"][0]["status"] == "blocked":
            raise StateConflictError("new owner")
        publish(path, fn)

    scenario.deps.bridge.queue.clear()
    scenario.deps.bridge.script(scenario.deps.bridge.malformed("invalid"))
    monkeypatch.setattr(scenario.deps.journal, "update_json_locked", conflict)
    with pytest.raises(StateConflictError):
        launch(scenario)
    assert scenario.deps.workspace.files[scenario.target] == BEFORE
    assert scenario.deps.archive.files == {}
