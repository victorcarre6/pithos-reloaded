"""Fixtures communes aux corpus de module et aux tests transverses."""

import pytest

from tests.support import load_double


@pytest.fixture
def double():
    return load_double


@pytest.fixture
def kernel_double():
    return load_double("kernel")


@pytest.fixture
def journal_double():
    return load_double("journal")
