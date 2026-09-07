"""Corpus partagé disque/mémoire, déplaçable dans tests/contracts après exception."""

import importlib.util
import inspect
from hashlib import sha256
from pathlib import Path

import pytest

from kernel.errors import PithosError
from kernel.facts import FileFact
from workspace import StaleContentError, TransactionPort, Workspace, WorkspacePort


def load_double(name):
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(f"workspace_contract_{name}", root / f"tests/doubles/{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


@pytest.fixture(params=["disk", "memory"])
def backend(request, tmp_path):
    files = {tmp_path / "tool.py": b"\xef\xbb\xbf# keep\r\ndef f(x):\r\n    return x\r\n"}
    if request.param == "memory":
        workspace = load_double("workspace").MemoryWorkspace(tmp_path, files)

        return workspace, workspace.files.__getitem__, workspace.files.__setitem__

    view = load_double("kernel").MemoryCodeView(files)
    workspace = Workspace(tmp_path, view=view, trace=load_double("journal"))
    for path, content in files.items():
        path.write_bytes(content)

    return workspace, Path.read_bytes, Path.write_bytes


def test_protocol_and_signatures(backend):
    workspace, _, _ = backend
    transaction = workspace.transaction(workspace.root / "tool.py")
    assert isinstance(workspace, WorkspacePort)
    assert isinstance(transaction, TransactionPort)
    for protocol, instance in ((WorkspacePort, workspace), (TransactionPort, transaction)):
        for name, method in protocol.__dict__.items():
            if not callable(method) or name.startswith("_"):
                continue
            expected = list(inspect.signature(method).parameters)[1:]
            actual = list(inspect.signature(getattr(instance, name)).parameters)
            assert actual == expected


def test_changed_bytes_and_fact_agree(backend):
    workspace, read, _ = backend
    path = workspace.root / "tool.py"
    before = read(path)
    fact = workspace.splice(path, "f", "def f(x):\n    return 7")
    assert FileFact.model_validate_json(fact.model_dump_json()) == fact
    assert fact.sha_before == sha256(before).hexdigest()
    assert fact.sha_after == sha256(read(path)).hexdigest()
    assert read(path) == before.replace(b"return x", b"return 7")


@pytest.mark.parametrize("target,source", [
    (".git/tool.py", "def f(x): pass"),
    ("tool.py", "{}"),
    ("tool.py", "def f(x, y): pass"),
    ("tool.py", "def f(x): break"),
    ("tool.py", "def f(x):\n    return x"),
])
def test_first_five_guards_have_same_outcome(backend, target, source):
    workspace, read, _ = backend
    path = workspace.root / "tool.py"
    before = read(path)
    with pytest.raises(PithosError):
        workspace.splice(Path(target), "f", source)
    assert read(path) == before


def test_sixth_guard_preserves_competing_content(backend):
    workspace, read, write = backend
    path = workspace.root / "tool.py"
    other = b"def f(x): return 99\n"
    with pytest.raises(StaleContentError):
        with workspace.transaction(path) as transaction:
            write(path, other)
            transaction.splice("f", "def f(x): return 7")
    assert read(path) == other


def test_rollback_and_failed_attempt_remain_inspectable(backend):
    workspace, read, _ = backend
    path = workspace.root / "tool.py"
    before = read(path)
    with pytest.raises(RuntimeError):
        with workspace.transaction(path) as transaction:
            transaction.splice("f", "def f(x): return 7")
            raise RuntimeError("red")
    assert read(path) == before
    assert transaction.last_plan.content != before
    assert transaction.before == before


def test_projection_and_policy(backend):
    workspace, _, _ = backend
    assert workspace.project(Path("tool.py"), 2, 2) == "def f(x):\r\n"
    with pytest.raises(PithosError):
        workspace.project(Path(".git/tool.py"), 1, 1)
    with pytest.raises(PithosError):
        workspace.project(Path("../outside.py"), 1, 1)


def test_memory_double_has_no_io(monkeypatch):
    module = load_double("workspace")
    root = Path("/memory")
    path = root / "tool.py"
    workspace = module.MemoryWorkspace(root, {path: b"def f(x): return x\n"})

    def forbidden(*args, **kwargs):
        raise AssertionError("double performed I/O")

    for name in ("resolve", "open", "read_bytes", "write_bytes", "stat"):
        monkeypatch.setattr(Path, name, forbidden)
    import os
    import subprocess

    monkeypatch.setattr(os, "open", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    with workspace.transaction(path) as transaction:
        transaction.splice("f", "def f(x): return 7")
        transaction.restore()
    assert workspace.project(path, 1, 1) == "def f(x): return x\n"
