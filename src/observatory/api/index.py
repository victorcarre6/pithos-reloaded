"""Index mémoire reconstruit depuis le disque au démarrage, suivi par `mtime`. Aucune écriture.

Le catalogue tient en mémoire ; les événements d'une mission se relisent à la demande.
"""

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from itertools import count
from pathlib import Path

import journal
from kernel.contracts import Contract, Event

MISSIONS_DIR = "missions"
EVENTS_NAME = "events.jsonl"


class MissionRow(Contract):
    """Ligne de catalogue : ce qu'une passe sur les segments produit sans retenir un événement."""

    mission_id: str
    n_events: int
    families: dict[str, int]
    first_ts: str | None
    last_ts: str | None
    segments: int
    anomalies: tuple[str, ...]


@dataclass
class Index:
    """Catalogue en mémoire et signatures de génération ; `watch_error` rend la fraîcheur visible."""

    logs_root: Path
    missions_root: Path
    built_at: str
    refreshed_at: str
    rows: dict[str, MissionRow] = field(default_factory=dict)
    signatures: dict[str, tuple] = field(default_factory=dict)
    watch_error: str | None = None


def parse_ts(value: str) -> datetime | None:
    "Instant ISO zoné d'un événement, ou None : un horodatage inutilisable est une anomalie."

    try:
        moment = datetime.fromisoformat(value)
    except ValueError:
        return None

    return moment if moment.tzinfo is not None else None


def segments(mission_dir: Path) -> list[Path]:
    "Segments d'un journal dans l'ordre d'écriture : `events.jsonl`, puis `events.<n>.jsonl`."

    base = mission_dir / EVENTS_NAME
    if not base.exists():
        return []

    paths = [base]
    for number in count(1):
        following = base.with_name(f"{base.stem}.{number}{base.suffix}")
        if not following.exists():
            break
        paths.append(following)

    return paths


def signature(paths: list[Path]) -> tuple[tuple[int, int], ...]:
    "Identité de génération suivie par `mtime` : taille et horodatage de chaque segment."

    stats = [path.stat() for path in paths]

    return tuple((entry.st_size, entry.st_mtime_ns) for entry in stats)


def read_events(paths: list[Path]) -> tuple[list[Event], list[str]]:
    """Lit les segments **par `journal`** et rend les événements avec les anomalies rencontrées.

    Une queue déchirée est déclarée, jamais réparée ; un segment illisible n'annule pas les autres.
    """

    events: list[Event] = []
    anomalies: list[str] = []
    for path in paths:
        try:
            for event in journal.read(path):
                events.append(event)
        except (OSError, ValueError) as failure:
            anomalies.append(f"unreadable:{path.name}:{type(failure).__name__}")
        torn = journal.torn_tail(path)
        if torn is not None:
            anomalies.append(f"torn_tail:{path.name}:{torn.offset}:{torn.n_bytes}")

    return events, anomalies


def families(events: list[Event]) -> dict[str, int]:
    "Comptage par famille d'événements, tel qu'il est servi au catalogue comme au détail."

    return dict(Counter(event.type.value for event in events))


def scan(mission_dir: Path) -> MissionRow:
    "Ligne de catalogue d'une mission : une passe sur ses segments, aucun événement retenu."

    paths = segments(mission_dir)
    events, anomalies = read_events(paths)

    # comptage par famille et bornes temporelles réellement lisibles
    moments = [parse_ts(event.ts) for event in events]
    stamps = sorted(moment for moment in moments if moment is not None)
    if len(stamps) < len(moments):
        anomalies.append(f"unusable_ts:{len(moments) - len(stamps)}")

    return MissionRow(
        mission_id=mission_dir.name,
        n_events=len(events),
        families=families(events),
        first_ts=stamps[0].isoformat() if stamps else None,
        last_ts=stamps[-1].isoformat() if stamps else None,
        segments=len(paths),
        anomalies=tuple(anomalies),
    )


def refresh(index: Index) -> None:
    """Relit les seules missions dont un segment a bougé ; l'index reste servi si le suivi échoue.

    L'échec est retenu dans `watch_error` : une panne de suivi ne fait pas tomber l'observation.
    """

    try:
        candidates = index.missions_root.iterdir()
        directories = [path for path in candidates if path.is_dir() and not path.is_symlink()]
        directories.sort()

        # une relecture par mission dont la taille ou l'horodatage d'un segment a bougé
        for mission_dir in directories:
            current = signature(segments(mission_dir))
            if index.signatures.get(mission_dir.name) == current:
                continue
            index.rows[mission_dir.name] = scan(mission_dir)
            index.signatures[mission_dir.name] = current
    except OSError as failure:
        index.watch_error = f"{type(failure).__name__}: {failure}"

        return

    index.watch_error = None
    index.refreshed_at = datetime.now(timezone.utc).isoformat()


def build_index(logs_root: Path) -> Index:
    "Index mémoire reconstruit depuis le disque au démarrage. Pas de collecteur permanent."

    return _build(logs_root, logs_root / MISSIONS_DIR)


def build_run_index(runs_root: Path) -> Index:
    "Indexe une collection explicite d'essais, sans supposer un sous-répertoire `missions`."

    return _build(runs_root, runs_root)


def _build(logs_root: Path, missions_root: Path) -> Index:
    "Construit le catalogue pour les deux dispositions publiées."

    now = datetime.now(timezone.utc).isoformat()
    index = Index(logs_root=logs_root, missions_root=missions_root, built_at=now, refreshed_at=now)
    refresh(index)

    return index


def mission_events(index: Index, mission_id: str) -> tuple[list[Event], tuple[str, ...]]:
    "Détail d'une mission, relu à la demande : le catalogue ne charge jamais les événements."

    if mission_id not in index.rows:
        return [], ()
    mission_dir = index.missions_root / mission_id
    if mission_dir.is_symlink():
        return [], ("unsafe_mission_path",)
    events, anomalies = read_events(segments(mission_dir))

    return events, tuple(anomalies)
