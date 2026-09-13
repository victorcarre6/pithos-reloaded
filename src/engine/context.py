"""Inventaire sans résumé, issu de Villani context_governance.py:11-71,200-220,252-266.

Villani : projet personnel, copie libre accordée (resources/MANIFEST.md).
Les contenus et estimations viennent du harness ; aucune I/O ni génération ici.
"""

from enum import StrEnum
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import Field, StrictInt, model_validator

from kernel.contracts import Contract, Criterion, Name, Node
from kernel.errors import Cause, PithosError
from kernel.facts import Digest


class ContextInclusionReason(StrEnum):
    TASK_RELEVANCE = "task_relevance"
    PLAN_TARGET = "plan_target"
    MEMORY_SIGNAL = "memory_signal"
    VALIDATION_SIGNAL = "validation_signal"
    REPAIR_SIGNAL = "repair_signal"
    CHECKPOINT_HANDOFF = "checkpoint_handoff"


class ContextExclusionReason(StrEnum):
    IRRELEVANT = "irrelevant"
    BUDGET_PRESSURE = "budget_pressure"
    DUPLICATE = "duplicate"
    STALE = "stale"


class ContextPressureLevel(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    OVERFLOW_RISK = "overflow_risk"


class ContextItem(Contract):
    source_id: Name
    source_type: Literal["instruction", "criterion", "file", "memory", "handoff", "validation"]
    content: str
    estimated_units: StrictInt = Field(ge=0)
    retention: Literal["required", "optional"]
    included_reason: ContextInclusionReason | None
    excluded_reason: ContextExclusionReason | None
    fingerprints: dict[Path, Digest]

    @model_validator(mode="after")
    def explicit_reason_and_provenance(self):
        # une seule raison ; une passation sans empreinte ne peut jamais être admise
        if (self.included_reason is None) == (self.excluded_reason is None):
            raise ValueError("exactly one inclusion or exclusion reason required")
        if self.source_type == "handoff" and not self.fingerprints:
            raise ValueError("handoff requires fingerprints of described files")

        return self


class ContextBudgetEstimate(Contract):
    total_units: StrictInt = Field(ge=0)
    budget_limit: StrictInt = Field(gt=0)
    pressure: float = Field(ge=0)
    pressure_level: ContextPressureLevel


class ContextPacket(Contract):
    node_id: Name
    criterion: Criterion | None
    items: tuple[ContextItem, ...]
    budget: ContextBudgetEstimate
    initial_pressure: float = Field(ge=0)
    evictions: StrictInt = Field(ge=0)
    blocked_cause: Literal[Cause.context_overflow, Cause.unverifiable] | None

    def render(self) -> str:
        """Rend les seuls contenus admis, intacts ; un paquet bloqué n'est pas un prompt."""

        if self.blocked_cause is not None:
            raise PithosError(self.blocked_cause, "context admission refused", "context")
        contents = [item.content for item in self.items if item.included_reason is not None]
        notice, _ = _omission(self.items)
        if notice:
            contents.insert(0, notice)

        return "\n\n".join(contents)


def detect_stale_context(item: ContextItem, fingerprints: dict[Path, str]) -> bool:
    """Une empreinte modifiée ou absente périme l'élément qui décrivait ce fichier."""

    return any(fingerprints.get(path) != digest for path, digest in item.fingerprints.items())


def _exclude(item: ContextItem, reason: ContextExclusionReason) -> ContextItem:
    values = item.model_dump()
    values.update(included_reason=None, excluded_reason=reason)

    return ContextItem.model_validate(values)


def _omission(items) -> tuple[str, int]:
    "Annonce les exclusions ; le marqueur et son séparateur consomment des unités estimées."

    reasons = Counter(item.excluded_reason.value for item in items if item.excluded_reason is not None)
    if not reasons:
        return "", 0
    counts = ", ".join(f"{reason}={count}" for reason, count in sorted(reasons.items()))
    notice = f"[omitted: {counts}]"
    units = (len(notice) + 2) // 4 + 1  # même estimation caractères/4 que le préflight bridge

    return notice, units


def assemble(node: Node, budget: int, *, items: list[ContextItem],
             fingerprints: dict[Path, str]) -> ContextPacket:
    """Écarte le périmé et les doublons, puis évince les éléments optionnels en FIFO."""

    # inventaire neuf à chaque nœud, avec conservation des exclusions antérieures
    if type(budget) is not int or budget <= 0:
        raise ValueError("context budget must be a positive integer")
    inventory = []
    seen = {}
    missing_required = False
    for candidate in items:
        item = ContextItem.model_validate(candidate.model_dump())
        if item.included_reason is not None:
            if detect_stale_context(item, fingerprints):
                item = _exclude(item, ContextExclusionReason.STALE)
            elif item.source_id in seen:
                if item != seen[item.source_id]:
                    raise ValueError("conflicting duplicate context source")
                item = _exclude(item, ContextExclusionReason.DUPLICATE)
            else:
                seen[item.source_id] = item
        if item.retention == "required" and item.excluded_reason not in {None, ContextExclusionReason.DUPLICATE}:
            missing_required = True
        inventory.append(item)

    # éviction par ancienneté jusqu'au palier moderate, sans retirer l'irréductible
    active = [item for item in inventory if item.included_reason is not None]
    total = sum(item.estimated_units for item in active)
    _, omission_units = _omission(inventory)
    total += omission_units
    initial_pressure = total / budget
    evictions = 0
    for index, item in enumerate(inventory):
        if total / budget < 0.75:
            break
        if item.included_reason is None or item.retention == "required":
            continue
        inventory[index] = _exclude(item, ContextExclusionReason.BUDGET_PRESSURE)
        total -= item.estimated_units
        total -= omission_units
        _, omission_units = _omission(inventory)
        total += omission_units
        evictions += 1

    # pression finale et admission mécanique ; aucune synthèse de remplacement
    pressure = total / budget
    if pressure < 0.45:
        level = ContextPressureLevel.LOW
    elif pressure < 0.75:
        level = ContextPressureLevel.MODERATE
    elif pressure < 1.0:
        level = ContextPressureLevel.HIGH
    else:
        level = ContextPressureLevel.OVERFLOW_RISK
    cause = Cause.unverifiable if missing_required else None
    if total > budget:
        cause = Cause.context_overflow
    estimate = ContextBudgetEstimate(
        total_units=total,
        budget_limit=budget,
        pressure=pressure,
        pressure_level=level,
    )

    return ContextPacket(
        node_id=node.id,
        criterion=node.criterion,
        items=tuple(inventory),
        budget=estimate,
        initial_pressure=initial_pressure,
        evictions=evictions,
        blocked_cause=cause,
    )
