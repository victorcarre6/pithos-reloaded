"""Graphe d'import du socle observatory."""

import ast

import pytest

from tests.graph import SRC, Source, assert_clean, check_imports, forbidden_calls


ROOT = SRC / "observatory"

ALLOWED = {
    "ast", "collections", "dataclasses", "datetime", "itertools", "os.path", "pathlib", "typing",
    "json", "hashlib", "argparse",
    "fastapi", "uvicorn", "journal", "kernel.contracts", "kernel.errors",
}
LOCAL = {"index", "render", "routes", "stats", "evidence", "api.index", "api.render", "api.routes", "api.stats", "api.evidence"}
# `journal` possède l'écriture ; l'observatoire n'en consomme que la lecture
JOURNAL_WRITERS = {"journal.emit", "journal.bind", "journal.update_json_locked"}


def violations(source):
    parsed = Source(source)
    errors = check_imports(parsed, allowed=ALLOWED, local=LOCAL)
    errors.extend(forbidden_calls(parsed, {"exec", "eval", "__import__"}))
    for node in parsed.attributes:
        resolved = parsed.resolve(node)
        if resolved in JOURNAL_WRITERS:
            errors.append(resolved)
    for node in parsed.imports:
        if isinstance(node, ast.ImportFrom) and node.module == "journal":
            errors.extend(f"journal.{alias.name}" for alias in node.names if f"journal.{alias.name}" in JOURNAL_WRITERS)

    return errors


def test_production_boundary():
    assert_clean(ROOT, lambda source, path: violations(source))


@pytest.mark.parametrize("source", [
    "import engine", "from campaign import store", "import verifier", "from workspace import splice",
    "import broker", "from bridge import call", "import lifecycle", "from refinery import gate",
    "import httpx", "import subprocess", "import socket", "import sqlite3", "import duckdb",
    "from kernel import secrets", "from ..bridge import call", "from .missing import thing",
    "exec('x')", "eval('x')", "__import__('engine')",
    "journal.emit(event)", "import journal as j; j.emit(event)",
    "from journal import bind", "journal.update_json_locked(path, fn)",
])
def test_boundary_test_detects_injected_violations(source):
    assert violations(source)
