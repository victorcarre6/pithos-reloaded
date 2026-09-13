"""Frontières de la double gate et de la vérification des faits injectés."""

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


@runtime_checkable
class Verifier(SourceVerifier, Protocol):
    def preflight(self, criterion: Criterion, source: str) -> None: ...

    def run(
        self, criterion: Criterion, facts: list[Fact], *, artifact_root: Path, timeout: float,
    ) -> Verdict: ...
