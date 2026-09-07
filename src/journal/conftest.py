"""Fixtures partagées : le chargeur de doubles, une mission jetable, un événement valide."""

import importlib.util
from pathlib import Path

import pytest

from journal.write import bind

DOUBLES_DIR = Path(__file__).resolve().parents[2] / "tests" / "doubles"


@pytest.fixture
def double():
    "Charge un double par nom : `tests/` n'est pas un paquet importable, on passe par le chemin."

    def load(name):
        spec = importlib.util.spec_from_file_location(f"doubles_{name}", DOUBLES_DIR / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        return module

    return load


@pytest.fixture
def bound(tmp_path):
    "Lie le journal à une mission jetable et rend ses deux chemins de sortie."

    events_path = tmp_path / "missions" / "m1" / "events.jsonl"
    live_path = tmp_path / "live.log"
    bind(events_path, live_path)

    return events_path, live_path


@pytest.fixture
def an_event(double):
    "Fabrique un événement par le double de `kernel` ; le payload distingue ceux d'un même test."

    kernel = double("kernel")

    def make(**payload):
        return kernel.event(payload=payload)

    return make
