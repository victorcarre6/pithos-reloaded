"""Fixtures verifier : contrats publics et double kernel, sans implémentation voisine."""

import importlib.util
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def kernel_double():
    path = Path(__file__).resolve().parents[2] / "tests/doubles/kernel.py"
    spec = importlib.util.spec_from_file_location("verifier_kernel_double", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


@pytest.fixture
def journal_double():
    path = Path(__file__).resolve().parents[2] / "tests/doubles/journal.py"
    spec = importlib.util.spec_from_file_location("verifier_journal_double", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module
