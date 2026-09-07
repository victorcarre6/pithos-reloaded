"""Forme des faits et du reçu ; l'émission appartient exclusivement à verifier."""

from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, StrictInt, model_validator

from .contracts import Contract, Name, PositiveInt, Relation


Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class FileFact(Contract):
    path: Path
    sha_before: Digest
    sha_after: Digest
    spliced_range: tuple[PositiveInt, PositiveInt]
    n_replacements: StrictInt = Field(ge=0)

    @model_validator(mode="after")
    def ordered_range(self):
        if self.spliced_range[0] > self.spliced_range[1]:
            raise ValueError("spliced_range must be ordered and inclusive")

        return self


Fact = FileFact


class Receipt(Contract):
    node_id: Name
    attempt: PositiveInt
    returncode: StrictInt | None
    artifact_path: Path
    facts: list[Fact]


class RecordKey(Contract):
    """Identité d'une vérification : mission, nœud, tentative, relation (décisions 22/30)."""

    kind: Literal["verification"]
    value: tuple[Name, Name, PositiveInt, Relation]


def same_identity(left: RecordKey | None, right: RecordKey | None) -> bool:
    return isinstance(left, RecordKey) and isinstance(right, RecordKey) and left == right
