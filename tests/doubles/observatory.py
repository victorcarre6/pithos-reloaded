"""Double mémoire de l'observatoire : mêmes fonctions, aucun accès au disque.

Les missions sont scriptées en assignant `missions` ; `logs_root` n'est jamais lu, et une queue
déchirée se simule en assignant `anomalies` — c'est ce qu'un lecteur doit tolérer, pas réparer.

`flatten_tree` et `status_text` sont des projections pures : le double serait la même chose.
"""

from datetime import datetime, timezone
from pathlib import Path

from kernel.contracts import Event
from observatory.api.index import Index, MissionRow, families, parse_ts
from observatory.api.render import flatten_tree, status_text  # projections pures

missions: dict[str, list[Event]] = {}
anomalies: dict[str, tuple[str, ...]] = {}


def reset() -> None:
    "Vide les missions scriptées et les anomalies simulées."

    missions.clear()
    anomalies.clear()


def _row(mission_id: str) -> MissionRow:
    "Ligne de catalogue dérivée des seuls événements scriptés."

    events = missions[mission_id]
    moments = [parse_ts(event.ts) for event in events]
    stamps = sorted(moment for moment in moments if moment is not None)

    return MissionRow(
        mission_id=mission_id,
        n_events=len(events),
        families=families(events),
        first_ts=stamps[0].isoformat() if stamps else None,
        last_ts=stamps[-1].isoformat() if stamps else None,
        segments=1,
        anomalies=anomalies.get(mission_id, ()),
    )


def build_index(logs_root: Path) -> Index:
    "Index bâti depuis les missions scriptées ; le chemin est retenu, jamais parcouru."

    now = datetime.now(timezone.utc).isoformat()
    index = Index(logs_root=logs_root, missions_root=logs_root / "missions", built_at=now, refreshed_at=now)
    refresh(index)

    return index


def build_run_index(runs_root: Path) -> Index:
    "Double d'une collection d'essais ; aucun disque consulté."

    index = build_index(runs_root)
    index.missions_root = runs_root

    return index


def refresh(index: Index) -> None:
    "Redérive le catalogue depuis les missions scriptées, sans jamais consulter un `mtime`."

    for mission_id in missions:
        index.rows[mission_id] = _row(mission_id)
        index.signatures[mission_id] = (len(missions[mission_id]),)
    index.watch_error = None
    index.refreshed_at = datetime.now(timezone.utc).isoformat()


def mission_events(index: Index, mission_id: str) -> tuple[list[Event], tuple[str, ...]]:
    "Détail d'une mission scriptée ; une mission inconnue est vide, jamais une erreur."

    return list(missions.get(mission_id, [])), anomalies.get(mission_id, ())
