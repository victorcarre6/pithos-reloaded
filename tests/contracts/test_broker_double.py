"""Contrat partagé implémentation ↔ double."""

import inspect
from pathlib import Path

import pytest

import broker
from broker import Broker
from kernel.errors import Cause, PithosError
from kernel.facts import FileFact

MEMBERS = ("repo_fact", "preflight", "commit", "open_pr", "automerge", "notify", "poll")


@pytest.fixture
def memory(double):
    "Le double chargé et remis à neuf ; son état de module survivrait d'un test à l'autre."

    module = double("broker")
    module.reset()

    return module


@pytest.fixture
def file_fact():
    return FileFact(
        path=Path("src/pithos/tool.py"),
        sha_before="a" * 64,
        sha_after="b" * 64,
        spliced_range=(4, 9),
        n_replacements=1,
    )


def test_both_satisfy_the_same_protocol(memory):
    assert isinstance(broker, Broker)
    assert isinstance(memory, Broker)


def test_both_share_every_public_signature(memory):
    for name in MEMBERS:
        # les paramètres d'injection sont keyword-only : ils ne font pas partie du contrat
        real = [parameter for parameter in inspect.signature(getattr(broker, name)).parameters.values()
                if parameter.kind is not parameter.KEYWORD_ONLY]
        fake = list(inspect.signature(getattr(memory, name)).parameters.values())
        assert [parameter.name for parameter in real] == [parameter.name for parameter in fake], name


def test_the_double_plays_a_repo_fact_agreeing_with_a_file_fact(memory, file_fact):
    memory.agree_with(file_fact)
    fact = memory.repo_fact(Path("/campaign"))
    assert [change.path for change in fact.changes] == [file_fact.path]


def test_the_double_plays_a_repo_fact_contradicting_a_file_fact(memory, file_fact):
    memory.contradict(file_fact)
    assert memory.repo_fact(Path("/campaign")).changes == []


def test_the_double_plays_a_dirty_repository_at_preflight(memory, file_fact):
    memory.agree_with(file_fact)
    with pytest.raises(PithosError) as failure:
        memory.preflight(Path("/campaign"))
    assert failure.value.cause is Cause.invariant_failed
    assert "tool.py" in failure.value.detail


def test_the_double_plays_a_transport_failure_then_a_retry(memory):
    memory.transport_down = True
    assert memory.notify("mission verte", "clé-1") is False
    assert memory.outgoing == []

    memory.transport_down = False
    assert memory.notify("mission verte", "clé-1") is True
    assert memory.notify("mission verte", "clé-1") is True
    assert memory.outgoing == [("mission verte", "clé-1")]


def test_the_double_commits_only_the_designated_paths(memory, file_fact):
    memory.changes[:] = [
        memory.Change(status=" M", path=Path("wanted.py"), origin=None),
        memory.Change(status=" M", path=Path("unwanted.py"), origin=None),
    ]
    memory.commit(Path("/campaign"), [Path("wanted.py")], "broker: chemin désigné")
    assert memory.history[-1]["paths"] == ["wanted.py"]
    assert [str(change.path) for change in memory.changes] == ["unwanted.py"]


def test_the_double_refuses_automerge_on_a_red_gate(memory):
    pull = memory.open_pr(Path("/campaign"), "work", "titre")
    memory.green = False
    with pytest.raises(PithosError):
        memory.automerge(pull)
    assert memory.merged == []


def test_signature_mutation_reaches_the_contract(memory, monkeypatch):
    test_both_share_every_public_signature(memory)
    monkeypatch.setattr(memory, "repo_fact", lambda wrong: None)
    with pytest.raises(AssertionError):
        test_both_share_every_public_signature(memory)
