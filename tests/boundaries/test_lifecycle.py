"""Graphe d'import de `lifecycle` — niveau 2 : verrou, launchd, custody, garde disque.

`subprocess` y est légitime — `launchctl` est un exécutable — mais aucune donnée n'en sort : la
contrainte dure n°5 veut que seul `broker` parle au réseau, et le graphe le tient.
"""

import pytest

from tests.graph import SRC, Source, assert_clean, check_imports
from tests.graph import imported_roots, sources


ROOT = SRC / "lifecycle"


ALLOWED = {
    "collections", "ctypes", "datetime", "enum", "hashlib", "json", "math", "multiprocessing", "os",
    "pathlib", "signal", "struct", "subprocess", "time", "typing", "uuid", "kernel", "journal",
}
FORBIDDEN_MODULES = {"bridge", "broker", "campaign", "engine", "observatory", "refinery",
                     "verifier", "workspace"}


def test_production_boundary():
    assert_clean(ROOT, lambda source, path: violations(source))


def test_lifecycle_reaches_no_module_above_its_level():
    reached = {root for path in sources("lifecycle") for root in imported_roots(path.read_text())}

    assert reached & FORBIDDEN_MODULES == set()


def test_lifecycle_makes_no_data_leave_the_machine():
    # contrainte dure n°5 : `broker` est la seule sortie, `launchctl` n'en est pas une
    reached = {root for path in sources("lifecycle") for root in imported_roots(path.read_text())}

    assert reached & {"httpx", "socket", "urllib", "requests", "smtplib"} == set()


@pytest.mark.parametrize("source", [
    "import bridge", "import engine", "from campaign import store", "import httpx", "import socket",
    "from broker.git import push", "import urllib.request",
])
def test_the_scan_detects_an_injected_violation(source):
    assert imported_roots(source) - ALLOWED


LOCAL = {"custody", "launchd", "lock", "process"}


def violations(source):
    return check_imports(Source(source), allowed=set(), local=LOCAL, roots=ALLOWED)
