"""Fixtures partagées : une racine de logs jetable et des événements typés ; doubles hérités."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def logs_root(tmp_path):
    "Racine de logs jetable ; jamais l'arbre vivant, que `observatory` ne doit pas non plus écrire."

    root = tmp_path / "logs"
    (root / "missions").mkdir(parents=True)

    return root


@pytest.fixture
def write_events(logs_root):
    """Dépose des lignes JSONL comme le ferait le journal, `event_id` compris.

    `torn` ajoute un fragment final non terminé par un LF, `segment` vise `events.<n>.jsonl`.
    """

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
def an_event(double):
    "Fabrique un événement par le double de `kernel` ; chaque appel porte son propre payload."

    kernel = double("kernel")

    def make(**changes):
        return kernel.event(**changes)

    return make


@pytest.fixture
def moment():
    "Horodatage zoné à la seconde près : les durées attendues restent lisibles dans les tests."

    def at(second):
        return f"2026-09-07T10:00:{second:02d}+00:00"

    return at


@pytest.fixture
def node_event(double, an_event):
    "Événement de statut portant un nœud, le contrat `Node` dumpé sous son nom dans le payload."

    kernel = double("kernel")

    def make(node_id, *, at, parent_id=None, depth=0, status="pending", **changes):
        node = kernel.node(id=node_id, parent_id=parent_id, depth=depth, status=status, **changes)

        return an_event(type="status", ts=at, payload={"node": node.model_dump(mode="json")})

    return make


@pytest.fixture
def validation_event(double, an_event):
    """Événement de validation à la forme publiée par `verifier` : portée, identité, reçu, verdict.

    Le verdict porte les six clés de `Verdict.model_dump(mode="json")` ; les trois preuves
    d'exécution restent nulles, l'observatoire ne les lit pas.
    """

    kernel = double("kernel")

    def make(*, at, relation="total", symbols=("f",), verification="passed", artifact="invariant.py"):
        criterion = kernel.criterion(relation=relation, symbols=list(symbols))
        receipt = kernel.receipt(artifact_path=Path(artifact))
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


@pytest.fixture
def model_call_event(an_event):
    "Événement de statut à la forme que `bridge` consigne : payload effectif, issue et usage."

    def make(*, at, prompt_estimate=None, prompt_tokens=None, max_tokens=512, outcome="completed"):
        usage = {"prompt_tokens": prompt_tokens, "completion_tokens": 12} if prompt_tokens is not None else {}
        payload = {
            "endpoint": "http://127.0.0.1:11434/v1/chat/completions",
            "model": "pithos/ling-3.0-tiny:8b-16k",
            "schema_sha256": "0" * 64,
            "max_tokens": max_tokens,
            "sampling": {"temperature": 0.3, "top_p": 0.95, "top_k": 20},
            "outcome": outcome,
            "raw_stop_reason": "stop",
            "prompt_estimate": prompt_estimate,
            "context_window": 16384,
            "context_provenance": "asserted",
            "usage": usage,
            "body_excerpt": "",
        }

        return an_event(type="status", ts=at, payload=payload)

    return make


@pytest.fixture
def tool_event(an_event):
    "Événement d'activité d'outil à la forme que `workspace` enregistre : opération et chemin."

    def make(operation, *, at, path="tool.py", **extra):
        payload = {"operation": operation, "path": path, **extra}

        return an_event(type="tool_activity", ts=at, payload=payload)

    return make
