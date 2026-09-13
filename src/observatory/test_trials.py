"""Projection des essais depuis leurs événements et artefacts, sans moteur ni modèle."""

import json
from hashlib import sha256

import pytest
from fastapi.testclient import TestClient

from observatory.api import routes
from observatory.api.index import build_run_index


@pytest.fixture
def trial(logs_root, write_events, an_event, double):
    kernel = double("kernel")
    before = "def f(x): return x + 1\n"
    after = "def f(x): return abs(x)\n"
    events = [
        an_event(type="status", payload={"scope": "engine", "node_id": "n", "operation": "running", "phase": "intent"}),
        an_event(type="tool_activity", payload={"operation": "write", "path": "tool.py", "before_hex": before.encode().hex(), "after_hex": after.encode().hex()}),
        an_event(type="status", payload={"scope": "engine", "node_id": "n", "operation": "blocked", "phase": "intent", "cause": "invariant_failed", "detail": "tautology"}),
    ]
    path = write_events("m1", events)
    node = kernel.node(id="n", status="blocked", blocked_cause="invariant_failed")
    (path.parent / "tree.json").write_text(json.dumps({"mission_id": "m1", "nodes": [node.model_dump(mode="json")]}))
    report = {
        "mode": "trial", "status": "blocked", "cause": "invariant_failed", "restored": True,
        "receipt_written": False, "elapsed_seconds": 35.0,
        "before_sha256": sha256(before.encode()).hexdigest(), "after_sha256": sha256(before.encode()).hexdigest(),
        "capability": {"context_window": 16384, "provenance": "asserted", "schema_honored": True},
        "components": {"bridge": "real", "git": "real"},
    }
    (path.parent / "result.json").write_text(json.dumps(report))
    for name, source, check in [("before", before, "failed"), ("after", after, "passed"), ("mutant", "def f(x): return None\n", "passed")]:
        directory = path.parent / f"invariant-{name}"
        directory.mkdir()
        (directory / "candidate.py").write_text(source)
        metadata = {
            "source_sha256": sha256(source.encode()).hexdigest(), "check": check,
            "execution": "completed", "returncode": 20 if check == "failed" else 0,
            "duration": 0.2, "diagnostic": "", "counterexample": "",
        }
        (directory / "meta.json").write_text(json.dumps(metadata))
    routes.bind_runs(logs_root / "missions")

    return TestClient(routes.app), path.parent


def test_direct_run_collection_preserves_the_existing_mission_contract(trial, logs_root):
    client, _ = trial
    index = build_run_index(logs_root / "missions")
    assert list(index.rows) == ["m1"]
    assert client.get("/ready").json()["ready"] is True
    assert client.get("/missions").json()["missions"][0]["mission_id"] == "m1"


def test_trial_projects_published_state_rejection_and_gate_evidence(trial):
    client, _ = trial
    body = client.get("/missions/m1").json()
    observed = body["trial"]
    assert observed["result"]["restored"] is True
    assert observed["reason"] == "tautology"
    assert observed["receipt_count"] == 0
    assert {gate["role"] for gate in observed["gates"]} == {"before", "after", "variant"}
    tree = client.get("/missions/m1/tree").json()
    assert tree["nodes"][0]["status"] == "blocked"
    assert tree["nodes"][0]["own_ms"] is None
    assert client.get("/stats/daily?mission=m1").json()["days"][0]["rejected"] == 1
    assert client.get("/indicators?mission=m1").json()["diagnosed_limitations"]["by_cause"] == {"invariant_failed": 1}


def test_intent_cannot_turn_a_published_running_node_green(trial):
    client, root = trial
    tree = json.loads((root / "tree.json").read_text())
    tree["nodes"][0].update(status="running", blocked_cause=None)
    (root / "tree.json").write_text(json.dumps(tree))
    body = client.get("/missions/m1/tree").json()
    assert body["nodes"][0]["status"] == "running"


def test_artifact_preview_is_bounded_and_cannot_escape_the_run(trial, tmp_path):
    client, root = trial
    response = client.get("/missions/m1/artifact", params={"path": "invariant-after/candidate.py", "limit": 1})
    body = response.json()
    assert response.status_code == 200
    assert body["text"] == "def f(x): return abs(x)"
    assert body["window"]["total"] == 1
    outside = tmp_path / "outside.txt"
    outside.write_text("private")
    (root / "invariant-after" / "stdout.txt").symlink_to(outside)
    for path in ["../outside.txt", str(outside), "invariant-after/stdout.txt", "workspace/tool.py"]:
        response = client.get("/missions/m1/artifact", params={"path": path})
        assert response.status_code == 404


def test_corrupt_sidecar_is_visible_and_never_interpreted_as_success(trial):
    client, root = trial
    (root / "result.json").write_text("{broken")
    body = client.get("/missions/m1").json()["trial"]
    assert body["result"] is None
    assert any("result.json" in item for item in body["anomalies"])


def test_admission_errors_remain_distinct_from_executed_trials(trial):
    client, root = trial
    empty = root.parent / "trial-preflight"
    empty.mkdir()
    (empty / "result.json").write_text(json.dumps({"mode": "trial", "error": "ValueError", "detail": "no HEAD"}))
    group = client.get("/stats/attempts").json()["by_mode"]["trial"]
    assert group["runs"] == 2
    assert group["with_state"] == 1
    assert group["admission_errors"] == 1


def test_duplicate_node_ids_in_distinct_trials_are_counted_independently(trial, write_events, an_event):
    client, root = trial
    node = json.loads((root / "tree.json").read_text())["nodes"][0]
    path = write_events("second", [an_event(payload={"node": node})])
    (path.parent / "tree.json").write_bytes((root / "tree.json").read_bytes())
    report = client.get("/indicators").json()
    assert report["diagnosed_limitations"]["by_cause"] == {"invariant_failed": 2}


def test_oversized_artifact_is_explicit_and_does_not_claim_a_line_count(trial):
    client, root = trial
    (root / "CONTEXT.md").write_text("x" * 2_000_001)
    response = client.get("/missions/m1/artifact", params={"path": "CONTEXT.md"})
    assert response.status_code == 413
    assert response.json()["detail"] == "artifact_too_large"
