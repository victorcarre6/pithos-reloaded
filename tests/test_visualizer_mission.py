"""Mission composée sur Git, Prefect, lifecycle et verifier réels ; modèle seul scénarisé."""

from functools import partial
import json
import multiprocessing
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

import pytest

from experiments.visualizer import mission
from experiments.visualizer.run import REFERENCE, SEED
from kernel.contracts import Domain


HANGING = (
    "def clamp_level(level):\n"
    "    import os, subprocess, sys, time\n"
    "    from pathlib import Path\n"
    "    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
    "    Path('gate-pids').write_text(f'{os.getpid()} {child.pid}')\n"
    "    time.sleep(60)\n"
    "    return level\n"
)


def scripted_worker(repo, output, budget, *, case):
    from tests.support import load_double
    import broker.finalize as publication

    model = load_double("bridge")
    source = "def clamp_level(level):\n    return max(0.0, min(2.0, level))\n" if case == "red" else REFERENCE
    if case == "cut":
        source = HANGING
    elif case == "legacy":
        source = (
            "def clamp_level(level):\n"
            "    if level < 0.0:\n        return 0.0\n"
            "    if level > 2.0:\n        return 2.0\n"
            "    return level\n"
        )
    model.script(model.conformant({"function_name": "clamp_level", "new_source": source}))
    if case == "resume":
        def forbidden():
            raise AssertionError("resume unnecessarily probed the model")

        model.probe = forbidden
    original = publication.record_result

    def lost(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError("commit acknowledgement lost")

    replacement = lost if case == "lost_ack" else original
    with (
        patch.object(mission, "bridge", model),
        patch.object(publication, "record_result", replacement),
    ):
        mission.execute(repo, output, budget)


def git(repo, *args):
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)

    return result.stdout.strip()


def test_composed_green_rejection_and_resume(tmp_path, monkeypatch):
    # isoler les threads du serveur de test du pytest qui exerce encore des forks
    if os.environ.get("PITHOS_MISSION_TEST_CHILD") != "1":
        env = dict(os.environ, PITHOS_MISSION_TEST_CHILD="1", PYTHONDONTWRITEBYTECODE="1")
        target = f"{__file__}::test_composed_green_rejection_and_resume"
        result = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", target],
                                env=env, capture_output=True, text=True, timeout=140)
        assert result.returncode == 0, result.stdout + result.stderr

        return

    from prefect import settings
    from prefect.testing.utilities import prefect_test_harness

    updates = {
        settings.PREFECT_SERVER_ANALYTICS_ENABLED: False,
        settings.PREFECT_CLOUD_ENABLE_ORCHESTRATION_TELEMETRY: False,
        settings.PREFECT_HOME: tmp_path / "prefect",
    }
    with settings.temporary_settings(updates), prefect_test_harness():
        monkeypatch.setenv("PREFECT_API_URL", settings.PREFECT_API_URL.value())
        monkeypatch.setenv("PREFECT_HOME", str(tmp_path / "worker-prefect"))
        for case in ("green", "lost_ack", "red", "cut", "legacy"):
            repo = tmp_path / case
            repo.mkdir()
            target = repo / "audio_visualizer.py"
            target.write_bytes(SEED.read_bytes())
            git(repo, "init", "-q", "-b", "main")
            git(repo, "config", "user.email", "test@pithos.local")
            git(repo, "config", "user.name", "Pithos test")
            git(repo, "add", "audio_visualizer.py")
            git(repo, "commit", "-qm", "seed")
            output = tmp_path / f"run-{case}"
            relation = "idempotent" if case == "legacy" else "unit_projection"
            if case == "legacy":
                # arbre antérieur à l'extension ; sa preuve reste limitée à l'idempotence
                output.mkdir()
                criterion = mission.projection_criterion().model_copy(update={"relation": mission.Relation.idempotent})
                node = mission.Node(id="clamp-level", parent_id=None, depth=0, target=target,
                                    criterion=criterion, status="pending", blocked_cause=None)
                mission_id = "audio-" + mission.sha256(str(output).encode()).hexdigest()[:16]
                tree = mission.Tree(mission_id=mission_id, nodes=(node,), cap_children=1)
                (output / "tree.json").write_text(tree.model_dump_json())
            worker = partial(scripted_worker, case=case)
            if case == "cut":
                import journal
                from engine.budget import Budget
                from lifecycle.execution import MissionProcess
                from lifecycle.lock import RunLock

                output.mkdir()
                control = repo.with_name(f".{repo.name}.pithos")
                control.mkdir()
                journal.bind(control / "events.jsonl", control / "live.log")
                lock = RunLock(control / "run.lock", max_seconds=10)
                process = MissionProcess(lock, events_path=control / "events.jsonl")
                with pytest.raises(TimeoutError):
                    process.run(partial(worker, repo, output, Budget(40)), time.monotonic() + 10)
                evidence = list(output.rglob("gate-pids"))
                assert len(evidence) == 1
                assert_processes_stopped(evidence[0])
                assert target.read_bytes() != SEED.read_bytes()
                assert json.loads((output / "tree.json").read_text())["nodes"][0]["status"] == "running"
            elif case == "lost_ack":
                with pytest.raises(RuntimeError, match="acknowledgement lost"):
                    mission.launch(repo, output, 40, worker=worker)
                partial_tree = json.loads((output / "tree.json").read_text())
                assert not partial_tree["finalized"]
                assert git(repo, "rev-list", "--count", "HEAD") == "2"
            else:
                mission.launch(repo, output, 40, worker=worker)
            mission.launch(repo, output, 40, worker=partial(scripted_worker, case="resume"))
            if case in {"green", "legacy"}:
                command = [sys.executable, str(Path(mission.__file__)), "--repo", str(repo),
                           "--run", str(output), "--seconds", "40"]
                result = subprocess.run(command, capture_output=True, text=True, timeout=60)
                assert result.returncode == 0, result.stdout + result.stderr
                assert json.loads(result.stdout)["finalized"] == 1
                assert json.loads(result.stdout)["criterion"]["relation"] == relation
            tree = json.loads((output / "tree.json").read_text())
            assert tree["nodes"][0]["criterion"]["relation"] == relation
            events = [json.loads(line) for line in (output / "events.jsonl").read_text().splitlines()]
            receipts = [event for event in events if event["type"] == "validation"]
            assert len(tree["attempts"]) == 1
            assert sum(event["payload"].get("operation") == "candidate_response" for event in events) == 1
            assert git(repo, "status", "--porcelain") == ""
            control = repo.with_name(f".{repo.name}.pithos")
            custody = [json.loads(line) for line in (control / "events.jsonl").read_text().splitlines()]
            admitted = [event for event in custody if event["payload"].get("process_scope") == "task"]
            assert len(admitted) == len(list(output.rglob("invariant.py")))
            from lifecycle.custody import active_processes

            assert not active_processes(control / "events.jsonl")
            if case in {"red", "cut"}:
                assert tree["nodes"][0]["status"] == "blocked"
                assert not receipts and not tree["finalized"]
                assert target.read_bytes() == SEED.read_bytes()
                assert git(repo, "rev-list", "--count", "HEAD") == "1"
            else:
                assert tree["nodes"][0]["status"] == "passed"
                assert len(receipts) == len(tree["finalized"]) == 1
                assert receipts[0]["payload"]["verification"]["criterion"]["relation"] == relation
                assert receipts[0]["payload"]["key"]["value"][-1] == relation
                assert target.read_bytes() != SEED.read_bytes()
                assert git(repo, "rev-list", "--count", "HEAD") == "2"


def test_launch_refuses_a_harness_target_before_any_worker(tmp_path):
    with pytest.raises(ValueError, match="dedicated"):
        mission.launch(mission.ROOT, tmp_path / "run", 40)
    assert not (tmp_path / "run").exists()


@pytest.mark.parametrize("changes", [
    {"relation": mission.Relation.total},
    {"symbols": ["other"]},
    {"domain": Domain.small_ints},
])
def test_resume_refuses_a_criterion_from_another_experiment(tmp_path, changes, monkeypatch):
    from engine.budget import Budget
    import engine.flow

    def forbidden(*args, **kwargs):
        raise AssertionError("an unrelated criterion reached the flow")

    monkeypatch.setattr(engine.flow, "mission", forbidden)
    criterion = mission.projection_criterion().model_copy(update=changes)
    node = mission.Node(id="clamp-level", parent_id=None, depth=0, target=tmp_path / "audio_visualizer.py",
                        criterion=criterion, status="pending", blocked_cause=None)
    mission_id = "audio-" + mission.sha256(str(tmp_path).encode()).hexdigest()[:16]
    tree = mission.Tree(mission_id=mission_id, nodes=(node,), cap_children=1)
    path = tmp_path / "tree.json"
    path.write_text(tree.model_dump_json())
    original = path.read_bytes()
    with pytest.raises(ValueError, match="persisted mission differs"):
        mission.execute(tmp_path, tmp_path, Budget(1))
    assert path.read_bytes() == original


def orphan_task(control):
    import verifier
    from kernel.contracts import Criterion
    from lifecycle.execution import run_command
    from verifier.runner import execute

    criterion = Criterion(relation="idempotent", symbols=["clamp_level"], domain="floats_finite")
    with verifier.execution_scope(run_command):
        execute(criterion, HANGING, artifact_root=control, timeout=60)


def orphan_owner(control):
    import journal
    from lifecycle.execution import MissionProcess
    from lifecycle.lock import RunLock

    journal.bind(control / "events.jsonl", control / "live.log")
    lock = RunLock(control / "run.lock", max_seconds=60)
    process = MissionProcess(lock, events_path=control / "events.jsonl")
    process.run(partial(orphan_task, control), time.monotonic() + 60)


def resumed_task(evidence):
    evidence.write_text("admitted after sweep")


def assert_processes_stopped(evidence):
    for pid in evidence.read_text().split():
        observed = subprocess.run(["/bin/ps", "-p", pid, "-o", "stat="], capture_output=True, text=True)
        assert not observed.stdout.strip() or observed.stdout.strip().startswith("Z")


def test_dead_supervisor_is_swept_before_admitting_another_worker(tmp_path):
    import journal
    from lifecycle.custody import active_processes
    from lifecycle.execution import MissionProcess
    from lifecycle.lock import RunLock

    context = multiprocessing.get_context("spawn")
    owner = context.Process(target=orphan_owner, args=(tmp_path,))
    owner.start()
    try:
        deadline = time.monotonic() + 10
        evidence = []
        while not evidence and time.monotonic() < deadline:
            time.sleep(0.02)
            evidence = list(tmp_path.rglob("gate-pids"))
        assert len(evidence) == 1
    finally:
        owner.kill()
        owner.join(timeout=2)
        assert not owner.is_alive()
    journal.bind(tmp_path / "events.jsonl", tmp_path / "live.log")
    lock = RunLock(tmp_path / "run.lock", max_seconds=60)
    process = MissionProcess(lock, events_path=tmp_path / "events.jsonl")
    process.run(partial(resumed_task, tmp_path / "resumed"), time.monotonic() + 5)
    assert (tmp_path / "resumed").read_text() == "admitted after sweep"
    assert not active_processes(tmp_path / "events.jsonl")
    assert_processes_stopped(evidence[0])
    assert not lock.path.exists()
