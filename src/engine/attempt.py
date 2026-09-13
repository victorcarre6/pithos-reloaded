"""Une nano-étape transactionnelle ; aucun retry, processus ou transport détenu ici."""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Callable, Protocol, runtime_checkable

from pydantic import ValidationError

from bridge import Bridge, Capability, Deadline, Ok, Outcome
from journal import Journal
from kernel.contracts import Event, NodeStatus
from kernel.errors import Cause, PithosError
from kernel.facts import Receipt, RecordKey, RepoFact
from verifier import Verifier
from workspace import WorkspacePort

from .budget import Budget
from .tree import Tree
from .walk import StateNotWrittenError, is_verifiable, split_node


@dataclass(frozen=True)
class Deps:
    workspace: WorkspacePort
    bridge: Bridge
    verifier: Verifier
    journal: Journal
    observe_repo: Callable[[], RepoFact]
    capability: Capability


@runtime_checkable
class NanoEngine(Protocol):
    def run_attempt(self, tree, node_id, budget, deps, *, tree_path, artifact_root,
                    system, instruction, attempt) -> Tree: ...


def _record(tree, node_id, operation, payload, journal):
    event = Event(
        ts=datetime.now(timezone.utc).isoformat(),
        v=1,
        type="status",
        durable=True,
        payload={
            "scope": "engine",
            "mission_id": tree.mission_id,
            "node_id": node_id,
            "operation": operation,
            **payload,
        },
    )
    if journal.emit(event) is not True:
        raise StateNotWrittenError("attempt event was not written")


def _transition(tree, node_id, status, cause, detail, tree_path, journal):
    # l'intention précède le cas de l'état de domaine
    nodes = []
    for node in tree.nodes:
        if node.id == node_id:
            values = node.model_dump()
            values.update(status=status, blocked_cause=cause if status == NodeStatus.blocked else None)
            node = type(node).model_validate(values)
        nodes.append(node)
    values = tree.model_dump()
    values["nodes"] = nodes
    updated = Tree.model_validate(values)
    payload = {"phase": "intent", "cause": cause, "detail": detail}
    _record(tree, node_id, status.value, payload, journal)

    def publish(current):
        if current != {} and Tree.model_validate(current) != tree:
            raise StateNotWrittenError("tree changed since observation")

        return updated.model_dump(mode="json")

    journal.update_json_locked(tree_path, publish)

    return updated


def run_attempt(tree: Tree, node_id: str, budget: Budget, deps: Deps, *, tree_path: Path,
                artifact_root: Path, system: str, instruction: str, attempt: int) -> Tree:
    """Tente un nœud pending ; seul le reçu durable autorise la publication du vert."""

    # aucune réexécution implicite d'un effet inconnu ou d'un résultat enregistré
    tree = Tree.model_validate_json(tree.model_dump_json())
    node = next(node for node in tree.nodes if node.id == node_id)
    if node.status != NodeStatus.pending:
        return tree
    if not is_verifiable(node):
        return split_node(tree, node_id, [], tree_path=tree_path, journal=deps.journal)
    key = RecordKey(kind="verification", value=(tree.mission_id, node_id, attempt, node.criterion.relation))

    try:
        # le dépôt et le critère doivent être admissibles avant l'appel modèle
        if not budget.can_start:
            raise PithosError(Cause.timeout, "admission budget exhausted")
        if not deps.capability.usable:
            raise PithosError(Cause.unverifiable, "model capability is not established")
        clean = RepoFact.model_validate_json(deps.observe_repo().model_dump_json())
        if not clean.complete or not clean.head or clean.changes or clean.diff:
            raise PithosError(Cause.unverifiable, "a complete clean repository is required")
        with deps.workspace.transaction(node.target) as transaction:
            initial = transaction.source_fact()
            source = initial.before.decode("utf-8-sig")
            deps.verifier.preflight(node.criterion, source)
            function_name = node.criterion.symbols[0]
            model = deps.bridge.candidate_model(function_name)
            schema = deps.bridge.normalize_schema(model)
            user = json.dumps({
                "instruction": instruction,
                "function_name": function_name,
                "source": source,
                "criterion": node.criterion.model_dump(mode="json"),
            }, ensure_ascii=False)
            tree = _transition(tree, node_id, NodeStatus.running, None, "candidate requested", tree_path, deps.journal)
            deadline = Deadline(budget.spendable, deps.capability.context_window, 2048, deps.capability.provenance.value)
            if deadline.seconds <= 0:
                raise PithosError(Cause.timeout, "model admission budget exhausted")
            response = deps.bridge.call(schema, system, user, deadline)
            _record(tree, node_id, "candidate_response", {
                "key": key.model_dump(mode="json"),
                "outcome": response.outcome.value,
                "content": response.content,
                "thinking": response.thinking,
                "raw_stop_reason": response.raw_stop_reason,
                "usage": response.usage,
            }, deps.journal)
            if response.outcome is not Outcome.completed:
                raise PithosError(Cause.unverifiable, response.outcome.value)
            candidate = deps.bridge.revalidate(response.content, schema, model)
            if not isinstance(candidate, Ok):
                raise PithosError(Cause.invalid_schema, candidate.code.value)
            if not budget.can_start:
                raise PithosError(Cause.timeout, "mutation admission budget exhausted")

            # transaction : toute exception, y compris la publication finale, restaure les octets
            proposed = candidate.value
            file = transaction.splice(proposed.function_name, proposed.new_source)
            sources = transaction.source_fact()
            repo = deps.observe_repo()
            facts = [file, sources, repo]
            verdict = deps.verifier.run(node.criterion, facts, artifact_root=artifact_root, timeout=budget.spendable)
            _record(tree, node_id, "verification_report", {
                "key": key.model_dump(mode="json"),
                "verification": verdict.model_dump(mode="json", exclude={"facts"}),
            }, deps.journal)
            if verdict.verification != "passed" or verdict.effect != "confirmed":
                raise PithosError(Cause.invariant_failed, verdict.reason)
            if budget.remaining <= 0:
                raise PithosError(Cause.timeout, "verification exceeded mission deadline")
            if transaction.source_fact() != sources or deps.observe_repo() != repo:
                raise PithosError(Cause.unverifiable, "observations changed during verification")
            receipt = deps.verifier.emit_receipt(node_id, attempt, facts, verdict.after.artifact_path,
                                                key=key, verdict=verdict, journal=deps.journal)
            if receipt is None:
                raise PithosError(Cause.receipt_not_written, "receipt was not acknowledged")
            receipt = Receipt.model_validate_json(receipt.model_dump_json())
            identity = (receipt.node_id, receipt.attempt, receipt.artifact_path, receipt.returncode)
            expected = (node_id, attempt, verdict.after.artifact_path, 0)
            if identity != expected or receipt.facts != facts:
                raise PithosError(Cause.unverifiable, "receipt does not attest this attempt")
            tree = _transition(tree, node_id, NodeStatus.passed, None, "receipt acknowledged", tree_path, deps.journal)
    except (PithosError, ValidationError, SyntaxError, UnicodeError) as error:
        cause = error.cause if isinstance(error, PithosError) else Cause.invalid_schema
        status = NodeStatus.budget_limited if cause == Cause.timeout else NodeStatus.blocked
        tree = _transition(tree, node_id, status, cause, str(error), tree_path, deps.journal)

    return tree
