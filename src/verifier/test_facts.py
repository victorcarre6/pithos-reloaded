"""Croisement des faits publics avant toute exécution de la double gate."""

from hashlib import sha256
from pathlib import Path
import subprocess

import pytest

import verifier
from kernel.facts import RecordKey
from verifier.models import fact_error


@pytest.fixture
def observations(kernel_double):
    before = b"def f(x): return x + 2\ndef g(x): return x - 1\n"
    after = before.replace(b"x + 2", b"x + 1")
    target = Path("/campaign/tool.py")
    source = kernel_double.source_fact(path=target, before=before, after=after)
    file = kernel_double.file_fact(
        path=target,
        sha_before=sha256(before).hexdigest(),
        sha_after=sha256(after).hexdigest(),
    )
    diff = (
        "diff --git a/tool.py b/tool.py\n"
        "--- a/tool.py\n+++ b/tool.py\n@@ -1,2 +1,2 @@\n"
        "-def f(x): return x + 2\n+def f(x): return x + 1\n"
        " def g(x): return x - 1\n"
    )
    repo = kernel_double.repo_fact(changes=[kernel_double.repo_change()], diff=diff, complete=True)

    return [file, source, repo]


@pytest.fixture
def criterion(kernel_double):
    return kernel_double.criterion(relation="round_trip", symbols=["f", "g"])


@pytest.mark.parametrize("case,reason", [
    ("missing", "missing_facts"), ("duplicate", "missing_facts"),
    ("incomplete", "incomplete_repository"), ("hash", "hash_mismatch"),
    ("path", "path_mismatch"), ("extra_file", "repository_mismatch"),
    ("other_diff", "repository_mismatch"), ("empty_diff", "repository_mismatch"),
    ("stale_diff", "repository_mismatch"), ("wrong_hunk", "repository_mismatch"),
    ("truncated_diff", "repository_mismatch"),
    ("outside_splice", "splice_mismatch"), ("no_replacement", "unchanged_source"),
])
def test_conflicting_facts_block_before_running_code(observations, criterion, case, reason, tmp_path, monkeypatch, kernel_double):
    file, source, repo = observations
    if case == "missing":
        observations.pop()
    elif case == "duplicate":
        observations.append(file)
    elif case == "incomplete":
        observations[2] = repo.model_copy(update={"complete": False})
    elif case == "hash":
        observations[0] = file.model_copy(update={"sha_after": "a" * 64})
    elif case == "path":
        observations[1] = source.model_copy(update={"path": Path("other.py")})
    elif case == "extra_file":
        observations[2] = repo.model_copy(update={"changes": [*repo.changes, kernel_double.repo_change(path=Path("extra.py"))]})
    elif case == "other_diff":
        observations[2] = repo.model_copy(update={"diff": repo.diff.replace("tool.py", "other.py")})
    elif case == "empty_diff":
        observations[2] = repo.model_copy(update={"diff": ""})
    elif case == "stale_diff":
        observations[2] = repo.model_copy(update={"diff": repo.diff.replace("x + 1", "x + 3")})
    elif case == "wrong_hunk":
        observations[2] = repo.model_copy(update={"diff": repo.diff.replace("@@ -1,2 +1,2 @@", "@@ -2,2 +2,2 @@")})
    elif case == "truncated_diff":
        observations[2] = repo.model_copy(update={"diff": repo.diff.rsplit(" def g", 1)[0]})
    elif case == "outside_splice":
        after = source.after.replace(b"x - 1", b"x - 2")
        observations[0] = file.model_copy(update={"sha_after": sha256(after).hexdigest()})
        observations[1] = source.model_copy(update={"after": after})
    elif case == "no_replacement":
        observations[0] = file.model_copy(update={"n_replacements": 0})

    def forbidden(*args, **kwargs):
        raise AssertionError("invalid observations reached execution")

    monkeypatch.setattr(verifier.gates, "check_sources", forbidden)
    result = verifier.run(criterion, observations, artifact_root=tmp_path, timeout=10)
    assert result.verification != "passed"
    assert result.effect == "unproven"
    assert result.reason == reason
    assert list(tmp_path.iterdir()) == []


def test_green_facts_bind_the_durable_receipt(observations, criterion, tmp_path, journal_double):
    result = verifier.run(criterion, observations, artifact_root=tmp_path, timeout=10)
    assert result.verification == "passed"
    assert result.effect == "confirmed"
    assert result.facts == observations
    key = RecordKey(kind="verification", value=("mission", "node", 1, criterion.relation))
    artifact = result.after.artifact_path
    receipt = verifier.emit_receipt("node", 1, observations, artifact, key=key, verdict=result, journal=journal_double)
    assert receipt is not None
    assert journal_double.events[-1].payload["effect"] == "confirmed"
    assert journal_double.events[-1].payload["scope"] == "node_verification"

    with pytest.raises(ValueError, match="facts"):
        verifier.emit_receipt("node", 1, observations[:1], artifact, key=key, verdict=result, journal=journal_double)

    # le reçu doit être durable même si les trois gates sont vertes
    journal_double.disk_full = True
    receipt = verifier.emit_receipt("node", 1, observations, artifact, key=key, verdict=result, journal=journal_double)
    assert receipt is None
    assert len(journal_double.events) == 1

    # remplacer après coup les sources et leurs empreintes ne transfère pas la preuve
    file, source, repo = observations
    after = source.after.replace(b"x + 1", b"x + 3")
    swapped = [
        file.model_copy(update={"sha_after": sha256(after).hexdigest()}),
        source.model_copy(update={"after": after}),
        repo.model_copy(update={"diff": repo.diff.replace("x + 1", "x + 3")}),
    ]
    forged = result.model_copy(update={"facts": swapped})
    with pytest.raises(ValueError, match="verified sources"):
        verifier.emit_receipt("node", 1, swapped, artifact, key=key, verdict=forged, journal=journal_double)


def test_fact_gate_reads_only_its_own_artifacts(observations, criterion, tmp_path, monkeypatch):
    original = Path.open

    def checked(path, *args, **kwargs):
        assert path.is_relative_to(tmp_path), path

        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", checked)
    result = verifier.run(criterion, observations, artifact_root=tmp_path, timeout=10)
    assert result.verification == "passed"


@pytest.mark.parametrize("variant", ["crlf", "bom", "no_final_newline", "two_hunks", "insertion", "deletion"])
def test_git_hunks_match_the_source_copies(observations, variant):
    file, source, repo = observations
    before, after, diff = source.before, source.after, repo.diff
    if variant == "crlf":
        before, after = before.replace(b"\n", b"\r\n"), after.replace(b"\n", b"\r\n")
    elif variant == "bom":
        before, after = b"\xef\xbb\xbf" + before, b"\xef\xbb\xbf" + after
        diff = diff.replace("-def f", "-\ufeffdef f").replace("+def f", "+\ufeffdef f")
    elif variant == "no_final_newline":
        before, after = before.rstrip(b"\n"), after.rstrip(b"\n")
        diff += "\\ No newline at end of file\n"
    elif variant == "two_hunks":
        before, after = b"a\nb\nc\nd\n", b"A\nb\nc\nD\n"
        diff = "diff --git a/tool.py b/tool.py\n--- a/tool.py\n+++ b/tool.py\n@@ -1 +1 @@\n-a\n+A\n@@ -4 +4 @@\n-d\n+D\n"
    elif variant == "insertion":
        before, after = b"a\n", b"b\na\n"
        diff = "diff --git a/tool.py b/tool.py\n--- a/tool.py\n+++ b/tool.py\n@@ -0,0 +1 @@\n+b\n"
    elif variant == "deletion":
        before, after = b"b\na\n", b"a\n"
        diff = "diff --git a/tool.py b/tool.py\n--- a/tool.py\n+++ b/tool.py\n@@ -1 +0,0 @@\n-b\n"
    facts = [
        file.model_copy(update={
            "sha_before": sha256(before).hexdigest(),
            "sha_after": sha256(after).hexdigest(),
            "spliced_range": (1, len(before.splitlines())),
        }),
        source.model_copy(update={"before": before, "after": after}),
        repo.model_copy(update={"diff": diff}),
    ]
    assert fact_error(facts) is None


@pytest.mark.parametrize("case,reason", [("invalid_shape", "invalid_facts"), ("encoding", "source_encoding")])
def test_invalid_observations_are_not_executed(observations, criterion, tmp_path, monkeypatch, case, reason):
    file, source, repo = observations
    if case == "invalid_shape":
        observations[2] = repo.model_copy(update={"complete": "true"})
    else:
        before = source.before.replace(b"x + 2", b"x + \xff")
        observations[0] = file.model_copy(update={"sha_before": sha256(before).hexdigest()})
        observations[1] = source.model_copy(update={"before": before})

    def forbidden(*args, **kwargs):
        raise AssertionError("invalid facts reached execution")

    monkeypatch.setattr(verifier.gates, "check_sources", forbidden)
    if case == "invalid_shape":
        with pytest.warns(UserWarning, match="Pydantic serializer warnings"):
            result = verifier.run(criterion, observations, artifact_root=tmp_path, timeout=10)
    else:
        result = verifier.run(criterion, observations, artifact_root=tmp_path, timeout=10)
    assert result.reason == reason
    assert result.effect == "unproven"


def test_memory_fact_gate_replays_without_io(observations, criterion, tmp_path, monkeypatch, double):
    actual = verifier.run(criterion, observations, artifact_root=tmp_path, timeout=10)
    memory = double("verifier").MemoryVerifier([(criterion, actual)])
    assert isinstance(memory, verifier.Verifier)

    def forbidden(*args, **kwargs):
        raise AssertionError("double performed I/O")

    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    replay = memory.run(criterion, observations, artifact_root=tmp_path, timeout=10)
    assert replay == actual
    replay.facts.clear()
    assert memory.run(criterion, observations, artifact_root=tmp_path, timeout=10) == actual
    with pytest.raises(ValueError, match="facts"):
        memory.run(criterion, [], artifact_root=tmp_path, timeout=10)


def test_fact_validation_spends_the_same_time_budget(observations, criterion, tmp_path, monkeypatch):
    clock = iter([0, 11])

    def forbidden(*args, **kwargs):
        raise AssertionError("gate started after deadline")

    monkeypatch.setattr(verifier.gates.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(verifier.gates, "check_sources", forbidden)
    result = verifier.run(criterion, observations, artifact_root=tmp_path, timeout=10)
    assert result.verification == "blocked"
    assert result.reason == "budget_exhausted"
