"""Lecture seule, processus séparé : le harness n'apprend rien de ce module.

L'index se reconstruit depuis les JSONL au démarrage — il n'y a ni base, ni collecteur permanent.
"""

from pathlib import Path
from typing import Protocol, runtime_checkable

from kernel.contracts import Event, Node

from .api.index import Index, MissionRow, build_index, build_run_index, mission_events, refresh
from .api.render import TreeRow, flatten_tree, status_text, window

__all__ = [
    "Index", "MissionRow", "Observatory", "TreeRow", "build_index", "flatten_tree",
    "build_run_index", "mission_events", "refresh", "status_text", "window",
]


@runtime_checkable
class Observatory(Protocol):
    """Ce qu'un consommateur attend de l'observatoire — les routes n'en sont qu'un transport.

    Les membres sont statiques : l'observatoire est un module, pas un objet à instancier.
    """

    @staticmethod
    def build_index(logs_root: Path) -> Index: ...

    @staticmethod
    def build_run_index(runs_root: Path) -> Index: ...

    @staticmethod
    def refresh(index: Index) -> None: ...

    @staticmethod
    def mission_events(index: Index, mission_id: str) -> tuple[list[Event], tuple[str, ...]]: ...

    @staticmethod
    def flatten_tree(events: list[Event], *, snapshot: tuple[Node, ...] = ()) -> tuple[list[TreeRow], list[str]]: ...

    @staticmethod
    def status_text(row: MissionRow, rows: list[TreeRow]) -> str: ...
