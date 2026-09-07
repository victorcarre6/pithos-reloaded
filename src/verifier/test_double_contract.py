"""Contrat partagé à déplacer dans tests/contracts/ après autorisation de périmètre."""

import importlib.util
import inspect
from pathlib import Path
import subprocess

import pytest

import verifier
from kernel.facts import RecordKey


def _load_double(name):
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(f"contract_{name}_double", root / "tests/doubles" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


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
    assert isinstance(verifier, verifier.SourceVerifier)
    assert isinstance(memory, verifier.SourceVerifier)
    for method in ("check_sources", "emit_receipt"):
        real = inspect.signature(getattr(verifier, method))
        fake = inspect.signature(getattr(memory, method))
        assert list(real.parameters) == list(fake.parameters)

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
