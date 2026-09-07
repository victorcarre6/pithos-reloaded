"""Le format des traces durables, dans les deux sens : un format, un parseur.

`observatory` lit par ce module plutôt que de reparser le JSONL de son côté.
"""

from pathlib import Path
from typing import Any, Callable, Iterator, Protocol, runtime_checkable

from kernel.contracts import Event

from .read import TornTail, generation_signature, next_event_id, read, tail, torn_tail
from .redact import redact
from .write import bind, emit, update_json_locked

__all__ = [
    "Journal", "TornTail", "bind", "emit", "generation_signature", "next_event_id",
    "read", "redact", "tail", "torn_tail", "update_json_locked",
]


@runtime_checkable
class Journal(Protocol):
    """Ce que tout module de niveau ≥ 2 attend du journal — implémentation comme double.

    Les membres sont statiques : le journal est un module, pas un objet à instancier.
    """

    @staticmethod
    def bind(events_path: Path, live_path: Path) -> None: ...

    @staticmethod
    def emit(event: Event) -> bool: ...

    @staticmethod
    def update_json_locked(path: Path, fn: Callable[[dict], dict]) -> None: ...

    @staticmethod
    def read(path: Path) -> Iterator[Event]: ...

    @staticmethod
    def tail(path: Path, n: int) -> tuple[list[Event], bool]: ...

    @staticmethod
    def next_event_id(path: Path) -> int: ...

    @staticmethod
    def torn_tail(path: Path) -> TornTail | None: ...

    @staticmethod
    def generation_signature(path: Path) -> dict: ...

    @staticmethod
    def redact(value: Any) -> tuple[Any, list[str]]: ...
