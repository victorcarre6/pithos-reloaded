"""Graphe d'import de `bridge` — niveau 2, et la deuxième des trois règles d'`AGENTS.md` § 3.

⚠️ **`bridge` n'importe jamais `engine`** !
→ La frontière modèle est en dessous du moteur, jamais l'inverse. La règle est ici, mécanique.

`httpx` y est légitime : c'est le seul module qui parle au serveur du modèle. Sa borne au loopback est
testée par `src/bridge/test_client.py`, pas par le graphe d'imports.
"""

import pytest

from tests.graph import SRC, Source, assert_clean, check_imports
from tests.graph import imported_roots, sources


ROOT = SRC / "bridge"


ALLOWED = {
    "dataclasses", "datetime", "enum", "hashlib", "json", "os", "pathlib", "typing", "urllib",
    "httpx", "pydantic", "kernel", "journal", "time",
}
FORBIDDEN_MODULES = {"engine", "campaign", "refinery", "verifier", "workspace", "broker",
                     "lifecycle", "observatory"}


def test_production_boundary():
    assert_clean(ROOT, lambda source, path: violations(source))


def test_bridge_never_imports_engine():
    # deuxième règle d'AGENTS.md § 3, tenue par le graphe et non par la discipline
    reached = {root for path in sources("bridge") for root in imported_roots(path.read_text())}

    assert reached & FORBIDDEN_MODULES == set()


def test_bridge_starts_no_process():
    reached = {root for path in sources("bridge") for root in imported_roots(path.read_text())}

    assert reached & {"subprocess", "multiprocessing", "socket"} == set()


@pytest.mark.parametrize("source", [
    "import engine", "from engine.walk import walk", "import campaign", "from verifier import gates",
    "import subprocess", "import socket", "from workspace import splice",
])
def test_the_scan_detects_an_injected_violation(source):
    assert imported_roots(source) - ALLOWED


LOCAL = {"client", "probe", "revalidate", "schema"}


def violations(source):
    return check_imports(Source(source), allowed=set(), local=LOCAL, roots=ALLOWED)
