"""La condition d'arrêt : une taxonomie fermée, et une raison qui énumère ce qui a été examiné.

PORTED_FROM: villani-code-main/villani_code/autonomous_stop.py:7-12,35-47 (MIT)
"""

from enum import StrEnum

from pydantic import StrictInt

from kernel.contracts import Contract, Name

from .store import ALIVE, Family, Store


RECURRENCE_STOP = 3


class StopCause(StrEnum):
    """Les cinq façons dont une campagne se termine ; `campaign` n'en propose que les deux premières."""

    no_proposal = "no_proposal"              # rien n'a été construit, et tout se répète
    all_redundant = "all_redundant"          # plus aucune proposition non redondante
    planner_churn = "planner_churn"          # boucle de planification sans activité modèle
    stagnation = "stagnation"                # des tours passent sans qu'un vert avance
    budget_exhausted = "budget_exhausted"    # le temps mural dur est atteint


class StopProposal(Contract):
    """Ce que la campagne propose d'arrêter, et sur quelle couverture elle le propose."""

    cause: StopCause
    examined: dict[Family, StrictInt]
    recurring: list[Name]
    detail: str


def should_stop(state: Store) -> StopProposal | None:
    """Propose l'arrêt quand la récurrence a tout envahi, jamais sur un magasin qui apprend encore.

    La récurrence est comptée dans la version de l'entrée `memory` : un doublon vu `RECURRENCE_STOP`
    fois remonte ici, avec tout ce qui a été examiné pour l'affirmer.
    """

    examined = {family: len(state.entries[family]) for family in ALIVE}
    seen = state.entries[Family.memory].values()
    repeated = [entry for entry in seen if entry.version >= RECURRENCE_STOP]
    if not repeated:
        return None

    # du plus vu au moins vu, la clé départageant les ex æquo pour rester déterministe
    ordered = sorted(repeated, key=lambda entry: (-entry.version, entry.key))
    recurring = [entry.key for entry in ordered]

    coverage = ", ".join(f"{family.value}={count}" for family, count in examined.items())
    repeats = ", ".join(f"{entry.key} seen {entry.version} times" for entry in ordered)
    log_content = f"examined: {coverage}; recurring: {repeats}"
    cause = StopCause.all_redundant if examined[Family.skill] else StopCause.no_proposal

    return StopProposal(cause=cause, examined=examined, recurring=recurring, detail=log_content)
