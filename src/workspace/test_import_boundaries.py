"""Graphe d'import du socle workspace, déplaçable dans tests/boundaries."""

import ast
from pathlib import Path

import pytest


ALLOWED = {
    "ast", "datetime", "difflib", "hashlib", "io", "os", "pathlib", "re", "stat",
    "tempfile", "threading", "tokenize", "typing", "journal", "kernel.codeview",
    "kernel.contracts", "kernel.errors", "kernel.facts", "kernel.protocol",
}
LOCAL = {"paths", "protocol", "splice", "transaction"}


def violations(source):
    tree = ast.parse(source)
    errors = []
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name] = alias.name
                if alias.name not in ALLOWED:
                    errors.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                if node.level != 1 or node.module not in LOCAL:
                    errors.append(f"relative:{node.module}")
                continue
            for alias in node.names:
                name = f"{node.module}.{alias.name}"
                aliases[alias.asname or alias.name] = name
                if node.module == "kernel":
                    if name not in ALLOWED:
                        errors.append(name)
                elif node.module not in ALLOWED:
                    errors.append(name)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {"exec", "eval", "__import__"}:
                errors.append(node.func.id)

    # os est nécessaire au filesystem, jamais pour lancer un programme
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = ast.unparse(node.func)
        prefix, _, suffix = name.partition(".")
        resolved = aliases.get(prefix, prefix) + (f".{suffix}" if suffix else "")
        if resolved.startswith(("os.exec", "os.spawn", "os.system", "os.popen", "os.fork")):
            errors.append(resolved)

    return errors


def test_workspace_imports_only_its_dependencies():
    root = Path(__file__).resolve().parents[2] / "src/workspace"
    sources = [path for path in root.glob("*.py") if not path.name.startswith("test_") and path.name != "conftest.py"]
    assert sources
    assert {path.name: violations(path.read_text()) for path in sources} == {path.name: [] for path in sources}


@pytest.mark.parametrize("source", [
    "import verifier", "from bridge import ask", "import engine", "from campaign import run",
    "import broker", "from kernel import secrets", "from journal.write import emit",
    "from ..bridge import ask", "import subprocess", "import socket", "import httpx",
    "exec('x')", "eval('x')", "__import__('bridge')",
    "import os as system; system.system('git status')", "from os import popen as run; run('git status')",
])
def test_boundary_test_detects_injected_violations(source):
    assert violations(source)
