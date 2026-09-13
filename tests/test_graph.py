from pathlib import Path

import pytest

from tests.graph import Source, check_imports, production_files, scan


def test_empty_or_missing_production_is_not_a_proof(tmp_path):
    with pytest.raises(AssertionError, match="production"):
        production_files(tmp_path)
    with pytest.raises(AssertionError, match="production"):
        production_files(tmp_path / "missing")


def test_scan_keeps_homonymous_files_and_nested_sources(tmp_path):
    (tmp_path / "api").mkdir()
    (tmp_path / "__init__.py").write_text("import engine\n")
    (tmp_path / "api/__init__.py").write_text("import broker\n")
    (tmp_path / "test_ignored.py").write_text("not python!")
    (tmp_path / "conftest.py").write_text("not python!")

    def check(source, path):
        return check_imports(Source(source), allowed=set(), local=set())

    found = scan(tmp_path, check)
    assert set(found) == {Path("__init__.py"), Path("api/__init__.py")}
    assert all(found.values())


@pytest.mark.parametrize("source", [
    "import engine", "from engine import walk", "from ..engine import walk",
    "from .. import engine", "from . import engine", "from .allowed import thing\nimport engine",
])
def test_import_policy_rejects_absolute_and_relative_escapes(source):
    assert check_imports(Source(source), allowed={"pathlib"}, local={"allowed"})


def test_import_policy_preserves_declared_submodules():
    source = Source("from kernel import facts\nfrom . import allowed\nimport pathlib")
    assert check_imports(source, allowed={"kernel.facts", "pathlib"}, local={"allowed"}) == []
    assert check_imports(Source("from kernel import secrets"), allowed={"kernel.facts"}, local=set())


@pytest.mark.parametrize("code,expected", [
    ("import os as system\nsystem.system('x')", "os.system"),
    ("from os import popen as run\nrun('x')", "os.popen"),
    ("import os.path\nos.path.exists('x')", "os.path.exists"),
    ("import journal as j\nj.emit(event)", "journal.emit"),
])
def test_call_aliases_are_resolved(code, expected):
    source = Source(code)
    assert source.resolve(source.calls[-1].func) == expected


def test_names_include_relative_targets_without_confusing_symbols_with_modules():
    source = Source("from pathlib import Path\nfrom . import engine\nfrom ..bridge import call")
    assert source.imported_names() == {"pathlib", "engine", "bridge"}
