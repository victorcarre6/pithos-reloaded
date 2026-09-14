"""L'enveloppe possède un cycle Prefect, jamais une seconde mission métier."""

import inspect
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

from engine.budget import Budget
from engine.tree import Tree
from engine.test_attempt import scenario
from engine.test_walk import mission as walking_mission


@pytest.fixture
def envelope(monkeypatch):
    from engine import flow
    from prefect import settings

    captured = {}

    def decorate(**options):
        captured.update(options)

        def wrap(fn):
            captured["parameters"] = inspect.signature(fn).parameters

            return fn

        return wrap

    monkeypatch.setattr(flow, "flow", decorate)
    monkeypatch.setattr(flow.SyncClientContext, "__enter__", lambda self: self)
    monkeypatch.setattr(flow.SyncClientContext, "__exit__", lambda *args: None)
    monkeypatch.setattr(flow, "getproxies", lambda: {})
    with settings.temporary_settings({settings.PREFECT_API_URL: "http://127.0.0.1:4200/api"}):
        yield flow, captured


def test_one_call_preserves_the_budget_and_keeps_domain_out_of_prefect(envelope, kernel_double, double, monkeypatch):
    flow, captured = envelope
    tree = Tree(mission_id="audio", nodes=(kernel_double.node(),), cap_children=2)
    memory = double("engine").MemoryEngine([tree])
    clock = [0]
    budget = Budget(60, clock=lambda: clock[0])
    clock[0] = 20
    deps = object()
    calls = []

    def walk(*args):
        calls.append(args)

        return memory.walk(*args)

    monkeypatch.setattr(flow, "walk", walk)
    result = flow.mission(tree, budget, deps)
    assert result == tree
    assert calls == [(tree, budget, deps)]
    assert budget.deadline == 60
    assert captured["name"] == "mission"
    assert captured["timeout_seconds"] == 100
    assert captured["retries"] == 0
    assert captured["persist_result"] is False
    assert captured["log_prints"] is False
    assert not captured["parameters"]


@pytest.mark.parametrize("error", [RuntimeError("interrupted write"), TimeoutError("transport timeout")])
def test_failure_is_propagated_without_a_second_walk(envelope, error, monkeypatch):
    flow, _ = envelope
    calls = []

    def fail(*args):
        calls.append(args)
        raise error

    monkeypatch.setattr(flow, "walk", fail)
    with pytest.raises(type(error)) as caught:
        flow.mission(None, Budget(60), None)
    assert caught.value is error
    assert len(calls) == 1


@pytest.mark.parametrize("url", [None, "https://api.prefect.cloud/api", "http://192.168.1.2/api",
                                 "http://localhost/api", "http://127.0.0.1.evil/api"])
def test_remote_or_missing_api_is_refused_before_flow_creation(envelope, url):
    from prefect import settings

    flow, captured = envelope
    with settings.temporary_settings({settings.PREFECT_API_URL: url}):
        with pytest.raises(ValueError, match="loopback"):
            flow.mission(None, Budget(60), None)
    assert captured == {}


def test_borrowed_context_and_proxy_are_refused_before_flow_creation(envelope, monkeypatch):
    flow, captured = envelope
    with monkeypatch.context() as patch:
        patch.setattr(flow.SyncClientContext, "get", lambda: object())
        with pytest.raises(ValueError, match="context"):
            flow.mission(None, Budget(60), None)
    monkeypatch.setattr(flow, "getproxies", lambda: {"http": "http://proxy.invalid"})
    with pytest.raises(ValueError, match="proxy"):
        flow.mission(None, Budget(60), None)
    assert captured == {}


def test_timeout_requires_the_main_thread_and_an_available_alarm(envelope, monkeypatch):
    flow, captured = envelope
    with monkeypatch.context() as patch:
        patch.setattr(flow, "current_thread", lambda: object())
        with pytest.raises(ValueError, match="main thread"):
            flow.mission(None, Budget(60), None)
    monkeypatch.setattr(signal, "getsignal", lambda _: lambda *args: None)
    with pytest.raises(ValueError, match="SIGALRM"):
        flow.mission(None, Budget(60), None)
    assert captured == {}


def test_mission_contract_rejects_signature_drift(kernel_double, double, monkeypatch):
    from engine import flow

    tree = Tree(mission_id="audio", nodes=(kernel_double.node(),), cap_children=2)
    memory = double("engine").MemoryEngine([tree])

    def assert_contract():
        assert isinstance(flow, flow.MissionRunner)
        assert isinstance(memory, flow.MissionRunner)
        expected = inspect.signature(flow.mission).parameters.values()
        actual = inspect.signature(memory.mission).parameters.values()
        assert [(p.name, p.kind, p.default) for p in actual] == [
            (p.name, p.kind, p.default) for p in expected
        ]

    assert_contract()
    with monkeypatch.context() as patch:
        def forbidden(*args, **kwargs):
            raise AssertionError("mission double performed I/O")

        patch.setattr(Path, "open", forbidden)
        assert memory.mission(tree, Budget(60), None) == tree
    monkeypatch.setattr(memory, "mission", lambda wrong: None)
    with pytest.raises(AssertionError):
        assert_contract()


def test_prefect_envelope_keeps_the_module_boundary():
    from engine import flow
    from tests.graph import imported_roots

    source = Path(flow.__file__).read_text()
    forbidden = {"broker", "campaign", "lifecycle", "subprocess", "socket", "httpx", "requests"}
    assert not imported_roots(source) & forbidden
    for name in forbidden:
        injected = source + f"\nimport {name}\n"
        assert imported_roots(injected) & forbidden


def test_envelope_preserves_finalization_in_the_soft_reserve(envelope, walking_mission):
    from engine.test_attempt import launch

    flow, _ = envelope
    scenario, deps = walking_mission
    green = launch(scenario)
    result = flow.mission(green, Budget(5, clock=lambda: 0), deps)
    assert len(result.finalized) == 1
    assert len(deps.attempt.bridge.calls) == 1
    assert deps.attempt.journal.events[-1].payload["exit_cause"] == "timeout"


def test_real_prefect_runs_once_without_persisting_domain_and_interrupts_at_timeout(
    tmp_path, kernel_double, double, monkeypatch,
):
    # le runtime Prefect ne doit pas laisser ses threads dans le pytest qui teste fork
    if os.environ.get("PITHOS_PREFECT_TEST_CHILD") != "1":
        env = dict(os.environ, PITHOS_PREFECT_TEST_CHILD="1", PYTHONDONTWRITEBYTECODE="1")
        target = f"{__file__}::test_real_prefect_runs_once_without_persisting_domain_and_interrupts_at_timeout"
        command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", target]
        result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=45)
        assert result.returncode == 0, result.stdout + result.stderr

        return

    from engine import flow
    from prefect import settings
    from prefect.context import FlowRunContext
    from prefect.testing.utilities import prefect_test_harness

    # serveur de test local, télémétrie coupée avant son démarrage
    updates = {
        settings.PREFECT_SERVER_ANALYTICS_ENABLED: False,
        settings.PREFECT_CLOUD_ENABLE_ORCHESTRATION_TELEMETRY: False,
        settings.PREFECT_HOME: tmp_path,
        settings.PREFECT_LOCAL_STORAGE_PATH: tmp_path / "results",
        settings.PREFECT_FLOW_DEFAULT_RETRIES: 3,
        settings.PREFECT_RESULTS_PERSIST_BY_DEFAULT: True,
        settings.PREFECT_LOGGING_LOG_PRINTS: True,
    }
    tree = Tree(mission_id="audio", nodes=(kernel_double.node(),), cap_children=2)
    memory = double("engine").MemoryEngine([tree])
    calls = []
    runs = []

    def replay(*args):
        context = FlowRunContext.get()
        assert context.flow.retries == 0
        assert context.flow.persist_result is False
        assert context.flow.log_prints is False
        assert settings.PREFECT_LOGGING_TO_API_ENABLED.value() is False
        assert settings.PREFECT_CLOUD_ENABLE_ORCHESTRATION_TELEMETRY.value() is False
        runs.append(context.flow_run.id)
        calls.append(args)

        return memory.walk(*args)

    monkeypatch.setattr(flow, "walk", replay)
    with settings.temporary_settings(updates), prefect_test_harness():
        budget = Budget(60)
        assert flow.mission(tree, budget, None) == tree
        assert calls == [(tree, budget, None)]
        with flow.SyncClientContext() as client_context:
            saved = client_context.client.read_flow_run(runs[0])
        assert saved.parameters == {}
        assert saved.state.is_completed()
        assert saved.state.data is None

        # un échec n'est ni repris par Prefect ni converti en arbre synthétique
        error = RuntimeError("write interrupted")

        def fail(*args):
            calls.append(args)
            raise error

        monkeypatch.setattr(flow, "walk", fail)
        with pytest.raises(RuntimeError, match="write interrupted"):
            flow.mission(tree, Budget(60), None)
        assert len(calls) == 2

        # l'alarme interrompt un appel bloquant et laisse dérouler son finally
        cleanup = []

        def blocked(*args):
            started = time.monotonic()
            calls.append(args)
            try:
                time.sleep(1)
            finally:
                cleanup.append(time.monotonic() - started)

        monkeypatch.setattr(flow, "walk", blocked)
        monkeypatch.setattr(flow, "LAST_RESORT_GRACE_SECONDS", 0.05)
        clock = [0]
        exhausted = Budget(1, clock=lambda: clock[0])
        clock[0] = 2
        with pytest.raises(TimeoutError):
            flow.mission(tree, exhausted, None)
        assert len(calls) == 3
        assert len(cleanup) == 1
        assert cleanup[0] < 0.8
        assert signal.getsignal(signal.SIGALRM) == signal.SIG_DFL
