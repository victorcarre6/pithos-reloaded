"""Conformité double ↔ implémentation, et la frontière d'import du niveau 1."""

import ast
import inspect
import sys
from pathlib import Path

import journal
from journal import Journal

MODULE_DIR = Path(__file__).resolve().parent
INTERNAL_MODULES = {path.name for path in MODULE_DIR.parent.iterdir() if path.is_dir()}


def test_the_implementation_satisfies_the_protocol():
    assert isinstance(journal, Journal)


def test_the_double_satisfies_the_protocol(double):
    assert isinstance(double("journal"), Journal)


def test_double_and_implementation_share_every_public_signature(double):
    journal_double = double("journal")

    for name in journal.__all__:
        implementation = getattr(journal, name)
        if not inspect.isfunction(implementation):
            continue
        assert inspect.signature(getattr(journal_double, name)) == inspect.signature(implementation), name


def module_imports() -> set[str]:
    "Modules importés par le code du journal, tests exclus : la frontière porte sur le module."

    sources = [path for path in MODULE_DIR.glob("*.py") if not path.name.startswith(("test_", "conftest"))]
    imported = set()
    for source_path in sources:
        for node in ast.walk(ast.parse(source_path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                imported.add(node.module.split(".")[0])

    return imported


def test_journal_imports_no_module_above_kernel():
    assert module_imports() & INTERNAL_MODULES == {"kernel"}


def test_journal_imports_nothing_outside_the_standard_library():
    external = module_imports() - INTERNAL_MODULES - sys.stdlib_module_names

    assert external == set()
