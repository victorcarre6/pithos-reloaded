"""Doubles de dépendances chargés sans modifier le reste du dépôt."""


import pytest


@pytest.fixture
def trace(double):
    return double("journal")
