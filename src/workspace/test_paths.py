from pathlib import Path

import pytest

from kernel.errors import PithosError


@pytest.mark.parametrize("name", [".git/tool.py", "build/tool.py", ".venv/tool.py", ".hidden.py", "private_key.pem"])
def test_same_policy_blocks_writes_and_projection(workspace, name):
    path = workspace.root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"def f(x): return x\n")
    for action in (
        lambda: workspace.splice(path, "f", "def f(x): return 7"),
        lambda: workspace.project(path, 1, 2),
        lambda: workspace.transaction(path).__enter__(),
    ):
        with pytest.raises(PithosError):
            action()
    assert path.read_bytes() == b"def f(x): return x\n"


@pytest.mark.parametrize("name", ["../outside.py", "../campaign2/tool.py", "/etc/passwd"])
def test_escape_is_refused_before_read(workspace, name, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("read outside workspace")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    with pytest.raises(PithosError):
        workspace.splice(Path(name), "f", "def f(x): return 7")


def test_symlink_escape_and_root_alias(workspace, tmp_path, kernel_double):
    from workspace import Workspace

    inside = workspace.root / "inside"
    inside.mkdir()
    outside = workspace.root / "outside.py"
    outside.write_bytes(b"def f(x): return x\n")
    (inside / "alias.py").symlink_to(outside)
    root_alias = workspace.root / "root_alias"
    root_alias.symlink_to(inside, target_is_directory=True)
    narrowed = Workspace(root_alias, view=kernel_double.MemoryCodeView({}))
    with pytest.raises(PithosError):
        narrowed.splice(Path("alias.py"), "f", "def f(x): return 7")
    assert outside.read_bytes() == b"def f(x): return x\n"


def test_symlink_to_non_authoritative_target_is_refused(workspace):
    build = workspace.root / "build"
    build.mkdir()
    target = build / "tool.py"
    target.write_bytes(b"def f(x): return x\n")
    alias = workspace.root / "tool.py"
    alias.symlink_to(target)
    with pytest.raises(PithosError):
        workspace.splice(alias, "f", "def f(x): return 7")


def test_normalization_precedes_policy(workspace):
    directory = workspace.root / "src"
    directory.mkdir()
    target = directory / "tool.py"
    target.write_bytes(b"def f(x): return x\n")
    fact = workspace.splice(Path('".\\src\\tool.py"'), "f", "def f(x): return 7")
    assert fact.path == target


def test_projection_delegates_bounded_read_to_double(workspace):
    target = workspace.root / "tool.py"
    workspace.view.sources[target] = b"def f(x):\n    return x\n"
    assert workspace.project(target, 1, 1) == "def f(x):\n"


def test_missing_target_is_not_created(workspace):
    target = workspace.root / "missing.py"
    with pytest.raises(FileNotFoundError):
        workspace.splice(target, "f", "def f(x): return 7")
    assert not target.exists()
