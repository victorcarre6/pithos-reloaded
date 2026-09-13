"""Une exception explicite pour le code candidat, sans élargir les champs de validation."""

import json

import pytest

import bridge


def test_candidate_schema_binds_the_harness_selected_symbol():
    model = bridge.candidate_model("clamp_level")
    schema = bridge.normalize_schema(model)
    assert schema["additionalProperties"] is False
    assert set(schema["properties"]) == {"function_name", "new_source"}
    assert schema["properties"]["function_name"]["const"] == "clamp_level"
    raw = json.dumps({"function_name": "clamp_level", "new_source": "def clamp_level(level): return level"})
    assert isinstance(bridge.revalidate(raw, schema, model), bridge.Ok)


@pytest.mark.parametrize("changes", [
    {"function_name": "other"}, {"new_source": 123}, {"new_source": ""},
    {"new_source": "x" * 8001}, {"expected": 0}, {"command": "python evil.py"},
    {"criterion": {"relation": "total"}},
])
def test_candidate_cannot_change_the_symbol_or_supply_validation(changes):
    model = bridge.candidate_model("clamp_level")
    schema = bridge.normalize_schema(model)
    payload = {"function_name": "clamp_level", "new_source": "def clamp_level(level): return level"}
    payload.update(changes)
    result = bridge.revalidate(json.dumps(payload), schema, model)
    assert isinstance(result, bridge.Err)
    assert result.code == bridge.ErrorCode.schema_violation


def test_double_exposes_the_same_candidate_contract(double):
    memory = double("bridge")
    assert memory.normalize_schema(memory.candidate_model("clamp_level")) == bridge.normalize_schema(bridge.candidate_model("clamp_level"))


def test_candidate_trace_keeps_the_full_generation(journal_double, monkeypatch):
    from bridge import client

    monkeypatch.setattr(client, "journal", journal_double)
    model = bridge.candidate_model("clamp_level")
    schema = bridge.normalize_schema(model)
    payload = client.build_payload(schema, "system", "user", bridge.Deadline(10, 16384, 2048))
    raw = "x" * 1500
    response = bridge.RawResponse(bridge.Outcome.truncated, "", "reasoning", "length", {}, 1)
    client._record(payload, response, raw, bridge.Deadline(10, 16384, 2048), 0.5)
    recorded = journal_double.events[-1].payload
    assert recorded["raw_content"] == raw
    assert recorded["thinking"] == "reasoning"
    assert recorded["request"] == payload
    assert len(recorded["body_excerpt"]) == 500
