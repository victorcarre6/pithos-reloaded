"""La sensibilité aux mutations ne prouve pas le contrat numérique d'une projection.

Cas réduit de trial-44kcg6ig ; les sources archivées restent intactes dans experiments/visualizer.
"""

import ast

import pytest

from verifier.gates import check_sources
from verifier.mutation import mutants


BEFORE = "def clamp_level(level):\n    return level + 0.1\n"
COMPACT = "def clamp_level(level):\n    return max(0.0, min(1.0, level))\n"
BRANCHES = (
    "def clamp_level(level):\n"
    "    if level < 0.0:\n"
    "        return 0.0\n"
    "    if level > 1.0:\n"
    "        return 1.0\n"
    "    return level\n"
)


@pytest.mark.parametrize("source,verification,reason", [
    (COMPACT, "rejected", "tautology"),
    (BRANCHES, "passed", "verified"),
    (BRANCHES.replace("1.0", "2.0"), "passed", "verified"),
])
def test_idempotence_sensitivity_depends_on_syntax_not_exact_bounds(
    tmp_path, kernel_double, source, verification, reason,
):
    criterion = kernel_double.criterion(
        relation="idempotent", symbols=["clamp_level"], domain="floats_finite",
    )
    result = check_sources(criterion, BEFORE, source, artifact_root=tmp_path, timeout=10)
    assert result.verification == verification
    assert result.reason == reason
    assert result.before.check == "failed"
    assert result.after.check == "passed"
    assert result.effect == "unproven"
    if source == COMPACT:
        expected = [
            "def clamp_level(level): return None",
            "def clamp_level(level): return max(1.0, min(1.0, level))",
            "def clamp_level(level): return max(0.0, min(2.0, level))",
        ]
        normalized = [ast.unparse(ast.parse(text)) for text in expected]
        assert [text for _, text in mutants(source)] == normalized
        assert len(result.mutation.attempts) == 3
        assert all(attempt.result.check == "passed" for attempt in result.mutation.attempts)
    else:
        assert result.mutation.status == "killed"
        assert result.mutation.attempts[-1].result.counterexample
