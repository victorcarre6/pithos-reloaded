"""Le magasin se relit sans jamais lever — corruption systématique de chaque champ."""

import json

import pytest

from campaign.store import Entry, Family, Source
from campaign import store
from kernel.errors import PithosError


VALID = {
    "title": "csv reader",
    "content": "reads a csv file into rows",
    "source": "model",
    "version": 3,
    "created_at": "2026-09-01T00:00:00+00:00",
    "updated_at": "2026-09-02T00:00:00+00:00",
    "reference": {"import": "tools.csv", "callable": "read"},
}
CORRUPTIONS = [None, 0, -1, 3.5, True, "", [], {}, {"deep": [1, {"x": None}]}, "x" * 5000]
DEGRADING = {"source", "version", "created_at", "updated_at"}


def write_state(path, families, schema=1):
    path.write_text(json.dumps({"schema": schema, "entries": families}), encoding="utf-8")


def valid_entry(**changes):
    fields = {"key": "tool", "family": Family.skill, **VALID, **changes}

    return Entry(**fields)


@pytest.mark.parametrize("corrupt", CORRUPTIONS)
@pytest.mark.parametrize("field", sorted(VALID))
def test_every_corrupted_field_is_survived(bound, field, corrupt):
    path, _ = bound
    write_state(path, {"skill": {"tool": {**VALID, field: corrupt}}})
    kept = store.load().entries[Family.skill]

    # les champs à défaut dégradent ; title et content non textuels ne laissent rien à enregistrer
    textual = isinstance(corrupt, str)
    survives = field in DEGRADING or (field == "content" and textual) or (field == "title" and textual and corrupt)
    assert set(kept) == ({"tool"} if survives else set())
    assert all(isinstance(entry, Entry) for entry in kept.values())


@pytest.mark.parametrize("families", [
    [], None, "entries", {"skill": []}, {"skill": None}, {"skill": {"tool": []}},
    {"skill": {"tool": "text"}}, {"skill": {"": VALID}}, {"unknown": {"tool": VALID}},
    {"prompt": {"tool": VALID}}, {"memory": {"note": {**VALID, "reference": None}}},
])
def test_malformed_containers_are_survived(bound, families):
    path, _ = bound
    write_state(path, families)
    state = store.load()

    assert set(state.entries) == {Family.skill, Family.memory}


@pytest.mark.parametrize("raw", [
    b"", b"{", b'{"schema": 1, "entries": {"skill": {"tool": {"title": "t"',
    b"\xff\xfe\x00binary", b"null", b"[1, 2]", b'"a string"', b'{"entries": {}}',
    b'{"schema": 2, "entries": {"skill": {"tool": {"title": "t", "content": "c"}}}}',
])
def test_unreadable_files_yield_an_empty_store(bound, raw):
    path, _ = bound
    path.write_bytes(raw)
    state = store.load()

    assert state.entries == {Family.skill: {}, Family.memory: {}}


def test_absent_file_and_unbound_store_are_empty(bound):
    assert store.load().entries[Family.skill] == {}
    store.bind(None)
    assert store.load().entries[Family.memory] == {}


def test_ignored_entry_is_journaled_with_its_reason(bound, journal_double):
    path, _ = bound
    write_state(path, {"skill": {"broken": {**VALID, "title": 7}, "tool": VALID}})
    kept = store.load().entries[Family.skill]
    payloads = [event.payload for event in journal_double.events]

    assert set(kept) == {"tool"}
    assert len(payloads) == 1
    assert payloads[0]["operation"] == "store_entry_ignored"
    assert payloads[0]["key"] == "broken"
    assert payloads[0]["reason"]


def test_unreadable_file_is_journaled_too(bound, journal_double):
    path, _ = bound
    path.write_bytes(b"{ not json")
    store.load()

    assert [event.payload["operation"] for event in journal_double.events] == ["store_read_failed"]


@pytest.mark.parametrize("reference", [
    {}, {"import": "tools.csv"}, {"callable": "read"}, {"import": "", "callable": "read"},
    {"import": "tools.csv", "callable": 7},
])
def test_a_skill_without_import_and_callable_never_enters_the_registry(bound, reference):
    path, _ = bound
    write_state(path, {"skill": {"tool": {**VALID, "reference": reference}},
                       "memory": {"note": {**VALID, "reference": reference}}})
    state = store.load()

    # la famille memory n'a pas cette exigence : une note n'est pas une capacité
    assert state.entries[Family.skill] == {}
    assert set(state.entries[Family.memory]) == {"note"}


def test_put_writes_through_the_journal_lock(bound, journal_double):
    path, _ = bound
    store.put(Family.skill, "tool", valid_entry())
    payload = journal_double.json_files[path]

    assert json.dumps(payload)  # ce qui est confié au journal est sérialisable
    assert set(store._parse(payload).entries[Family.skill]) == {"tool"}


def test_put_bumps_the_version_and_keeps_the_creation_date(bound, journal_double):
    path, _ = bound
    for content in ("first", "second", "third"):
        store.put(Family.skill, "tool", valid_entry(content=content))
    written = store._parse(journal_double.json_files[path]).entries[Family.skill]["tool"]

    assert (written.version, written.content) == (3, "third")
    assert written.created_at == VALID["created_at"]
    assert written.updated_at != VALID["updated_at"]


def test_put_preserves_the_rest_of_the_file(bound, journal_double):
    path, _ = bound
    store.put(Family.memory, "note", valid_entry(family=Family.memory))
    store.put(Family.skill, "tool", valid_entry())
    state = store._parse(journal_double.json_files[path])

    assert set(state.entries[Family.memory]) == {"note"}
    assert set(state.entries[Family.skill]) == {"tool"}


@pytest.mark.parametrize("family", [Family.prompt, Family.subagent])
def test_put_refuses_the_families_without_a_consumer(bound, family):
    with pytest.raises(PithosError) as raised:
        store.put(family, "tool", valid_entry(family=family))

    assert raised.value.field_path == "family"


def test_a_displayed_identifier_is_accepted_verbatim(bound, journal_double):
    path, _ = bound
    store.put(Family.skill, "skill:tool", valid_entry())

    assert set(store._parse(journal_double.json_files[path]).entries[Family.skill]) == {"tool"}


def test_render_compact_declares_what_it_omits(bound):
    path, _ = bound
    records = {f"tool{index}": {**VALID, "title": f"tool {index}"} for index in range(12)}
    write_state(path, {"skill": records})
    rendered = store.render_compact(Family.skill, 400)

    assert len(rendered) <= 400
    assert rendered.splitlines()[0] == "skill: 12"
    assert rendered.splitlines()[-1].endswith("more")
    assert "[skill:tool0]" in rendered


def test_render_compact_bounds_a_long_entry_visibly(bound):
    path, _ = bound
    write_state(path, {"skill": {"tool": {**VALID, "content": "long " * 400}}})
    rendered = store.render_compact(Family.skill, 4000)

    assert "…" in rendered
    assert len(rendered) < 400


def test_render_compact_shows_provenance_and_reference(bound):
    path, _ = bound
    write_state(path, {"skill": {"tool": {**VALID, "source": Source.derived.value}},
                       "memory": {"note": VALID}})

    assert "(v3, derived) ref=" in store.render_compact(Family.skill, 400)
    assert "ref=" not in store.render_compact(Family.memory, 400)
