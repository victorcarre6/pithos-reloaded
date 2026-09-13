"""Graphe d'import de campaign.

Deux propriétés y sont mécaniques plutôt que déclaratives : **aucune décision de politique ne peut
appeler le modèle**, puisque `bridge` et tout client réseau sont hors du graphe ; et `campaign` n'est
importé que par `refinery`.
"""

import pytest

from tests.graph import SRC, Source, assert_clean, check_imports, forbidden_calls
from tests.graph import imported_roots, process_calls, production_files, sources


ROOT = SRC / "campaign"


ALLOWED = {
    "ast", "dataclasses", "datetime", "difflib", "enum", "hashlib", "json", "pathlib", "re", "typing",
    "unicodedata", "pydantic", "journal", "kernel.contracts", "kernel.errors", "kernel.facts",
}
LOCAL = {"admit", "mcpconfig", "propose", "registry", "stop", "store"}
FORBIDDEN_CALLS = {"exec", "eval", "__import__", "compile"}


def violations(source):
    parsed = Source(source)
    errors = check_imports(parsed, allowed=ALLOWED, local=LOCAL)
    errors.extend(forbidden_calls(parsed, FORBIDDEN_CALLS))
    errors.extend(process_calls(parsed))

    return errors


def test_production_boundary():
    assert_clean(ROOT, lambda source, path: violations(source))


def test_no_policy_decision_can_reach_the_model():
    unreachable = {"bridge", "httpx", "openai", "socket", "subprocess", "urllib", "engine"}
    reached = set()
    for path in sources("campaign"):
        reached.update(imported_roots(path.read_text()))
    assert not reached & unreachable


def test_campaign_is_imported_by_refinery_only():
    importers = []
    for root in SRC.iterdir():
        if not (root / "MODULE.md").is_file() or root.name in {"campaign", "refinery"}:
            continue
        for path in production_files(root):
            if "campaign" in imported_roots(path.read_text()):
                importers.append(path)
    assert importers == []


@pytest.mark.parametrize("source", [
    "import bridge", "from bridge import call", "import engine", "from engine import walk",
    "import broker", "from broker.git import push", "import httpx", "import subprocess",
    "import socket", "from kernel import secrets", "from ..bridge import call",
    "from . import bridge", "from . import store, engine", "from .bridge import call",
    "exec('x')", "eval('x')", "compile('x', 'f', 'exec')", "__import__('bridge')",
    "import os as system; system.system('git status')", "from os import popen as run; run('id')",
])
def test_the_boundary_test_detects_injected_violations(source):
    assert violations(source)
