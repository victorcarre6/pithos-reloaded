"""Frontières verifier ; tests partagés à déplacer après autorisation de périmètre."""

import ast
from pathlib import Path
import subprocess
import sys

import pytest

from kernel.contracts import Criterion
from verifier.runner import execute


ALLOWED = {
    "ast", "copy", "datetime", "hashlib", "hypothesis", "json", "math", "os", "pathlib",
    "signal", "subprocess", "sys", "tempfile", "textwrap", "time", "typing", "pydantic", "journal", "kernel",
}
LOCAL = {"gates", "models", "protocol", "receipt", "domains", "runner", "relations", "mutation"}
FILESYSTEM = {"open", "read_text", "read_bytes", "write_text", "write_bytes", "unlink", "mkdir", "rmdir", "resolve", "glob", "rglob", "iterdir"}


def violations(source, module):
    errors = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                if node.level != 1 or node.module not in LOCAL:
                    errors.append("relative import")
                continue
            names = [node.module]
            if node.module == "kernel":
                names = [f"kernel.{alias.name}" for alias in node.names]
        else:
            names = []
        for name in names:
            if name.split(".")[0] not in ALLOWED:
                errors.append(f"forbidden import: {name}")
            if name.startswith("kernel.") and name not in {"kernel.contracts", "kernel.errors", "kernel.facts"}:
                errors.append("kernel implementation")
            if name.startswith("journal."):
                errors.append("journal implementation")
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id in {"exec", "eval", "__import__", "open"}:
            errors.append("dynamic execution or bare I/O")
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in FILESYSTEM and module != "runner":
                errors.append("I/O outside runner")
            if node.func.attr in {"Popen", "run", "call", "check_call", "check_output", "system", "popen"}:
                if module != "runner" or node.func.attr != "Popen":
                    errors.append("unowned process")

    return errors


def test_production_import_graph():
    root = Path(__file__).resolve().parents[2]
    for path in (root / "src/verifier").glob("*.py"):
        if path.name.startswith("test_") or path.name == "conftest.py":
            continue
        assert violations(path.read_text(), path.stem) == [], path


@pytest.mark.parametrize("source", [
    "import bridge", "from engine import walk", "import workspace", "import broker", "import lifecycle",
    "import httpx", "from kernel import codeview", "from journal.write import emit",
    "from ..bridge import call", "Path('workspace.py').read_bytes()", "subprocess.run(['git', 'status'])",
    "os.system('git status')", "exec('code')", "__import__('bridge')",
])
def test_boundary_guard_detects_violations(source):
    assert violations(source, "gates")


def test_runner_accesses_only_its_new_artifacts(tmp_path, monkeypatch):
    owned = tmp_path / "owned"
    owned.mkdir()
    original_open = Path.open
    original_popen = subprocess.Popen
    accessed = []

    def checked_open(path, *args, **kwargs):
        assert path.is_relative_to(owned), path
        accessed.append(path)

        return original_open(path, *args, **kwargs)

    def checked_popen(command, **kwargs):
        assert command[:3] == [sys.executable, "-I", "-B"]
        assert Path(command[3]).is_relative_to(owned)
        assert kwargs["cwd"].is_relative_to(owned)
        assert kwargs.get("shell", False) is False
        assert set(kwargs["env"]) == {"HYPOTHESIS_STORAGE_DIRECTORY"}

        return original_popen(command, **kwargs)

    monkeypatch.setattr(Path, "open", checked_open)
    monkeypatch.setattr(subprocess, "Popen", checked_popen)
    criterion = Criterion(relation="total", symbols=["f"], domain="small_ints")
    result = execute(criterion, "def f(x): return x", artifact_root=owned, timeout=10)
    assert result.check == "passed"
    assert accessed
