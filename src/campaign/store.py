"""Le magasin : deux familles vivantes, une relecture qui ne lève jamais.

La famille `skill` *est* le registre d'outils — il n'y a pas deux objets. Un magasin écrit par un
modèle doit se relire sans jamais lever : une entrée mal formée est ignorée avec sa raison
journalisée, jamais propagée en exception.

PORTED_FROM: prime-agent-main/prime-agent-runtime/src/rlm/harness.py:94-275,722-769 (MIT)
"""

import json
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path

from pydantic import Field, JsonValue, model_validator

import journal
from kernel.contracts import Contract, Event, Name, PositiveInt
from kernel.errors import Cause, PithosError


SCHEMA = 1
CLIP = 120


class Family(StrEnum):
    skill = "skill"        # LE registre d'outils
    memory = "memory"      # alimentée dès le socle (décision 31)
    prompt = "prompt"      # consommée par refinery seul — enabled: false
    subagent = "subagent"  # vide tant que le mode agentic est différé


class Source(StrEnum):
    model = "model"
    derived = "derived"


ALIVE = (Family.skill, Family.memory)
_FAMILY_VALUES = frozenset(member.value for member in Family)
_SOURCE_VALUES = frozenset(member.value for member in Source)


class Entry(Contract):
    """Une entrée du magasin : ce qu'elle est, d'où elle vient, et depuis quand."""

    key: Name
    family: Family
    title: Name
    content: str
    source: Source
    version: PositiveInt
    created_at: Name
    updated_at: Name
    reference: dict[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def callable_skill(self):
        # une capacité non appelable n'entre pas au registre
        if self.family is not Family.skill:
            return self

        for field_name in ("import", "callable"):
            value = self.reference.get(field_name)
            if not isinstance(value, str) or not value:
                raise ValueError("a skill entry requires an import and a callable")

        return self


class Store(Contract):
    """Instantané en lecture du magasin ; toute écriture repasse par `put`."""

    entries: dict[Family, dict[str, Entry]]


_path: Path | None = None
_trace = journal


def bind(path: Path | None, *, trace=journal) -> None:
    "Désigne le fichier du magasin et le journal qui le rend durable."

    global _path, _trace

    _path = path
    _trace = trace


def normalize(key: str) -> str:
    "Accepte verbatim un identifiant affiché `famille:clé` — le modèle recopie ce qu'il a lu."

    prefix, separator, rest = key.partition(":")
    if separator and rest and prefix in _FAMILY_VALUES:
        return rest

    return key


def _record(operation: str, reason: str, **payload) -> None:
    "Journalise ce que la relecture a écarté ; la relecture continue sans lever."

    event = Event(
        ts=datetime.now(timezone.utc).isoformat(),
        v=1,
        type="status",
        durable=True,
        payload={"scope": "campaign", "operation": operation, "reason": reason, **payload},
    )
    _trace.emit(event)


def _as_dict(value) -> dict:
    return value if isinstance(value, dict) else {}


def _empty() -> Store:
    return Store(entries={family: {} for family in ALIVE})


def _coerce(family: Family, key: str, raw: dict) -> tuple[Entry | None, str]:
    """Ramène une entrée brute à un `Entry`, ou rend la raison de son rejet.

    Un champ de type faux prend son défaut tant que l'entrée garde un sens ; `title` et `content`
    non textuels la disqualifient, parce qu'il ne reste alors rien à enregistrer.
    """

    # les deux champs sans défaut possible
    title = raw.get("title")
    content = raw.get("content")
    if not isinstance(title, str) or not isinstance(content, str):
        return None, "title and content must both be strings"

    # champs à défaut : un type faux dégrade, il ne disqualifie pas
    version = raw.get("version")
    if isinstance(version, str) and version.isdigit():
        version = int(version)
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        version = 1
    source = raw.get("source")
    if not isinstance(source, str) or source not in _SOURCE_VALUES:
        source = Source.model
    now = datetime.now(timezone.utc).isoformat()
    stamps = {}
    for name in ("created_at", "updated_at"):
        stamp = raw.get(name)
        stamps[name] = stamp if isinstance(stamp, str) and stamp else now

    # dernier filet : un contrat refusé est une entrée ignorée, jamais une exception
    try:
        entry = Entry(
            key=key,
            family=family,
            title=title,
            content=content,
            source=source,
            version=version,
            reference=_as_dict(raw.get("reference")),
            **stamps,
        )
    except ValueError as error:
        return None, str(error).replace("\n", " ")

    return entry, ""


def _parse(data) -> Store:
    "Reconstruit le magasin depuis un état brut relu, en ignorant tout ce qui ne se relit pas."

    # un état dont la forme ou la version est inconnue est un magasin vide, jamais une exception
    schema = _as_dict(data).get("schema")
    if schema != SCHEMA:
        log_content = f"unknown schema {schema!r}"
        _record("store_read_failed", log_content)

        return _empty()

    state = _empty()
    families = _as_dict(data.get("entries"))
    for family in ALIVE:
        records = _as_dict(families.get(family.value))
        for key, raw in records.items():
            if not isinstance(raw, dict):
                _record("store_entry_ignored", "entry is not a JSON object", family=family, key=str(key))
                continue
            entry, reason = _coerce(family, str(key), raw)
            if entry is None:
                _record("store_entry_ignored", reason, family=family, key=str(key))
                continue
            state.entries[family][entry.key] = entry

    return state


def load() -> Store:
    "Relit le magasin champ par champ. NE LÈVE JAMAIS : ce qui ne se relit pas est journalisé."

    if _path is None:
        return _empty()

    try:
        content = _path.read_text(encoding="utf-8")
        data = json.loads(content)
    except FileNotFoundError:
        return _empty()
    except (OSError, ValueError) as error:
        log_content = f"unreadable state file: {error}"
        _record("store_read_failed", log_content)

        return _empty()

    return _parse(data)


def _with_entry(data: dict, entry: Entry) -> dict:
    """Insère l'entrée dans l'état brut relu sous le verrou, sans journaliser.

    Une clé déjà présente garde sa date de création et voit sa version incrémentée : le fichier
    fait autorité sur les deux, jamais l'appelant.
    """

    families = _as_dict(data.get("entries"))
    records = _as_dict(families.get(entry.family.value))
    previous = _as_dict(records.get(entry.key))

    # héritage défensif : ce que la précédente porte de lisible est repris, le reste repart à neuf
    version = previous.get("version")
    created_at = previous.get("created_at")
    written = entry.model_dump(mode="json")
    written["version"] = version + 1 if isinstance(version, int) and not isinstance(version, bool) else 1
    written["created_at"] = created_at if isinstance(created_at, str) and created_at else entry.created_at

    merged = {**families, entry.family.value: {**records, entry.key: written}}

    return {**_as_dict(data), "schema": SCHEMA, "entries": merged}


def put(family: Family, key: str, entry: Entry) -> None:
    "Écrit l'entrée sous le verrou du journal, la clé et la famille de l'appelant faisant autorité."

    if family not in ALIVE:
        raise PithosError(Cause.invalid_schema, "prompt and subagent have no consumer at the socle", "family")

    written = Entry.model_validate({
        **entry.model_dump(),
        "key": normalize(key),
        "family": family,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })
    _trace.update_json_locked(_path, lambda data: _with_entry(data, written))


def _clip(text: str, limit: int) -> str:
    "Borne un texte en laissant le marqueur de troncature visible."

    if len(text) <= limit:
        return text

    return text[:limit - 1] + "…"


def _entry_line(entry: Entry) -> str:
    "Une ligne par entrée : identifiant recopiable, provenance, version, résumé borné."

    summary = _clip(" ".join(entry.content.split()), CLIP)
    reference = ""
    if entry.family is Family.skill:
        reference = " ref=" + _clip(json.dumps(entry.reference, ensure_ascii=False, sort_keys=True), CLIP)

    return f"  - [{entry.family}:{entry.key}] {entry.title} (v{entry.version}, {entry.source}){reference}: {summary}"


def render_compact(family: Family, budget: int) -> str:
    """Rend une famille en au plus `budget` caractères, le bornage toujours déclaré.

    C'est ce qui entre dans le prompt : ce qui est tronqué le montre, ce qui est omis se compte.
    """

    records = load().entries.get(family, {})
    header = f"{family}: {len(records)}"

    # place réservée d'avance au marqueur d'omission, pour que la borne tienne strictement
    marker = f"  - +{len(records)} more"
    available = budget - len(marker) - 1

    lines = [header]
    used = len(header)
    for entry in records.values():
        line = _entry_line(entry)
        if used + len(line) + 1 > available:
            break
        lines.append(line)
        used += len(line) + 1

    # une surface tronquée déclare ce qu'elle omet (décision 29)
    omitted = len(records) - len(lines) + 1
    if omitted:
        lines.append(f"  - +{omitted} more")

    return "\n".join(lines)
