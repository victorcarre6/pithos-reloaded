"""`normalize_schema` — un schéma réellement décodable, validé avant envoi."""

import json

import pytest
from pydantic import BaseModel, Field

from bridge.schema import INTEGER_MAXIMUM, INTEGER_MINIMUM, SUPPORTED_KEYWORDS, normalize_schema
from kernel.contracts import Criterion


def test_the_criterion_schema_carries_no_defs_and_no_ref():
    schema = normalize_schema(Criterion)
    rendered = json.dumps(schema)

    assert "$defs" not in rendered
    assert "$ref" not in rendered


def test_each_enum_is_inlined_where_pydantic_had_put_a_reference():
    schema = normalize_schema(Criterion)

    relation = schema["properties"]["relation"]
    assert relation["type"] == "string"
    assert "round_trip" in relation["enum"]
    assert len(schema["properties"]["domain"]["enum"]) == 5


def test_the_field_constraints_survive_normalization():
    symbols = normalize_schema(Criterion)["properties"]["symbols"]

    assert (symbols["minItems"], symbols["maxItems"]) == (1, 2)
    assert symbols["items"]["minLength"] == 1


def test_an_integer_receives_explicit_bounds():
    class Depth(BaseModel):
        depth: int

    schema = normalize_schema(Depth)

    assert schema["properties"]["depth"]["minimum"] == INTEGER_MINIMUM
    assert schema["properties"]["depth"]["maximum"] == INTEGER_MAXIMUM


def test_declared_bounds_are_never_overwritten():
    class Depth(BaseModel):
        depth: int = Field(ge=0, le=3)

    schema = normalize_schema(Depth)

    assert (schema["properties"]["depth"]["minimum"], schema["properties"]["depth"]["maximum"]) == (0, 3)


def test_no_unsupported_keyword_reaches_the_schema():
    def keywords(node):
        "Mots-clés de schéma rencontrés ; sous `properties`, ce sont des noms de champ."

        if isinstance(node, list):
            return {found for item in node for found in keywords(item)}
        if not isinstance(node, dict):
            return set()

        found = set(node)
        for keyword, item in node.items():
            children = item.values() if keyword == "properties" else [item]
            for child in children:
                found |= keywords(child)

        return found

    assert keywords(normalize_schema(Criterion)) <= SUPPORTED_KEYWORDS


def test_a_title_never_reaches_the_model():
    schema = normalize_schema(Criterion)

    assert "title" not in json.dumps(schema)


def test_a_recursive_model_is_refused_before_being_sent():
    class Branch(BaseModel):
        child: "Branch | None" = None

    Branch.model_rebuild()

    with pytest.raises(ValueError, match="référence locale non résolue"):
        normalize_schema(Branch)


def test_a_model_without_properties_is_refused_before_being_sent():
    class Empty(BaseModel):
        pass

    with pytest.raises(ValueError, match="objet à propriétés"):
        normalize_schema(Empty)
