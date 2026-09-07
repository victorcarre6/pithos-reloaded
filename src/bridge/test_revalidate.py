"""`revalidate` — cinq codes fermés, et rien ne passe par une autre porte."""

import json

from bridge.revalidate import Err, ErrorCode, Ok, revalidate, schema_sha256
from bridge.schema import normalize_schema
from kernel.contracts import Criterion

SCHEMA = normalize_schema(Criterion)
VALID = json.dumps({"relation": "total", "symbols": ["f"], "domain": "small_ints"})


def test_a_conformant_output_is_accepted_and_rebuilt():
    verdict = revalidate(VALID, SCHEMA, Criterion)

    assert isinstance(verdict, Ok)
    assert verdict.value == Criterion(relation="total", symbols=["f"], domain="small_ints")


def test_every_verdict_is_bound_to_the_exact_schema_sent():
    accepted = revalidate(VALID, SCHEMA, Criterion)
    rejected = revalidate("{", SCHEMA, Criterion)

    assert accepted.schema_sha256 == rejected.schema_sha256 == schema_sha256(SCHEMA)


def test_a_truncated_json_is_rejected_and_never_repaired():
    verdict = revalidate('{"relation": "total", "symbols": ["f"]', SCHEMA, Criterion)

    assert verdict.code == ErrorCode.invalid_json


def test_nan_and_infinity_are_refused_as_their_own_closed_code():
    for literal in ("NaN", "Infinity", "-Infinity"):
        raw = '{"relation": "total", "symbols": ["f"], "domain": ' + literal + "}"

        assert revalidate(raw, SCHEMA, Criterion).code == ErrorCode.constant_refused


def test_a_root_that_is_not_an_object_is_named_as_such():
    assert revalidate('["total"]', SCHEMA, Criterion).code == ErrorCode.arguments_not_object
    assert revalidate('"total"', SCHEMA, Criterion).code == ErrorCode.arguments_not_object


def test_an_output_the_transport_accepted_but_the_schema_forbids_is_rejected_locally():
    raw = json.dumps({"relation": "does_not_exist", "symbols": ["f"], "domain": "small_ints"})

    verdict = revalidate(raw, SCHEMA, Criterion)

    assert verdict.code == ErrorCode.schema_violation
    assert verdict.detail.startswith("relation:")


def test_an_extra_field_is_a_violation_and_is_never_dropped_silently():
    raw = json.dumps({"relation": "total", "symbols": ["f"], "domain": "small_ints", "hint": "x"})

    assert revalidate(raw, SCHEMA, Criterion).code == ErrorCode.schema_violation


def test_no_coercion_repairs_a_wrong_type():
    raw = json.dumps({"relation": "total", "symbols": "f", "domain": "small_ints"})

    verdict = revalidate(raw, SCHEMA, Criterion)

    assert verdict.code == ErrorCode.schema_violation
    assert verdict.detail.startswith("symbols:")


def test_a_relation_that_needs_two_symbols_is_rejected_with_one():
    raw = json.dumps({"relation": "round_trip", "symbols": ["f"], "domain": "small_ints"})

    assert revalidate(raw, SCHEMA, Criterion).code == ErrorCode.schema_violation


def test_a_schema_that_is_not_the_models_schema_is_an_unknown_tool():
    foreign = dict(SCHEMA, properties=dict(SCHEMA["properties"], extra={"type": "string"}))

    verdict = revalidate(VALID, foreign, Criterion)

    assert verdict.code == ErrorCode.unknown_tool
    assert verdict.schema_sha256 == schema_sha256(foreign)


def test_the_five_codes_are_the_whole_closed_set():
    assert {code.value for code in ErrorCode} == {
        "invalid_json",
        "arguments_not_object",
        "unknown_tool",
        "schema_violation",
        "constant_refused",
    }
