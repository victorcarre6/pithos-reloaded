"""La mission conserve ses verts et reprend sans dupliquer les effets."""

from dataclasses import replace
import builtins
import inspect
import json
from pathlib import Path

import pytest

from engine.budget import Budget
from engine.test_attempt import AFTER, BEFORE, scenario
from engine.tree import Tree
from engine.walk import GreenFinalizer, StateNotWrittenError, WalkDeps, Walker, walk
from kernel.contracts import NodeStatus
from kernel.errors import Cause, PithosError
from kernel.facts import RecordKey


@pytest.fixture
def mission(scenario, double):
    dirty = scenario.receipt.facts[-1]
    clean = dirty.model_copy(update={"changes": [], "diff": ""})
    committed = clean.model_copy(update={"head": "b" * 40})
    finalizer = double("engine").MemoryFinalizer([committed])

    def observe():
        if finalizer.recorded:
            return committed
        if scenario.deps.workspace.files[scenario.target] == BEFORE:
            return clean

        return dirty

    scenario.deps = replace(scenario.deps, observe_repo=observe)
    deps = WalkDeps(attempt=scenario.deps, finalizer=finalizer,
                    tree_path=Path("/evidence/tree.json"), events_path=Path("/evidence/events.jsonl"),
                    artifact_root=Path("/evidence"), system="candidate contract", instruction="clamp")

    return scenario, deps


def test_green_is_finalized_once_and_baseline_is_recorded(mission):
    scenario, deps = mission
    result = walk(scenario.tree, Budget(60), deps)
    assert result.nodes[0].status == "passed"
    assert result.finalized["node-1"].head == "b" * 40
    assert [call[0] for call in deps.finalizer.calls] == ["reconcile", "finalize"]
    baseline = deps.attempt.journal.events[-1].payload
    assert baseline["operation"] == "baseline"
    assert baseline["green_nodes"] == baseline["attempted_nodes"] == 1
    assert baseline["exit_cause"] == "completed"
    assert baseline["wall_seconds"] >= 0
    assert walk(result, Budget(60), deps) == result
    assert len(deps.finalizer.calls) == 2
    assert len(deps.attempt.bridge.calls) == 1


def test_soft_deadline_finalizes_green_and_leaves_sibling_pending(mission, kernel_double, monkeypatch):
    scenario, deps = mission
    sibling = kernel_double.node(id="later", target=scenario.target)
    tree = scenario.tree.model_copy(update={"nodes": (*scenario.tree.nodes, sibling)})
    clock = [0]
    budget = Budget(60, clock=lambda: clock[0])
    emit_receipt = deps.attempt.verifier.emit_receipt

    def delayed(*args, **kwargs):
        clock[0] = 56

        return emit_receipt(*args, **kwargs)

    monkeypatch.setattr(deps.attempt.verifier, "emit_receipt", delayed)
    result = walk(tree, budget, deps)
    assert [node.status for node in result.nodes] == ["passed", "pending"]
    assert len(result.finalized) == 1
    assert deps.finalizer.calls[-1][-1] == 4
    assert deps.attempt.journal.events[-1].payload["exit_cause"] == "timeout"


def test_finalization_crash_is_reconciled_before_any_republication(mission, monkeypatch):
    scenario, deps = mission
    finalize = deps.finalizer.finalize

    def interrupted(*args):
        finalize(*args)
        raise RuntimeError("commit acknowledgement lost")

    monkeypatch.setattr(deps.finalizer, "finalize", interrupted)
    with pytest.raises(RuntimeError, match="acknowledgement lost"):
        walk(scenario.tree, Budget(60), deps)
    saved = Tree.model_validate_json(json.dumps(deps.attempt.journal.json_files[deps.tree_path]))
    assert saved.nodes[0].status == "passed"
    assert saved.finalized == {}
    monkeypatch.setattr(deps.finalizer, "finalize", finalize)
    result = walk(saved, Budget(60), deps)
    assert len(result.finalized) == 1
    assert [call[0] for call in deps.finalizer.calls] == ["reconcile", "finalize", "reconcile"]
    assert len(deps.attempt.bridge.calls) == 1


@pytest.mark.parametrize("status", [value for value in NodeStatus if value not in {NodeStatus.running, NodeStatus.passed}])
def test_criterion_free_nodes_never_reach_the_model(mission, status):
    scenario, deps = mission
    cause = "unverifiable" if status == NodeStatus.blocked else None
    values = scenario.tree.nodes[0].model_dump()
    values.update(criterion=None, status=status, blocked_cause=cause)
    node = type(scenario.tree.nodes[0]).model_validate(values)
    tree = scenario.tree.model_copy(update={"nodes": (node,)})
    result = walk(tree, Budget(60), deps)
    assert result.nodes[0].status != "passed"
    assert deps.attempt.bridge.calls == []
    assert scenario.deps.workspace.files[scenario.target] == BEFORE


def test_parent_disposition_is_bound_to_the_receipt(mission, kernel_double):
    scenario, deps = mission
    parent = kernel_double.node(id="root", criterion=None)
    child = scenario.tree.nodes[0].model_copy(update={"parent_id": "root", "depth": 1})
    tree = scenario.tree.model_copy(update={"nodes": (parent, child)})
    result = walk(tree, Budget(60), deps)
    disposition, = result.current_dispositions()
    assert disposition.child_id == child.id
    assert disposition.disposition == "integrated"
    receipt = result.receipts[child.id].model_copy(update={"artifact_path": Path("/another.py")})
    changed = result.model_copy(update={"receipts": {child.id: receipt}})
    assert changed.current_dispositions() == ()


def test_walk_protocol_and_double_reject_a_signature_drift(mission, double, monkeypatch):
    scenario, deps = mission
    memory = double("engine").MemoryEngine([scenario.tree])
    assert isinstance(memory, Walker)
    assert list(inspect.signature(walk).parameters) == list(inspect.signature(memory.walk).parameters)
    assert memory.walk(scenario.tree, Budget(60), deps) == scenario.tree
    monkeypatch.setattr(memory, "walk", lambda wrong: None)
    assert list(inspect.signature(walk).parameters) != list(inspect.signature(memory.walk).parameters)


def test_full_walk_does_not_need_prefect(mission, monkeypatch):
    scenario, deps = mission
    original_import = builtins.__import__

    def guarded(name, *args, **kwargs):
        if name.split(".")[0] == "prefect":
            raise ModuleNotFoundError("Prefect intentionally unavailable")

        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)
    assert len(walk(scenario.tree, Budget(60), deps).finalized) == 1


def test_transport_timeout_does_not_retry_in_the_same_invocation(mission, monkeypatch):
    scenario, deps = mission
    calls = []

    def timed_out(*args):
        calls.append(args)
        raise PithosError(Cause.timeout, "transport timed out before deadline")

    monkeypatch.setattr(deps.attempt.bridge, "call", timed_out)
    result = walk(scenario.tree, Budget(60, clock=lambda: 0), deps)
    assert result.nodes[0].status == "budget_limited"
    assert len(calls) == 1
    assert deps.attempt.journal.events[-1].payload["exit_cause"] == "timeout"


def test_budget_limited_attempt_resumes_with_a_new_identity(mission):
    scenario, deps = mission
    node = scenario.tree.nodes[0].model_copy(update={"status": NodeStatus.budget_limited})
    tree = scenario.tree.model_copy(update={"nodes": (node,), "attempts": {node.id: 1}})
    key = RecordKey(kind="verification", value=(tree.mission_id, node.id, 2, node.criterion.relation))
    deps.attempt.verifier.receipts[key] = scenario.receipt.model_copy(update={"attempt": 2})
    result = walk(tree, Budget(60), deps)
    assert result.attempts[node.id] == 2
    assert result.receipts[node.id].attempt == 2
    assert len(result.finalized) == 1


def test_model_crash_preserves_running_state_and_records_baseline(mission, monkeypatch):
    scenario, deps = mission

    def crash(*args):
        raise RuntimeError("model process lost")

    monkeypatch.setattr(deps.attempt.bridge, "call", crash)
    with pytest.raises(RuntimeError, match="model process lost"):
        walk(scenario.tree, Budget(60), deps)
    saved = Tree.model_validate_json(json.dumps(deps.attempt.journal.json_files[deps.tree_path]))
    assert saved.nodes[0].status == "running"
    baseline = deps.attempt.journal.events[-1].payload
    assert baseline["attempted_nodes"] == 1
    assert baseline["green_nodes"] == 0
    assert baseline["exit_cause"] == "error"
    resumed = walk(saved, Budget(60), deps)
    assert resumed.nodes[0].blocked_cause == "interrupted"


@pytest.mark.parametrize("fault", ["dirty", "same_head", "foreign_repo", "source_changed"])
def test_finalization_requires_a_clean_observed_result(mission, monkeypatch, fault):
    scenario, deps = mission
    original = deps.finalizer.finalize

    def invalid(*args):
        result = original(*args)
        if fault == "dirty":
            result = scenario.receipt.facts[-1]
        elif fault == "same_head":
            result = result.model_copy(update={"head": scenario.receipt.facts[-1].head})
        elif fault == "foreign_repo":
            result = result.model_copy(update={"repo": Path("/foreign")})
        else:
            deps.attempt.workspace.files[scenario.target] = b"external edit"

        return result

    monkeypatch.setattr(deps.finalizer, "finalize", invalid)
    with pytest.raises(PithosError):
        walk(scenario.tree, Budget(60), deps)
    saved = Tree.model_validate_json(json.dumps(deps.attempt.journal.json_files[deps.tree_path]))
    assert saved.finalized == {}
    assert deps.attempt.journal.events[-1].payload["exit_cause"] == "error"


def test_soft_reserve_still_allows_finalization(mission):
    scenario, deps = mission
    from engine.test_attempt import launch

    green = launch(scenario)
    result = walk(green, Budget(5, clock=lambda: 0), deps)
    assert len(result.finalized) == 1
    assert len(deps.finalizer.calls) == 2
    assert deps.attempt.journal.events[-1].payload["exit_cause"] == "timeout"


def test_two_greens_are_separated_by_a_clean_repository(mission, kernel_double, double):
    scenario, deps = mission
    second_path = Path("/campaign/second.py")
    deps.attempt.workspace.files[second_path] = BEFORE
    criterion = kernel_double.criterion(relation="idempotent", symbols=["clamp_level"], domain="small_ints")
    second = kernel_double.node(id="second", target=second_path, criterion=criterion)
    tree = scenario.tree.model_copy(update={"nodes": (*scenario.tree.nodes, second)})
    first_dirty = scenario.receipt.facts[-1]
    first_clean = first_dirty.model_copy(update={"changes": [], "diff": ""})
    first_committed = first_clean.model_copy(update={"head": "b" * 40})
    second_committed = first_clean.model_copy(update={"head": "c" * 40})
    second_dirty = first_dirty.model_copy(update={
        "head": first_committed.head,
        "changes": [kernel_double.repo_change(path=Path("second.py"))],
        "diff": first_dirty.diff.replace("audio_visualizer.py", "second.py"),
    })
    facts = [fact.model_copy(update={"path": second_path}) for fact in scenario.receipt.facts[:2]]
    facts.append(second_dirty)
    verdict = scenario.verdict.model_copy(update={"criterion": criterion, "facts": facts})
    receipt = scenario.receipt.model_copy(update={"node_id": second.id, "facts": facts})
    key = RecordKey(kind="verification", value=(tree.mission_id, second.id, 1, criterion.relation))
    verifier = double("verifier").MemoryVerifier(
        [(scenario.verdict.criterion, scenario.verdict), (criterion, verdict)],
        [(scenario.key, scenario.receipt), (key, receipt)],
    )
    finalizer = double("engine").MemoryFinalizer([first_committed, second_committed])

    def observe():
        if key in finalizer.recorded:
            return second_committed
        if scenario.key in finalizer.recorded:
            return second_dirty if deps.attempt.workspace.files[second_path] == AFTER else first_committed

        return first_dirty if deps.attempt.workspace.files[scenario.target] == AFTER else first_clean

    ports = replace(deps.attempt, verifier=verifier, observe_repo=observe)
    ports.bridge.script(ports.bridge.conformant({"function_name": "clamp_level", "new_source": AFTER.decode()}))
    deps = replace(deps, attempt=ports, finalizer=finalizer)
    result = walk(tree, Budget(60), deps)
    assert len(result.finalized) == 2
    assert len(ports.bridge.calls) == 2
    assert [call[0] for call in finalizer.calls] == ["reconcile", "finalize", "reconcile", "finalize"]
    assert ports.journal.events[-1].payload["green_nodes"] == 2
    assert ports.journal.events[-1].payload["attempted_nodes"] == 2


def test_hard_deadline_keeps_green_for_next_finalization(mission):
    scenario, deps = mission
    from engine.test_attempt import launch

    green = launch(scenario)
    clock = [0]
    budget = Budget(5, clock=lambda: clock[0])
    clock[0] = 6
    result = walk(green, budget, deps)
    assert result.nodes[0].status == "passed"
    assert result.finalized == {}
    assert deps.finalizer.calls == []
    resumed = walk(result, Budget(60), deps)
    assert len(resumed.finalized) == 1
    assert len(deps.attempt.bridge.calls) == 1


def test_finalizer_contract_detects_a_signature_drift(mission, monkeypatch):
    _, deps = mission

    def assert_contract():
        assert isinstance(deps.finalizer, GreenFinalizer)
        for name in ("reconcile", "finalize"):
            expected = list(inspect.signature(getattr(GreenFinalizer, name)).parameters.values())[1:]
            actual = list(inspect.signature(getattr(deps.finalizer, name)).parameters.values())
            assert [(item.name, item.kind, item.default) for item in actual] == [
                (item.name, item.kind, item.default) for item in expected
            ]

    assert_contract()
    monkeypatch.setattr(deps.finalizer, "finalize", lambda wrong: None)
    with pytest.raises(AssertionError):
        assert_contract()


def test_publication_failure_baseline_counts_the_durable_attempt(mission, monkeypatch):
    scenario, deps = mission
    original = deps.attempt.journal.update_json_locked

    def fail_passed(path, fn):
        current = deps.attempt.journal.json_files.get(path, {})
        updated = fn(current)
        if updated["nodes"][0]["status"] == "passed":
            raise StateNotWrittenError("tree write interrupted")
        original(path, fn)

    monkeypatch.setattr(deps.attempt.journal, "update_json_locked", fail_passed)
    with pytest.raises(StateNotWrittenError):
        walk(scenario.tree, Budget(60), deps)
    baseline = deps.attempt.journal.events[-1].payload
    assert baseline["attempted_nodes"] == 1
    assert baseline["green_nodes"] == 0
    assert baseline["exit_cause"] == "error"
    assert deps.attempt.workspace.files[scenario.target] == BEFORE
