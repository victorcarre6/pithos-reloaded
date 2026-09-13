"""Résultat d'exécution distinct d'une attestation de changement et d'un reçu durable."""

from hashlib import sha256
from pathlib import Path
import re
from typing import Literal

from pydantic import Field, StrictInt, model_validator
from kernel.contracts import Contract, Criterion
from kernel.facts import Digest, Fact, FileFact, RepoFact, SourceFact


def source_digests(before, after):
    before_hash = sha256(before.encode("utf-8")).hexdigest()
    after_hash = sha256(after.encode("utf-8")).hexdigest()

    return before_hash, after_hash


def fact_error(facts):
    """Croise les trois observations de la tranche mono-fichier sans aucune I/O."""

    # cardinalité et observations complètes
    by_type = {type(fact): fact for fact in facts}
    if len(facts) != 3 or set(by_type) != {FileFact, SourceFact, RepoFact}:
        return "missing_facts"
    file, source, repo = by_type[FileFact], by_type[SourceFact], by_type[RepoFact]
    if not repo.complete or not repo.head:
        return "incomplete_repository"
    if file.path != source.path or not repo.repo.is_absolute():
        return "path_mismatch"
    try:
        relative = file.path.relative_to(repo.repo) if file.path.is_absolute() else file.path
    except ValueError:
        return "path_mismatch"
    if not relative.parts or ".." in relative.parts:
        return "path_mismatch"

    # accord des octets et bilan de la mutation
    before_hash = sha256(source.before).hexdigest()
    after_hash = sha256(source.after).hexdigest()
    if (before_hash, after_hash) != (file.sha_before, file.sha_after):
        return "hash_mismatch"
    if source.before == source.after or file.n_replacements != 1:
        return "unchanged_source"
    start, end = file.spliced_range
    lines = source.before.splitlines(keepends=True)
    prefix = b"".join(lines[:start - 1])
    suffix = b"".join(lines[end:])
    if end > len(lines) or len(source.after) < len(prefix) + len(suffix):
        return "splice_mismatch"
    if not source.after.startswith(prefix) or not source.after.endswith(suffix):
        return "splice_mismatch"

    # le dépôt ne doit signaler qu'une modification de cette cible
    if len(repo.changes) != 1:
        return "repository_mismatch"
    change = repo.changes[0]
    if change.path != relative or change.origin is not None or change.status not in {" M", "M ", "MM"}:
        return "repository_mismatch"
    diff_lines = repo.diff.splitlines(keepends=True)
    path = relative.as_posix()
    expected = f"diff --git a/{path} b/{path}\n"
    if not diff_lines or diff_lines.pop(0) != expected:
        return "repository_mismatch"

    # seul le diff texte ordinaire d'une cible existante est admis
    if diff_lines and diff_lines[0].startswith("index "):
        diff_lines.pop(0)
    file_headers = [f"--- a/{path}", f"+++ b/{path}"]
    actual_headers = [line.rstrip("\t\n") for line in diff_lines[:2]]
    if actual_headers != file_headers:
        return "repository_mismatch"
    try:
        before = source.before.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        after = source.after.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeError:
        return "source_encoding"
    old_lines, new_lines = before.splitlines(keepends=True), after.splitlines(keepends=True)
    old_cursor, new_cursor, index = 0, 0, 2
    changed = False
    while index < len(diff_lines):
        match = re.fullmatch(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\n]*\n", diff_lines[index])
        if match is None:
            return "repository_mismatch"
        old_start, old_count, new_start, new_count = match.groups()
        old_count, new_count = int(old_count or 1), int(new_count or 1)
        old_start = int(old_start) - (old_count > 0)
        new_start = int(new_start) - (new_count > 0)
        if old_start < old_cursor or new_start < new_cursor:
            return "repository_mismatch"
        if old_start > len(old_lines) or new_start > len(new_lines):
            return "repository_mismatch"
        if old_lines[old_cursor:old_start] != new_lines[new_cursor:new_start]:
            return "repository_mismatch"
        old_chunk, new_chunk = [], []
        index += 1
        while index < len(diff_lines) and not diff_lines[index].startswith("@@ "):
            row = diff_lines[index]
            if not row or row[0] not in {" ", "+", "-"} or not row.endswith("\n"):
                return "repository_mismatch"
            content = row[1:]
            index += 1
            if index < len(diff_lines) and diff_lines[index] == "\\ No newline at end of file\n":
                content = content[:-1]
                index += 1
            if row[0] in {" ", "-"}:
                old_chunk.append(content)
            if row[0] in {" ", "+"}:
                new_chunk.append(content)
            changed |= row[0] in {"+", "-"}
        old_cursor, new_cursor = old_start + old_count, new_start + new_count
        if len(old_chunk) != old_count or len(new_chunk) != new_count:
            return "repository_mismatch"
        if old_lines[old_start:old_cursor] != old_chunk or new_lines[new_start:new_cursor] != new_chunk:
            return "repository_mismatch"
    if not changed or old_lines[old_cursor:] != new_lines[new_cursor:]:
        return "repository_mismatch"

    return None


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
    """Axes de vérification et d'effet distincts ; aucune durabilité déduite d'un verdict."""

    criterion: Criterion
    verification: Literal["passed", "rejected", "blocked"]
    reason: Literal[
        "verified", "unchanged_source", "before_green", "before_unverifiable",
        "after_red", "tautology", "mutation_unavailable", "budget_exhausted",
        "invalid_facts", "missing_facts", "incomplete_repository", "path_mismatch",
        "hash_mismatch", "splice_mismatch", "repository_mismatch", "source_encoding",
    ]
    before: ExecutionResult | None = None
    after: ExecutionResult | None = None
    mutation: KillReport | None = None
    effect: Literal["unproven", "confirmed"] = "unproven"
    facts: list[Fact] = Field(default_factory=list)
    source_hashes: tuple[Digest, Digest] | None = None

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

        # les octets attestés doivent correspondre aux sources soumises à la gate
        if self.effect == "confirmed":
            if fact_error(self.facts) is not None:
                raise ValueError("confirmed effect requires coherent facts")
            if self.verification == "passed":
                source = next(fact for fact in self.facts if isinstance(fact, SourceFact))
                expected = source_digests(source.before.decode("utf-8-sig"), source.after.decode("utf-8-sig"))
                if self.source_hashes != expected:
                    raise ValueError("facts do not match the verified sources")

        return self
