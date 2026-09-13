"""Fixtures du corpus de contrat : événements typés et racine de logs jetable.

Elles sont bâties sur le chargeur de `tests/conftest.py`, jamais sur le `conftest.py` privé d'un
module — un test de contrat n'appartient à aucun module et ne peut pas en dépendre.
"""

import json
from pathlib import Path

import pytest


@pytest.fixture
def logs_root(tmp_path):
    "Racine de logs jetable ; jamais l'arbre vivant, qu'aucun lecteur ne doit écrire."

    root = tmp_path / "logs"
    (root / "missions").mkdir(parents=True)

    return root


@pytest.fixture
def write_events(logs_root):
    "Dépose des lignes JSONL comme le ferait le journal, `event_id` compris."

    def write(mission_id, events, *, segment=0, torn=""):
        mission_dir = logs_root / "missions" / mission_id
        mission_dir.mkdir(parents=True, exist_ok=True)
        name = "events.jsonl" if segment == 0 else f"events.{segment}.jsonl"
        path = mission_dir / name

        # une ligne complète par événement, puis le fragment déchiré éventuel
        rows = []
        for number, event in enumerate(events, start=1):
            row = event.model_dump(mode="json")
            row["event_id"] = number
            rows.append(json.dumps(row, ensure_ascii=False))
        content = "".join(f"{row}\n" for row in rows) + torn
        path.write_text(content, encoding="utf-8")

        return path

    return write


@pytest.fixture
def moment():
    "Horodatage zoné à la seconde près : les durées attendues restent lisibles dans les tests."

    def at(second):
        return f"2026-09-07T10:00:{second:02d}+00:00"

    return at


@pytest.fixture
def an_event(kernel_double):
    "Fabrique un événement par le double de `kernel` ; chaque appel porte son propre payload."

    def make(**changes):
        return kernel_double.event(**changes)

    return make


@pytest.fixture
def node_event(kernel_double, an_event):
    "Événement de statut portant un nœud, le contrat `Node` dumpé sous son nom dans le payload."

    def make(node_id, *, at, parent_id=None, depth=0, status="pending", **changes):
        node = kernel_double.node(id=node_id, parent_id=parent_id, depth=depth, status=status, **changes)

        return an_event(type="status", ts=at, payload={"node": node.model_dump(mode="json")})

    return make


@pytest.fixture
def validation_event(kernel_double, an_event):
    """Événement de validation à la forme publiée par `verifier` : portée, identité, reçu, verdict.

    Le verdict porte les six clés de `Verdict.model_dump(mode="json")` ; les trois preuves
    d'exécution restent nulles, l'observatoire ne les lit pas.
    """

    def make(*, at, relation="total", symbols=("f",), verification="passed", artifact="invariant.py"):
        criterion = kernel_double.criterion(relation=relation, symbols=list(symbols))
        receipt = kernel_double.receipt(artifact_path=Path(artifact))
        verdict = {
            "criterion": criterion.model_dump(mode="json"),
            "verification": verification,
            "reason": "verified" if verification == "passed" else "after_red",
            "before": None,
            "after": None,
            "mutation": None,
        }
        payload = {
            "scope": "source_verification",
            "effect": "unproven",
            "key": {"kind": "verification", "value": ["m1", receipt.node_id, 1, relation]},
            "receipt": receipt.model_dump(mode="json"),
            "verification": verdict,
        }

        return an_event(type="validation", ts=at, payload=payload)

    return make
