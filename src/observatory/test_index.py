"""L'index se reconstruit depuis le disque, tolère les journaux abîmés et déclare ce qu'il a vu."""

from dataclasses import fields

import pytest

from observatory.api.index import build_index, mission_events, refresh, scan, segments


def test_torn_tail_does_not_prevent_the_index_from_building(logs_root, write_events, an_event):
    fragment = '{"ts": "2026'
    path = write_events("m1", [an_event(payload={"n": 1}), an_event(payload={"n": 2})], torn=fragment)
    index = build_index(logs_root)
    row = index.rows["m1"]
    offset = path.stat().st_size - len(fragment)
    assert row.n_events == 2
    assert row.anomalies == (f"torn_tail:events.jsonl:{offset}:{len(fragment)}",)


def test_an_unreadable_line_is_declared_and_the_earlier_events_are_kept(logs_root, write_events, an_event):
    path = write_events("m1", [an_event(payload={"n": 1})])
    with path.open("a", encoding="utf-8") as handle:
        handle.write("{ not json }\n")
    row = scan(path.parent)
    assert row.n_events == 1
    assert row.anomalies == ("unreadable:events.jsonl:JSONDecodeError",)


def test_segments_are_read_in_writing_order(logs_root, write_events, an_event):
    write_events("m1", [an_event(payload={"n": 1})], torn='{"partial"')
    write_events("m1", [an_event(payload={"n": 2}), an_event(payload={"n": 3})], segment=1)
    index = build_index(logs_root)
    events, anomalies = mission_events(index, "m1")
    assert index.rows["m1"].segments == 2
    assert [event.payload["n"] for event in events] == [1, 2, 3]
    assert [anomaly.split(":")[0] for anomaly in anomalies] == ["torn_tail"]


def test_the_catalogue_holds_no_event(logs_root, write_events, an_event):
    write_events("m1", [an_event(payload={"n": 1})])
    index = build_index(logs_root)
    names = {field.name for field in fields(index)}
    assert names == {"logs_root", "missions_root", "built_at", "refreshed_at", "rows", "signatures", "watch_error"}
    assert index.rows["m1"].families == {"validation": 1}
    assert [event.payload["n"] for event in mission_events(index, "m1")[0]] == [1]


def test_a_file_growing_after_the_build_is_picked_up_by_the_next_refresh(logs_root, write_events, an_event):
    write_events("m1", [an_event(payload={"n": 1})])
    index = build_index(logs_root)
    first_signature = index.signatures["m1"]
    write_events("m1", [an_event(payload={"n": 1}), an_event(payload={"n": 2})])
    refresh(index)
    assert index.rows["m1"].n_events == 2
    assert index.signatures["m1"] != first_signature


def test_an_unusable_timestamp_is_counted_without_dropping_the_event(logs_root, write_events, an_event):
    write_events("m1", [an_event(ts="hier soir"), an_event(ts="2026-09-07T10:00:00+00:00")])
    row = scan(logs_root / "missions" / "m1")
    assert row.n_events == 2
    assert row.anomalies == ("unusable_ts:1",)
    assert row.first_ts == row.last_ts == "2026-09-07T10:00:00+00:00"


def test_a_missing_missions_directory_keeps_the_index_served(logs_root, write_events, an_event):
    write_events("m1", [an_event(payload={"n": 1})])
    index = build_index(logs_root)
    (logs_root / "missions" / "m1" / "events.jsonl").unlink()
    (logs_root / "missions" / "m1").rmdir()
    (logs_root / "missions").rmdir()
    refresh(index)
    assert index.watch_error.startswith("FileNotFoundError")
    assert index.rows["m1"].n_events == 1


@pytest.mark.parametrize("mission_id", ["absente", "..", "m1/../m2"])
def test_an_unknown_mission_reads_no_event(logs_root, write_events, an_event, mission_id):
    write_events("m1", [an_event(payload={"n": 1})])
    index = build_index(logs_root)
    assert mission_events(index, mission_id) == ([], ())
    assert segments(logs_root / "missions" / mission_id) == []
