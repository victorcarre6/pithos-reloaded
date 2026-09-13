"""La proposition d'arrêt : taxonomie fermée, et une raison qui énumère ce qui a été examiné."""

import pytest

from campaign.stop import RECURRENCE_STOP, StopCause, StopProposal, should_stop
from campaign.store import ALIVE, Entry, Family, Source, Store


def entry(key, family, version):
    return Entry(key=key, family=family, title=f"the {key} tool", content=f"what {key} does",
                 source=Source.model, version=version,
                 created_at="2026-09-01T00:00:00+00:00", updated_at="2026-09-01T00:00:00+00:00",
                 reference={"import": f"tools.{key}", "callable": "run"})


def store_of(*entries):
    state = Store(entries={family: {} for family in ALIVE})
    for item in entries:
        state.entries[item.family][item.key] = item

    return state


def test_the_taxonomy_is_closed_and_names_the_two_failure_modes_of_v1():
    assert {member.value for member in StopCause} == {
        "no_proposal", "all_redundant", "planner_churn", "stagnation", "budget_exhausted"}


def test_an_empty_store_never_proposes_a_stop():
    assert should_stop(store_of()) is None


def test_a_store_that_still_learns_never_proposes_a_stop():
    state = store_of(entry("read_csv", Family.skill, 1), entry("parse_json", Family.memory, 2))

    assert should_stop(state) is None


def test_a_duplicate_rejected_three_times_rises_into_the_stop_proposal():
    state = store_of(entry("read_csv", Family.skill, 1),
                     entry("parse_json", Family.memory, RECURRENCE_STOP))
    verdict = should_stop(state)

    assert verdict.cause is StopCause.all_redundant
    assert verdict.recurring == ["parse_json"]


def test_recurrences_rise_most_seen_first():
    state = store_of(entry("read_csv", Family.skill, 1),
                     entry("seen_thrice", Family.memory, 3),
                     entry("seen_five", Family.memory, 5),
                     entry("seen_four", Family.memory, 4),
                     entry("seen_once", Family.memory, 1))

    assert should_stop(state).recurring == ["seen_five", "seen_four", "seen_thrice"]


def test_a_campaign_that_never_built_anything_says_so():
    state = store_of(entry("parse_json", Family.memory, RECURRENCE_STOP))
    verdict = should_stop(state)

    assert verdict.cause is StopCause.no_proposal
    assert verdict.examined[Family.skill] == 0


def test_the_reason_enumerates_what_was_examined():
    # un arrêt qui ne dit pas ce qu'il a couvert n'est pas auditable
    state = store_of(entry("read_csv", Family.skill, 1), entry("dump_json", Family.skill, 2),
                     entry("parse_json", Family.memory, RECURRENCE_STOP))
    verdict = should_stop(state)

    assert verdict.examined == {Family.skill: 2, Family.memory: 1}
    assert "skill=2" in verdict.detail
    assert "memory=1" in verdict.detail
    assert "parse_json" in verdict.detail


def test_the_proposal_round_trips_through_json():
    state = store_of(entry("parse_json", Family.memory, RECURRENCE_STOP))
    verdict = should_stop(state)

    assert StopProposal.model_validate_json(verdict.model_dump_json()) == verdict


@pytest.mark.parametrize("version", range(1, RECURRENCE_STOP))
def test_below_the_threshold_nothing_rises(version):
    assert should_stop(store_of(entry("parse_json", Family.memory, version))) is None
