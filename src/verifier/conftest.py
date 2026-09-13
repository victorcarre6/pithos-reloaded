"""Fixtures verifier : contrats publics et double kernel, sans implémentation voisine."""

import pytest

from tests.support import load_double


@pytest.fixture(scope="session")
def kernel_double():
    return load_double("kernel")
