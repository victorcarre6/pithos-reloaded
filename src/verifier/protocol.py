"""Frontière exécutable de la tranche sur sources en mémoire, avant raccordement des faits."""

from pathlib import Path
from typing import Protocol, runtime_checkable

from kernel.contracts import Criterion
from kernel.facts import Fact, Receipt, RecordKey
from journal import Journal

from .models import Verdict


@runtime_checkable
class SourceVerifier(Protocol):
    def check_sources(
        self, criterion: Criterion, before: str, after: str, *, artifact_root: Path, timeout: float,
    ) -> Verdict: ...

    def emit_receipt(
        self, node_id: str, attempt: int, facts: list[Fact], artifact: Path, *,
        key: RecordKey, verdict: Verdict, journal: Journal,
    ) -> Receipt | None: ...
