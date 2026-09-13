"""Admission et scission du marcheur ; le chemin d'exécution attend ses contrats.

Transitions explicites et intention avant effet adaptées de Pi
packages/agent/src/harness/runtime/drive.ts et drive/generation.ts:132-184.
"""

from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from journal import Journal
from kernel.contracts import Event, Node, NodeStatus
from kernel.errors import Cause

from .classify import ActionClass, RepoIndex, TaskMode, analyze_instruction
from .tree import ChildDisposition, Tree, result_sha256


class StateNotWrittenError(RuntimeError):
    """L'intention n'est pas durable ; aucune transition ne peut être publiée."""


def is_verifiable(node: Node) -> bool:
    """Préflight structurel du critère ; l'exécutabilité effective appartient à verifier."""

    try:
        validated = Node.model_validate(node.model_dump())
    except ValidationError:
        return False

    return validated.criterion is not None


def split_node(tree: Tree, node_id: str, targets: list[Path], *,
               tree_path: Path, journal: Journal) -> Tree:
    """Publie une scission déterministe complète ou un blocage, jamais une liste tronquée."""

    # revalidation de l'instantané avant de choisir la transition
    tree = Tree.model_validate_json(tree.model_dump_json())
    by_id = {node.id: node for node in tree.nodes}
    node = by_id[node_id]
    if node.status != NodeStatus.pending or any(child.parent_id == node_id for child in tree.nodes):
        return tree
    if is_verifiable(node):
        raise ValueError("a node carrying a criterion cannot enter criterion-free splitting")
    unique = set(targets)
    candidates = sorted(unique)
    if node.depth == 3:
        reason = "depth_limit"
    elif len(candidates) > tree.cap_children:
        reason = "width_limit"
    elif not candidates:
        reason = "no_candidates"
    else:
        reason = "split"

    # résultat préparé et validé intégralement avant journalisation
    nodes = list(tree.nodes)
    dispositions = list(tree.dispositions)
    if reason == "split":
        for index, target in enumerate(candidates, start=1):
            child = Node(
                id=f"{node_id}/{index}",
                parent_id=node_id,
                depth=node.depth + 1,
                target=target,
                criterion=None,
                status=NodeStatus.pending,
                blocked_cause=None,
            )
            nodes.append(child)
    else:
        values = node.model_dump()
        values.update(status=NodeStatus.blocked, blocked_cause=Cause.unverifiable)
        blocked = Node.model_validate(values)
        nodes[nodes.index(node)] = blocked
        if node.parent_id is not None:
            dispositions.append(ChildDisposition(
                parent_id=node.parent_id,
                child_id=node.id,
                disposition="deferred",
                result_sha256=result_sha256(blocked),
            ))
    updated = Tree(
        mission_id=tree.mission_id,
        nodes=tuple(nodes),
        cap_children=tree.cap_children,
        dispositions=tuple(dispositions),
    )

    # logging : intention durable, puis cas du tree.json sous le verrou du journal
    payload = {
        "scope": "engine",
        "mission_id": tree.mission_id,
        "node_id": node_id,
        "operation": "split" if reason == "split" else "blocked",
        "phase": "intent",
        "reason": reason,
        "candidates": [str(target) for target in candidates],
        "family": "tree" if reason == "split" else "memory",
        "cause": None if reason == "split" else Cause.unverifiable.value,
    }
    event = Event(ts=datetime.now(timezone.utc).isoformat(), v=1, type="status", durable=True, payload=payload)
    if journal.emit(event) is not True:
        raise StateNotWrittenError("tree transition intent was not written")

    def publish(current):
        # aucun écrasement d'une version concurrente ou illisible
        if current != {} and Tree.model_validate(current) != tree:
            raise StateNotWrittenError("tree changed since observation")

        return updated.model_dump(mode="json")

    journal.update_json_locked(tree_path, publish)

    return updated


def decompose(tree: Tree, node_id: str, instruction: str, index: RepoIndex, *,
              tree_path: Path, journal: Journal) -> Tree:
    """Branche la classification déterministe sur la scission, sans appel modèle."""

    # la classification nourrit les cibles, les enums et leurs traces
    analysis = analyze_instruction(instruction, index)
    read_only = {ActionClass.READ_ONLY, ActionClass.SHELL_READ_ONLY, ActionClass.GIT_SAFE}
    write_actions = set(analysis.action_classes) - read_only
    targets = []
    if write_actions and analysis.task_mode != TaskMode.INSPECT_AND_PLAN:
        targets = [candidate.target for candidate in analysis.candidate_targets]

    # logging
    payload = {
        "scope": "engine",
        "mission_id": tree.mission_id,
        "node_id": node_id,
        "operation": "classification",
        "analysis": analysis.model_dump(mode="json"),
    }
    event = Event(ts=datetime.now(timezone.utc).isoformat(), v=1, type="status", durable=True, payload=payload)
    if journal.emit(event) is not True:
        raise StateNotWrittenError("classification was not written")

    return split_node(tree, node_id, targets, tree_path=tree_path, journal=journal)
