"""Lecture des traces durables : itération, lecture bornée, détection de queue déchirée."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from kernel.contracts import Event


@dataclass(frozen=True, slots=True)
class TornTail:
    "Fragment final non terminé par un LF : diagnostiqué, jamais réparé."

    offset: int
    n_bytes: int


def _lines(path: Path) -> list[bytes]:
    "Lignes complètes du fichier ; le framing est sur LF, et un fragment final est écarté."

    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return []

    return raw.split(b"\n")[:-1]


def _event(line: bytes) -> Event:
    "Reconstruit l'événement d'une ligne ; l'enveloppe d'identifiant appartient au journal."

    row = json.loads(line)
    row.pop("event_id", None)

    return Event.model_validate(row)


def read(path: Path) -> Iterator[Event]:
    """Itère les événements complets ; un fragment final déchiré n'est jamais rendu.

    Une ligne intérieure illisible lève : un journal corrompu ne se lit pas « comme vide ».
    """

    for line in _lines(path):
        yield _event(line)


def tail(path: Path, n: int) -> tuple[list[Event], bool]:
    "Rend les `n` derniers événements et si un préfixe a été omis."

    lines = _lines(path)
    kept = lines[-n:] if n > 0 else []
    events = [_event(line) for line in kept]

    return events, len(kept) < len(lines)


def next_event_id(path: Path) -> int:
    "Reprend la numérotation après redémarrage en relisant les identifiants déjà écrits."

    next_id = 1
    for line in _lines(path):
        written_id = json.loads(line).get("event_id")
        if isinstance(written_id, int) and written_id >= next_id:
            next_id = written_id + 1

    return next_id


def torn_tail(path: Path) -> TornTail | None:
    "Détecte un fragment final non terminé par un LF. Ne répare rien, jamais."

    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return None

    if not raw or raw.endswith(b"\n"):
        return None

    offset = raw.rfind(b"\n") + 1

    return TornTail(offset=offset, n_bytes=len(raw) - offset)


def generation_signature(path: Path) -> dict:
    "Identité d'une génération de fichier : hash de la première ligne et taille en octets."

    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            first = handle.readline().rstrip(b"\n")
    except OSError:
        return {}

    return {
        "first_line_sha256": hashlib.sha256(first).hexdigest(),
        "size": size,
    }
