import pytest


@pytest.fixture
def workspace(tmp_path, kernel_double, journal_double):
    from workspace import Workspace

    return Workspace(tmp_path, view=kernel_double.MemoryCodeView({}), trace=journal_double)
