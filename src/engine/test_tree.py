from pathlib import Path

import pytest
from pydantic import ValidationError

from engine.tree import ChildDisposition, Tree, result_sha256
from engine.walk import StateNotWrittenError, is_verifiable, split_node
from kernel.contracts import Node, NodeStatus
from kernel.errors import Cause


@pytest.mark.parametrize("status", list(NodeStatus))
def test_node_without_criterion_is_never_admissible(kernel_double, status):
    values = kernel_double.node().model_dump()
    values.update(criterion=None, status=status)
    if status == NodeStatus.blocked:
        values["blocked_cause"] = Cause.unverifiable
    if status in {NodeStatus.running, NodeStatus.passed}:
        with pytest.raises(ValidationError):
            Node.model_validate(values)
        return
    assert not is_verifiable(Node.model_validate(values))


def test_forged_node_is_revalidated_at_admission(kernel_double):
    forged = kernel_double.node().model_copy(update={"criterion": {"relation": "invented"}})
    with pytest.warns(UserWarning, match="Pydantic serializer warnings"):
        assert not is_verifiable(forged)


def test_criterion_admission_is_not_an_execution_proof(kernel_double):
    assert is_verifiable(kernel_double.node())


@pytest.mark.parametrize("fault", ["duplicate", "orphan", "wrong_depth", "too_wide"])
def test_tree_rejects_inconsistent_structure(kernel_double, fault):
    root = kernel_double.node(id="root")
    child = kernel_double.node(id="child", parent_id="root", depth=1)
    nodes = [root, child]
    if fault == "duplicate":
        nodes.append(child)
    elif fault == "orphan":
        nodes = [child]
    elif fault == "wrong_depth":
        nodes[1] = kernel_double.node(id="child", parent_id="root", depth=2)
    else:
        nodes.append(kernel_double.node(id="second", parent_id="root", depth=1))
    with pytest.raises(ValidationError):
        Tree(mission_id="mission", nodes=tuple(nodes), cap_children=1)


def test_split_is_atomic_at_width_limit_and_records_all_candidates(kernel_double, journal_double):
    parent = kernel_double.node(criterion=None)
    tree = Tree(mission_id="mission", nodes=(parent,), cap_children=1)
    targets = [Path("a.py"), Path("b.py")]
    result = split_node(tree, parent.id, targets, tree_path=Path("mission/tree.json"), journal=journal_double)
    assert len(result.nodes) == 1
    assert result.nodes[0].status == NodeStatus.blocked
    assert result.nodes[0].blocked_cause == Cause.unverifiable
    event = journal_double.events[-1]
    assert event.payload["reason"] == "width_limit"
    assert event.payload["candidates"] == ["a.py", "b.py"]
    assert event.payload["family"] == "memory"
    assert tree.nodes[0].status == NodeStatus.pending


def test_depth_three_cannot_be_split(kernel_double, journal_double):
    nodes = [kernel_double.node(id="n0", criterion=None)]
    for depth in range(1, 4):
        nodes.append(kernel_double.node(id=f"n{depth}", parent_id=f"n{depth - 1}", depth=depth, criterion=None))
    tree = Tree(mission_id="mission", nodes=tuple(nodes), cap_children=2)
    result = split_node(tree, "n3", [Path("a.py")], tree_path=Path("mission/tree.json"), journal=journal_double)
    assert len(result.nodes) == 4
    assert result.nodes[-1].blocked_cause == Cause.unverifiable
    assert journal_double.events[-1].payload["reason"] == "depth_limit"


def test_split_persists_intention_before_tree_and_is_not_repeated(kernel_double, journal_double):
    tree = Tree(mission_id="mission", nodes=(kernel_double.node(criterion=None),), cap_children=2)
    root = tree.nodes[0]
    result = split_node(tree, root.id, [Path("b.py"), Path("a.py"), Path("a.py")], tree_path=Path("mission/tree.json"), journal=journal_double)
    children = [node for node in result.nodes if node.parent_id == root.id]
    assert [node.target for node in children] == [Path("a.py"), Path("b.py")]
    assert all(node.depth == 1 and node.criterion is None for node in children)
    path = Path("mission/tree.json")
    saved = Tree.model_validate(journal_double.json_files[path])
    assert saved == result
    assert journal_double.events[0].payload["operation"] == "split"
    repeated = split_node(result, root.id, [Path("new.py")], tree_path=path, journal=journal_double)
    assert repeated == result
    assert len(journal_double.events) == 1


def test_no_candidate_blocks_with_typed_cause(kernel_double, journal_double):
    tree = Tree(mission_id="mission", nodes=(kernel_double.node(criterion=None),), cap_children=2)
    result = split_node(tree, tree.nodes[0].id, [], tree_path=Path("mission/tree.json"), journal=journal_double)
    assert result.nodes[0].blocked_cause == Cause.unverifiable
    assert journal_double.events[-1].payload["reason"] == "no_candidates"


def test_no_tree_change_if_intention_is_not_durable(kernel_double, journal_double):
    tree = Tree(mission_id="mission", nodes=(kernel_double.node(criterion=None),), cap_children=2)
    journal_double.disk_full = True
    with pytest.raises(StateNotWrittenError):
        split_node(tree, tree.nodes[0].id, [Path("a.py")], tree_path=Path("mission/tree.json"), journal=journal_double)
    assert journal_double.json_files == {}
    assert len(tree.nodes) == 1


def test_disposition_is_bound_to_exact_child_result(kernel_double):
    parent = kernel_double.node(id="parent", criterion=None)
    child = kernel_double.node(id="child", parent_id="parent", depth=1, status="blocked", blocked_cause="unverifiable")
    disposition = ChildDisposition(parent_id="parent", child_id="child", disposition="deferred", result_sha256=result_sha256(child))
    tree = Tree(mission_id="mission", nodes=(parent, child), cap_children=2, dispositions=(disposition,))
    assert tree.current_dispositions() == (disposition,)
    changed = kernel_double.node(id="child", parent_id="parent", depth=1, status="failed")
    newer = Tree(mission_id="mission", nodes=(parent, changed), cap_children=2, dispositions=tree.dispositions)
    assert newer.current_dispositions() == ()
    assert newer.dispositions == (disposition,)


def test_disposition_requires_actual_parent_child_edge(kernel_double):
    parent = kernel_double.node(id="parent")
    child = kernel_double.node(id="child")
    disposition = ChildDisposition(parent_id="parent", child_id="child", disposition="deferred", result_sha256=result_sha256(child))
    with pytest.raises(ValidationError):
        Tree(mission_id="mission", nodes=(parent, child), cap_children=2, dispositions=(disposition,))


def test_stale_tree_cannot_overwrite_newer_state(kernel_double, journal_double):
    tree = Tree(mission_id="mission", nodes=(kernel_double.node(criterion=None),), cap_children=2)
    path = Path("mission/tree.json")
    saved = split_node(tree, tree.nodes[0].id, [Path("a.py")], tree_path=path, journal=journal_double)
    with pytest.raises(StateNotWrittenError, match="changed"):
        split_node(tree, tree.nodes[0].id, [Path("b.py")], tree_path=path, journal=journal_double)
    assert Tree.model_validate(journal_double.json_files[path]) == saved
    assert len(journal_double.events) == 2  # les deux intentions restent, même le cas refusé


def test_failed_tree_write_preserves_intention_and_input(kernel_double, journal_double, monkeypatch):
    tree = Tree(mission_id="mission", nodes=(kernel_double.node(criterion=None),), cap_children=2)

    def unavailable(path, fn):
        raise TimeoutError("journal lock unavailable")

    monkeypatch.setattr(journal_double, "update_json_locked", unavailable)
    with pytest.raises(TimeoutError):
        split_node(tree, tree.nodes[0].id, [Path("a.py")], tree_path=Path("mission/tree.json"), journal=journal_double)
    assert len(journal_double.events) == 1
    assert len(tree.nodes) == 1
    assert journal_double.json_files == {}


def test_child_identifier_collision_is_rejected_before_intention(kernel_double, journal_double):
    parent = kernel_double.node(id="parent", criterion=None)
    other = kernel_double.node(id="parent/1")
    tree = Tree(mission_id="mission", nodes=(parent, other), cap_children=2)
    with pytest.raises(ValidationError):
        split_node(tree, parent.id, [Path("a.py")], tree_path=Path("mission/tree.json"), journal=journal_double)
    assert journal_double.events == []


def test_blocked_child_publishes_parent_disposition(kernel_double, journal_double):
    parent = kernel_double.node(id="parent", criterion=None)
    child = kernel_double.node(id="child", parent_id=parent.id, depth=1, criterion=None)
    tree = Tree(mission_id="mission", nodes=(parent, child), cap_children=2)
    result = split_node(tree, child.id, [], tree_path=Path("mission/tree.json"), journal=journal_double)
    disposition, = result.current_dispositions()
    assert disposition.child_id == child.id
    assert disposition.parent_id == parent.id
    assert disposition.disposition == "deferred"


@pytest.mark.parametrize("invalid", [None, False, 0, [], ""])
def test_non_object_persisted_state_is_not_treated_as_absent(kernel_double, journal_double, invalid):
    tree = Tree(mission_id="mission", nodes=(kernel_double.node(criterion=None),), cap_children=2)
    path = Path("mission/tree.json")
    journal_double.json_files[path] = invalid
    with pytest.raises(ValidationError):
        split_node(tree, tree.nodes[0].id, [], tree_path=path, journal=journal_double)
    assert journal_double.json_files[path] is invalid
