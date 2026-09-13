"""Les règles d'admission d'une proposition ; le mécanisme d'accumulation appartient à `kernel`.

Une proposition à trois défauts rend **trois** violations, chacune avec le chemin exact de son champ.
Sans cela elle coûterait trois sessions à 16 k au lieu d'une.

Sur les placeholders, deux sources s'opposent frontalement et le choix est tranché : Pi exécute la
commande contenue dans une valeur de configuration (`resolve-config-value.ts:10`, **écarté**) ;
OpenHands interdit toute expression évaluable dans un placeholder (`manifest-template.ts:76`, **repris**).

PORTED_FROM: OpenHands-main/src/manifests/manifest-template.ts:12,21,40-43,65-80 (MIT)
"""

import re
from dataclasses import dataclass
from enum import StrEnum

from pydantic import Field, ValidationError

from kernel.contracts import Contract, Criterion, Name
from kernel.errors import Cause, ErrorAccumulator

from .store import Source


ARGUMENT_ROOT = "args"
ALLOWED_MODULE_PREFIXES = ("tools.",)
SHELL_METACHARACTERS = frozenset(";|&$`<>()[]*?!~\\'\"\n\r\t")
FORBIDDEN = SHELL_METACHARACTERS | {"{", "}"}

NAME_PATTERN = re.compile(r"[a-z][a-z0-9_]{2,63}")
ARGUMENT_PATTERN = re.compile(r"[a-z][a-z0-9_]{0,63}")
MODULE_PATTERN = re.compile(r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+")
PLACEHOLDER_PATTERN = re.compile(r"\{\{[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)*\}\}")
BRACED_PATTERN = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)


class BlastRadius(StrEnum):
    file = "file"
    module = "module"
    repo = "repo"


class Proposal(Contract):
    """Une proposition d'outil : ce qu'elle vise, sur quelle preuve, et comment on l'appellerait."""

    name: Name
    title: Name
    description: str
    evidence: list[Name] = Field(min_length=1)  # une opportunité sans preuve n'existe pas
    blast_radius: BlastRadius
    source: Source
    module: Name
    call: Name
    arguments: list[Name]
    template: str
    criterion: Criterion | None


class Violation(Contract):
    """Un défaut nommé : sa cause fermée, le chemin exact de son champ, et de quoi le corriger."""

    field_path: Name
    cause: Cause
    detail: str


@dataclass(frozen=True, slots=True)
class Ok[T]:
    "Verdict favorable : la forme et les règles sont toutes deux passées."

    value: T


@dataclass(frozen=True, slots=True)
class Err[T]:
    "Rejet portant **toutes** les violations, jamais seulement la première."

    violations: T


def _check_name(errors: ErrorAccumulator, raw: dict) -> None:
    "Le nom de l'outil : alphabet fermé — donc sans métacaractère shell — et bornes de longueur."

    name = raw.get("name")
    if not isinstance(name, str):
        return

    if NAME_PATTERN.fullmatch(name) is None:
        log_content = f"a tool name must match /{NAME_PATTERN.pattern}/"
        errors.add("name", Cause.invalid_symbol, log_content)


def _check_arguments(errors: ErrorAccumulator, raw: dict) -> None:
    "Un argument déclaré porte le même alphabet fermé que le nom de l'outil : il entre dans un gabarit."

    arguments = raw.get("arguments")
    if not isinstance(arguments, list):
        return

    for index, argument in enumerate(arguments):
        if isinstance(argument, str) and ARGUMENT_PATTERN.fullmatch(argument) is None:
            log_content = f"an argument name must match /{ARGUMENT_PATTERN.pattern}/"
            errors.add(f"arguments.{index}", Cause.invalid_symbol, log_content)


def _check_module(errors: ErrorAccumulator, raw: dict) -> None:
    "Le module d'import : chemin pointé en minuscules, et un préfixe de la liste autorisée."

    module = raw.get("module")
    if not isinstance(module, str):
        return

    if MODULE_PATTERN.fullmatch(module) is None:
        errors.add("module", Cause.invalid_symbol, "a module must be a dotted lowercase path")
    elif not module.startswith(ALLOWED_MODULE_PREFIXES):
        log_content = f"a module must start with one of {ALLOWED_MODULE_PREFIXES}"
        errors.add("module", Cause.invalid_symbol, log_content)


def _check_placeholder(errors: ErrorAccumulator, index: int, braced: str, declared: set) -> None:
    "Un placeholder nomme un argument déclaré, par un chemin fermé, et rien d'autre."

    field_path = f"template.{index}"
    if PLACEHOLDER_PATTERN.fullmatch(braced) is None:
        log_content = f"{braced} is not a closed path: no expression is ever evaluated here"
        errors.add(field_path, Cause.invalid_schema, log_content)

        return

    root, _, leaf = braced[2:-2].partition(".")
    if root != ARGUMENT_ROOT or not leaf or "." in leaf:
        log_content = f"{braced} must read exactly one declared argument as {{{{{ARGUMENT_ROOT}.<name>}}}}"
        errors.add(field_path, Cause.invalid_schema, log_content)
    elif leaf not in declared:
        log_content = f"{braced} names {leaf!r}, which the proposal does not declare"
        errors.add(field_path, Cause.invalid_symbol, log_content)


def _check_template(errors: ErrorAccumulator, raw: dict) -> None:
    "Le gabarit d'appel : placeholders fermés, et aucun métacaractère shell autour d'eux."

    template = raw.get("template")
    if not isinstance(template, str):
        return

    arguments = raw.get("arguments")
    declared = {name for name in arguments if isinstance(name, str)} if isinstance(arguments, list) else set()
    for index, match in enumerate(BRACED_PATTERN.finditer(template)):
        _check_placeholder(errors, index, match.group(0), declared)

    # ce qui reste hors placeholder est du texte littéral : ni métacaractère, ni accolade orpheline
    literal = BRACED_PATTERN.sub("", template)
    stray = sorted(set(literal) & FORBIDDEN)
    if stray:
        log_content = f"forbidden characters outside placeholders: {''.join(stray)!r}"
        errors.add("template", Cause.invalid_schema, log_content)


def admit(proposal: dict) -> Ok[Proposal] | Err[list[Violation]]:
    """Rend la proposition admise, ou **toutes** ses violations en une seule passe.

    Les règles tournent sur le dict brut et la forme est validée ensuite : un défaut de forme ne
    masque donc jamais un défaut de règle, et le modèle n'a pas deux allers-retours à payer.
    """

    errors = ErrorAccumulator()
    _check_name(errors, proposal)
    _check_arguments(errors, proposal)
    _check_module(errors, proposal)
    _check_template(errors, proposal)

    admitted = None
    try:
        admitted = Proposal.model_validate(proposal)
    except ValidationError as failure:
        for detail in failure.errors():
            field_path = ".".join(str(part) for part in detail["loc"]) or "proposal"
            errors.add(field_path, Cause.invalid_schema, detail["msg"])

    violations = [
        Violation(field_path=error.field_path, cause=error.cause, detail=error.detail)
        for error in errors.violations
    ]
    if violations:
        return Err(violations)

    return Ok(admitted)
