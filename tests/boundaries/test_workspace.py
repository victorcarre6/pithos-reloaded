"""Graphe d'import du socle workspace."""

import pytest

from tests.graph import SRC, Source, assert_clean, check_imports, forbidden_calls
from tests.graph import process_calls


ROOT = SRC / "workspace"


ALLOWED = {
    "ast", "datetime", "difflib", "hashlib", "io", "os", "pathlib", "re", "stat",
    "tempfile", "threading", "tokenize", "typing", "journal", "kernel.codeview",
    "kernel.contracts", "kernel.errors", "kernel.facts", "kernel.protocol",
}
LOCAL = {"paths", "protocol", "splice", "transaction"}


def violations(source):
    parsed = Source(source)
    errors = check_imports(parsed, allowed=ALLOWED, local=LOCAL)
    errors.extend(forbidden_calls(parsed, {"exec", "eval", "__import__"}))
    errors.extend(process_calls(parsed))

    return errors


def test_production_boundary():
    assert_clean(ROOT, lambda source, path: violations(source))


@pytest.mark.parametrize("source", [
    "import verifier", "from bridge import ask", "import engine", "from campaign import run",
    "import broker", "from kernel import secrets", "from journal.write import emit",
    "from ..bridge import ask", "import subprocess", "import socket", "import httpx",
    "exec('x')", "eval('x')", "__import__('bridge')",
    "import os as system; system.system('git status')", "from os import popen as run; run('git status')",
])
def test_boundary_test_detects_injected_violations(source):
    assert violations(source)
