"""Tranche verifier sur sources en mémoire ; l'acceptation des faits externes reste à raccorder."""

from .gates import check_sources
from .models import ExecutionResult, KillReport, Verdict
from .protocol import SourceVerifier
from .receipt import emit_receipt

__all__ = ["check_sources", "emit_receipt", "ExecutionResult", "KillReport", "SourceVerifier", "Verdict"]
