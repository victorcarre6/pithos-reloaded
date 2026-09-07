"""Double en mémoire du journal : mêmes fonctions, aucune écriture sur disque.

Deux pannes se simulent en assignant un attribut du module, parce que tout le reste du projet en
dépend : `disk_full = True` fait rendre `False` à `emit`, et `torn = TornTail(...)` donne au
lecteur une queue déchirée à tolérer.
"""

from pathlib import Path
from typing import Any, Callable, Iterator

from journal.read import TornTail
from journal.redact import redact  # fonction pure : le double serait la même chose
from kernel.contracts import Event

events: list[Event] = []
live: list[str] = []
json_files: dict[Path, dict] = {}
disk_full = False
torn: TornTail | None = None


def reset() -> None:
    "Vide l'état accumulé et rétablit les deux pannes simulables à l'arrêt."

    global disk_full, torn

    events.clear()
    live.clear()
    json_files.clear()
    disk_full = False
    torn = None


def bind(events_path: Path, live_path: Path) -> None:
    "Accepte la liaison sans rien ouvrir ; le double n'a qu'une seule mission."


def emit(event: Event) -> bool:
    "Accumule l'événement et sa projection, ou rend `False` quand le disque est plein."

    if disk_full:
        return False

    events.append(event)
    live.append(f"#{len(events)} {event.type} (payload omitted: {len(event.payload)} keys)")

    return True


def update_json_locked(path: Path, fn: Callable[[dict], dict]) -> None:
    "Applique la mutation sur l'état courant du chemin, comme le ferait un verrou tenu."

    json_files[path] = fn(json_files.get(path, {}))


def read(path: Path) -> Iterator[Event]:
    "Itère les événements accumulés ; une queue déchirée n'est jamais rendue."

    return iter(list(events))


def tail(path: Path, n: int) -> tuple[list[Event], bool]:
    "Rend les `n` derniers événements et si un préfixe a été omis."

    kept = events[-n:] if n > 0 else []

    return list(kept), len(kept) < len(events)


def next_event_id(path: Path) -> int:
    "Reprend la numérotation là où le double s'est arrêté."

    return len(events) + 1


def torn_tail(path: Path) -> TornTail | None:
    "Rend la queue déchirée configurée par le test, sans jamais la réparer."

    return torn


def generation_signature(path: Path) -> dict:
    "Signature de génération dérivée du seul nombre d'événements accumulés."

    return {"first_line_sha256": "0" * 64, "size": len(events)}
