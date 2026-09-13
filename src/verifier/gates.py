"""Double gate sur sources fournies ; le raccordement aux faits et au journal reste distinct."""

from pathlib import Path
import time
from typing import Literal

from pydantic import TypeAdapter, ValidationError
from kernel.contracts import Criterion
from kernel.facts import Fact, SourceFact

from .models import Verdict, fact_error, source_digests
from .mutation import kill_check
from .runner import execute
from .relations import admit, render


FACTS = TypeAdapter(list[Fact])


def preflight(criterion: Criterion, source: str) -> None:
    """Admet les symboles et le couple relation/domaine sans lire, écrire ni exécuter."""

    admit(criterion, source)
    render(criterion, Path("candidate.py"))


def cmp_outcome(returncode: int | None) -> Literal["equal", "different", "tool_error"]:
    """Interprète un résultat cmp fourni sans lancer de commande ni coercer un statut inconnu."""

    if type(returncode) is not int:
        return "tool_error"
    if returncode == 0:
        return "equal"
    if returncode == 1:
        return "different"

    return "tool_error"


def check_sources(criterion: Criterion, before: str, after: str, *, artifact_root: Path, timeout: float) -> Verdict:
    """Vérifie rouge-avant, vert-après et sensibilité sans lire le workspace ni émettre de reçu."""

    # refus sans exécution si les octets fournis n'ont pas changé
    criterion = Criterion.model_validate(criterion.model_dump())
    if before == after:
        return Verdict(criterion=criterion, verification="rejected", reason="unchanged_source")
    started = time.monotonic()
    baseline = execute(criterion, before, artifact_root=artifact_root, timeout=timeout)
    if baseline.check == "passed":
        return Verdict(criterion=criterion, verification="rejected", reason="before_green", before=baseline)
    if baseline.check != "failed":
        return Verdict(criterion=criterion, verification="blocked", reason="before_unverifiable", before=baseline)

    # kill_check exécute une seule fois la source après, puis ses mutants
    remaining = timeout - (time.monotonic() - started)
    if remaining <= 0:
        return Verdict(criterion=criterion, verification="blocked", reason="budget_exhausted", before=baseline)
    report = kill_check(criterion, after, artifact_root=artifact_root, timeout=remaining)
    if report.baseline.check == "failed":
        verification, reason = "rejected", "after_red"
    elif report.status == "survived":
        verification, reason = "rejected", "tautology"
    elif report.status == "killed":
        verification, reason = "passed", "verified"
    else:
        verification, reason = "blocked", "mutation_unavailable"

    return Verdict(
        criterion=criterion,
        verification=verification,
        reason=reason,
        before=baseline,
        after=report.baseline,
        mutation=report,
        source_hashes=source_digests(before, after),
    )


def run(criterion: Criterion, facts: list[Fact], *, artifact_root: Path, timeout: float) -> Verdict:
    """Croise les faits avant toute exécution, puis vérifie exclusivement leurs copies source."""

    # instantanés revalidés, y compris les model_copy non validés de l'appelant
    started = time.monotonic()
    criterion = Criterion.model_validate(criterion.model_dump())
    try:
        values = [fact.model_dump() for fact in facts]
        observed = FACTS.validate_python(values)
    except (AttributeError, TypeError, ValidationError):
        return Verdict(criterion=criterion, verification="blocked", reason="invalid_facts")
    reason = fact_error(observed)
    if reason is not None:
        return Verdict(criterion=criterion, verification="blocked", reason=reason)

    # le décodage ne normalise pas les fins de ligne ; seuls les BOM utf-8 sont retirés
    source = next(fact for fact in observed if isinstance(fact, SourceFact))
    try:
        before = source.before.decode("utf-8-sig")
        after = source.after.decode("utf-8-sig")
    except UnicodeError:
        return Verdict(criterion=criterion, verification="blocked", reason="source_encoding")
    remaining = timeout - (time.monotonic() - started)
    if remaining <= 0:
        return Verdict(criterion=criterion, verification="blocked", reason="budget_exhausted")
    result = check_sources(criterion, before, after, artifact_root=artifact_root, timeout=remaining)
    values = result.model_dump()
    values.update(effect="confirmed", facts=observed)

    return Verdict.model_validate(values)
