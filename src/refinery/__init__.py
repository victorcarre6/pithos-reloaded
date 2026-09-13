"""La politique d'auto-amélioration — **éteinte au socle**.

`enabled: false` est une décision, pas un défaut de configuration : les conditions d'allumage sont
écrites au § 8 du `MODULE.md`, et la première est que dix missions aient tourné et écrit leur baseline.
Ce module reste séparé pour que cette condition reste **relisible** ; une politique invisible dans
`campaign` s'allumerait un jour sans que personne ne relise sa condition.
"""

from typing import Protocol, runtime_checkable

from campaign.store import Store

from .gate import Baseline, Decision, Edit, Effect, Label, NodeEvidence, gate, refuse
from .propose import plan_refinement

ENABLED = False

__all__ = [
    "Baseline", "Decision", "ENABLED", "Edit", "Effect", "Label", "NodeEvidence", "Refinery",
    "gate", "plan_refinement", "refuse",
]


@runtime_checkable
class Refinery(Protocol):
    """Ce qu'appellerait un jour la fin de mission — implémentation comme double.

    Les membres sont statiques : la politique est un module, pas un objet à instancier.
    """

    @staticmethod
    def plan_refinement(state: Store, baseline: Baseline) -> list[Edit]: ...

    @staticmethod
    def gate(edit: Edit, before: Baseline, after: Baseline) -> Decision: ...
