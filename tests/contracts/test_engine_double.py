"""Contrats partagés de nano-étape, marcheur, enveloppe et finalisation."""

import inspect
from pathlib import Path
import subprocess

import pytest

from engine import attempt
from engine.tree import Tree


def call_shape(method):
    parameters = inspect.signature(method).parameters.values()

    return [(p.name, p.kind, p.default) for p in parameters if p.name != "self"]


def assert_contract(memory):
    from engine import flow, walk

    for contract, real, name in (
        (attempt.NanoEngine, attempt, "run_attempt"),
        (walk.Walker, walk, "walk"),
        (flow.MissionRunner, flow, "mission"),
    ):
        assert isinstance(real, contract)
        assert isinstance(memory, contract)
        expected = call_shape(getattr(contract, name))
        assert call_shape(getattr(real, name)) == expected
        assert call_shape(getattr(memory, name)) == expected


def test_nano_engine_replays_an_independent_tree_without_io(kernel_double, double, monkeypatch):
    tree = Tree(mission_id="audio", nodes=(kernel_double.node(),), cap_children=2)
    memory = double("engine").MemoryEngine([tree])
    assert_contract(memory)

    def forbidden(*args, **kwargs):
        raise AssertionError("double performed I/O")

    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    result = memory.run_attempt(tree, "node-1", None, None, tree_path=Path("tree.json"),
                                artifact_root=Path("proof"), system="", instruction="", attempt=1)
    assert result == tree
    assert result is not tree


@pytest.mark.parametrize("name", ["run_attempt", "walk", "mission"])
def test_signature_mutation_reaches_the_contract(double, monkeypatch, name):
    memory = double("engine").MemoryEngine([])
    assert_contract(memory)
    monkeypatch.setattr(memory, name, lambda wrong: None)
    with pytest.raises(AssertionError):
        assert_contract(memory)


@pytest.mark.parametrize("name", ["walk", "mission"])
def test_mission_ports_replay_an_independent_tree_without_io(kernel_double, double, monkeypatch, name):
    tree = Tree(mission_id="audio", nodes=(kernel_double.node(),), cap_children=2)
    memory = double("engine").MemoryEngine([tree])
    assert_contract(memory)

    def forbidden(*args, **kwargs):
        raise AssertionError("double performed I/O")

    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    result = getattr(memory, name)(tree, None, None)
    assert result == tree
    assert result is not tree


def test_keyword_only_drift_is_detected(double, monkeypatch):
    memory = double("engine").MemoryEngine([])

    def keyword_only(tree, budget, *, deps):
        pass

    monkeypatch.setattr(memory, "walk", keyword_only)
    with pytest.raises(AssertionError):
        assert_contract(memory)


def assert_finalizer_contract(memory):
    from broker import GreenFinalizer as Publication
    from engine.walk import GreenFinalizer

    assert isinstance(memory, GreenFinalizer)
    for name in ("reconcile", "finalize"):
        expected = call_shape(getattr(GreenFinalizer, name))
        assert call_shape(getattr(Publication, name)) == expected
        assert call_shape(getattr(memory, name)) == expected


@pytest.mark.parametrize("owner", ["engine", "broker"])
@pytest.mark.parametrize("name", ["reconcile", "finalize"])
def test_finalizer_signatures_detect_drift_in_both_doubles(kernel_double, double, monkeypatch, owner, name):
    memory = double(owner)
    result = kernel_double.repo_fact()
    fake = memory.MemoryFinalizer([result]) if owner == "engine" else memory.MemoryGreenFinalizer(result)
    assert_finalizer_contract(fake)
    monkeypatch.setattr(fake, name, lambda wrong: None)
    with pytest.raises(AssertionError):
        assert_finalizer_contract(fake)
