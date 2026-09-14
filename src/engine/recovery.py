"""Réconciliation distincte du nominal, adaptée de Pi runtime/restore.ts et drive/recovery.ts.

Le détenteur du verrou de mission interroge les preuves et les octets avant tout effet.
Les traces partielles restent inconnues ; aucune consommation modèle synthétique.
"""

import json

from kernel.contracts import NodeStatus
from kernel.errors import Cause, PithosError
from kernel.facts import Receipt, RecordKey, RepoFact, SourceFact
from verifier.models import Verdict

from .attempt import _record, _transition, checked_receipt
from .tree import Tree, publish


def reconcile(tree: Tree, node_id: str, deps, *, tree_path, events_path) -> Tree:
    """Reconnaît un vert durable ou restaure un candidat connu, sans exécuter le modèle."""

    # le cas refuse une ancienne incarnation avant toute éventuelle restauration
    tree = Tree.model_validate_json(tree.model_dump_json())
    node = next(node for node in tree.nodes if node.id == node_id)
    if node.status != NodeStatus.running:
        return tree
    publish(tree, tree, tree_path, deps.journal)
    status, cause, detail = NodeStatus.blocked, Cause.unverifiable, "missing attempt snapshot"
    evidence = {}

    try:
        # lecture des seules preuves de la tentative réclamée, jamais de la dernière réponse globale
        attempt = tree.attempts.get(node_id)
        if attempt is None:
            raise PithosError(cause, detail)
        key = RecordKey(kind="verification", value=(tree.mission_id, node_id, attempt, node.criterion.relation))
        snapshot, intended, receipt, clean = None, None, None, None
        receipt_error = None
        for event in deps.journal.read(events_path):
            payload = event.payload
            if not event.durable or payload.get("key") != key.model_dump(mode="json"):
                continue
            operation = payload.get("operation") if payload.get("scope") == "engine" else None
            if operation == "running":
                snapshot = SourceFact.model_validate_json(json.dumps(payload["snapshot"]))
                clean = RepoFact.model_validate(payload["repo"])
            elif operation == "mutation_intent":
                intended = SourceFact.model_validate_json(json.dumps(payload["source"]))
            verified = event.type == "validation" and payload.get("scope") == "node_verification"
            if verified or operation == "passed":
                try:
                    verdict = Verdict.model_validate_json(json.dumps(payload["verification"]))
                    recorded = Receipt.model_validate_json(json.dumps(payload["receipt"]))
                    receipt = checked_receipt(node, key, recorded, verdict)
                except (PithosError, ValueError, KeyError) as error:
                    receipt_error = str(error)
        if snapshot is None or clean is None or snapshot.before != snapshot.after:
            raise ValueError("missing or inconsistent attempt snapshot")
        if not clean.complete or not clean.head or clean.changes or clean.diff:
            raise ValueError("attempt did not start from a complete clean repository")
        if intended is not None and (intended.path != snapshot.path or intended.before != snapshot.before):
            raise ValueError("mutation does not extend the captured snapshot")

        # l'observation des octets tranche ; un fichier étranger n'est jamais écrasé
        with deps.workspace.transaction(node.target) as transaction:
            current = transaction.source_fact()
            if current.path != snapshot.path:
                raise ValueError("snapshot target differs from the current target")
            if current.after == snapshot.before:
                cause, detail = Cause.interrupted, "original bytes observed; no candidate replayed"
            elif intended is None or current.after != intended.after:
                raise ValueError("current bytes match neither snapshot nor intended candidate")
            else:
                cause, detail = Cause.interrupted, "unreceipted candidate restored exactly"
                if receipt is not None and receipt_error is None:
                    source = next(fact for fact in receipt.facts if isinstance(fact, SourceFact))
                    repo = next(fact for fact in receipt.facts if isinstance(fact, RepoFact))
                    observed = RepoFact.model_validate_json(deps.observe_repo().model_dump_json())
                    consistent = source == intended and repo.repo == clean.repo and repo.head == clean.head
                    if consistent and observed == repo and transaction.source_fact() == current:
                        status, cause, detail = NodeStatus.passed, None, "durable receipt reconciled against current facts"
                        evidence = {"receipt": receipt.model_dump(mode="json")}
                    else:
                        cause, detail = Cause.unverifiable, "current observations differ from the receipt"
                if status != NodeStatus.passed:
                    _record(tree, node_id, "restore_intent", {"key": key.model_dump(mode="json")}, deps.journal)
                    transaction.cas_write(snapshot.before)
        if receipt_error is not None:
            cause, detail = Cause.unverifiable, receipt_error
    except (PithosError, ValueError, KeyError) as error:
        cause = error.cause if isinstance(error, PithosError) else Cause.unverifiable
        detail = str(error)

    # la restauration est achevée avant publication : un cas refusé ne la défait pas
    return _transition(tree, node_id, status, cause, detail, tree_path, deps.journal, **evidence)
