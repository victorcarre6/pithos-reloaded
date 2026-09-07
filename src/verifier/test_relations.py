"""Relations exécutées dans un vrai subprocess sur des copies produites par verifier."""

import ast
from pathlib import Path

import pytest

from kernel.contracts import Domain, Relation
from kernel.errors import PithosError
from verifier.domains import DOMAINS
from verifier.relations import admit, render
from verifier.runner import execute


CASES = [
    ("round_trip", ["f", "g"], "def f(x): return str(x)\ndef g(x): return int(x)\n"),
    ("idempotent", ["f"], "def f(x): return abs(x)\n"),
    ("commutes_with", ["f", "g"], "def f(x): return x + 1\ndef g(x): return x + 2\n"),
    ("preserves", ["f", "p"], "def f(x): return -x\ndef p(x): return abs(x)\n"),
    ("invariant_under", ["f", "t"], "def f(x): return abs(x)\ndef t(x): return -x\n"),
    ("monotone", ["f"], "def f(x): return x + 1\n"),
    ("total", ["f"], "def f(x): return x\n"),
    ("raises_on", ["f", "E"], "class E(ValueError): pass\ndef f(x): raise E(x)\n"),
]


@pytest.mark.parametrize("relation,symbols,source", CASES)
def test_supported_relation_executes(kernel_double, tmp_path, relation, symbols, source):
    criterion = kernel_double.criterion(relation=relation, symbols=symbols)
    result = execute(criterion, source, artifact_root=tmp_path, timeout=10)
    assert result.execution == "completed", result.diagnostic
    assert result.check == "passed", result.diagnostic
    assert result.returncode == 0
    assert result.artifact_path.read_text().startswith("# invariant")
    assert (result.artifact_path.parent / "candidate.py").read_text() == source
    assert (result.artifact_path.parent / "meta.json").is_file()


@pytest.mark.parametrize("domain", list(Domain))
def test_domains_execute_identity_round_trip(kernel_double, tmp_path, domain):
    criterion = kernel_double.criterion(relation="round_trip", symbols=["f", "g"], domain=domain)
    source = "def f(x): return x\ndef g(x): return x\n"
    result = execute(criterion, source, artifact_root=tmp_path, timeout=10)
    assert result.check == "passed", result.diagnostic
    assert set(DOMAINS) == set(Domain)


def test_round_trip_red_has_shrunk_example(kernel_double, tmp_path):
    criterion = kernel_double.criterion(relation="round_trip", symbols=["f", "g"])
    source = "def f(x): return str(x)\ndef g(x): return int(x) + 1\n"
    result = execute(criterion, source, artifact_root=tmp_path, timeout=10)
    assert result.check == "failed"
    assert result.returncode == 20
    assert "x=0" in result.diagnostic
    assert "invariant(" in result.diagnostic
    assert "x=0" in result.counterexample


def test_renderer_is_pure_and_escapes_target(kernel_double, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("render opened a file")

    monkeypatch.setattr(Path, "open", forbidden)
    criterion = kernel_double.criterion()
    script = render(criterion, Path("odd'\nname.py"))
    ast.parse(script)
    assert "odd'\\nname.py" in script


@pytest.mark.parametrize("source", [
    "def other(x): return x\n",
    "async def f(x): return x\n",
    "def f(): return 1\n",
    "def f(x, y): return x\n",
    "def f(x, *, required): return x\n",
    "def f(x): return x\nf = 42\n",
    "@decorator\ndef f(x): return x\n",
    "def f(x): return x\nasync def f(x): return x\n",
    "def f(x): return x\nfrom math import fabs as f\n",
    "def f(x): return x\nimport math as f\n",
])
def test_unusable_symbols_refused_before_execution(kernel_double, source):
    with pytest.raises(PithosError):
        admit(kernel_double.criterion(), source)


def test_schema_binding_is_explicitly_unavailable(kernel_double):
    criterion = kernel_double.criterion(relation="schema_conform")
    with pytest.raises(PithosError, match="schema_binding_missing"):
        render(criterion, Path("candidate.py"))


def test_mutated_pydantic_instance_is_revalidated(kernel_double):
    criterion = kernel_double.criterion()
    criterion.symbols[0] = "f(); injected()"
    with pytest.raises(ValueError):
        render(criterion, Path("candidate.py"))


def test_monotone_only_uses_ordered_numeric_domains(kernel_double):
    criterion = kernel_double.criterion(relation=Relation.monotone, domain=Domain.json_values)
    with pytest.raises(PithosError, match="unordered_domain"):
        render(criterion, Path("candidate.py"))


def test_nested_generator_does_not_make_outer_function_a_generator(kernel_double):
    source = "def f(x):\n    def nested():\n        yield x\n    return x\n"
    admit(kernel_double.criterion(), source)
