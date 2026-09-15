"""Le port ne décide jamais du verdict ; le rapport et le code de retour restent croisés."""

import subprocess

from verifier.runner import execute, execution_scope


def test_scoped_executor_receives_only_owned_artifacts_and_cannot_invent_success(tmp_path, kernel_double):
    calls = []

    def observed(command, *, directory, environment, timeout):
        calls.append((command, directory, environment, timeout))
        assert directory.is_relative_to(tmp_path)
        assert (directory / "candidate.py").is_file()
        assert (directory / "invariant.py").is_file()
        assert (directory / "stdout.txt").read_bytes() == b""
        assert (directory / "stderr.txt").read_bytes() == b""
        return 0

    with execution_scope(observed):
        result = execute(kernel_double.criterion(), "def f(x): return x", artifact_root=tmp_path, timeout=5)
    assert result.execution == "tool_error" and result.check == "not_run"
    assert len(calls) == 1
    assert 0 < calls[0][-1] <= 5
    assert set(calls[0][2]) == {"HYPOTHESIS_STORAGE_DIRECTORY"}
    # sortie de scope : l'exécuteur réel est restauré
    result = execute(kernel_double.criterion(), "def f(x): return x", artifact_root=tmp_path, timeout=5)
    assert result.check == "passed"
    assert len(calls) == 1


def test_executor_timeout_preserves_an_unknown_gate(tmp_path, kernel_double):
    def timeout(command, *, directory, environment, timeout):
        raise subprocess.TimeoutExpired(command, timeout)

    with execution_scope(timeout):
        result = execute(kernel_double.criterion(), "def f(x): return x", artifact_root=tmp_path, timeout=5)
    assert result.execution == "timed_out"
    assert result.check == "not_run" and result.returncode is None
    assert (result.artifact_path.parent / "meta.json").is_file()
