import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def kernel_double():
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("workspace_kernel_double", root / "tests/doubles/kernel.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


@pytest.fixture
def journal_double():
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("workspace_journal_double", root / "tests/doubles/journal.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


@pytest.fixture
def workspace(tmp_path, kernel_double, journal_double):
    from workspace import Workspace

    return Workspace(tmp_path, view=kernel_double.MemoryCodeView({}), trace=journal_double)
