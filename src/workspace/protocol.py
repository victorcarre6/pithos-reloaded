"""Façade commune au filesystem réel et au double mémoire."""

from pathlib import Path
from typing import Protocol, runtime_checkable

from kernel.facts import FileFact

from .splice import SplicePlan


@runtime_checkable
class TransactionPort(Protocol):
    before: bytes | None
    last_plan: SplicePlan | None

    def __enter__(self) -> "TransactionPort": ...
    def __exit__(self, exc_type, exc, traceback): ...
    def splice(self, function_name: str, new_source: str) -> FileFact: ...
    def cas_write(self, content: bytes) -> None: ...
    def restore(self) -> None: ...


@runtime_checkable
class WorkspacePort(Protocol):
    def transaction(self, target: Path) -> TransactionPort: ...
    def splice(self, target: Path, function_name: str, new_source: str) -> FileFact: ...
    def project(self, target: Path, start: int, end: int) -> str: ...
