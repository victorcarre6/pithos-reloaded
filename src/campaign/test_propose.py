"""La redondance en deux temps, le classement lexicographique, et le filet déterministe."""

import pytest

from campaign.admit import Ok, Proposal, admit
from campaign.propose import (
    AXES, DERIVE_AFTER, Redundancy, Signal, SignalKind, Stage, axes, contract_fingerprint,
    counters, dedup, derive, rank, related, remember, terms,
)
from campaign.store import ALIVE, Entry, Family, Source, Store
from kernel.contracts import Criterion, Domain, Relation


CRITERION = Criterion(relation=Relation.round_trip, symbols=["dump", "load"], domain=Domain.json_values)


def proposal(**changes):
    fields = {
        "name": "read_csv",
        "title": "read a csv file into rows",
        "description": "a tool that parses a csv file and returns its rows",
        "evidence": ["mission-3 asked twice for csv parsing"],
        "blast_radius": "file",
        "source": Source.model,
        "module": "tools.csv",
        "call": "read",
        "arguments": ["path"],
        "template": "read_csv --path {{args.path}}",
        "criterion": None,
    }

    return Proposal(**{**fields, **changes})


def entry(**changes):
    fields = {
        "key": "read_csv",
        "family": Family.skill,
        "title": "read a csv file into rows",
        "content": "a tool that parses a csv file and returns its rows",
        "source": Source.model,
        "version": 1,
        "created_at": "2026-09-01T00:00:00+00:00",
        "updated_at": "2026-09-01T00:00:00+00:00",
        "reference": {"import": "tools.csv", "callable": "read"},
    }

    return Entry(**{**fields, **changes})


def store_of(*entries):
    state = Store(entries={family: {} for family in ALIVE})
    for item in entries:
        state.entries[item.family][item.key] = item

    return state


def test_terms_yield_the_compound_and_each_of_its_parts():
    assert terms("read_csv rows") == ["read_csv", "read", "csv", "rows"]


@pytest.mark.parametrize("left,right,expected", [
    ("parse", "parse", True),
    ("parser", "parsers", True),
    ("render", "rendering", True),
    ("parse", "parsing", False),  # limite assumée : le préfixe diverge, ce n'est pas de la désuffixation
    ("csv", "csvs", False),
    ("read", "write", False),
    ("parse", "parsimonious", False),
])
def test_related_tolerates_inflection_but_not_a_different_word(left, right, expected):
    assert related(left, right) is expected


def test_a_lexical_restatement_is_rejected_without_any_model_call(monkeypatch):
    import httpx

    def forbidden(*args, **kwargs):
        raise AssertionError("dedup instantiated a model client")

    for name in ("Client", "AsyncClient", "post", "get", "request"):
        monkeypatch.setattr(httpx, name, forbidden)
    restated = proposal(title="parse a csv file into rows",
                        description="a tool that reads a csv file and returns the rows")
    verdict = dedup(restated, store_of(entry()))

    assert verdict.stage is Stage.lexical
    assert verdict.key == "read_csv"


def test_an_unrelated_proposal_passes_both_stages():
    unrelated = proposal(name="send_email", title="send an email through smtp",
                         description="delivers a message to a mailbox")

    assert dedup(unrelated, store_of(entry())) is None


def test_two_wordings_of_the_same_contract_are_the_same_tool():
    # le temps 2 tranche là où le lexical est aveugle : rien de commun dans les mots
    twin = proposal(name="round_trip_json", title="verify json round tripping",
                    description="checks that dumping then loading gives back the value",
                    criterion=CRITERION)
    covered = entry(key="json_codec", title="encode and decode json",
                    content="turns a value into text and back",
                    reference={"import": "tools.json", "callable": "codec",
                               "contract": contract_fingerprint(CRITERION)})
    verdict = dedup(twin, store_of(covered))

    assert verdict.stage is Stage.contract
    assert verdict.key == "json_codec"


def test_the_contract_fingerprint_ignores_key_ordering_and_nothing_else():
    other = Criterion(relation=Relation.round_trip, symbols=["load", "dump"], domain=Domain.json_values)

    assert contract_fingerprint(CRITERION) == contract_fingerprint(CRITERION)
    assert contract_fingerprint(CRITERION) != contract_fingerprint(other)
    assert contract_fingerprint(None) == ""


def test_a_proposal_without_a_criterion_is_never_caught_by_the_contract_stage():
    covered = entry(reference={"import": "tools.csv", "callable": "read", "contract": ""})

    assert dedup(proposal(name="send_email", title="send an email", description="smtp"), store_of(covered)) is None


def test_recurrence_is_counted_and_reopens_instead_of_being_discarded(bound, journal_double):
    path, _ = bound
    from campaign import store

    for _ in range(3):
        state = store.load()
        verdict = dedup(proposal(), state) or Redundancy(stage=Stage.lexical, key="read_csv",
                                                         detail="first sighting", count=1)
        remember(proposal(), verdict)
    counted = store._parse(journal_double.json_files[path]).entries[Family.memory]["read_csv"]

    assert counted.version == 3
    assert counted.source is Source.model


def test_the_ranking_is_a_lexicographic_tuple_of_named_axes():
    assert len(AXES) == len(axes(proposal()))
    assert AXES == ("blast_radius", "evidence", "source", "name")


def test_every_tie_break_is_attributable_to_one_named_axis():
    candidates = [
        proposal(name="wide_tool", blast_radius="repo"),
        proposal(name="narrow_tool", blast_radius="file"),
        proposal(name="proven_tool", evidence=["once", "twice"]),
        proposal(name="derived_tool", source=Source.derived),
        proposal(name="alpha_tool"),
    ]
    ranked = rank(candidates)
    for left, right in zip(ranked, ranked[1:]):
        differing = [index for index, pair in enumerate(zip(axes(left), axes(right))) if pair[0] != pair[1]]

        assert differing, "deux propositions indiscernables : le classement n'est pas total"
        assert AXES[differing[0]]
        assert axes(left)[differing[0]] < axes(right)[differing[0]]


def test_the_narrowest_and_best_evidenced_proposal_comes_first():
    ranked = rank([proposal(name="wide_tool", blast_radius="repo"), proposal(name="narrow_tool")])

    assert [candidate.name for candidate in ranked] == ["narrow_tool", "wide_tool"]


def test_ranking_never_reads_a_weighted_scalar():
    # deux propositions n'ayant que le dernier axe pour les séparer restent départagées par lui seul
    ranked = rank([proposal(name="b_tool"), proposal(name="a_tool")])

    assert [candidate.name for candidate in ranked] == ["a_tool", "b_tool"]


SIGNALS = [Signal(kind=SignalKind.todo, path="tools/csv.py", symbol="read_rows"),
           Signal(kind=SignalKind.untested, path="tools/json.py", symbol="dump")]


@pytest.mark.parametrize("rejections", range(DERIVE_AFTER))
def test_the_net_stays_shut_below_three_consecutive_rejections(rejections):
    assert derive(SIGNALS, rejections) == []


def test_the_net_fires_after_three_consecutive_rejections():
    derived = derive(SIGNALS, DERIVE_AFTER)

    assert len(derived) == len(SIGNALS)
    assert {candidate.source for candidate in derived} == {Source.derived}


def test_everything_the_net_emits_passes_the_admission_rules():
    for candidate in derive(SIGNALS, DERIVE_AFTER):
        assert isinstance(admit(candidate.model_dump(mode="json")), Ok)


def test_the_net_is_deterministic():
    assert derive(SIGNALS, DERIVE_AFTER) == derive(list(reversed(SIGNALS)), DERIVE_AFTER)


def test_the_two_counters_stay_separated():
    state = store_of(entry(key="from_model"), entry(key="from_net", source=Source.derived),
                     entry(key="also_net", source=Source.derived))

    assert counters(state) == {Source.model: 1, Source.derived: 2}
