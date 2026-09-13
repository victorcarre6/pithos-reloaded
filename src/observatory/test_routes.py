"""Les routes servent une lecture bornée : catalogue léger, détail à la demande, rien d'écrit."""

import pytest
from fastapi.testclient import TestClient

from observatory.api import routes


@pytest.fixture
def client(logs_root):
    "Client lié à une racine de logs jetable ; l'arbre vivant n'est jamais servi par un test."

    routes.bind(logs_root)

    return TestClient(routes.app)


def test_the_catalogue_lists_missions_without_loading_their_events(client, write_events, an_event, moment):
    write_events("m1", [an_event(ts=moment(1)), an_event(ts=moment(2))])
    write_events("m2", [an_event(ts=moment(3))])
    body = client.get("/missions", params={"limit": 1}).json()
    assert [row["mission_id"] for row in body["missions"]] == ["m2"]
    assert body["window"] == {"total": 2, "above": 0, "below": 1}
    assert body["has_more"] is True
    assert set(body["missions"][0]) == {
        "mission_id", "n_events", "families", "first_ts", "last_ts", "segments", "anomalies",
    }


def test_the_detail_bounds_its_digest_and_declares_the_omission(client, write_events, an_event, moment, logs_root):
    events = [an_event(ts=moment(second % 60), payload={"n": second}) for second in range(30)]
    write_events("m1", events)
    body = client.get("/missions/m1").json()
    assert body["n_events"] == 30
    assert len(body["digest"]["events"]) == 25
    events_path = logs_root / "missions" / "m1" / "events.jsonl"
    assert body["digest"]["window"] == {"path": str(events_path), "total": 30, "above": 5, "below": 0}
    assert body["families"] == {"validation": 30}
    assert "mission: m1" in body["status_text"]


def test_the_artifact_manifest_reports_presence_and_size(client, write_events, validation_event, moment, logs_root):
    path = write_events("m1", [validation_event(at=moment(1), artifact="invariant.py")])
    (path.parent / "tree.json").write_text("{}\n", encoding="utf-8")
    manifest = client.get("/missions/m1/artifacts").json()["artifacts"]
    assert manifest["events.jsonl"]["size"] == path.stat().st_size
    assert manifest["tree.json"] == {"path": str(path.parent / "tree.json"), "exists": True, "size": 3}
    assert manifest["CONTEXT.md"] == {"path": str(path.parent / "CONTEXT.md"), "exists": False, "size": None}
    assert manifest["invariant.py"]["exists"] is False


def test_the_tree_route_serves_flattened_rows_with_their_anomalies(client, write_events, node_event, moment):
    events = [
        node_event("root", at=moment(1)),
        node_event("a", at=moment(2), parent_id="root", depth=1),
        node_event("a", at=moment(3), parent_id="ailleurs", depth=1),
    ]
    write_events("m1", events, torn='{"ts"')
    body = client.get("/missions/m1/tree").json()
    assert [row["node_id"] for row in body["nodes"]] == ["root", "a"]
    assert body["window"] == {"total": 2, "above": 0, "below": 0}
    assert body["anomalies"][0].startswith("torn_tail:")
    assert "duplicate_id:a" in body["anomalies"]


@pytest.mark.parametrize("route", ["/missions/{}", "/missions/{}/tree", "/missions/{}/artifacts"])
@pytest.mark.parametrize("mission_id", ["absente", "..", "%2e%2e%2f%2e%2e", "m1%2f.."])
def test_an_unindexed_mission_is_a_404_and_never_a_path(client, write_events, an_event, moment, route, mission_id):
    write_events("m1", [an_event(ts=moment(1))])
    response = client.get(route.format(mission_id))
    assert response.status_code == 404


def test_a_payload_carrying_markup_is_served_as_data_not_as_a_document(client, write_events, an_event, moment):
    trace = "<script>alert(1)</script>"
    write_events("m1", [an_event(ts=moment(1), payload={"trace": trace})])
    response = client.get("/missions/m1")
    assert response.headers["content-type"].startswith("application/json")
    assert "text/html" not in response.headers["content-type"]
    assert response.json()["digest"]["events"][0]["payload"]["trace"] == trace


def test_every_response_carries_the_freshness_of_the_index(client, write_events, an_event, moment):
    write_events("m1", [an_event(ts=moment(1))])
    freshness = client.get("/missions").json()["freshness"]
    assert freshness["missions"] == 1
    assert freshness["watch_error"] is None
    assert freshness["built_at"] <= freshness["refreshed_at"]


def test_readiness_comes_from_the_index_not_from_the_spawn(client, logs_root, write_events, an_event, moment):
    write_events("m1", [an_event(ts=moment(1))])
    assert client.get("/ready").json()["ready"] is True

    # le suivi tombe : l'index reste servi, et la panne est visible
    (logs_root / "missions" / "m1" / "events.jsonl").unlink()
    (logs_root / "missions" / "m1").rmdir()
    (logs_root / "missions").rmdir()
    body = client.get("/ready").json()
    assert body["ready"] is False
    assert body["freshness"]["watch_error"].startswith("FileNotFoundError")
    assert client.get("/missions").json()["missions"][0]["mission_id"] == "m1"


def test_the_aggregate_routes_scope_to_a_mission_or_to_the_whole_catalogue(client, write_events, moment,
                                                                           model_call_event, tool_event,
                                                                           validation_event):
    write_events("m1", [model_call_event(at=moment(1), prompt_estimate=100, prompt_tokens=120)])
    write_events("m2", [
        tool_event("splice", at=moment(2), function_name="f", new_source="def f(): ..."),
        validation_event(at=moment(3), symbols=("f",)),
    ])
    assert len(client.get("/stats/context").json()["calls"]) == 1
    assert client.get("/stats/context", params={"mission": "m2"}).json()["calls"] == []
    assert client.get("/stats/tools", params={"mission": "m1"}).json()["tools"] == []
    assert client.get("/stats/daily").json()["days"][0]["events"] == 3
    assert client.get("/indicators").json()["progress_without_intervention"]["value"] is None
    assert client.get("/stats/daily", params={"mission": "absente"}).status_code == 404
