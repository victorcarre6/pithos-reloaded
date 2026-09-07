"""Vocabulaire du socle ; aucune présence de symbole ni preuve n'est attestée ici."""

from enum import StrEnum
from keyword import iskeyword
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, JsonValue, StrictBool, StrictInt, TypeAdapter
from pydantic import field_validator, model_validator

from .errors import Cause


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, frozen=True)


Name = Annotated[str, Field(min_length=1)]
PositiveInt = Annotated[StrictInt, Field(ge=1)]
BlockedCause = Cause
FINITE_JSON = TypeAdapter(dict[str, JsonValue], config=ConfigDict(allow_inf_nan=False))


class NodeStatus(StrEnum):
    pending = "pending"
    running = "running"
    passed = "passed"
    failed = "failed"
    blocked = "blocked"
    retryable = "retryable"
    exhausted = "exhausted"
    budget_limited = "budget_limited"


class Relation(StrEnum):
    round_trip = "round_trip"
    idempotent = "idempotent"
    commutes_with = "commutes_with"
    preserves = "preserves"
    invariant_under = "invariant_under"
    monotone = "monotone"
    total = "total"
    raises_on = "raises_on"
    schema_conform = "schema_conform"


class Domain(StrEnum):
    small_ints = "small_ints"
    floats_finite = "floats_finite"
    text_unicode = "text_unicode"
    json_values = "json_values"
    paths = "paths"


class Criterion(Contract):
    relation: Relation
    symbols: list[Name] = Field(strict=True, min_length=1, max_length=2)
    domain: Domain

    @field_validator("symbols")
    @classmethod
    def symbol_names(cls, names):
        # grammaire de nom ; présence vérifiée séparément depuis l'ast
        for name in names:
            if not name.isidentifier() or iskeyword(name):
                raise ValueError("a symbol must be a Python identifier")

        return names

    @model_validator(mode="after")
    def symbol_count(self):
        # cardinalité fermée de chaque relation du catalogue
        unary = {Relation.idempotent, Relation.monotone, Relation.total, Relation.schema_conform}
        expected = 1 if self.relation in unary else 2
        if len(self.symbols) != expected:
            raise ValueError("symbol count does not match the relation")

        return self


class Node(Contract):
    id: Name
    parent_id: Name | None
    depth: StrictInt = Field(ge=0, le=3)
    target: Path
    criterion: Criterion | None
    status: NodeStatus
    blocked_cause: BlockedCause | None

    @model_validator(mode="after")
    def consistent_state(self):
        # parenté locale ; l'arbre vérifie existence et unicité
        if self.parent_id == self.id or (self.parent_id is None) != (self.depth == 0):
            raise ValueError("parent and depth are inconsistent")

        # un état exécuté exige un critère ; un blocage exige sa cause
        if self.status in {NodeStatus.running, NodeStatus.passed} and self.criterion is None:
            raise ValueError("running or passed nodes require a criterion")
        if (self.status == NodeStatus.blocked) != (self.blocked_cause is not None):
            raise ValueError("blocked status requires a cause, exclusively")

        return self


class EventType(StrEnum):
    status = "status"
    validation = "validation"
    tool_activity = "tool_activity"


class Event(Contract):
    ts: Name
    v: StrictInt = Field(ge=1, le=1)
    type: EventType
    durable: StrictBool
    payload: dict[str, JsonValue]

    @field_validator("payload", mode="before")
    @classmethod
    def finite_payload(cls, value):
        return FINITE_JSON.validate_python(value)  # même validation pour entrée Python et JSON
