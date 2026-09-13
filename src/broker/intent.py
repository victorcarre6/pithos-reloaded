"""Persister l'intention avant l'effet : une reprise distingue *non commencé* d'*effet inconnu*.

Sans cette distinction, rejouer un effet externe est un pari. L'ordre d'écriture est la protection :
l'intention, puis l'effet, puis le résultat.
"""

from enum import StrEnum
from pathlib import Path
from typing import Callable

import journal

from .identity import EffectIdentity


class Stage(StrEnum):
    unstarted = "unstarted"
    unknown_effect = "unknown_effect"
    recorded = "recorded"


def read_ledger(ledger: Path, *, trace=journal) -> dict:
    "Lit le registre sous le verrou du journal, sans le modifier."

    captured: dict = {}

    def capture(state):
        captured.update(state)

        return state

    trace.update_json_locked(ledger, capture)

    return captured


def _merge(ledger: Path, key: str, fields: dict, *, trace) -> None:
    "Fusionne les champs dans l'entrée du résultat, sous le verrou du journal."

    trace.update_json_locked(ledger, lambda state: {**state, key: {**state.get(key, {}), **fields}})


def record_intent(ledger: Path, identity: EffectIdentity, intent: dict, *, trace=journal) -> None:
    "Écrit l'intention **avant** l'effet ; l'entrée est celle du résultat visé, pas du transport."

    _merge(ledger, identity.result, {"transport": identity.transport, "intent": intent}, trace=trace)


def record_result(ledger: Path, identity: EffectIdentity, result: dict, *, trace=journal) -> None:
    "Écrit le résultat **après** l'effet ; c'est cette écriture qui clôt l'effet inconnu."

    _merge(ledger, identity.result, {"transport": identity.transport, "result": result}, trace=trace)


def stage(ledger: Path, result: str, *, trace=journal) -> Stage:
    "Ce qu'une reprise sait d'un effet : rien d'écrit, intention seule, ou résultat enregistré."

    entry = read_ledger(ledger, trace=trace).get(result)
    if entry is None:
        return Stage.unstarted

    return Stage.recorded if "result" in entry else Stage.unknown_effect


def resume(ledger: Path, identity: EffectIdentity, probe: Callable[[], dict | None], *, trace=journal):
    """Rend le résultat déjà acquis, ou `None` quand l'effet reste à exécuter.

    Un effet inconnu **interroge d'abord l'hôte** : `probe` rend ce qui existe chez lui, ou `None`.
    Un effet non commencé n'interroge rien — il n'y a rien à retrouver.
    """

    current = stage(ledger, identity.result, trace=trace)
    if current is Stage.recorded:
        return read_ledger(ledger, trace=trace)[identity.result]["result"]
    if current is Stage.unstarted:
        return None

    # effet inconnu : l'état distant fait foi avant tout rejeu
    found = probe()
    if found is not None:
        record_result(ledger, identity, found, trace=trace)

    return found
