"""La politique : le magasin, le registre, l'admission, la redondance et l'arrêt.

La famille `skill` du magasin *est* le registre d'outils. Il n'y a pas deux objets.
"""

from pathlib import Path
from typing import Protocol, runtime_checkable

from .admit import Err, Ok, Proposal, Violation, admit
from .mcpconfig import managed_layer, write_managed
from .propose import Redundancy, Signal, Stage, counters, dedup, derive, rank, remember
from .registry import Omission, Projection, TaskLifecycle, ToolEntry, is_satisfied, project
from .stop import StopCause, StopProposal, should_stop
from .store import Entry, Family, Source, Store, bind, load, put, render_compact

__all__ = [
    "Campaign", "Entry", "Err", "Family", "Ok", "Omission", "Projection", "Proposal", "Redundancy",
    "Signal", "Source", "Stage", "StopCause", "StopProposal", "Store", "TaskLifecycle", "ToolEntry",
    "Violation", "admit", "bind", "counters", "dedup", "derive", "is_satisfied", "load",
    "managed_layer", "project", "put", "rank", "remember", "render_compact", "should_stop",
    "write_managed",
]


@runtime_checkable
class Campaign(Protocol):
    """Ce que `refinery` attend de la politique — implémentation comme double.

    Les membres sont statiques : la politique est un module, pas un objet à instancier.
    """

    @staticmethod
    def bind(path: Path | None) -> None: ...

    @staticmethod
    def load() -> Store: ...

    @staticmethod
    def put(family: Family, key: str, entry: Entry) -> None: ...

    @staticmethod
    def render_compact(family: Family, budget: int) -> str: ...

    @staticmethod
    def admit(proposal: dict) -> Ok[Proposal] | Err[list[Violation]]: ...

    @staticmethod
    def dedup(proposal: Proposal, state: Store) -> Redundancy | None: ...

    @staticmethod
    def rank(proposals: list[Proposal]) -> list[Proposal]: ...

    @staticmethod
    def derive(signals: list[Signal], rejections: int) -> list[Proposal]: ...

    @staticmethod
    def should_stop(state: Store) -> StopProposal | None: ...
