"""Corpus partagé bridge/double : la même frontière modèle, vue des deux côtés.

⚠️ **Le transport n'est pas dans ce corpus** !
→ `call` et `probe` parlent à un serveur ; le vrai module ne peut donc pas les jouer ici. Leur borne
au loopback et leurs six cas de réponse sont testés par `src/bridge/test_client.py` contre une route
scénarisée. Ce qui se vérifie ici est ce qui doit coïncider **sans réseau** : le protocole, les
signatures, et les deux fonctions pures que la frontière expose.
"""

import inspect
import json

import pytest

import bridge
from bridge import Bridge, Ok
from kernel.contracts import Criterion


@pytest.fixture(params=["bridge", "double"])
def frontier(request, double):
    if request.param == "double":
        module = double("bridge")
        module.reset()

        return module

    return bridge


def test_both_satisfy_the_same_protocol_and_the_same_signatures(frontier):
    assert isinstance(frontier, Bridge)
    for name in Bridge.__protocol_attrs__:
        expected = list(inspect.signature(getattr(bridge, name)).parameters)
        assert list(inspect.signature(getattr(frontier, name)).parameters) == expected


def test_the_normalized_schema_is_the_same_on_both_sides(frontier):
    normalized = frontier.normalize_schema(Criterion)

    assert normalized == bridge.normalize_schema(Criterion)
    assert normalized["type"] == "object"


@pytest.mark.parametrize("relation,domain", [("idempotent", "small_ints"), ("unit_projection", "floats_finite")])
def test_a_conformant_payload_revalidates_on_both_sides(frontier, relation, domain):
    schema = bridge.normalize_schema(Criterion)
    raw = json.dumps({"relation": relation, "symbols": ["f"], "domain": domain})
    verdict = frontier.revalidate(raw, schema, Criterion)

    assert isinstance(verdict, Ok)
    assert verdict.value.relation == relation


@pytest.mark.parametrize("raw,code", [
    ("{not json", "invalid_json"),
    ('{"relation": "unknown_relation", "symbols": ["f"], "domain": "small_ints"}', "schema_violation"),
    ('{"relation": "idempotent", "symbols": ["f", "g"], "domain": "small_ints"}', "schema_violation"),
    ("[1, 2]", "arguments_not_object"),
])
def test_a_rejected_payload_carries_the_same_closed_code_on_both_sides(frontier, raw, code):
    schema = bridge.normalize_schema(Criterion)
    verdict = frontier.revalidate(raw, schema, Criterion)

    assert not isinstance(verdict, Ok)
    assert verdict.code.value == code


def test_the_verdict_is_bound_to_the_exact_schema_that_was_sent(frontier):
    schema = bridge.normalize_schema(Criterion)
    raw = '{"relation": "idempotent", "symbols": ["f"], "domain": "small_ints"}'
    verdict = frontier.revalidate(raw, schema, Criterion)

    assert verdict.schema_sha256 == bridge.revalidate(raw, schema, Criterion).schema_sha256


def test_only_the_double_can_be_scripted(frontier):
    if frontier is bridge:
        pytest.skip("la frontière réelle n'a pas de file à charger")
    frontier.script(frontier.conformant({"relation": "total", "symbols": ["f"], "domain": "small_ints"}))

    assert frontier.call({}, "system", "user", bridge.Deadline(30.0, 16384, 512)).content


def test_signature_mutation_reaches_the_contract(double, monkeypatch):
    memory = double("bridge")
    test_both_satisfy_the_same_protocol_and_the_same_signatures(memory)
    monkeypatch.setattr(memory, "call", lambda wrong: None)
    with pytest.raises(AssertionError):
        test_both_satisfy_the_same_protocol_and_the_same_signatures(memory)
