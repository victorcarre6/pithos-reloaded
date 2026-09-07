"""Contrat kernel, à installer dans tests/contracts/ après autorisation de périmètre."""

import importlib.util
import inspect
from pathlib import Path

import pytest
from pydantic import ValidationError

from kernel import codeview
from kernel.contracts import Criterion, Event, Node
from kernel.facts import FileFact, Receipt
from kernel.protocol import CodeView


@pytest.fixture
def double():
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("kernel_double", root / "tests/doubles/kernel.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_double_and_implementation_satisfy_protocol(double):
    memory = double.MemoryCodeView({})
    assert isinstance(codeview, CodeView)
    assert isinstance(memory, CodeView)
    names = [name for name in CodeView.__dict__ if not name.startswith("_")]
    for name in names:
        real_signature = inspect.signature(getattr(codeview, name))
        fake_signature = inspect.signature(getattr(memory, name))
        assert list(real_signature.parameters) == list(fake_signature.parameters)


@pytest.mark.parametrize("factory,model", [
    ("node", Node), ("criterion", Criterion), ("event", Event),
    ("file_fact", FileFact), ("receipt", Receipt),
])
def test_constructors_return_valid_serializable_models(double, factory, model):
    value = getattr(double, factory)()
    assert isinstance(value, model)
    assert model.model_validate_json(value.model_dump_json()) == value


def test_double_does_not_bypass_model_rejections(double):
    with pytest.raises(ValidationError):
        double.node(target=[Path("one"), Path("two")])
    assert double.receipt(returncode=None).returncode is None


def test_memory_and_disk_agree_on_structural_corpus(double, tmp_path):
    source = (
        'def first(a: tuple, /, b: float = 0.25, *args: int, flag: bool, end=None, **kwargs) -> tuple:\n'
        '    return a\n'
        'async def second(*, required: str, optional=1):\n'
        '    pass\n'
        'class Tool:\n'
        '    pass\n'
    )
    path = tmp_path / "tool.py"
    path.write_text(source)
    memory = double.MemoryCodeView({path: source})
    assert memory.symbols(path) == codeview.symbols(path)
    assert memory.module_defs(path) == codeview.module_defs(path)
    assert memory.snippet(path, 2, 3) == codeview.snippet(path, 2, 3)
    assert memory.is_binary(path) == codeview.is_binary(path)
    assert memory.is_path_within(path, tmp_path)
    assert not memory.is_path_within(tmp_path / "other" / "a", tmp_path / "repo")
    assert memory.classify_repo_path(Path("tool.py")) == codeview.PathClass.authoritative


def test_memory_reads_no_files_and_executes_no_source(double, monkeypatch):
    path = Path("tool.py")
    source = 'raise RuntimeError("never execute")\ndef f(x: int):\n    return x\n'
    memory = double.MemoryCodeView({path: source})

    def forbidden(*args, **kwargs):
        raise AssertionError("the double touched the filesystem")

    for name in ("open", "read_text", "read_bytes", "resolve"):
        monkeypatch.setattr(Path, name, forbidden)
    assert memory.symbols(path)[0].name == "f"
    assert memory.module_defs(path) == ["f"]
    assert memory.snippet(path, 2, 2) == "def f(x: int):\n"
    assert not memory.is_binary(path)
    assert memory.is_path_within(path, Path("."))
    assert memory.classify_repo_path(path) == codeview.PathClass.authoritative
    assert double.node().target == path


@pytest.mark.parametrize("raw", [b"\0", b"\xff\xfe", b"\x01" * 4 + b"a" * 6, b"plain"])
def test_memory_binary_matches_disk(double, tmp_path, raw):
    path = tmp_path / "file.txt"
    path.write_bytes(raw)
    memory = double.MemoryCodeView({path: raw})
    assert memory.is_binary(path) == codeview.is_binary(path)


def test_memory_preserves_read_errors(double, tmp_path):
    missing = tmp_path / "missing.py"
    memory = double.MemoryCodeView({})
    for reader in (codeview, memory):
        with pytest.raises(FileNotFoundError):
            reader.symbols(missing)
        with pytest.raises(FileNotFoundError):
            reader.snippet(missing, 1, 1)
