"""Vérification métamorphique de sources et de faits externes injectés."""

from .gates import check_sources, preflight, run
from .models import ExecutionResult, KillReport, Verdict
from .protocol import SourceVerifier, Verifier
from .receipt import emit_receipt
from .runner import CommandExecutor, execution_scope

__all__ = ["check_sources", "preflight", "run", "emit_receipt", "ExecutionResult", "KillReport", "SourceVerifier", "Verifier", "Verdict"]
__all__ += ["CommandExecutor", "execution_scope"]
