"""Marcheur de mission sans framework, reprise et finalisation par ports injectés.

Transitions explicites et intention avant effet adaptées de Pi
packages/agent/src/harness/runtime/drive.ts et drive/generation.ts:132-184.
"""

from datetime import datetime, timezone
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Protocol, runtime_checkable

from pydantic import ValidationError

from journal import Journal
from kernel.contracts import Event, Node, NodeStatus
from kernel.errors import Cause, PithosError
from kernel.facts import Receipt, RecordKey, RepoFact, SourceFact

from .attempt import Deps, _record, _transition, run_attempt
from .budget import Budget
from .classify import ActionClass, RepoIndex, TaskMode, analyze_instruction
from .tree import ChildDisposition, StateConflictError, StateNotWrittenError, Tree, publish, result_sha256


@runtime_checkable
class GreenFinalizer(Protocol):
    def reconcile(self, key: RecordKey, receipt: Receipt, timeout: float) -> RepoFact | None: ...
    def finalize(self, key: RecordKey, receipt: Receipt, timeout: float) -> RepoFact: ...


@dataclass(frozen=True)
class WalkDeps:
    attempt: Deps
    finalizer: GreenFinalizer
    tree_path: Path
    events_path: Path
    artifact_root: Path
    system: str
    instruction: str
    index: RepoIndex | None = None


@runtime_checkable
class Walker(Protocol):
    def walk(self, tree: Tree, budget: Budget, deps: WalkDeps) -> Tree: ...


def finalize_green_nodes(tree: Tree, budget: Budget, deps: WalkDeps) -> Tree:
    """Interroge la publication avant tout rejeu et conserve son résultat dans l'arbre."""

    # un résultat déjà finalisé ne produit aucun nouvel effet sortant
    ports = deps.attempt
    for node in tree.nodes:
        if node.status != NodeStatus.passed or node.id in tree.finalized:
            continue
        receipt = tree.receipts.get(node.id)
        if receipt is None:
            tree = _transition(tree, node.id, NodeStatus.blocked, Cause.unverifiable,
                               "passed node has no durable receipt", deps.tree_path, ports.journal)
            continue
        if budget.remaining <= 0:
            break
        key = RecordKey(kind="verification", value=(tree.mission_id, node.id, receipt.attempt, node.criterion.relation))
        source = next(fact for fact in receipt.facts if isinstance(fact, SourceFact))
        before = next(fact for fact in receipt.facts if isinstance(fact, RepoFact))
        publish(tree, tree, deps.tree_path, ports.journal)

        # le port interroge l'identité logique même après une perte d'acquittement
        with ports.workspace.transaction(node.target) as transaction:
            current = transaction.source_fact()
            if current.path != source.path or current.after != source.after:
                raise PithosError(Cause.unverifiable, "green source changed before finalization")
            result = deps.finalizer.reconcile(key, receipt, budget.remaining)
            if result is None:
                if ports.observe_repo() != before:
                    raise PithosError(Cause.unverifiable, "repository changed before finalization")
                if budget.remaining <= 0:
                    break
                _record(tree, node.id, "finalize_intent", {"key": key.model_dump(mode="json")}, ports.journal)
                result = deps.finalizer.finalize(key, receipt, budget.remaining)
            result = RepoFact.model_validate_json(result.model_dump_json())
            if not result.complete or result.changes or result.diff or not result.head:
                raise PithosError(Cause.unverifiable, "finalization did not produce a complete clean repository")
            if result.repo != before.repo or result.head == before.head or ports.observe_repo() != result:
                raise PithosError(Cause.unverifiable, "finalization does not match the observed repository")
            if transaction.source_fact() != current:
                raise PithosError(Cause.unverifiable, "green source changed during finalization")

        # le résultat de publication est immuable pour cette tentative
        values = tree.model_dump()
        values["finalized"][node.id] = result
        updated = Tree.model_validate(values)
        _record(tree, node.id, "finalized", {
            "key": key.model_dump(mode="json"),
            "repo": result.model_dump(mode="json"),
        }, ports.journal)
        publish(tree, updated, deps.tree_path, ports.journal)
        tree = updated

    return tree


def walk(tree: Tree, budget: Budget, deps: WalkDeps) -> Tree:
    """Marche sous verrou de mission détenu par l'appelant ; chaque retour est reprenable."""

    from .recovery import reconcile

    # valider et réconcilier les effets inconnus avant toute nouvelle admission
    tree = Tree.model_validate_json(tree.model_dump_json())
    ports = deps.attempt
    cause, owned = "error", True
    try:
        publish(tree, tree, deps.tree_path, ports.journal)
        for node in tree.nodes:
            if node.status == NodeStatus.running:
                tree = reconcile(tree, node.id, ports, tree_path=deps.tree_path, events_path=deps.events_path)
        tree = finalize_green_nodes(tree, budget, deps)
        for node in tree.nodes:
            if node.status == NodeStatus.budget_limited and budget.can_start:
                tree = _transition(tree, node.id, NodeStatus.pending, None, "new mission budget",
                                   deps.tree_path, ports.journal)

        # parcours stable des feuilles ; aucune boucle de retry d'un échec métier
        while budget.can_start:
            parents = {node.parent_id for node in tree.nodes}
            pending = [node for node in tree.nodes if node.id not in parents and node.status == NodeStatus.pending]
            if not pending:
                break
            if any(node.status == NodeStatus.passed and node.id not in tree.finalized for node in tree.nodes):
                break
            node = pending[0]
            if not is_verifiable(node) and deps.index is not None:
                tree = decompose(tree, node.id, deps.instruction, deps.index,
                                 tree_path=deps.tree_path, journal=ports.journal)
            else:
                attempt = tree.attempts.get(node.id, 0) + 1
                tree = run_attempt(tree, node.id, budget, ports, tree_path=deps.tree_path,
                                   artifact_root=deps.artifact_root, system=deps.system,
                                   instruction=deps.instruction, attempt=attempt)
            tree = finalize_green_nodes(tree, budget, deps)
        cause = "completed"
        if any(node.status in {NodeStatus.blocked, NodeStatus.failed, NodeStatus.exhausted, NodeStatus.retryable}
               for node in tree.nodes):
            cause = "blocked"
        if not budget.can_start or any(node.status == NodeStatus.budget_limited for node in tree.nodes):
            cause = "timeout"
    except StateConflictError:
        cause, owned = "state_conflict", False
        raise
    except KeyboardInterrupt:
        cause = "interrupted"
        raise
    finally:
        # relire les transitions qu'une tentative a pu publier avant de lever
        if owned:
            def capture(current):
                nonlocal tree
                if current != {}:
                    tree = Tree.model_validate_json(json.dumps(current))

                return tree.model_dump(mode="json")

            ports.journal.update_json_locked(deps.tree_path, capture)
            dispositions = list(tree.dispositions)
            current_dispositions = {item.child_id: item for item in tree.current_dispositions()}
            for node in tree.nodes:
                if node.parent_id is None or node.status in {NodeStatus.pending, NodeStatus.running}:
                    continue
                disposition = ChildDisposition(
                    parent_id=node.parent_id,
                    child_id=node.id,
                    disposition="integrated" if node.id in tree.finalized else "deferred",
                    result_sha256=result_sha256(node, tree.receipts.get(node.id)),
                )
                if disposition != current_dispositions.get(node.id):
                    dispositions.append(disposition)
            updated = tree.model_copy(update={"dispositions": tuple(dispositions)})
            publish(tree, updated, deps.tree_path, ports.journal)
            tree = updated

        # logging : une baseline par invocation, même sans tentative admise
        _record(tree, None, "baseline", {
            "green_nodes": sum(node.status == NodeStatus.passed for node in tree.nodes),
            "attempted_nodes": len(tree.attempts),
            "finalized_nodes": len(tree.finalized),
            "wall_seconds": budget.elapsed,
            "exit_cause": cause,
        }, ports.journal)

    return tree


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
    values = tree.model_dump()
    values.update(nodes=nodes, dispositions=dispositions)
    updated = Tree.model_validate(values)

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

    publish(tree, updated, tree_path, journal)

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
