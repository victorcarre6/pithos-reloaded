"""Résultat d'exécution distinct d'une attestation de changement et d'un reçu durable."""

from pathlib import Path
from typing import Literal

from pydantic import Field, StrictInt, model_validator
from kernel.contracts import Contract, Criterion


class ExecutionResult(Contract):
    execution: Literal["completed", "invalid", "tool_error", "timed_out"]
    check: Literal["passed", "failed", "not_run"]
    returncode: StrictInt | None
    artifact_path: Path | None
    diagnostic: str = Field(max_length=1800)
    counterexample: str = Field(default="", max_length=1800)
    duration: float = Field(ge=0)
    seed: StrictInt = 0
    stdout_bytes: StrictInt = Field(default=0, ge=0)
    stderr_bytes: StrictInt = Field(default=0, ge=0)

    @model_validator(mode="after")
    def consistent_execution(self):
        # aucun succès sans code de retour connu et artefact identifié
        if self.execution == "completed":
            expected = {"passed": 0, "failed": 20}
            if self.check not in expected or self.returncode != expected[self.check] or self.artifact_path is None:
                raise ValueError("completed checks require a matching code and artifact")
        elif self.check != "not_run":
            raise ValueError("an incomplete execution proves no invariant")

        return self


class MutationAttempt(Contract):
    operator: str
    result: ExecutionResult


class KillReport(Contract):
    status: Literal["killed", "survived", "blocked"]
    reason: Literal[
        "killed", "survived", "no_mutants", "baseline_not_green",
        "execution_failure", "budget_exhausted", "mutant_limit",
    ]
    baseline: ExecutionResult
    attempts: tuple[MutationAttempt, ...]

    @model_validator(mode="after")
    def evidence_matches_status(self):
        # le rapport ne peut renommer une panne ou une survie en kill
        if (self.status in {"killed", "survived"} or self.reason in {"killed", "survived"}) and self.status != self.reason:
            raise ValueError("mutation reason must match the observed status")
        if self.status != "blocked" and self.baseline.check != "passed":
            raise ValueError("mutation evidence requires a passing baseline")
        if self.status == "killed" and not any(attempt.result.check == "failed" for attempt in self.attempts):
            raise ValueError("a kill requires a failing invariant")
        if self.status == "survived":
            if not self.attempts or any(attempt.result.check != "passed" for attempt in self.attempts):
                raise ValueError("survival requires successful mutant executions")

        return self


class Verdict(Contract):
    """Verdict de la double gate uniquement ; n'atteste ni l'effet externe ni sa durabilité."""

    criterion: Criterion
    verification: Literal["passed", "rejected", "blocked"]
    reason: Literal[
        "verified", "unchanged_source", "before_green", "before_unverifiable",
        "after_red", "tautology", "mutation_unavailable", "budget_exhausted",
    ]
    before: ExecutionResult | None = None
    after: ExecutionResult | None = None
    mutation: KillReport | None = None

    @model_validator(mode="after")
    def no_success_without_double_gate(self):
        # les trois preuves restent liées dans le même verdict
        if self.verification == "passed":
            if self.reason != "verified" or self.before is None or self.before.check != "failed":
                raise ValueError("verification requires red-before evidence")
            if self.after is None or self.after.check != "passed" or self.mutation is None:
                raise ValueError("verification requires green-after and mutation evidence")
            if self.mutation.status != "killed" or self.after != self.mutation.baseline:
                raise ValueError("the killed mutation must use the verified baseline")
        elif self.reason == "verified":
            raise ValueError("verified reason requires passed verification")

        return self
