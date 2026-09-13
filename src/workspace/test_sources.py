"""Snapshots publics relus sur le filesystem réel et son double."""

from hashlib import sha256

import pytest

from kernel.facts import SourceFact


@pytest.fixture(params=["disk", "memory"])
def backend(request, tmp_path, workspace, double):
    path = tmp_path / "tool.py"
    raw = b"\xef\xbb\xbf# keep\r\ndef f(x):\r\n    return x + 1\r\n"
    if request.param == "memory":
        memory = double("workspace").MemoryWorkspace(tmp_path, {path: raw})

        return memory, path, raw, memory.files.__setitem__
    path.write_bytes(raw)

    return workspace, path, raw, type(path).write_bytes


def test_public_snapshot_agrees_with_actual_splice_and_survives_restore(backend):
    workspace, path, before, _ = backend
    with workspace.transaction(path) as transaction:
        fact = transaction.splice("f", "def f(x):\n    return x")
        sources = transaction.source_fact()
        assert sources.path == fact.path
        assert sources.before == before
        assert sha256(sources.before).hexdigest() == fact.sha_before
        assert sha256(sources.after).hexdigest() == fact.sha_after
        assert SourceFact.model_validate_json(sources.model_dump_json()) == sources
        transaction.restore()
        restored = transaction.source_fact()

    assert restored.before == restored.after == before
    assert sources.after != before


def test_snapshot_observes_external_bytes_instead_of_reusing_the_plan(backend):
    workspace, path, before, write = backend
    with workspace.transaction(path) as transaction:
        transaction.splice("f", "def f(x):\n    return x")
        external = b"# external\n"
        write(path, external)
        observed = transaction.source_fact()

    assert observed.before == before
    assert observed.after == external


def test_snapshot_requires_an_active_transaction(backend):
    workspace, path, _, _ = backend
    transaction = workspace.transaction(path)
    with pytest.raises(RuntimeError, match="not active"):
        transaction.source_fact()
    with transaction:
        transaction.source_fact()
    with pytest.raises(RuntimeError, match="not active"):
        transaction.source_fact()
