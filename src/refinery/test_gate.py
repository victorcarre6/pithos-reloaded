"""La gate d'effet, contre des baselines fabriquées : amélioration, régression, et bruit."""

import pytest

from campaign.store import Family
from kernel.contracts import Relation
from refinery.gate import (
    BASE_KEY, Baseline, Decision, Edit, Effect, Label, NodeEvidence, Z_PROMOTE, gate, refuse, z_score,
)


def nodes(green, attempted):
    verified = ["accepted"] * green + ["rejected"] * (attempted - green)

    return [NodeEvidence(node_id=f"n{index}", relation=Relation.round_trip, verification=state)
            for index, state in enumerate(verified)]


def baseline(green, attempted, **changes):
    fields = {"mission_id": "m1", "wall_seconds": 900.0, "exit_cause": "budget_exhausted",
              "nodes": nodes(green, attempted)}

    return Baseline(**{**fields, **changes})


def edit(**changes):
    fields = {"family": Family.memory, "key": "csv_lesson", "version": 2,
              "content": "csv parsing needs an explicit delimiter", "evidence": nodes(0, 1)}

    return Edit(**{**fields, **changes})


def test_the_triplet_derives_its_rate_instead_of_repeating_it():
    measured = baseline(3, 10)

    assert (measured.green, measured.attempted) == (3, 10)


def test_a_measurable_improvement_moves_the_active_label():
    verdict = gate(edit(), baseline(20, 100), baseline(60, 100))

    assert verdict.effect is Effect.promoted
    assert verdict.label is Label.active
    assert verdict.version == 2


def test_a_measurable_regression_leaves_the_label_where_it_was():
    verdict = gate(edit(), baseline(60, 100), baseline(20, 100))

    assert verdict.effect is Effect.reverted
    assert verdict.label is Label.shadow


def test_a_variation_inside_the_noise_holds_the_edit_in_shadow():
    # six verts sur dix contre sept sur dix : l'écart ne sort pas de son propre bruit
    verdict = gate(edit(), baseline(6, 10), baseline(7, 10))

    assert verdict.effect is Effect.held
    assert verdict.label is Label.shadow


@pytest.mark.parametrize("after_green,expected", [(63, Effect.held), (64, Effect.promoted)])
def test_the_threshold_is_the_noise_itself_not_a_round_number(after_green, expected):
    assert gate(edit(), baseline(50, 100), baseline(after_green, 100)).effect is expected


def test_the_same_counts_on_a_larger_sample_can_leave_the_noise():
    small = gate(edit(), baseline(6, 10), baseline(7, 10))
    large = gate(edit(), baseline(600, 1000), baseline(700, 1000))

    assert (small.effect, large.effect) == (Effect.held, Effect.promoted)


@pytest.mark.parametrize("before,after", [((0, 0), (5, 10)), ((5, 10), (0, 0)), ((10, 10), (10, 10))])
def test_an_undecidable_comparison_never_promotes(before, after):
    verdict = gate(edit(), baseline(*before), baseline(*after))

    assert verdict.effect is Effect.held
    assert z_score(baseline(*before), baseline(*after)) == 0.0


@pytest.mark.parametrize("key", [BASE_KEY, f"prompt:{BASE_KEY}"])
def test_the_base_entry_is_refused_mechanically(key):
    verdict = gate(edit(family=Family.prompt, key=key), baseline(20, 100), baseline(60, 100))

    assert verdict.effect is Effect.refused
    assert verdict.label is Label.shadow
    assert "base" in verdict.detail


@pytest.mark.parametrize("family", [Family.skill, Family.subagent])
def test_a_family_refinery_does_not_own_is_refused(family):
    assert refuse(edit(family=family))


def test_an_invalid_edit_is_recorded_and_never_fatal():
    verdict = gate(edit(family=Family.skill), baseline(20, 100), baseline(60, 100))

    assert isinstance(verdict, Decision)
    assert verdict.detail
    assert verdict.evidence == edit().evidence


def test_the_decision_moves_a_label_and_never_carries_content():
    verdict = gate(edit(), baseline(20, 100), baseline(60, 100))

    assert set(verdict.model_dump()) == {"effect", "label", "version", "evidence", "detail"}
    assert "csv parsing needs an explicit delimiter" not in verdict.model_dump_json()


def test_the_detail_states_both_sides_and_the_threshold_it_used():
    detail = gate(edit(), baseline(20, 100), baseline(60, 100)).detail

    assert "before=20/100" in detail
    assert "after=60/100" in detail
    assert str(Z_PROMOTE) in detail


def test_evidence_is_a_node_and_a_verdict_and_can_never_be_a_rationale():
    with pytest.raises(ValueError):
        NodeEvidence(node_id="n1", relation=Relation.round_trip, verification="rejected",
                     rationale="the model thinks the prompt was unclear")
    with pytest.raises(ValueError):
        NodeEvidence(node_id="n1", relation=Relation.round_trip, verification="the model was unsure")


def test_an_edit_without_evidence_does_not_exist():
    with pytest.raises(ValueError):
        edit(evidence=[])


def test_the_decision_round_trips_through_json():
    verdict = gate(edit(), baseline(20, 100), baseline(60, 100))

    assert Decision.model_validate_json(verdict.model_dump_json()) == verdict
