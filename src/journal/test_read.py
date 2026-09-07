"""Sens lecture — itération, lecture bornée, reprise d'identifiant, queue déchirée."""

import json

import pytest

from journal.read import generation_signature, next_event_id, read, tail, torn_tail
from kernel.contracts import Event


def a_line(event_id: int) -> bytes:
    "Ligne JSONL complète et valide, portant l'identifiant demandé."

    row = {
        "ts": "2026-09-06T18:00:00+00:00",
        "v": 1,
        "type": "status",
        "durable": True,
        "payload": {"i": event_id},
        "event_id": event_id,
    }

    return (json.dumps(row) + "\n").encode("utf-8")


def test_read_yields_every_complete_event(tmp_path):
    events_path = tmp_path / "events.jsonl"
    events_path.write_bytes(a_line(1) + a_line(2))

    events = list(read(events_path))

    assert [event.payload for event in events] == [{"i": 1}, {"i": 2}]
    assert all(isinstance(event, Event) for event in events)


def test_read_never_yields_a_torn_final_fragment(tmp_path):
    events_path = tmp_path / "events.jsonl"
    events_path.write_bytes(a_line(1) + b'{"ts": "t", "v": 1, "typ')

    assert [event.payload for event in read(events_path)] == [{"i": 1}]


def test_read_fails_closed_on_a_malformed_interior_line(tmp_path):
    events_path = tmp_path / "events.jsonl"
    events_path.write_bytes(a_line(1) + b"not json\n" + a_line(3))

    with pytest.raises(json.JSONDecodeError):
        list(read(events_path))


def test_read_of_an_absent_journal_is_empty(tmp_path):
    assert list(read(tmp_path / "absent.jsonl")) == []


def test_tail_reports_that_a_prefix_was_omitted(tmp_path):
    events_path = tmp_path / "events.jsonl"
    events_path.write_bytes(b"".join(a_line(index) for index in range(1, 6)))

    events, omitted = tail(events_path, 2)

    assert [event.payload for event in events] == [{"i": 4}, {"i": 5}]
    assert omitted is True


def test_tail_reports_no_omission_when_the_whole_journal_fits(tmp_path):
    events_path = tmp_path / "events.jsonl"
    events_path.write_bytes(a_line(1) + a_line(2))

    events, omitted = tail(events_path, 10)

    assert len(events) == 2
    assert omitted is False


def test_tail_of_zero_lines_omits_everything(tmp_path):
    events_path = tmp_path / "events.jsonl"
    events_path.write_bytes(a_line(1))

    assert tail(events_path, 0) == ([], True)


def test_next_event_id_resumes_on_a_ten_thousand_line_journal(tmp_path):
    events_path = tmp_path / "events.jsonl"
    events_path.write_bytes(b"".join(a_line(index) for index in range(1, 10_001)))

    assert next_event_id(events_path) == 10_001


def test_next_event_id_starts_at_one_on_an_absent_journal(tmp_path):
    assert next_event_id(tmp_path / "absent.jsonl") == 1


def test_torn_tail_locates_the_fragment_without_touching_the_file(tmp_path):
    events_path = tmp_path / "events.jsonl"
    complete = a_line(1)
    events_path.write_bytes(complete + b'{"ts": "t"')
    before = events_path.read_bytes()

    torn = torn_tail(events_path)

    assert (torn.offset, torn.n_bytes) == (len(complete), 10)
    assert events_path.read_bytes() == before


def test_a_complete_journal_has_no_torn_tail(tmp_path):
    events_path = tmp_path / "events.jsonl"
    events_path.write_bytes(a_line(1))

    assert torn_tail(events_path) is None
    assert torn_tail(tmp_path / "absent.jsonl") is None


def test_a_generation_signature_changes_with_the_first_line_or_the_size(tmp_path):
    events_path = tmp_path / "events.jsonl"
    events_path.write_bytes(a_line(1))
    first = generation_signature(events_path)

    events_path.write_bytes(a_line(1) + a_line(2))
    grown = generation_signature(events_path)
    events_path.write_bytes(a_line(9))
    rotated = generation_signature(events_path)

    assert grown["first_line_sha256"] == first["first_line_sha256"]
    assert grown["size"] > first["size"]
    assert rotated["first_line_sha256"] != first["first_line_sha256"]
