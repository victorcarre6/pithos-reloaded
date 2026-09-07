"""Normalisation d'un modèle Pydantic en JSON Schema qu'une grammaire de décodage sait appliquer."""

from pydantic import BaseModel

# sous-ensemble de mots-clés réellement supporté, déclaré plutôt que supposé
SUPPORTED_KEYWORDS = frozenset({
    "additionalProperties", "anyOf", "const", "enum", "items", "maxItems", "maxLength",
    "maximum", "minItems", "minLength", "minimum", "properties", "required", "type",
})
# un integer sans bornes fait échouer certaines grammaires ; les bornes sont donc explicites
INTEGER_MINIMUM = -(2 ** 53 - 1)
INTEGER_MAXIMUM = 2 ** 53 - 1

LOCAL_REF_PREFIX = "#/$defs/"


def _inline(value, definitions: dict, seen: frozenset):
    "Remplace un `$ref` local par sa définition — Pydantic en émet un par enum et modèle imbriqué."

    if isinstance(value, list):
        return [_inline(item, definitions, seen) for item in value]

    if not isinstance(value, dict):
        return value

    reference = value.get("$ref")
    if isinstance(reference, str) and reference.startswith(LOCAL_REF_PREFIX):
        name = reference[len(LOCAL_REF_PREFIX):]
        if name in definitions and name not in seen:
            siblings = {key: item for key, item in value.items() if key != "$ref"}
            resolved = {**definitions[name], **siblings}

            return _inline(resolved, definitions, seen | {name})

    return {key: _inline(item, definitions, seen) for key, item in value.items()}


def _restrict(value):
    "Ne garde que les mots-clés supportés, borne les integers, et refuse un `$ref` non résolu."

    if isinstance(value, list):
        return [_restrict(item) for item in value]

    if not isinstance(value, dict):
        return value

    if "$ref" in value:
        raise ValueError(f"bridge: référence locale non résolue — {value['$ref']}")

    # `properties` porte des noms de champ, jamais des mots-clés : il ne se filtre pas
    kept = {}
    for keyword, item in value.items():
        if keyword not in SUPPORTED_KEYWORDS:
            continue
        if keyword == "properties":
            kept[keyword] = {name: _restrict(schema) for name, schema in item.items()}
        else:
            kept[keyword] = _restrict(item)

    if kept.get("type") == "integer":
        kept.setdefault("minimum", INTEGER_MINIMUM)
        kept.setdefault("maximum", INTEGER_MAXIMUM)

    return kept


def normalize_schema(model: type[BaseModel]) -> dict:
    """Résout `$defs`/`$ref`, borne les integers, restreint au sous-ensemble supporté.

    Lève si le résultat n'est pas envoyable : la validation a lieu ici, avant tout envoi.
    """

    document = model.model_json_schema()
    definitions = document.get("$defs", {})
    body = {keyword: item for keyword, item in document.items() if keyword != "$defs"}
    schema = _restrict(_inline(body, definitions, frozenset()))

    if schema.get("type") != "object" or not schema.get("properties"):
        raise ValueError(f"bridge: {model.__name__} ne produit pas un objet à propriétés")

    return schema
