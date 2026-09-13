"""Prouve les tests de balayage sur copies jetables, jamais sur le code de travail."""

import importlib

import pytest

from tests.graph import SRC, production_files


MODULES = (
    "kernel", "journal", "verifier", "bridge", "workspace", "engine", "campaign",
    "lifecycle", "broker", "observatory", "refinery",
)


@pytest.mark.parametrize("module", MODULES)
def test_each_production_file_can_make_its_actual_boundary_test_fail(module, tmp_path, monkeypatch):
    # copie complète, y compris les __init__.py homonymes dans les sous-paquets
    boundary = importlib.import_module(f"tests.boundaries.test_{module}")
    root = SRC / module
    paths = production_files(root)
    for path in paths:
        target = tmp_path / path.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
    nested = tmp_path / "future_package/__init__.py"
    nested.parent.mkdir()
    nested.write_text('"""Nouveau sous-paquet sans import."""\n')
    monkeypatch.setattr(boundary, "ROOT", tmp_path)
    boundary.test_production_boundary()

    # exécute le vrai test, pas seulement sa fonction violations
    forbidden = {"engine": "socket", "refinery": "bridge"}.get(module, "engine")
    for path in production_files(tmp_path):
        if module == "engine" and path == tmp_path / "flow.py":
            continue  # l'adaptateur Prefect est explicitement hors de cette règle de pureté
        original = path.read_text()
        mutated = f"{original}\nimport {forbidden}\n"
        path.write_text(mutated)
        try:
            with pytest.raises(AssertionError):
                boundary.test_production_boundary()
        finally:
            path.write_text(original)


@pytest.mark.parametrize("module", MODULES)
def test_actual_boundary_test_rejects_an_empty_scan(module, tmp_path, monkeypatch):
    boundary = importlib.import_module(f"tests.boundaries.test_{module}")
    monkeypatch.setattr(boundary, "ROOT", tmp_path)
    with pytest.raises(AssertionError, match="production"):
        boundary.test_production_boundary()


@pytest.mark.parametrize("module,filename,violation", [
    ("kernel", "codeview.py", "target.open('rb')"),
    ("verifier", "runner.py", "target.read_bytes()"),
    ("engine", "flow.py", "import socket"),
])
def test_file_specific_exemptions_do_not_cover_homonymous_subpackage_files(module, filename, violation, tmp_path, monkeypatch):
    boundary = importlib.import_module(f"tests.boundaries.test_{module}")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / filename).write_text(violation)
    monkeypatch.setattr(boundary, "ROOT", tmp_path)
    with pytest.raises(AssertionError):
        boundary.test_production_boundary()
