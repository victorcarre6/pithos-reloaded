"""Les pannes et les sorties prématurées ne deviennent jamais un invariant rouge ou vert."""

import json
from pathlib import Path
import subprocess
import time

import pytest
from pydantic import ValidationError

from verifier.models import ExecutionResult
from verifier.runner import compact_failure_output, execute


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf"), True])
def test_invalid_timeout_has_no_effect(kernel_double, tmp_path, timeout):
    with pytest.raises(ValueError):
        execute(kernel_double.criterion(), "def f(x): return x", artifact_root=tmp_path, timeout=timeout)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("code", [0, 1, 20, 70, 127, 9009])
def test_premature_exit_is_tool_failure(kernel_double, tmp_path, code):
    source = f"raise SystemExit({code})\ndef f(x): return x\n"
    result = execute(kernel_double.criterion(), source, artifact_root=tmp_path, timeout=10)
    assert result.execution == "tool_error"
    assert result.check == "not_run"


def test_timeout_keeps_artifact_and_unknown_status(kernel_double, tmp_path):
    source = "while True: pass\ndef f(x): return x\n"
    started = time.monotonic()
    result = execute(kernel_double.criterion(), source, artifact_root=tmp_path, timeout=0.4)
    assert time.monotonic() - started < 3
    assert result.execution == "timed_out"
    assert result.check == "not_run"
    assert result.returncode is None
    assert result.artifact_path.is_file()
    assert json.loads((result.artifact_path.parent / "meta.json").read_text())["returncode"] is None


def test_launch_failure_keeps_source(kernel_double, tmp_path, monkeypatch):
    def unavailable(*args, **kwargs):
        raise FileNotFoundError("python unavailable")

    monkeypatch.setattr(subprocess, "Popen", unavailable)
    result = execute(kernel_double.criterion(), "def f(x): return x", artifact_root=tmp_path, timeout=10)
    assert result.execution == "tool_error"
    assert result.returncode is None
    assert "python unavailable" in result.diagnostic
    assert result.artifact_path.is_file()


def test_unknown_exit_is_not_coerced_to_success(kernel_double, tmp_path, monkeypatch):
    class UnknownExit:
        pid = 99999999

        def wait(self, timeout=None):
            return None

    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: UnknownExit())
    result = execute(kernel_double.criterion(), "def f(x): return x", artifact_root=tmp_path, timeout=10)
    assert result.execution == "tool_error"
    assert result.returncode is None
    assert result.check == "not_run"


def test_output_complete_on_disk_bounded_in_feedback(kernel_double, tmp_path):
    source = "print('HEAD' + 'é' * 20000 + 'TAIL')\ndef f(x): return x\n"
    result = execute(kernel_double.criterion(), source, artifact_root=tmp_path, timeout=10)
    raw = (result.artifact_path.parent / "stdout.txt").read_bytes()
    assert raw.startswith(b"HEAD")
    assert raw.endswith(b"TAIL\n")
    assert len(raw) == result.stdout_bytes == 40009
    assert result.diagnostic.startswith("HEAD")
    assert result.diagnostic.endswith("TAIL")
    assert len(result.diagnostic) <= 1800
    assert len(result.diagnostic.splitlines()) <= 24


def test_head_and_tail_survive_both_caps():
    raw = "\n".join(f"line-{i}:" + "x" * 300 for i in range(100))
    preview = compact_failure_output(raw)
    assert preview.startswith("line-0:")
    assert "line-99:" in preview
    assert len(preview) <= 1800
    assert len(preview.splitlines()) <= 24


def test_artifacts_are_unique_and_never_replaced(kernel_double, tmp_path):
    first = execute(kernel_double.criterion(), "def f(x): return x", artifact_root=tmp_path, timeout=10)
    previous = {path.name: path.read_bytes() for path in first.artifact_path.parent.iterdir() if path.is_file()}
    second = execute(kernel_double.criterion(), "def f(x): return x", artifact_root=tmp_path, timeout=10)
    assert first.artifact_path != second.artifact_path
    assert previous == {path.name: path.read_bytes() for path in first.artifact_path.parent.iterdir() if path.is_file()}


def test_relative_artifact_root(kernel_double, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = execute(kernel_double.criterion(), "def f(x): return x", artifact_root=Path("."), timeout=10)
    assert result.check == "passed", result.diagnostic


def test_child_holding_output_does_not_hold_runner(kernel_double, tmp_path):
    source = (
        "import subprocess, sys\n"
        "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
        "def f(x): return x\n"
    )
    started = time.monotonic()
    result = execute(kernel_double.criterion(), source, artifact_root=tmp_path, timeout=5)
    assert result.check == "passed", result.diagnostic
    assert time.monotonic() - started < 5


def test_invalid_input_creates_no_artifacts(kernel_double, tmp_path):
    result = execute(kernel_double.criterion(), "def other(x): return x", artifact_root=tmp_path, timeout=10)
    assert result.execution == "invalid"
    assert result.artifact_path is None
    assert list(tmp_path.iterdir()) == []


def test_metadata_write_failure_removes_success(kernel_double, tmp_path, monkeypatch):
    original = Path.open

    def faulty(path, *args, **kwargs):
        if path.name == "meta.json":
            raise OSError("disk full")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", faulty)
    result = execute(kernel_double.criterion(), "def f(x): return x", artifact_root=tmp_path, timeout=10)
    assert result.execution == "tool_error"
    assert result.check == "not_run"
    assert "disk full" in result.diagnostic
    assert result.artifact_path.is_file()


def test_typed_result_rejects_false_success():
    with pytest.raises(ValidationError):
        ExecutionResult(execution="completed", check="passed", returncode=None,
                        artifact_path=Path("invariant.py"), diagnostic="", duration=0)


def test_candidate_mutation_cannot_change_expected_input(kernel_double, tmp_path):
    source = "def f(x):\n    if isinstance(x, (list, dict)):\n        x.clear()\n    return x\ndef g(x): return x\n"
    criterion = kernel_double.criterion(relation="round_trip", symbols=["f", "g"], domain="json_values")
    result = execute(criterion, source, artifact_root=tmp_path, timeout=10)
    assert result.check == "failed"


def test_exact_exception_type_rejects_subclasses(kernel_double, tmp_path):
    source = "class E(ValueError): pass\nclass Child(E): pass\ndef f(x): raise Child()\n"
    criterion = kernel_double.criterion(relation="raises_on", symbols=["f", "E"])
    result = execute(criterion, source, artifact_root=tmp_path, timeout=10)
    assert result.check == "failed"
