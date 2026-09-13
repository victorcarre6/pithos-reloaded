"""Corpus partagé politique/double."""

import inspect

import pytest

import refinery
from campaign.store import ALIVE, Family, Store
from kernel.contracts import Relation
from refinery import Baseline, Decision, Edit, Effect, Label, NodeEvidence, Refinery
from refinery.gate import BASE_KEY
from tests.support import load_double


PUBLIC = ("plan_refinement", "gate")


def nodes(green, attempted):
    verified = ["accepted"] * green + ["rejected"] * (attempted - green)

    return [NodeEvidence(node_id=f"n{index}", relation=Relation.round_trip, verification=state)
            for index, state in enumerate(verified)]


def baseline(green, attempted):
    return Baseline(mission_id="m1", wall_seconds=900.0, exit_cause="stagnation",
                    nodes=nodes(green, attempted))


def edit(**changes):
    fields = {"family": Family.memory, "key": "csv_lesson", "version": 2,
              "content": "csv parsing needs an explicit delimiter", "evidence": nodes(0, 1)}

    return Edit(**{**fields, **changes})


@pytest.fixture(params=["policy", "double"])
def policy(request):
    if request.param == "double":
        module = load_double("refinery")
        module.reset()

        return module

    return refinery


def test_both_satisfy_the_same_protocol_and_the_same_signatures(policy):
    assert isinstance(policy, Refinery)
    for name in PUBLIC:
        expected = inspect.signature(getattr(refinery, name)).parameters.keys()
        assert inspect.signature(getattr(policy, name)).parameters.keys() == expected


def test_both_stay_disabled(policy):
    assert policy.ENABLED is False


def test_neither_promotes_an_edit_aimed_at_the_base_entry(policy):
    verdict = policy.gate(edit(family=Family.prompt, key=BASE_KEY), baseline(20, 100), baseline(60, 100))

    assert verdict.effect is Effect.refused
    assert verdict.label is Label.shadow


def test_neither_promotes_on_a_variation_inside_the_noise(policy):
    verdict = policy.gate(edit(), baseline(6, 10), baseline(7, 10))

    assert isinstance(verdict, Decision)
    assert verdict.label is Label.shadow


def test_a_plan_is_a_list_of_edits_in_both(policy):
    plan = policy.plan_refinement(Store(entries={family: {} for family in ALIVE}), baseline(3, 10))

    assert isinstance(plan, list)
    assert all(isinstance(proposed, Edit) for proposed in plan)


def test_a_forced_verdict_only_moves_the_double(policy):
    if policy is refinery:
        pytest.skip("la politique réelle n'a rien à scripter")
    policy.decision = Decision(effect=Effect.promoted, label=Label.active, version=2,
                               evidence=nodes(0, 1), detail="scripted")

    assert policy.gate(edit(), baseline(6, 10), baseline(7, 10)).effect is Effect.promoted


def test_signature_mutation_reaches_the_contract(monkeypatch):
    memory = load_double("refinery")
    test_both_satisfy_the_same_protocol_and_the_same_signatures(memory)
    monkeypatch.setattr(memory, "gate", lambda wrong: None)
    with pytest.raises(AssertionError):
        test_both_satisfy_the_same_protocol_and_the_same_signatures(memory)
