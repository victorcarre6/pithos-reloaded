"""Corpus partagé journal/double : la même durabilité vue des deux côtés de la frontière.

Le double n'ouvre aucun fichier ; le vrai journal en ouvre deux. Ce qui doit coïncider est le
**contrat** : la même signature, le même ordre d'événements relus, le même `False` quand l'écriture
n'a pas eu lieu, et la même numérotation reprise.
"""

import inspect
import json
from typing import NamedTuple

import pytest

import journal
from journal import Journal


class Durable(NamedTuple):
    """Un côté de la frontière : le module, ses chemins, et de quoi relire ce qu'il a écrit."""

    module: object
    events_path: object
    kernel: object
    state_path: object
    read_state: object


@pytest.fixture(params=["journal", "double"])
def durable(request, tmp_path, double, kernel_double):
    "Rend le module à éprouver, son chemin d'événements, et de quoi relire son état JSON."

    events_path = tmp_path / "missions" / "m1" / "events.jsonl"
    state_path = tmp_path / "state.json"
    if request.param == "double":
        module = double("journal")
        module.reset()
        read_state = lambda: module.json_files[state_path]
    else:
        module = journal
        read_state = lambda: json.loads(state_path.read_text(encoding="utf-8"))

    module.bind(events_path, tmp_path / "live.log")

    return Durable(module, events_path, kernel_double, state_path, read_state)


def test_both_satisfy_the_same_protocol_and_the_same_signatures(durable):
    module = durable.module

    assert isinstance(module, Journal)
    for name in Journal.__protocol_attrs__:
        expected = list(inspect.signature(getattr(journal, name)).parameters)
        assert list(inspect.signature(getattr(module, name)).parameters) == expected


def test_an_emitted_event_comes_back_in_the_order_it_was_written(durable):
    module, events_path, kernel = durable.module, durable.events_path, durable.kernel
    written = [kernel.event(payload={"n": index}) for index in range(3)]
    for event in written:
        assert module.emit(event) is True

    assert [event.payload["n"] for event in module.read(events_path)] == [0, 1, 2]


def test_the_numbering_resumes_where_the_writing_stopped(durable):
    module, events_path, kernel = durable.module, durable.events_path, durable.kernel
    assert module.next_event_id(events_path) == 1
    module.emit(kernel.event(payload={"n": 0}))

    assert module.next_event_id(events_path) == 2


def test_a_tail_says_when_it_omitted_a_prefix(durable):
    module, events_path, kernel = durable.module, durable.events_path, durable.kernel
    for index in range(4):
        module.emit(kernel.event(payload={"n": index}))
    kept, omitted = module.tail(events_path, 2)

    assert [event.payload["n"] for event in kept] == [2, 3]
    assert omitted is True


def test_a_failed_write_returns_false_and_never_raises(durable, monkeypatch):
    module, kernel = durable.module, durable.kernel
    if module is journal:
        # côté réel, la panne se joue sur la syscall : la garde est la même, la cause diffère
        monkeypatch.setattr(journal.write, "_write_once", lambda fd, data: False)
    else:
        module.disk_full = True

    assert module.emit(kernel.event(payload={"n": 0})) is False


def test_a_locked_json_update_reads_the_state_it_writes_over(durable):
    # la mutation lit ce qui est déjà là : sans cela, deux écrivains concurrents se perdent
    durable.module.update_json_locked(durable.state_path, lambda data: {**data, "seen": 1})
    durable.module.update_json_locked(durable.state_path, lambda data: {**data, "seen": data["seen"] + 1})

    assert durable.read_state()["seen"] == 2


def test_signature_mutation_reaches_the_contract(double, monkeypatch):
    memory = double("journal")
    durable = Durable(memory, None, None, None, None)
    test_both_satisfy_the_same_protocol_and_the_same_signatures(durable)
    monkeypatch.setattr(memory, "emit", lambda wrong: None)
    with pytest.raises(AssertionError):
        test_both_satisfy_the_same_protocol_and_the_same_signatures(durable)
