"""Vérification métamorphique de sources et de faits externes injectés."""

from .gates import check_sources, preflight, run
from .models import ExecutionResult, KillReport, Verdict
from .protocol import SourceVerifier, Verifier
from .receipt import emit_receipt

__all__ = ["check_sources", "preflight", "run", "emit_receipt", "ExecutionResult", "KillReport", "SourceVerifier", "Verifier", "Verdict"]
