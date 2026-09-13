"""Intention écrite avant l'effet, résultat après : les trois états d'une reprise."""

from pathlib import Path

import pytest

from broker.identity import Effect, new_identity
from broker.intent import Stage, record_intent, record_result, resume, stage

LEDGER = Path("effects.json")


@pytest.fixture
def identity():
    return new_identity("mission-1", "node-7", 2, Effect.pull_request)


def test_nothing_written_is_unstarted(trace, identity):
    assert stage(LEDGER, identity.result, trace=trace) is Stage.unstarted


def test_intent_without_result_is_an_unknown_effect(trace, identity):
    record_intent(LEDGER, identity, {"branch": "work"}, trace=trace)
    assert stage(LEDGER, identity.result, trace=trace) is Stage.unknown_effect


def test_result_written_closes_the_effect(trace, identity):
    record_intent(LEDGER, identity, {"branch": "work"}, trace=trace)
    record_result(LEDGER, identity, {"number": 12}, trace=trace)
    assert stage(LEDGER, identity.result, trace=trace) is Stage.recorded


def test_the_intent_is_written_before_the_effect_runs(trace, identity):
    seen = []

    def effect():
        seen.append(stage(LEDGER, identity.result, trace=trace))

    record_intent(LEDGER, identity, {"branch": "work"}, trace=trace)
    effect()
    record_result(LEDGER, identity, {"number": 12}, trace=trace)
    assert seen == [Stage.unknown_effect]


def test_a_resume_interrogates_the_host_before_replaying(trace, identity):
    calls = []
    record_intent(LEDGER, identity, {"branch": "work"}, trace=trace)
    found = resume(LEDGER, identity, lambda: calls.append("probe") or {"number": 12}, trace=trace)
    assert (calls, found) == (["probe"], {"number": 12})
    assert stage(LEDGER, identity.result, trace=trace) is Stage.recorded


def test_a_resume_that_finds_nothing_hands_the_effect_back(trace, identity):
    record_intent(LEDGER, identity, {"branch": "work"}, trace=trace)
    assert resume(LEDGER, identity, lambda: None, trace=trace) is None
    assert stage(LEDGER, identity.result, trace=trace) is Stage.unknown_effect


def test_an_unstarted_effect_is_never_interrogated(trace, identity):
    calls = []
    assert resume(LEDGER, identity, lambda: calls.append("probe"), trace=trace) is None
    assert calls == []


def test_a_recorded_result_is_rendered_without_interrogation(trace, identity):
    calls = []
    record_intent(LEDGER, identity, {"branch": "work"}, trace=trace)
    record_result(LEDGER, identity, {"number": 12}, trace=trace)
    found = resume(LEDGER, identity, lambda: calls.append("probe"), trace=trace)
    assert (found, calls) == ({"number": 12}, [])


def test_a_retry_of_the_same_effect_never_counts_twice(trace, identity):
    record_intent(LEDGER, identity, {"branch": "work"}, trace=trace)
    record_result(LEDGER, identity, {"number": 12}, trace=trace)

    # même résultat, transport neuf — le registre ne gagne pas une seconde entrée
    retry = new_identity("mission-1", "node-7", 2, Effect.pull_request)
    record_intent(LEDGER, retry, {"branch": "work"}, trace=trace)
    record_result(LEDGER, retry, {"number": 12}, trace=trace)
    assert len(trace.json_files[LEDGER]) == 1
    assert trace.json_files[LEDGER][identity.result]["transport"] == retry.transport
