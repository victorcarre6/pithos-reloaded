"""Passation déterministe du harness ; archive complète et contexte réinjectable distincts."""

from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Protocol, runtime_checkable

from pydantic import Field, model_validator

from kernel.contracts import Contract, NodeStatus
from kernel.errors import Cause, PithosError
from kernel.facts import Digest, RecordKey
from verifier.models import Verdict

from .context import ContextItem, ContextPacket


MARKER = "\n```pithos-context-v1\n"


class Handoff(Contract):
    key: RecordKey
    packet: ContextPacket
    status: NodeStatus
    verdict: Verdict | None
    fingerprints: dict[Path, Digest] = Field(min_length=1)

    @model_validator(mode="after")
    def consistent_identity(self):
        criterion = self.packet.criterion
        if self.key.value[1] != self.packet.node_id or criterion is None or self.key.value[3] != criterion.relation:
            raise ValueError("handoff identity differs from the admitted context")
        if self.verdict is not None and self.verdict.criterion != criterion:
            raise ValueError("handoff verdict differs from the admitted criterion")

        return self


@runtime_checkable
class ContextArchive(Protocol):
    def dump(self, section: Handoff, *, path: Path) -> None: ...
    def read(self, mission_id: str, *, path: Path) -> list[ContextItem]: ...


def handoff_text(section: Handoff) -> str:
    """Décrit la session observée sans réinjecter ses anciennes sources ou instructions."""

    values = section.model_dump(mode="json", exclude={"packet", "verdict"})
    values["criterion"] = section.packet.criterion.model_dump(mode="json")
    values["budget"] = section.packet.budget.model_dump(mode="json")
    values["evictions"] = section.packet.evictions
    values["inventory"] = [entry.model_dump(mode="json", exclude={"content", "fingerprints"}) for entry in section.packet.items]
    values["verification"] = None if section.verdict is None else section.verdict.model_dump(
        mode="json", include={"verification", "effect", "reason", "source_hashes"},
    )

    return json.dumps(values, ensure_ascii=False, indent=2)


def render(section: Handoff) -> str:
    """Rend une section Markdown dont le JSON complet reste relisible sans analyser la prose."""

    section = Handoff.model_validate_json(section.model_dump_json())
    timestamp = datetime.now(timezone.utc).isoformat()
    summary = handoff_text(section)
    raw = section.model_dump_json()

    return f"\n## Session — {timestamp}\n\n```json\n{summary}\n```\n{MARKER}{raw}\n```\n"


def dump(section: Handoff, *, path: Path) -> None:
    """Ajoute une section sous le verrou de mission détenu par l'appelant, puis fsync."""

    content = render(section).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def parse(text: str, mission_id: str) -> list[ContextItem]:
    """Revalide les sections complètes ; une archive inconnue ou déchirée est refusée."""

    if not text:
        return []
    sections = text.split(MARKER)
    if len(sections) == 1:
        raise PithosError(Cause.unverifiable, "unrecognized context archive")
    items = []
    for index, part in enumerate(sections[1:], start=1):
        raw, end, tail = part.partition("\n```\n")
        try:
            if not end:
                raise ValueError("incomplete context section")
            if index == len(sections) - 1 and tail.strip():
                raise ValueError("incomplete context archive tail")
            section = Handoff.model_validate_json(raw)
        except ValueError as error:
            raise PithosError(Cause.unverifiable, str(error), "CONTEXT.md") from error
        if section.key.value[0] != mission_id:
            continue
        content = handoff_text(section)
        items.append(ContextItem(
            source_id=sha256(raw.encode("utf-8")).hexdigest(),
            source_type="handoff",
            content=content,
            estimated_units=len(content) // 4 + 1,
            retention="optional",
            included_reason="checkpoint_handoff",
            excluded_reason=None,
            fingerprints=section.fingerprints,
        ))

    return items


def read(mission_id: str, *, path: Path) -> list[ContextItem]:
    """Relit l'archive de mission ; absence permise, illisibilité explicite."""

    # ponytail: lecture de la mission entière ; indexer via journal si le volume mesuré l'exige
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    except UnicodeError as error:
        raise PithosError(Cause.unverifiable, "invalid context archive encoding", "CONTEXT.md") from error

    return parse(text, mission_id)
