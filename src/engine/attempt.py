"""Une nano-étape transactionnelle ; aucun retry, processus ou transport détenu ici."""

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Callable, Protocol, runtime_checkable

from pydantic import ValidationError

from bridge import Bridge, Capability, Deadline, Ok, Outcome
from journal import Journal
from kernel.contracts import Event, NodeStatus
from kernel.errors import Cause, PithosError
from kernel.facts import Receipt, RecordKey, RepoFact, SourceFact
from verifier import Verifier
from verifier.models import Verdict
from workspace import WorkspacePort, prepare_splice

from . import dump as context_archive
from .budget import Budget
from .context import ContextItem, assemble
from .dump import ContextArchive, Handoff
from .tree import StateConflictError, StateNotWrittenError, Tree, publish


@dataclass(frozen=True)
class Deps:
    workspace: WorkspacePort
    bridge: Bridge
    verifier: Verifier
    journal: Journal
    observe_repo: Callable[[], RepoFact]
    capability: Capability
    archive: ContextArchive = context_archive


@runtime_checkable
class NanoEngine(Protocol):
    def run_attempt(self, tree, node_id, budget, deps, *, tree_path, artifact_root,
                    system, instruction, attempt) -> Tree: ...


def checked_receipt(node, key, receipt, verdict):
    """Revalide l'acquittement de verifier et son lien exact à la double gate."""

    receipt = Receipt.model_validate_json(receipt.model_dump_json())
    verdict = Verdict.model_validate_json(verdict.model_dump_json())
    if verdict.verification != "passed" or verdict.effect != "confirmed" or verdict.criterion != node.criterion:
        raise PithosError(Cause.unverifiable, "receipt lacks the admitted double gate")
    identity = (receipt.node_id, receipt.attempt, receipt.artifact_path, receipt.returncode)
    expected = (node.id, key.value[2], verdict.after.artifact_path, 0)
    if identity != expected or receipt.facts != verdict.facts:
        raise PithosError(Cause.unverifiable, "receipt does not attest this attempt")

    return receipt


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


def _transition(tree, node_id, status, cause, detail, tree_path, journal, **evidence):
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
    if status == NodeStatus.running and "key" in evidence:
        values["attempts"][node_id] = evidence["key"]["value"][2]
    if "receipt" in evidence:
        values["receipts"][node_id] = Receipt.model_validate_json(json.dumps(evidence["receipt"]))
    updated = Tree.model_validate(values)
    payload = {"phase": "intent", "cause": cause, "detail": detail, **evidence}
    if status == NodeStatus.blocked:
        payload["family"] = "memory"
    _record(tree, node_id, status.value, payload, journal)
    publish(tree, updated, tree_path, journal)

    return updated


def run_attempt(tree: Tree, node_id: str, budget: Budget, deps: Deps, *, tree_path: Path,
                artifact_root: Path, system: str, instruction: str, attempt: int) -> Tree:
    """Tente un nœud pending ; seul le reçu durable autorise la publication du vert."""

    from .walk import is_verifiable, split_node

    # aucune réexécution implicite d'un effet inconnu ou d'un résultat enregistré
    tree = Tree.model_validate_json(tree.model_dump_json())
    node = next(node for node in tree.nodes if node.id == node_id)
    if node.status != NodeStatus.pending:
        return tree
    if not is_verifiable(node):
        return split_node(tree, node_id, [], tree_path=tree_path, journal=deps.journal)
    key = RecordKey(kind="verification", value=(tree.mission_id, node_id, attempt, node.criterion.relation))
    if attempt <= tree.attempts.get(node_id, 0):
        raise ValueError("a new admission requires a new attempt identity")

    packet = None
    verdict = None
    archive_path = artifact_root / "CONTEXT.md"
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
            available = deps.capability.context_window - 2048
            if available <= 0:
                raise PithosError(Cause.context_overflow, "no context capacity above reserved output")
            fingerprint = {initial.path: sha256(initial.before).hexdigest()}
            items = deps.archive.read(tree.mission_id, path=archive_path)
            for name, kind, content, reason in (
                ("system", "instruction", system, "task_relevance"),
                ("request", "file", user, "plan_target"),
                ("schema", "validation", json.dumps(schema), "validation_signal"),
            ):
                items.append(ContextItem(
                    source_id=name,
                    source_type=kind,
                    content=content,
                    estimated_units=len(content) // 4 + 1,
                    retention="required",
                    included_reason=reason,
                    excluded_reason=None,
                    fingerprints=fingerprint if kind == "file" else {},
                ))
            packet = assemble(node, available, items=items, fingerprints=fingerprint)
            _record(tree, node_id, "context", {
                "key": key.model_dump(mode="json"),
                "packet": packet.model_dump(mode="json"),
            }, deps.journal)
            if packet.blocked_cause is not None:
                raise PithosError(packet.blocked_cause, "irreducible context exceeds model capacity")
            user_items = tuple(item for item in packet.items if item.source_id not in {"system", "schema"})
            user = packet.model_copy(update={"items": user_items}).render()
            tree = _transition(tree, node_id, NodeStatus.running, None, "candidate requested", tree_path, deps.journal,
                               key=key.model_dump(mode="json"), snapshot=initial.model_dump(mode="json"),
                               repo=clean.model_dump(mode="json"))
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
            plan = prepare_splice(initial.before, proposed.function_name, proposed.new_source, target=initial.path)
            intended = SourceFact(path=initial.path, before=initial.before, after=plan.content)
            _record(tree, node_id, "mutation_intent", {
                "key": key.model_dump(mode="json"),
                "source": intended.model_dump(mode="json"),
            }, deps.journal)
            file = transaction.splice(proposed.function_name, proposed.new_source)
            sources = transaction.source_fact()
            repo = deps.observe_repo()
            facts = [file, sources, repo]
            report = deps.verifier.run(node.criterion, facts, artifact_root=artifact_root, timeout=budget.spendable)
            report = Verdict.model_validate_json(report.model_dump_json())
            _record(tree, node_id, "verification_report", {
                "key": key.model_dump(mode="json"),
                "verification": report.model_dump(mode="json", exclude={"facts"}),
            }, deps.journal)
            if report.criterion != node.criterion:
                raise PithosError(Cause.unverifiable, "verification criterion differs from admission")
            verdict = report
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
            receipt = checked_receipt(node, key, receipt, verdict)
            if receipt.facts != facts:
                raise PithosError(Cause.unverifiable, "receipt does not attest this attempt")
            tree = _transition(tree, node_id, NodeStatus.passed, None, "receipt acknowledged", tree_path, deps.journal,
                               key=key.model_dump(mode="json"), receipt=receipt.model_dump(mode="json"),
                               verification=verdict.model_dump(mode="json"))
    except (PithosError, ValidationError, SyntaxError, UnicodeError) as error:
        cause = error.cause if isinstance(error, PithosError) else Cause.invalid_schema
        status = NodeStatus.budget_limited if cause == Cause.timeout else NodeStatus.blocked
        tree = _transition(tree, node_id, status, cause, str(error), tree_path, deps.journal)
    finally:
        # après sortie de transaction : empreinte courante, y compris après restauration
        if packet is not None and not isinstance(sys.exception(), StateConflictError):
            with deps.workspace.transaction(node.target) as observation:
                current = observation.source_fact()
            terminal = next(entry for entry in tree.nodes if entry.id == node_id)
            section = Handoff(
                key=key,
                packet=packet,
                status=terminal.status,
                verdict=verdict,
                fingerprints={current.path: sha256(current.after).hexdigest()},
            )
            deps.archive.dump(section, path=archive_path)

    return tree
