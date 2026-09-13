"""Frontières du moteur pur et absence de dépendance inverse."""

import builtins
import importlib
from pathlib import Path
import subprocess

import pytest

from tests.graph import SRC, assert_clean
from tests.graph import imported_roots, sources


ROOT = SRC / "engine"


LOWER_MODULES = {"kernel", "journal", "verifier", "bridge", "workspace", "lifecycle", "broker", "observatory"}


ENGINE = SRC / "engine"


def test_no_lower_module_imports_engine():
    for name in LOWER_MODULES:
        for path in sources(name):
            assert "engine" not in imported_roots(path.read_text()), path


@pytest.mark.parametrize("source", ["import engine", "from engine.walk import walk",
                                    "from ..engine import walk", "from .. import engine"])
def test_boundary_guard_detects_upward_imports(source):
    assert "engine" in imported_roots(source)


def test_production_boundary():
    forbidden = {"prefect", "subprocess", "socket", "httpx", "requests", "broker", "campaign", "lifecycle"}
    assert_clean(ROOT, lambda source, path: imported_roots(source) & forbidden if path != Path("flow.py") else set())


def test_admission_runs_with_prefect_imports_and_subprocess_forbidden(kernel_double, journal_double, monkeypatch):
    # dependencies loaded first; the tested call uses only their memory doubles
    from engine.tree import Tree

    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name.split(".")[0] == "prefect":
            raise ModuleNotFoundError("Prefect intentionally unavailable")

        return original_import(name, *args, **kwargs)

    def forbidden_process(*args, **kwargs):
        raise AssertionError("engine admission started a subprocess")

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.setattr(subprocess, "Popen", forbidden_process)
    path = ENGINE / "walk.py"
    spec = importlib.util.spec_from_file_location("engine._without_prefect", path)
    admission = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(admission)
    tree = Tree(mission_id="mission", nodes=(kernel_double.node(criterion=None),), cap_children=2)
    result = admission.split_node(tree, tree.nodes[0].id, [], tree_path=Path("mission/tree.json"), journal=journal_double)
    assert result.nodes[0].status == "blocked"
