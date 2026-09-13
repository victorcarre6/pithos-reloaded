"""Frontières kernel : imports du socle et lectures déclarées."""

import ast

import pytest

from tests.graph import SRC, Source, assert_clean, check_imports, forbidden_calls


ROOT = SRC / "kernel"


EXTERNAL_IMPORTS = {"ast", "enum", "keyword", "pathlib", "typing", "pydantic"}
LOCAL_IMPORTS = {"contracts", "facts", "errors", "codeview", "protocol"}
IO_METHODS = {
    "open", "read", "read_text", "read_bytes", "write", "write_text", "write_bytes",
    "mkdir", "unlink", "rename", "replace", "rmdir", "touch", "stat", "resolve",
}


def violations(source, filename):
    parsed = Source(source)
    issues = check_imports(parsed, allowed=set(), local=LOCAL_IMPORTS, roots=EXTERNAL_IMPORTS)
    issues.extend(forbidden_calls(parsed, {"eval", "exec", "compile", "__import__", "open"}))
    for node in parsed.calls:
        function = node.func
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


def test_production_boundary():
    assert_clean(ROOT, lambda source, path: violations(source, path.as_posix()))


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
