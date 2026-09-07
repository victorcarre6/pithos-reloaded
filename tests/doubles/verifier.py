"""Double déterministe de la double gate sur sources ; aucun processus ni fichier."""

from kernel.contracts import Criterion
from kernel.facts import Receipt, RecordKey
from verifier.models import Verdict


def _key(criterion):
    validated = Criterion.model_validate(criterion.model_dump())

    return validated.relation, tuple(validated.symbols), validated.domain


class MemoryVerifier:
    """Rend les verdicts de la table de couples (Criterion, Verdict), sans repli implicite."""

    def __init__(self, scenarios, receipts=()):
        self.scenarios = {}
        for criterion, verdict in scenarios:
            key = _key(criterion)
            if key in self.scenarios:
                raise ValueError("duplicate criterion scenario")
            self.scenarios[key] = Verdict.model_validate_json(verdict.model_dump_json())
        self.receipts = {}
        for key, receipt in receipts:
            if not isinstance(key, RecordKey) or key in self.receipts:
                raise ValueError("unique typed receipt identity required")
            self.receipts[key] = None if receipt is None else Receipt.model_validate_json(receipt.model_dump_json())

    def check_sources(self, criterion, before, after, *, artifact_root, timeout):
        verdict = self.scenarios[_key(criterion)]

        return Verdict.model_validate_json(verdict.model_dump_json())

    def emit_receipt(self, node_id, attempt, facts, artifact, *, key, verdict, journal):
        receipt = self.receipts[key]

        return None if receipt is None else Receipt.model_validate_json(receipt.model_dump_json())
