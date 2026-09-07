"""Reçu de vérification publié avant retour ; l'effet workspace doit être attesté séparément."""

from datetime import datetime, timezone
from pathlib import Path

from journal import Journal
from kernel.contracts import Event
from kernel.facts import Fact, Receipt, RecordKey

from .models import Verdict


def emit_receipt(node_id: str, attempt: int, facts: list[Fact], artifact: Path, *,
                 key: RecordKey, verdict: Verdict, journal: Journal) -> Receipt | None:
    """Persiste une double gate vérifiée ; rend None si le journal n'acquitte pas l'écriture."""

    # validation complète avant toute tentative de persistance
    if not isinstance(key, RecordKey):
        raise ValueError("typed record identity required")
    key = RecordKey.model_validate_json(key.model_dump_json())
    verdict = Verdict.model_validate_json(verdict.model_dump_json())
    expected = (node_id, attempt, verdict.criterion.relation)
    if key.value[1:] != expected:
        raise ValueError("receipt identity does not match the verified criterion")
    if verdict.verification != "passed":
        raise ValueError("a verified double gate is required")
    if artifact != verdict.after.artifact_path:
        raise ValueError("receipt artifact does not match the verified execution")
    receipt = Receipt(
        node_id=node_id,
        attempt=attempt,
        returncode=verdict.after.returncode,
        artifact_path=artifact,
        facts=facts,
    )
    receipt = Receipt.model_validate_json(receipt.model_dump_json())

    # la trace nomme sa portée ; ce reçu seul ne rend aucun nœud vert
    event = Event(
        ts=datetime.now(timezone.utc).isoformat(),
        v=1,
        type="validation",
        durable=True,
        payload={
            "scope": "source_verification",
            "effect": "unproven",
            "key": key.model_dump(mode="json"),
            "receipt": receipt.model_dump(mode="json"),
            "verification": verdict.model_dump(mode="json"),
        },
    )
    if journal.emit(event) is not True:
        return None

    return receipt
