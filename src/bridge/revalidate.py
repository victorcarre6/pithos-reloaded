"""Revalidation locale contre le schéma exact envoyé : cinq codes fermés, aucune récupération."""

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel, ValidationError

from .schema import normalize_schema

DETAIL_MAX_CHARS = 200


class ErrorCode(StrEnum):
    invalid_json = "invalid_json"
    arguments_not_object = "arguments_not_object"
    unknown_tool = "unknown_tool"
    schema_violation = "schema_violation"
    constant_refused = "constant_refused"


class ConstantRefused(Exception):
    "`NaN` et `Infinity` ne sont pas du JSON : une classe de littéral illégal fermée d'une ligne."


@dataclass(frozen=True, slots=True)
class Ok[T]:
    "Verdict favorable, lié par empreinte au schéma exactement envoyé."

    value: T
    schema_sha256: str


@dataclass(frozen=True, slots=True)
class Err[T]:
    "Rejet nommé par un code fermé, lié par empreinte au schéma exactement envoyé."

    code: T
    schema_sha256: str
    detail: str


def schema_sha256(schema: dict) -> str:
    "Empreinte canonique d'un schéma : elle lie un verdict au schéma exactement envoyé."

    canonical = json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _refuse_constant(name: str):
    "Appelé par le décodeur sur `NaN`, `Infinity` et `-Infinity`, jamais sur autre chose."

    raise ConstantRefused(name)


def _violation_detail(violation: ValidationError) -> str:
    "Nomme le chemin exact du premier champ fautif, borné — le corps complet vit dans l'artefact."

    first = violation.errors()[0]
    field_path = ".".join(str(part) for part in first["loc"])
    detail = f"{field_path}: {first['msg']}"

    return detail[:DETAIL_MAX_CHARS]


def revalidate(raw: str, schema: dict, model: type[BaseModel]) -> Ok[BaseModel] | Err[ErrorCode]:
    """Revalide localement une sortie brute contre le schéma exact envoyé.

    L'acceptation par le transport n'autorise rien, et rien n'est extrait, réparé ni coercé : une
    sortie mal formée est rejetée avec son code.
    """

    digest = schema_sha256(schema)

    # le schéma envoyé et le modèle validé doivent être le même artefact, sinon le verdict ne vaut rien
    if schema != normalize_schema(model):
        return Err(ErrorCode.unknown_tool, digest, f"schéma étranger à {model.__name__}")

    try:
        arguments = json.loads(raw, parse_constant=_refuse_constant)
    except ConstantRefused as refused:
        return Err(ErrorCode.constant_refused, digest, f"constante non JSON: {refused}")
    except (TypeError, ValueError) as malformed:
        return Err(ErrorCode.invalid_json, digest, str(malformed)[:DETAIL_MAX_CHARS])

    if not isinstance(arguments, dict):
        return Err(ErrorCode.arguments_not_object, digest, f"racine de type {type(arguments).__name__}")

    try:
        return Ok(model.model_validate(arguments), digest)
    except ValidationError as violation:
        return Err(ErrorCode.schema_violation, digest, _violation_detail(violation))
