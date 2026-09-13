"""Admission sans artefact avant toute proposition ou mutation de la cible."""

from pathlib import Path
import subprocess

import pytest

import verifier
from kernel.errors import PithosError


@pytest.mark.parametrize("relation,domain,source,valid", [
    ("idempotent", "floats_finite", "def f(x): return x + 0.1", True),
    ("schema_conform", "json_values", "def f(x): return x", False),
    ("monotone", "json_values", "def f(x): return x", False),
    ("total", "small_ints", "def other(x): return x", False),
])
def test_preflight_and_double_reject_before_io(kernel_double, double, monkeypatch, relation, domain, source, valid):
    criterion = kernel_double.criterion(relation=relation, symbols=["f"], domain=domain)
    memory = double("verifier").MemoryVerifier([])

    def forbidden(*args, **kwargs):
        raise AssertionError("admission performed I/O")

    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    for frontier in (verifier, memory):
        if valid:
            assert frontier.preflight(criterion, source) is None
        else:
            with pytest.raises(PithosError):
                frontier.preflight(criterion, source)
