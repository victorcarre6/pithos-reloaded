"""Contrat du premier exécuteur de nano-étape, avant le marcheur de mission complet."""

import inspect
from pathlib import Path
import subprocess

import pytest

from engine import attempt
from engine.tree import Tree


def assert_contract(memory):
    assert isinstance(attempt, attempt.NanoEngine)
    assert isinstance(memory, attempt.NanoEngine)
    real = inspect.signature(attempt.run_attempt)
    fake = inspect.signature(memory.run_attempt)
    assert list(real.parameters) == list(fake.parameters)


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


def test_signature_mutation_reaches_the_contract(double, monkeypatch):
    memory = double("engine").MemoryEngine([])
    assert_contract(memory)
    monkeypatch.setattr(memory, "run_attempt", lambda wrong: None)
    with pytest.raises(AssertionError):
        assert_contract(memory)
