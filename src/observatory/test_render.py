"""L'arbre aplati conserve la parenté, sépare les durées et montre ce qu'il a redressé."""

from observatory.api.index import MissionRow
from observatory.api.render import flatten_tree, status_text, window


def test_the_tree_is_flattened_depth_first_with_parentage(node_event, moment):
    events = [
        node_event("root", at=moment(0)),
        node_event("a", at=moment(1), parent_id="root", depth=1),
        node_event("a1", at=moment(2), parent_id="a", depth=2),
        node_event("b", at=moment(3), parent_id="root", depth=1),
    ]
    rows, anomalies = flatten_tree(events)
    assert [(row.node_id, row.depth) for row in rows] == [("root", 0), ("a", 1), ("a1", 2), ("b", 1)]
    assert [row.parent_id for row in rows] == [None, "root", "a", "root"]
    assert anomalies == []


def test_a_duplicated_id_never_becomes_a_second_node(node_event, moment):
    events = [
        node_event("root", at=moment(0)),
        node_event("a", at=moment(1), parent_id="root", depth=1),
        node_event("a", at=moment(2), parent_id="other", depth=1),
    ]
    rows, anomalies = flatten_tree(events)
    assert [row.node_id for row in rows] == ["root", "a"]
    assert rows[1].parent_id == "root"
    assert rows[1].n_entries == 2
    assert anomalies == ["duplicate_id:a"]


def test_the_status_comes_from_the_last_entry_not_from_a_stored_field(node_event, moment):
    events = [
        node_event("root", at=moment(0), status="pending"),
        node_event("root", at=moment(1), status="running"),
        node_event("root", at=moment(2), status="passed"),
    ]
    rows, _ = flatten_tree(events)
    assert rows[0].status == "passed"
    assert rows[0].n_entries == 3


def test_a_negative_duration_is_shown_and_never_corrected(node_event, moment):
    events = [
        node_event("root", at=moment(9)),
        node_event("root", at=moment(4)),
    ]
    rows, _ = flatten_tree(events)
    assert rows[0].own_ms == -5000
    assert rows[0].anomalies == ("negative_duration:root",)


def test_the_subtree_envelope_is_never_a_sum_of_concurrent_durations(node_event, moment):
    events = [
        node_event("root", at=moment(0)),
        node_event("a", at=moment(1), parent_id="root", depth=1),
        node_event("a", at=moment(7), parent_id="root", depth=1),
        node_event("b", at=moment(2), parent_id="root", depth=1),
        node_event("b", at=moment(8), parent_id="root", depth=1),
        node_event("root", at=moment(3)),
    ]
    rows, _ = flatten_tree(events)
    by_id = {row.node_id: row for row in rows}
    concurrent_sum = by_id["a"].own_ms + by_id["b"].own_ms
    assert (by_id["a"].own_ms, by_id["b"].own_ms) == (6000, 6000)
    assert by_id["root"].own_ms == 3000
    assert by_id["root"].subtree_ms == 8000
    assert by_id["root"].subtree_ms < concurrent_sum


def test_an_unknown_parent_becomes_a_root_and_says_so(node_event, moment):
    events = [node_event("a", at=moment(0), parent_id="disparu", depth=1)]
    rows, anomalies = flatten_tree(events)
    assert [(row.node_id, row.depth) for row in rows] == [("a", 0)]
    assert set(anomalies) == {"orphan:a"}
    assert "depth_mismatch:a" in rows[0].anomalies


def test_a_cycle_shows_each_node_once(node_event, moment):
    events = [
        node_event("a", at=moment(0), parent_id="b", depth=1),
        node_event("b", at=moment(1), parent_id="a", depth=1),
    ]
    rows, anomalies = flatten_tree(events)
    assert sorted(row.node_id for row in rows) == ["a", "b"]
    assert sorted(anomalies) == ["unreachable:a", "unreachable:b"]


def test_a_payload_that_is_not_a_node_is_declared_not_dropped_silently(an_event, node_event, moment):
    events = [
        an_event(type="status", ts=moment(0), payload={"node": {"id": "sans le reste"}}),
        an_event(type="status", ts=moment(1), payload={"endpoint": "http://127.0.0.1:11434/v1"}),
        node_event("root", at=moment(2)),
    ]
    rows, anomalies = flatten_tree(events)
    assert [row.node_id for row in rows] == ["root"]
    assert anomalies == [f"invalid_node:{moment(0)}"]


def test_a_partial_projection_declares_what_it_omits():
    selected, omission = window(list(range(10)), limit=3, offset=4)
    assert selected == [4, 5, 6]
    assert omission == {"total": 10, "above": 4, "below": 3}


def test_status_text_names_what_was_not_observed(node_event, moment):
    row = MissionRow(
        mission_id="m1",
        n_events=0,
        families={},
        first_ts=None,
        last_ts=None,
        segments=0,
        anomalies=(),
    )
    text = status_text(row, [])
    assert "window: unavailable → unavailable" in text
    assert "families: unavailable" in text
    assert "anomalies: none" in text


def test_status_text_bounds_its_node_preview(node_event, moment):
    events = [node_event(f"n{number}", at=moment(number)) for number in range(12)]
    rows, _ = flatten_tree(events)
    row = MissionRow(
        mission_id="m1",
        n_events=len(events),
        families={"status": len(events)},
        first_ts=moment(0),
        last_ts=moment(11),
        segments=1,
        anomalies=("torn_tail:events.jsonl:10:4",),
    )
    text = status_text(row, rows)
    assert "node_status_omitted: 2" in text
    assert "n9" in text and "n11" not in text
    assert "anomalies: torn_tail:events.jsonl:10:4" in text
