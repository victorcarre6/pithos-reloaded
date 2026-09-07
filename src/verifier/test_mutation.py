"""Un kill exige un contre-exemple, jamais une erreur de compilation ou d'outillage."""

import ast

import pytest

from verifier.mutation import kill_check, mutants


SOURCE = "def f(x):\n    if x < 0:\n        return x + 1\n    return x - 1\n"


def test_five_operators_produce_distinct_compilable_mutants():
    generated = list(mutants(SOURCE))
    names = {name.split(":")[0] for name, _ in generated}
    assert names == {"return_none", "invert_if", "swap_arithmetic", "flip_compare", "shift_number"}
    normalized = ast.unparse(ast.parse(SOURCE))
    assert len({source for _, source in generated}) == len(generated)
    for name, source in generated:
        ast.parse(source)
        compile(source, name, "exec")
        assert source != normalized
    assert list(mutants(SOURCE)) == generated


def test_mutations_do_not_change_signature_or_module_constants():
    source = "LIMIT = 10\ndef f(x: int = 2, *, flag=True) -> int:\n    return x + 1\n"
    original = ast.parse(source)
    for _, mutated in mutants(source):
        tree = ast.parse(mutated)
        assert ast.dump(tree.body[0]) == ast.dump(original.body[0])
        assert ast.dump(tree.body[1].args) == ast.dump(original.body[1].args)
        assert ast.dump(tree.body[1].returns) == ast.dump(original.body[1].returns)


def test_nested_definition_signature_is_preserved():
    source = "def f(x):\n    def nested(y: int = 2):\n        return y + 3\n    return x + 1\n"
    nested = ast.parse(source).body[0].body[0]
    for _, mutated in mutants(source):
        definition = ast.parse(mutated).body[0].body[0]
        assert ast.dump(definition) == ast.dump(nested)


def test_round_trip_kills_mutant(kernel_double, tmp_path):
    criterion = kernel_double.criterion(relation="round_trip", symbols=["f", "g"])
    report = kill_check(criterion, "def f(x): return x + 1\ndef g(x): return x - 1\n",
                        artifact_root=tmp_path, timeout=10)
    assert report.status == "killed"
    assert report.baseline.check == "passed"
    assert any(attempt.result.check == "failed" for attempt in report.attempts)
    assert all(attempt.result.artifact_path.is_file() for attempt in report.attempts)


def test_tautology_survives_all_mutations(kernel_double, tmp_path):
    criterion = kernel_double.criterion(relation="total", symbols=["f"])
    report = kill_check(criterion, "def f(x): return x + 1\n", artifact_root=tmp_path, timeout=10)
    assert report.status == "survived"
    assert report.attempts
    assert all(attempt.result.check == "passed" for attempt in report.attempts)


def test_invalid_mutant_is_not_a_kill(kernel_double, tmp_path, monkeypatch):
    monkeypatch.setattr("verifier.mutation.mutants", lambda source: iter([("bad", "def f(:")]))
    report = kill_check(kernel_double.criterion(), "def f(x): return x + 1\n", artifact_root=tmp_path, timeout=10)
    assert report.status == "blocked"
    assert report.reason == "execution_failure"
    assert report.attempts[0].result.check == "not_run"


def test_mutant_launch_failure_is_not_a_kill(kernel_double, tmp_path, monkeypatch):
    source = "raise SystemExit(127)\ndef f(x): return x\n"
    monkeypatch.setattr("verifier.mutation.mutants", lambda original: iter([("bad", source)]))
    report = kill_check(kernel_double.criterion(), "def f(x): return x + 1\n", artifact_root=tmp_path, timeout=10)
    assert report.status == "blocked"
    assert report.reason == "execution_failure"


def test_non_green_baseline_never_mutated(kernel_double, tmp_path, monkeypatch):
    def forbidden(source):
        raise AssertionError("mutated a failing baseline")

    monkeypatch.setattr("verifier.mutation.mutants", forbidden)
    report = kill_check(kernel_double.criterion(), "def f(x): raise ValueError(x)\n", artifact_root=tmp_path, timeout=10)
    assert report.status == "blocked"
    assert report.reason == "baseline_not_green"
    assert report.attempts == ()


def test_zero_mutants_is_not_evidence_of_sensitivity(kernel_double, tmp_path):
    report = kill_check(kernel_double.criterion(), "def f(x): pass\n", artifact_root=tmp_path, timeout=10)
    assert report.status == "blocked"
    assert report.reason == "no_mutants"


def test_mutation_budget_is_shared(kernel_double, tmp_path, monkeypatch):
    source = "while True: pass\ndef f(x): return x\n"
    monkeypatch.setattr("verifier.mutation.mutants", lambda original: iter([("loop", source)]))
    report = kill_check(kernel_double.criterion(), "def f(x): return x\n", artifact_root=tmp_path, timeout=0.8)
    assert report.status == "blocked"
    assert report.attempts[0].result.execution == "timed_out"


def test_mutant_limit_cannot_mean_tautology(kernel_double, tmp_path, monkeypatch):
    monkeypatch.setattr("verifier.mutation.MAX_MUTANTS", 1)
    report = kill_check(kernel_double.criterion(), SOURCE, artifact_root=tmp_path, timeout=10)
    assert report.status == "blocked"
    assert report.reason == "mutant_limit"
