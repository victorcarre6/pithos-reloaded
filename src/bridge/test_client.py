"""`call` — un POST borné, une issue discriminée, et rien d'exploitable hors d'une fin propre."""

import json
import time

import pytest

from bridge import client
from bridge.client import Deadline, Outcome, base_url, call, normalize_base_url
from bridge.conftest import completion
from bridge.schema import normalize_schema
from kernel.contracts import Criterion

SCHEMA = normalize_schema(Criterion)
VALID = json.dumps({"relation": "total", "symbols": ["f"], "domain": "small_ints"})
ROOMY = Deadline(seconds=5.0, context_window=16384, reserved_output=512)


def test_the_payload_carries_the_strict_schema_and_the_measured_sampling(route):
    route.scenario = lambda received: (200, completion(VALID), 0)

    call(SCHEMA, "sys", "user", ROOMY)

    sent = route.requests[0]
    assert sent["model"] == client.MODEL
    assert sent["stream"] is False
    assert sent["response_format"]["json_schema"]["strict"] is True
    assert sent["response_format"]["json_schema"]["schema"] == SCHEMA
    assert (sent["temperature"], sent["top_p"], sent["top_k"]) == (0.3, 0.95, 20)
    assert sent["max_tokens"] == ROOMY.reserved_output


def test_a_finished_generation_is_exploitable(route):
    route.scenario = lambda received: (200, completion(VALID), 0)

    response = call(SCHEMA, "sys", "user", ROOMY)

    assert response.outcome is Outcome.completed
    assert json.loads(response.content) == json.loads(VALID)
    assert response.usage["completion_tokens"] == 7


def test_a_truncated_generation_never_yields_an_exploitable_object(route):
    route.scenario = lambda received: (200, completion(VALID, finish_reason="length"), 0)

    response = call(SCHEMA, "sys", "user", ROOMY)

    assert response.outcome is Outcome.truncated
    assert response.content == ""
    assert response.raw_stop_reason == "length"


def test_an_unknown_terminal_reason_is_an_explicit_failure(route):
    route.scenario = lambda received: (200, completion(VALID, finish_reason="content_filter"), 0)

    response = call(SCHEMA, "sys", "user", ROOMY)

    assert response.outcome is Outcome.unknown_stop
    assert response.content == ""
    assert response.raw_stop_reason == "content_filter"


def test_thinking_carried_in_its_own_field_never_reaches_the_content(route):
    route.scenario = lambda received: (200, completion(VALID, reasoning_content="je réfléchis"), 0)

    response = call(SCHEMA, "sys", "user", ROOMY)

    assert response.content == VALID
    assert response.thinking == "je réfléchis"


def test_an_inline_think_block_is_moved_out_of_the_content(route):
    body = f"<think>le critère doit être total</think>{VALID}"
    route.scenario = lambda received: (200, completion(body), 0)

    response = call(SCHEMA, "sys", "user", ROOMY)

    assert response.content == VALID
    assert "le critère doit être total" in response.thinking


def test_a_transient_error_is_never_retried_implicitly(route):
    route.scenario = lambda received: (503, {"error": "busy"}, 0)

    response = call(SCHEMA, "sys", "user", ROOMY)

    assert response.outcome is Outcome.transport_error
    assert len(route.requests) == 1


def test_a_contract_that_does_not_fit_the_window_is_never_sent(route):
    tight = Deadline(seconds=5.0, context_window=64, reserved_output=512)

    response = call(SCHEMA, "sys", "user", tight)

    assert response.outcome is Outcome.budget_refused
    assert route.requests == []


def test_giving_up_the_wait_does_not_kill_the_operation(route):
    route.scenario = lambda received: (200, completion(VALID), 0.6)

    response = call(SCHEMA, "sys", "user", Deadline(seconds=0.2, context_window=16384, reserved_output=512))

    assert response.outcome is Outcome.transport_error
    deadline = time.monotonic() + 3.0
    while not route.effects and time.monotonic() < deadline:
        time.sleep(0.02)
    assert route.effects, "l'effet serveur a été perdu avec l'attente du client"


def test_the_effective_payload_is_recorded_for_the_rejection_rate_to_be_measurable(route, double, monkeypatch):
    journal_double = double("journal")
    monkeypatch.setattr(client, "journal", journal_double)
    route.scenario = lambda received: (200, completion(VALID), 0)

    call(SCHEMA, "sys", "user", ROOMY)

    recorded = journal_double.events[-1].payload
    assert recorded["model"] == client.MODEL
    assert recorded["outcome"] == "completed"
    assert recorded["sampling"] == {"temperature": 0.3, "top_p": 0.95, "top_k": 20}
    assert recorded["endpoint"].endswith("/v1/chat/completions")


def test_a_refused_budget_is_recorded_too(route, double, monkeypatch):
    journal_double = double("journal")
    monkeypatch.setattr(client, "journal", journal_double)

    call(SCHEMA, "sys", "user", Deadline(seconds=5.0, context_window=64, reserved_output=512))

    assert journal_double.events[-1].payload["outcome"] == "budget_refused"


def test_the_base_url_gains_v1_idempotently():
    assert normalize_base_url("http://127.0.0.1:11434") == "http://127.0.0.1:11434/v1"
    assert normalize_base_url("http://127.0.0.1:11434/") == "http://127.0.0.1:11434/v1"
    assert normalize_base_url("http://127.0.0.1:11434/v1") == "http://127.0.0.1:11434/v1"


def test_a_route_outside_loopback_is_refused(monkeypatch):
    with pytest.raises(ValueError, match="hors loopback"):
        normalize_base_url("http://example.com:11434")

    monkeypatch.setenv("PITHOS_OLLAMA_URL", "http://10.0.0.5:11434")
    with pytest.raises(ValueError, match="hors loopback"):
        base_url()
