"""Projection exacte sur [0, 1] : constantes, bornes voisines et arrondis sont refusés."""

from pathlib import Path

import pytest

from kernel.errors import PithosError
from verifier.gates import check_sources
from verifier.relations import render
from verifier.runner import execute


COMPACT = "def f(x): return max(0.0, min(1.0, x))\n"
BRANCHES = (
    "def f(x):\n"
    "    if x < 0.0:\n"
    "        return 0.0\n"
    "    if x > 1.0:\n"
    "        return 1.0\n"
    "    return x\n"
)


@pytest.mark.parametrize("source", [COMPACT, BRANCHES])
def test_projection_passes_both_spellings_and_kills_a_mutant(kernel_double, tmp_path, source):
    criterion = kernel_double.criterion(relation="unit_projection", domain="floats_finite")
    result = check_sources(criterion, "def f(x): return x + 0.1", source,
                           artifact_root=tmp_path, timeout=10)
    assert result.verification == "passed", result
    assert result.before.check == "failed"
    assert result.after.check == "passed"
    assert result.mutation.status == "killed"
    assert result.mutation.attempts[-1].result.check == "failed"
    assert result.mutation.attempts[-1].result.counterexample


@pytest.mark.parametrize("expression", [
    "None", "0.0", "1.0", "0.5", "x", "abs(x)",
    "max(0.0, min(2.0, x))",
    "max(-1.0, min(1.0, x))",
    "round(max(0.0, min(1.0, x)))",
    "max(0.0, min(1.0, x)) / 2.0",
    "0.5 if x < 0.0 or x > 1.0 else x",
    "False if x < 0.0 else True if x > 1.0 else x",
    "float('nan')", "float('inf')", "str(x)",
    "0.0 if 0.0 < x < 1e-300 else max(0.0, min(1.0, x))",
    "1.0 if 0.9999999999999999 <= x <= 1.0 else max(0.0, min(1.0, x))",
    "x if 1.0 < x <= 1.0000000000000002 else max(0.0, min(1.0, x))",
    "x if -5e-324 <= x < 0.0 else max(0.0, min(1.0, x))",
])
def test_projection_rejects_incorrect_or_non_numeric_outputs(kernel_double, tmp_path, expression):
    criterion = kernel_double.criterion(relation="unit_projection", domain="floats_finite")
    source = f"def f(x): return {expression}\n"
    result = execute(criterion, source, artifact_root=tmp_path, timeout=5)
    assert result.execution == "completed", result.diagnostic
    assert result.check == "failed"
    assert result.returncode == 20
    assert result.counterexample


@pytest.mark.parametrize("domain", ["small_ints", "text_unicode", "json_values", "paths"])
def test_projection_refuses_domains_without_the_finite_float_contract(kernel_double, domain):
    criterion = kernel_double.criterion(relation="unit_projection", domain=domain)
    with pytest.raises(PithosError, match="projection_requires_finite_floats"):
        render(criterion, Path("candidate.py"))
