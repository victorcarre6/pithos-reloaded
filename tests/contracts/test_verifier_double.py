"""Contrat partagé entre implémentation et double."""

import inspect
from pathlib import Path
import subprocess

import pytest

import verifier
from kernel.facts import RecordKey
from tests.support import load_double as _load_double


@pytest.mark.parametrize("kind,relation,symbols,before,after,expected", [
    ("green", "round_trip", ["f", "g"], "def f(x): return x + 2\ndef g(x): return x - 1", "def f(x): return x + 1\ndef g(x): return x - 1", "passed"),
    ("red", "round_trip", ["f", "g"], "def f(x): return x + 2\ndef g(x): return x - 1", "def f(x): return x + 3\ndef g(x): return x - 1", "rejected"),
    ("tautology", "total", ["f"], "def f(x): raise ValueError(x)", "def f(x): return x + 1", "rejected"),
    ("blocked", "total", ["f"], "raise SystemExit(127)\ndef f(x): return x", "def f(x): return x", "blocked"),
])
def test_same_protocol_and_scenarios(tmp_path, monkeypatch, kind, relation, symbols, before, after, expected):
    kernel = _load_double("kernel")
    journal = _load_double("journal")
    memory_module = _load_double("verifier")
    criterion = kernel.criterion(relation=relation, symbols=symbols)
    actual = verifier.check_sources(criterion, before, after, artifact_root=tmp_path, timeout=10)
    assert actual.verification == expected
    if kind == "red":
        assert actual.after.counterexample
    if kind == "tautology":
        assert actual.reason == "tautology"
    key = RecordKey(kind="verification", value=("mission-1", "node-1", 1, relation))
    memory = memory_module.MemoryVerifier([(criterion, actual)], [(key, None)])
    assert_protocol_and_signatures(memory)

    # aucun accès disque ni lancement, y compris avec un faux reçu absent
    def forbidden(*args, **kwargs):
        raise AssertionError("double performed I/O")

    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    replay = memory.check_sources(criterion, before, after, artifact_root=tmp_path, timeout=10)
    assert replay == actual
    assert replay is not actual
    assert memory.emit_receipt("node-1", 1, [], Path("artifact.py"), key=key, verdict=actual, journal=journal) is None


def test_double_rejects_unscripted_criterion(tmp_path):
    kernel_double = _load_double("kernel")
    memory = _load_double("verifier").MemoryVerifier([])
    with pytest.raises(KeyError):
        memory.check_sources(kernel_double.criterion(), "before", "after", artifact_root=tmp_path, timeout=10)


def assert_protocol_and_signatures(memory):
    assert isinstance(verifier, verifier.Verifier)
    assert isinstance(memory, verifier.Verifier)
    for method in ("preflight", "check_sources", "run", "emit_receipt"):
        real = inspect.signature(getattr(verifier, method))
        fake = inspect.signature(getattr(memory, method))
        assert list(real.parameters) == list(fake.parameters)


def test_signature_mutation_reaches_the_contract(monkeypatch):
    memory = _load_double("verifier").MemoryVerifier([])
    assert_protocol_and_signatures(memory)
    monkeypatch.setattr(memory, "check_sources", lambda wrong: None)
    with pytest.raises(AssertionError):
        assert_protocol_and_signatures(memory)


def assert_command_executors(memory):
    from lifecycle.execution import run_command
    from verifier.runner import local_command

    expected = inspect.signature(verifier.CommandExecutor.__call__)
    expected = expected.replace(parameters=list(expected.parameters.values())[1:])
    for executor in (local_command, run_command, memory):
        assert isinstance(executor, verifier.CommandExecutor)
        assert inspect.signature(executor) == expected


def test_command_executor_signatures():
    assert_command_executors(_load_double("verifier").MemoryCommandExecutor())


def test_command_executor_signature_mutation(monkeypatch):
    memory = _load_double("verifier")
    assert_command_executors(memory.MemoryCommandExecutor())
    monkeypatch.setattr(memory.MemoryCommandExecutor, "__call__", lambda self, wrong: 0)
    with pytest.raises(AssertionError):
        assert_command_executors(memory.MemoryCommandExecutor())


def test_command_executor_double_does_not_launch(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("double performed I/O")

    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    memory = _load_double("verifier").MemoryCommandExecutor(20)
    assert memory(["program"], directory=tmp_path, environment={}, timeout=1) == 20
    assert memory.calls == [(["program"], tmp_path, {}, 1)]
