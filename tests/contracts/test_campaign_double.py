"""Corpus partagé politique/double.

Le double du journal garde en mémoire ce que le vrai journal écrit sur disque, or le magasin relit
son fichier lui-même — c'est le blocage consigné dans `STATE.md`. `DiskBackedTrace` est l'adaptateur
de test qui referme exactement cet écart, sans jamais toucher à l'implémentation du voisin.
"""

import inspect
import json

import pytest

import campaign
from campaign import Campaign, Family, Ok, Proposal, Store, Entry
from campaign.propose import Redundancy, Stage, contract_fingerprint
from campaign.stop import RECURRENCE_STOP, StopCause
from kernel.contracts import Criterion, Domain, Relation
from tests.support import load_double


PUBLIC = ("bind", "load", "put", "render_compact", "admit", "dedup", "rank", "derive", "should_stop")
CRITERION = Criterion(relation=Relation.round_trip, symbols=["dump", "load"], domain=Domain.json_values)
STAMP = "2026-09-01T00:00:00+00:00"


class DiskBackedTrace:
    "Adaptateur de test : rend durable ce que le double du journal garde en mémoire."

    def __init__(self, double, path):
        self.double = double
        self.path = path

    def emit(self, event):
        return self.double.emit(event)

    def update_json_locked(self, path, fn):
        self.double.update_json_locked(path, fn)
        path.write_text(json.dumps(self.double.json_files[path]), encoding="utf-8")


def entry(key="read_csv", family=Family.skill, **changes):
    fields = {
        "key": key, "family": family, "title": "read a csv file into rows",
        "content": "a tool that parses a csv file and returns its rows",
        "source": "model", "version": 1, "created_at": STAMP, "updated_at": STAMP,
        "reference": {"import": "tools.csv", "callable": "read"},
    }

    return Entry(**{**fields, **changes})


def proposal(**changes):
    fields = {
        "name": "read_csv", "title": "read a csv file into rows",
        "description": "a tool that parses a csv file and returns its rows",
        "evidence": ["mission-3 asked twice"], "blast_radius": "file", "source": "model",
        "module": "tools.csv", "call": "read", "arguments": ["path"],
        "template": "read_csv --path {{args.path}}", "criterion": None,
    }

    return Proposal(**{**fields, **changes})


@pytest.fixture(params=["policy", "double"])
def policy(request, tmp_path, journal_double):
    if request.param == "double":
        module = load_double("campaign")
        module.reset()

        def corrupt(family, key, raw):
            module.malformed[family][key] = raw

        yield module, corrupt

        return

    path = tmp_path / "store.json"
    campaign.bind(path, trace=DiskBackedTrace(journal_double, path))

    def corrupt(family, key, raw):
        state = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"schema": 1, "entries": {}}
        state.setdefault("entries", {}).setdefault(family.value, {})[key] = raw
        path.write_text(json.dumps({**state, "schema": 1}), encoding="utf-8")

    yield campaign, corrupt
    campaign.bind(None)


def test_both_satisfy_the_same_protocol_and_the_same_signatures(policy):
    module, _ = policy

    assert isinstance(module, Campaign)
    for name in PUBLIC:
        expected = inspect.signature(getattr(campaign, name)).parameters.keys()
        assert inspect.signature(getattr(module, name)).parameters.keys() == expected


def test_a_malformed_entry_is_ignored_without_ever_raising(policy):
    module, corrupt = policy
    module.put(Family.skill, "read_csv", entry())
    corrupt(Family.skill, "broken", {"title": 7, "content": None})
    state = module.load()

    assert set(state.entries[Family.skill]) == {"read_csv"}
    assert isinstance(state, Store)


def test_a_written_entry_comes_back_with_its_version_raised(policy):
    module, _ = policy
    for content in ("first", "second"):
        module.put(Family.memory, "note", entry(key="note", family=Family.memory, content=content))
    written = module.load().entries[Family.memory]["note"]

    assert (written.version, written.content) == (2, "second")
    assert written.created_at == STAMP


def test_the_compact_rendering_holds_its_budget_and_declares_its_omissions(policy):
    module, _ = policy
    for index in range(8):
        module.put(Family.skill, f"tool{index}", entry(key=f"tool{index}"))
    rendered = module.render_compact(Family.skill, 320)

    assert len(rendered) <= 320
    assert rendered.splitlines()[0] == "skill: 8"
    assert rendered.splitlines()[-1].endswith("more")


def test_a_lexical_duplicate_is_rejected_by_both(policy):
    module, _ = policy
    module.put(Family.skill, "read_csv", entry())
    restated = proposal(name="parse_csv", title="parse a csv file into rows",
                        description="a tool that reads a csv file and returns the rows")
    verdict = module.dedup(restated, module.load())

    assert verdict.stage is Stage.lexical
    assert verdict.key == "read_csv"


def test_a_contract_duplicate_is_rejected_by_both(policy):
    module, _ = policy
    covered = entry(key="json_codec", title="encode and decode json", content="a value into text and back",
                    reference={"import": "tools.json", "callable": "codec",
                               "contract": contract_fingerprint(CRITERION)})
    module.put(Family.skill, "json_codec", covered)
    twin = proposal(name="round_trip_json", title="verify json round tripping",
                    description="checks that dumping then loading gives back the value",
                    criterion=CRITERION)
    verdict = module.dedup(twin, module.load())

    assert verdict.stage is Stage.contract
    assert verdict.key == "json_codec"


def test_a_stop_proposal_comes_back_from_both(policy):
    module, _ = policy
    module.put(Family.skill, "read_csv", entry())
    for _ in range(RECURRENCE_STOP):
        module.put(Family.memory, "parse_json", entry(key="parse_json", family=Family.memory))
    verdict = module.should_stop(module.load())

    assert verdict.cause is StopCause.all_redundant
    assert verdict.recurring == ["parse_json"]


def test_a_forced_verdict_only_moves_the_double(policy):
    module, _ = policy
    forced = Redundancy(stage=Stage.contract, key="forced", detail="scripted", count=1)
    if module is campaign:
        pytest.skip("la politique réelle n'a rien à scripter")
    module.redundancy = forced

    assert module.dedup(proposal(), module.load()) == forced


def test_both_admit_a_well_formed_proposal_and_refuse_a_broken_one(policy):
    module, _ = policy

    assert isinstance(module.admit(proposal().model_dump(mode="json")), Ok)
    assert not isinstance(module.admit({"name": "x"}), Ok)


def test_signature_mutation_reaches_the_contract(monkeypatch):
    memory = load_double("campaign")
    policy = (memory, None)
    test_both_satisfy_the_same_protocol_and_the_same_signatures(policy)
    monkeypatch.setattr(memory, "put", lambda wrong: None)
    with pytest.raises(AssertionError):
        test_both_satisfy_the_same_protocol_and_the_same_signatures(policy)
