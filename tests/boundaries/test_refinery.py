"""Graphe d'import de refinery.

Deux propriétés y sont mécaniques plutôt que déclaratives : **aucun chemin d'exécution du socle
n'atteint ce module**, puisque personne ne l'importe ; et le plan de raffinement ne peut appeler aucun
modèle, `bridge` et tout client réseau étant hors de son graphe.
"""


from pathlib import Path

import pytest

from tests.graph import SRC, Source, assert_clean, check_imports, forbidden_calls
from tests.graph import imported_roots, process_calls, sources


ROOT = SRC / "refinery"


ALLOWED = {
    "ast", "enum", "math", "pathlib", "typing", "pydantic", "campaign.stop", "campaign.store",
    "kernel.contracts", "kernel.errors",
}
LOCAL = {"gate", "propose"}
FORBIDDEN_CALLS = {"exec", "eval", "__import__", "compile"}


def violations(source):
    parsed = Source(source)
    errors = check_imports(parsed, allowed=ALLOWED, local=LOCAL)
    errors.extend(forbidden_calls(parsed, FORBIDDEN_CALLS))
    errors.extend(process_calls(parsed))

    return errors


def test_production_boundary():
    assert_clean(ROOT, lambda source, path: violations(source))


def reaches_refinery(source):
    return "refinery" in imported_roots(source)


def test_no_module_imports_refinery():
    # c'est la forme mécanique de `enabled: false` : aucun chemin du socle n'atteint ce module
    root = Path(__file__).resolve().parents[2] / "src"
    reached = []
    for module in sorted(entry.name for entry in root.iterdir() if entry.is_dir()):
        if module == "refinery":
            continue
        reached += [f"{module}/{path.name}" for path in sources(module) if reaches_refinery(path.read_text())]

    assert reached == []


@pytest.mark.parametrize("source", [
    "import refinery", "from refinery import gate", "from refinery.gate import Decision",
    "import refinery.propose", "import refinery as r",
])
def test_the_reachability_scan_detects_an_injected_call_path(source):
    assert reaches_refinery(source)


@pytest.mark.parametrize("source", ["import campaign", "from campaign.store import Store", "x = 1"])
def test_the_reachability_scan_does_not_cry_wolf(source):
    assert not reaches_refinery(source)


def test_no_refinement_decision_can_reach_the_model():
    unreachable = {"bridge", "httpx", "openai", "socket", "subprocess", "urllib", "engine"}
    reached = set()
    for path in sources("refinery"):
        reached.update(imported_roots(path.read_text()))
    assert not reached & unreachable


@pytest.mark.parametrize("source", [
    "import bridge", "from bridge import call", "import engine", "import broker", "import httpx",
    "import subprocess", "import socket", "from campaign import admit", "from kernel import secrets",
    "from . import bridge", "from .bridge import call", "from ..bridge import call",
    "exec('x')", "eval('x')", "compile('x', 'f', 'exec')", "__import__('bridge')",
    "import os as system; system.system('git status')", "from os import popen as run; run('id')",
])
def test_the_boundary_test_detects_injected_violations(source):
    assert violations(source)
