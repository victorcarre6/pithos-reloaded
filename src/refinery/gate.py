"""La gate d'effet : un edit reste en `shadow` tant qu'il n'a pas démontré un effet mesurable.

C'est le mutation-check transposé du code vers le contexte. Prime Agent est le seul des neuf dépôts à
implémenter l'auto-amélioration de bout en bout, et il le fait **en boucle ouverte** : son
`expectedOutcome` n'est jamais évalué. L'autorité de validation manque exactement là.

⚠️ **Une entrée de magasin atteint le *prompt*, jamais l'*exécution*** !
→ C'est ce qui rend ce module compatible avec la contrainte dure n°1 : elle porte sur les littéraux
exécutés, pas sur ce que le modèle lit.

PORTED_FROM: prime-agent-main/packages/coding-agent/src/core/refinement/refinement.ts:673-682,716-750 (MIT)
"""

import math
from enum import StrEnum
from typing import Literal

from pydantic import Field

from campaign.stop import StopCause
from campaign.store import Family, normalize
from kernel.contracts import Contract, Name, PositiveInt, Relation


BASE_KEY = "base_system_prompt"
EDITABLE = (Family.prompt, Family.memory)
Z_PROMOTE = 1.96  # ~95 % : en deçà, l'écart des taux de verts est du bruit d'échantillonnage


class Label(StrEnum):
    shadow = "shadow"
    active = "active"


class Effect(StrEnum):
    promoted = "promoted"  # effet mesurable positif : le label `active` se déplace
    held = "held"          # l'effet est dans le bruit : rien ne bouge
    reverted = "reverted"  # effet mesurable négatif : le label reste où il était
    refused = "refused"    # edit invalide : enregistré, jamais fatal


class NodeEvidence(Contract):
    """La preuve d'un raffinement : un nœud, sa relation, son verdict — jamais une rationale."""

    node_id: Name
    relation: Relation
    verification: Literal["accepted", "rejected", "blocked"]


class Baseline(Contract):
    """Ce que `engine` écrit en fin de mission ; le taux de verts s'en dérive, il ne s'y répète pas."""

    mission_id: Name
    wall_seconds: float = Field(ge=0)
    exit_cause: StopCause
    nodes: list[NodeEvidence]

    @property
    def attempted(self) -> int:
        return len(self.nodes)

    @property
    def green(self) -> int:
        return sum(1 for node in self.nodes if node.verification == "accepted")


class Edit(Contract):
    """Une modification du harness lui-même : une version nouvelle, jamais un contenu réécrit."""

    family: Family
    key: Name
    version: PositiveInt
    content: str
    evidence: list[NodeEvidence] = Field(min_length=1)


class Decision(Contract):
    """Le verdict de la gate : où va le label, sur quelle version, et sur quelle preuve."""

    effect: Effect
    label: Label
    version: PositiveInt
    evidence: list[NodeEvidence]
    detail: str


def refuse(edit: Edit) -> str:
    "Rend la raison de refus d'un edit, ou la chaîne vide — trois lignes qui séparent deux destins."

    if edit.family not in EDITABLE:
        return f"{edit.family} is not a family refinery edits"
    if edit.family is Family.prompt and normalize(edit.key) == BASE_KEY:
        return "the base system prompt is immutable"

    return ""


def z_score(before: Baseline, after: Baseline) -> float:
    "Écart des deux taux de verts, exprimé en unités de son propre bruit d'échantillonnage."

    if not before.attempted or not after.attempted:
        return 0.0

    pooled = (before.green + after.green) / (before.attempted + after.attempted)
    spread = pooled * (1 - pooled) * (1 / before.attempted + 1 / after.attempted)
    if spread <= 0:
        return 0.0

    gap = after.green / after.attempted - before.green / before.attempted

    return gap / math.sqrt(spread)


def gate(edit: Edit, before: Baseline, after: Baseline) -> Decision:
    """Promeut un edit sur un effet mesurable seulement, jamais sur une variation dans le bruit.

    La promotion **déplace le label `active`** vers la version que l'edit a créée. Le contenu versionné
    n'est jamais modifié : le déplacement du label est le seul acte que cette gate contrôle.
    """

    reason = refuse(edit)
    if reason:
        return Decision(effect=Effect.refused, label=Label.shadow, version=edit.version,
                        evidence=edit.evidence, detail=reason)

    score = z_score(before, after)
    effect = Effect.held
    if score >= Z_PROMOTE:
        effect = Effect.promoted
    elif score <= -Z_PROMOTE:
        effect = Effect.reverted

    log_content = (
        f"z={score:.2f} threshold={Z_PROMOTE} "
        f"before={before.green}/{before.attempted} after={after.green}/{after.attempted} "
        f"exit={after.exit_cause.value} wall={after.wall_seconds:.0f}s"
    )
    label = Label.active if effect is Effect.promoted else Label.shadow

    return Decision(effect=effect, label=label, version=edit.version,
                    evidence=edit.evidence, detail=log_content)
