"""Contrôle kernel, à installer dans tests/boundaries/ après autorisation de périmètre."""

import ast
from pathlib import Path

import pytest


EXTERNAL_IMPORTS = {"ast", "enum", "keyword", "pathlib", "typing", "pydantic"}
LOCAL_IMPORTS = {"contracts", "facts", "errors", "codeview", "protocol"}
IO_METHODS = {
    "open", "read", "read_text", "read_bytes", "write", "write_text", "write_bytes",
    "mkdir", "unlink", "rename", "replace", "rmdir", "touch", "stat", "resolve",
}


def violations(source, filename):
    """Contrôle les imports directs et les appels d'I/O du code kernel."""

    issues = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in EXTERNAL_IMPORTS:
                    issues.append((node.lineno, "import", alias.name))
        if isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if node.level:
                allowed = node.level == 1 and root in LOCAL_IMPORTS
            else:
                allowed = root in EXTERNAL_IMPORTS
            if not allowed:
                issues.append((node.lineno, "import", root))
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if isinstance(function, ast.Name) and function.id in {"eval", "exec", "compile", "__import__", "open"}:
            issues.append((node.lineno, "execution", function.id))
        if not isinstance(function, ast.Attribute) or function.attr not in IO_METHODS:
            continue
        if filename != "codeview.py":
            issues.append((node.lineno, "io", function.attr))
        elif function.attr not in {"open", "read", "resolve"}:
            issues.append((node.lineno, "write", function.attr))
        elif function.attr == "open":
            modes = [arg.value for arg in node.args if isinstance(arg, ast.Constant)]
            if modes != ["rb"]:
                issues.append((node.lineno, "mode", modes))

    return issues


def test_kernel_import_graph_and_io_boundaries():
    root = Path(__file__).resolve().parents[2]
    paths = (root / "src/kernel").rglob("*.py")
    production = [path for path in paths if not path.name.startswith("test_")]
    assert production  # un dossier vide ne constitue pas une preuve
    issues = {}
    for path in production:
        found = violations(path.read_text(), path.name)
        if found:
            issues[str(path)] = found
    assert issues == {}


@pytest.mark.parametrize("source,filename", [
    ("import engine", "contracts.py"), ("from bridge import client", "codeview.py"),
    ("from .engine import walk", "contracts.py"), ("from .. import engine", "facts.py"),
    ("import socket", "codeview.py"), ("import logging", "errors.py"),
    ("import subprocess", "codeview.py"), ("__import__('engine')", "codeview.py"),
    ("exec(source)", "codeview.py"), ("target.read_text()", "contracts.py"),
    ("target.open('w')", "codeview.py"), ("target.write_bytes(b'x')", "codeview.py"),
])
def test_boundary_checker_detects_forbidden_operations(source, filename):
    assert violations(source, filename)


def test_boundary_checker_allows_declared_reads():
    assert violations("from .facts import FileFact", "contracts.py") == []
    assert violations("path.open('rb').read(8000)", "codeview.py") == []
