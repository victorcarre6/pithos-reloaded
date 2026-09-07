"""Double gate sur sources fournies ; le passage de cette gate n'émet aucun reçu."""

import pytest

from verifier.gates import check_sources, cmp_outcome


GOOD = "def f(x): return x + 1\ndef g(x): return x - 1\n"
BAD = "def f(x): return x + 2\ndef g(x): return x - 1\n"


def test_red_before_green_after_and_kill(kernel_double, tmp_path):
    criterion = kernel_double.criterion(relation="round_trip", symbols=["f", "g"])
    result = check_sources(criterion, BAD, GOOD, artifact_root=tmp_path, timeout=10)
    assert result.verification == "passed"
    assert result.reason == "verified"
    assert result.before.check == "failed"
    assert result.after.check == "passed"
    assert result.mutation.status == "killed"
    assert result.after == result.mutation.baseline


def test_green_before_rejected_without_testing_after(kernel_double, tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("tested after an already green baseline")

    monkeypatch.setattr("verifier.gates.kill_check", forbidden)
    criterion = kernel_double.criterion(relation="round_trip", symbols=["f", "g"])
    result = check_sources(criterion, GOOD, GOOD + "\n", artifact_root=tmp_path, timeout=10)
    assert result.verification == "rejected"
    assert result.reason == "before_green"
    assert result.after is None
    assert result.mutation is None


def test_tautology_is_rejected(kernel_double, tmp_path):
    criterion = kernel_double.criterion()
    result = check_sources(criterion, "def f(x): raise ValueError(x)", "def f(x): return x + 1",
                           artifact_root=tmp_path, timeout=10)
    assert result.verification == "rejected"
    assert result.reason == "tautology"
    assert result.mutation.status == "survived"


def test_after_still_red_is_rejected(kernel_double, tmp_path):
    criterion = kernel_double.criterion(relation="round_trip", symbols=["f", "g"])
    result = check_sources(criterion, BAD, BAD + "\n", artifact_root=tmp_path, timeout=10)
    assert result.verification == "rejected"
    assert result.reason == "after_red"


def test_before_tool_failure_cannot_establish_red(kernel_double, tmp_path):
    criterion = kernel_double.criterion(relation="round_trip", symbols=["f", "g"])
    result = check_sources(criterion, "raise SystemExit(127)\n" + GOOD, GOOD, artifact_root=tmp_path, timeout=10)
    assert result.verification == "blocked"
    assert result.reason == "before_unverifiable"
    assert result.after is None


def test_after_tool_failure_blocks(kernel_double, tmp_path):
    criterion = kernel_double.criterion(relation="round_trip", symbols=["f", "g"])
    result = check_sources(criterion, BAD, "raise SystemExit(127)\n" + GOOD, artifact_root=tmp_path, timeout=10)
    assert result.verification == "blocked"
    assert result.reason == "mutation_unavailable"


def test_identical_sources_are_rejected_without_io(kernel_double, tmp_path):
    result = check_sources(kernel_double.criterion(), GOOD, GOOD, artifact_root=tmp_path, timeout=10)
    assert result.verification == "rejected"
    assert result.reason == "unchanged_source"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("code,expected", [
    (0, "equal"), (1, "different"), (2, "tool_error"), (127, "tool_error"),
    (None, "tool_error"), (-9, "tool_error"), (True, "tool_error"), ("0", "tool_error"),
])
def test_cmp_exit_semantics(code, expected):
    assert cmp_outcome(code) == expected
