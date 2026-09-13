"""Fixtures partagées : une mission jetable et un événement valide ; doubles hérités."""

import pytest

from journal.write import bind


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
