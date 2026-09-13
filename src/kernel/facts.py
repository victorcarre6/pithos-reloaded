"""Forme des faits et du reçu ; l'émission appartient exclusivement à verifier."""

from pathlib import Path
from typing import Annotated, Literal

from pydantic import ConfigDict, Field, StrictBool, StrictInt, StrictStr, model_validator

from .codeview import MAX_SOURCE_BYTES
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


class SourceFact(Contract):
    """Octets complets capturés par workspace ; leur accord avec FileFact appartient à verifier."""

    model_config = ConfigDict(ser_json_bytes="hex", val_json_bytes="hex")

    path: Path
    before: bytes = Field(strict=True, max_length=MAX_SOURCE_BYTES)
    after: bytes = Field(strict=True, max_length=MAX_SOURCE_BYTES)


class RepoChange(Contract):
    """Entrée porcelain relative au dépôt, avec origine obligatoire pour un rename ou une copie."""

    status: StrictStr = Field(pattern=r"^[ MADRCUT?!]{2}$")
    path: Path
    origin: Path | None

    @model_validator(mode="after")
    def scoped_change(self):
        # une entrée réelle, avec les deux côtés d'un déplacement
        renamed = bool(set(self.status) & {"R", "C"})
        if self.status == "  " or renamed != (self.origin is not None):
            raise ValueError("status and origin are inconsistent")
        for path in (self.path, self.origin):
            if path is not None and (path.is_absolute() or ".." in path.parts or not path.parts):
                raise ValueError("repository changes require nonempty relative paths")

        return self


class RepoFact(Contract):
    """Observation broker du dépôt ; une collecte incomplète ne devient jamais complète par défaut."""

    repo: Path
    head: StrictStr
    changes: list[RepoChange]
    diff: StrictStr
    complete: StrictBool = False


Fact = FileFact | SourceFact | RepoFact


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
