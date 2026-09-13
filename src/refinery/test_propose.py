"""Le plan de raffinement : déterministe, et sans qu'aucun client de modèle ne soit instancié."""

import pytest

from campaign.store import ALIVE, Entry, Family, Source, Store
from kernel.contracts import Relation
from refinery.gate import Baseline, NodeEvidence, refuse
from refinery.propose import RECURRENCE_MIN, plan_refinement


def nodes(green, attempted):
    verified = ["accepted"] * green + ["rejected"] * (attempted - green)

    return [NodeEvidence(node_id=f"n{index}", relation=Relation.round_trip, verification=state)
            for index, state in enumerate(verified)]


def baseline(green, attempted, **changes):
    fields = {"mission_id": "m1", "wall_seconds": 900.0, "exit_cause": "stagnation",
              "nodes": nodes(green, attempted)}

    return Baseline(**{**fields, **changes})


def entry(key, version, content="what the mission learned"):
    return Entry(key=key, family=Family.memory, title=f"the {key} lesson", content=content,
                 source=Source.model, version=version,
                 created_at="2026-09-01T00:00:00+00:00", updated_at="2026-09-01T00:00:00+00:00")


def store_of(*entries):
    state = Store(entries={family: {} for family in ALIVE})
    for item in entries:
        state.entries[item.family][item.key] = item

    return state


def test_a_mission_that_missed_nothing_gets_no_plan():
    # on ne réécrit pas un harness qui tient
    assert plan_refinement(store_of(entry("csv", RECURRENCE_MIN)), baseline(10, 10)) == []


def test_the_plan_is_deterministic_on_the_same_store_and_baseline():
    state = store_of(entry("csv", 4), entry("json", 4), entry("yaml", 9))

    assert plan_refinement(state, baseline(3, 10)) == plan_refinement(state, baseline(3, 10))


def test_the_plan_never_instantiates_a_model_client(monkeypatch):
    import httpx

    def forbidden(*args, **kwargs):
        raise AssertionError("plan_refinement instantiated a model client")

    for name in ("Client", "AsyncClient", "post", "get", "request", "stream"):
        monkeypatch.setattr(httpx, name, forbidden)

    assert plan_refinement(store_of(entry("csv", 4)), baseline(3, 10))


def test_the_plan_edits_the_single_most_recurrent_memory_entry():
    state = store_of(entry("csv", RECURRENCE_MIN), entry("json", 9), entry("yaml", 4))
    plan = plan_refinement(state, baseline(3, 10))

    assert len(plan) == 1
    assert (plan[0].key, plan[0].family) == ("json", Family.memory)
    assert plan[0].version == 10


def test_a_tie_on_recurrence_is_broken_by_the_key():
    state = store_of(entry("zebra", 5), entry("alpha", 5))

    assert plan_refinement(state, baseline(3, 10))[0].key == "alpha"


def test_an_entry_below_the_recurrence_floor_is_not_a_recurring_fact():
    state = store_of(entry("csv", RECURRENCE_MIN - 1))
    plan = plan_refinement(state, baseline(3, 10))

    assert plan[0].key != "csv"
    assert plan[0].version == 1


def test_with_nothing_recurring_the_plan_records_the_mission_itself():
    plan = plan_refinement(store_of(), baseline(3, 10, mission_id="m7"))

    assert plan[0].key == "mission-m7"
    assert (plan[0].family, plan[0].version) == (Family.memory, 1)


def test_the_edit_keeps_what_the_entry_already_said():
    state = store_of(entry("csv", 4, content="an earlier lesson"))
    written = plan_refinement(state, baseline(3, 10))[0].content

    assert written.startswith("an earlier lesson")
    assert "7/10" in written


def test_the_evidence_is_exactly_the_nodes_that_did_not_verify():
    measured = baseline(3, 10)
    evidence = plan_refinement(store_of(), measured)[0].evidence

    assert evidence == [node for node in measured.nodes if node.verification != "accepted"]
    assert all(node.verification == "rejected" for node in evidence)


@pytest.mark.parametrize("state", [
    lambda: store_of(),
    lambda: store_of(entry("csv", 9)),
    lambda: store_of(entry("base_system_prompt", 9)),
])
def test_nothing_the_plan_emits_would_be_refused_by_the_gate(state):
    for proposed in plan_refinement(state(), baseline(3, 10)):
        assert refuse(proposed) == ""
