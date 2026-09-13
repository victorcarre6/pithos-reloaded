"""Graphe d'import de `journal` — niveau 1 : il ne connaît que `kernel`.

Forme compacte : le scan rend l'ensemble des racines importées, et le test le compare à un ensemble
autorisé fermé. C'est la même garantie que les scanners AST plus longs des autres modules, écrite en
moins de lignes parce que ce module n'a aucun cas particulier à traiter.
"""

import pytest

from tests.graph import SRC, Source, assert_clean, check_imports
from tests.graph import imported_roots, sources


ROOT = SRC / "journal"


ALLOWED = {
    "dataclasses", "datetime", "fcntl", "hashlib", "json", "os", "pathlib", "threading", "time",
    "typing", "uuid", "kernel",
}
MODULES = {"bridge", "broker", "campaign", "engine", "lifecycle", "observatory", "refinery",
           "verifier", "workspace"}


def test_production_boundary():
    assert_clean(ROOT, lambda source, path: violations(source))


def test_journal_reaches_no_other_module():
    reached = {root for path in sources("journal") for root in imported_roots(path.read_text())}

    assert reached & MODULES == set()


def test_journal_speaks_no_network():
    # la contrainte dure n°5 : seul `broker` fait sortir une donnée
    reached = {root for path in sources("journal") for root in imported_roots(path.read_text())}

    assert reached & {"httpx", "socket", "urllib", "requests", "subprocess"} == set()


@pytest.mark.parametrize("source", [
    "import bridge", "from engine import walk", "import httpx", "import subprocess",
    "from verifier import gates", "import socket",
])
def test_the_scan_detects_an_injected_violation(source):
    assert imported_roots(source) - ALLOWED


LOCAL = {"read", "redact", "write"}


def violations(source):
    return check_imports(Source(source), allowed=set(), local=LOCAL, roots=ALLOWED)
