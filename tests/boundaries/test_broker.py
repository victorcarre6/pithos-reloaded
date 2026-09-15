"""Graphe d'import du broker, et l'egress unique du projet."""

import pytest

from tests.graph import SRC, Source, assert_clean, check_imports, forbidden_calls
from tests.graph import imported_names, sources


ROOT = SRC / "broker"

ALLOWED = {
    "datetime", "enum", "functools", "hashlib", "json", "math", "os", "pathlib", "re", "subprocess", "time", "typing", "uuid",
    "httpx", "pydantic", "journal", "journal.redact", "kernel.contracts", "kernel.errors",
    "kernel.facts",
}
LOCAL = {"finalize", "git", "identity", "intent", "telegram"}
FORBIDDEN_MODULES = {"bridge", "campaign", "engine", "lifecycle", "observatory", "refinery", "verifier", "workspace"}


def violations(source):
    parsed = Source(source)
    errors = check_imports(parsed, allowed=ALLOWED, local=LOCAL)
    errors.extend(forbidden_calls(parsed, {"exec", "eval", "__import__"}))

    return errors


def test_production_boundary():
    assert_clean(ROOT, lambda source, path: violations(source))


@pytest.mark.parametrize("source", [
    "import engine", "from campaign import run", "import verifier", "from bridge import ask",
    "import workspace", "from observatory import stats", "from git import GitPython",
    "from ..bridge import ask", "from .flow import walk",
    "exec('x')", "eval('x')", "__import__('engine')",
])
def test_boundary_test_detects_injected_violations(source):
    assert violations(source)


def test_broker_never_reaches_a_module_above_it():
    imported = set()
    for path in sources("broker"):
        imported.update(name.split(".")[0] for name in imported_names(path.read_text()))

    assert imported & FORBIDDEN_MODULES == set()


def test_broker_is_the_only_egress_module():
    """Seuls `broker` et `bridge` parlent HTTP, et `bridge` est borné au loopback par son client.

    Cette borne-là est testée dans `src/bridge/test_client.py` ; ici on garde l'ensemble fermé.
    """

    modules = [path.name for path in SRC.iterdir() if path.is_dir() and not path.name.startswith("_")]
    speakers = {module for module in modules
                for path in sources(module) if "httpx" in imported_names(path.read_text())}

    assert speakers == {"bridge", "broker"}


def test_no_module_opens_a_raw_socket():
    modules = [path.name for path in SRC.iterdir() if path.is_dir() and not path.name.startswith("_")]
    openers = {module for module in modules
               for path in sources(module) if imported_names(path.read_text()) & {"socket", "socketserver"}}

    assert openers == set()
