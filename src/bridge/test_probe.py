"""`probe` — la fenêtre est lue, le schéma est éprouvé, et un doute refuse de démarrer."""

import json

from bridge.conftest import completion
from bridge.probe import PROMPT_PATH, Provenance, probe, read_window, system_prompt

VALID = json.dumps({"relation": "total", "symbols": ["parse"], "domain": "small_ints"})


def test_the_window_is_read_from_the_route_not_supposed(route, monkeypatch):
    monkeypatch.delenv("PITHOS_CONTEXT_WINDOW", raising=False)

    assert read_window() == (Provenance.confirmed, 16384)


def test_an_unreadable_window_stays_unprobeable_and_refuses_to_start(route, monkeypatch):
    monkeypatch.delenv("PITHOS_CONTEXT_WINDOW", raising=False)
    route.models = []

    capability = probe()

    assert capability.provenance is Provenance.unprobeable
    assert capability.usable is False
    assert capability.context_window == 0
    assert route.requests == [], "aucun appel ne doit partir sur une fenêtre inconnue"


def test_an_operator_acknowledgement_is_asserted_never_confirmed(route, monkeypatch):
    route.models = []
    monkeypatch.setenv("PITHOS_CONTEXT_WINDOW", "8192")

    assert read_window() == (Provenance.asserted, 8192)


def test_a_route_that_honours_the_schema_is_usable(route, monkeypatch):
    monkeypatch.delenv("PITHOS_CONTEXT_WINDOW", raising=False)
    route.scenario = lambda received: (200, completion(VALID), 0)

    capability = probe()

    assert capability.usable is True
    assert (capability.provenance, capability.context_window) == (Provenance.confirmed, 16384)
    assert capability.detail == ""


def test_a_route_that_accepts_the_schema_but_ignores_it_refuses_to_start(route, monkeypatch):
    monkeypatch.delenv("PITHOS_CONTEXT_WINDOW", raising=False)
    route.scenario = lambda received: (200, completion('{"relation": "invented"}'), 0)

    capability = probe()

    assert capability.usable is False
    assert capability.detail == "revalidation: schema_violation"


def test_a_truncated_probe_answer_refuses_to_start(route, monkeypatch):
    monkeypatch.delenv("PITHOS_CONTEXT_WINDOW", raising=False)
    route.scenario = lambda received: (200, completion(VALID, finish_reason="length"), 0)

    capability = probe()

    assert capability.usable is False
    assert capability.detail == "appel de sonde: truncated"


def test_the_probe_sends_a_real_criterion_schema(route, monkeypatch):
    monkeypatch.delenv("PITHOS_CONTEXT_WINDOW", raising=False)
    route.scenario = lambda received: (200, completion(VALID), 0)

    probe()

    sent = route.requests[0]["response_format"]["json_schema"]["schema"]
    assert set(sent["properties"]) == {"relation", "symbols", "domain"}


def test_the_system_prompt_stays_a_short_countermeasure_log(route):
    lines = [line for line in system_prompt().splitlines() if line.strip()]

    assert PROMPT_PATH.suffix == ".md"
    assert len(lines) <= 25, "un ajout au prompt doit citer la mission où le mode d'échec a été observé"
