"""Erreurs à cause fermée, sans politique de retry ni I/O."""

from enum import StrEnum


class Cause(StrEnum):
    invalid_schema = "invalid_schema"
    invalid_symbol = "invalid_symbol"
    invalid_path = "invalid_path"
    timeout = "timeout"
    interrupted = "interrupted"
    invariant_failed = "invariant_failed"
    receipt_not_written = "receipt_not_written"
    unverifiable = "unverifiable"
    context_overflow = "context_overflow"


class PithosError(Exception):
    """Porte une cause mécanique et le chemin du champ fautif."""

    def __init__(self, cause: Cause, detail: str, field_path: str | None = None):
        # données mécaniques accessibles sans analyser le message
        self.cause = Cause(cause)
        self.field_path = field_path
        self.detail = detail
        self.violations: tuple[PithosError, ...] = ()
        super().__init__(detail)


class ErrorAccumulator:
    """Collecte toutes les violations avant de lever une seule erreur structurée."""

    def __init__(self):
        self.violations: list[PithosError] = []

    def add(self, field_path: str, cause: Cause, detail: str) -> None:
        self.violations.append(PithosError(cause, detail, field_path))

    def raise_if_any(self) -> None:
        # instantané des violations ; l'accumulateur reste disponible
        if self.violations:
            details = [f"{error.field_path}: {error.detail}" for error in self.violations]
            error = PithosError(Cause.invalid_schema, "; ".join(details))
            error.violations = tuple(self.violations)
            raise error
