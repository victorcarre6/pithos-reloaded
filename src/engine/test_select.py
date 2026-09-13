"""Sélection et fermeture sur un index fourni, sans découverte ni appel modèle."""

from pathlib import Path
import subprocess

import pytest

from engine.classify import RepoIndex
from engine.select import impact_files, import_closure, relevant_files


@pytest.fixture
def index():
    return RepoIndex(
        files=(Path("api.py"), Path("codec.py"), Path("util.py"), Path("tests/test_api.py"), Path("other.py")),
        imports={
            Path("api.py"): (Path("codec.py"),),
            Path("codec.py"): (Path("util.py"),),
            Path("util.py"): (Path("codec.py"),),
            Path("tests/test_api.py"): (Path("api.py"),),
        },
    )


def test_relevant_files_preserve_classifier_reasons(index):
    selected = relevant_files("fix api.py", index)
    assert [(row.target, row.reason) for row in selected] == [(Path("api.py"), "instruction_path")]
    assert relevant_files("unrelated request", index) == ()


def test_forward_closure_deduplicates_cycles_and_keeps_target(index):
    selected = import_closure([Path("api.py"), Path("api.py")], index)
    reasons = {row.target: row.reason for row in selected}
    assert reasons == {
        Path("api.py"): "target",
        Path("codec.py"): "dependency depth 1",
        Path("util.py"): "dependency depth 2",
    }


def test_impact_uses_reverse_edges_with_explicit_depth(index):
    immediate = impact_files(Path("codec.py"), index, depth=1)
    assert {row.target for row in immediate} == {Path("codec.py"), Path("api.py"), Path("util.py")}
    transitive = impact_files(Path("codec.py"), index, depth=2)
    reasons = {row.target: row.reason for row in transitive}
    assert reasons[Path("codec.py")] == "target"
    assert reasons[Path("tests/test_api.py")] == "imports depth 2"
    assert len(reasons) == 4


@pytest.mark.parametrize("depth", [0, -1, 6, True, 1.5])
def test_depth_is_not_coerced(index, depth):
    with pytest.raises(ValueError, match="depth"):
        impact_files(Path("codec.py"), index, depth=depth)


@pytest.mark.parametrize("method", [impact_files, import_closure])
def test_unknown_target_is_not_an_empty_success(index, method):
    target = Path("absent.py")
    argument = [target] if method is import_closure else target
    with pytest.raises(ValueError, match="target"):
        method(argument, index)


@pytest.mark.parametrize("imports", [
    {Path("unknown.py"): (Path("api.py"),)},
    {Path("api.py"): (Path("unknown.py"),)},
    {Path("api.py"): (Path("../secret.py"),)},
])
def test_edges_must_be_in_the_supplied_index(imports):
    with pytest.raises(ValueError, match="imports"):
        RepoIndex(files=(Path("api.py"),), imports=imports)


def test_runtime_files_are_excluded_even_through_imports():
    index = RepoIndex(
        files=(Path("api.py"), Path(".villani_code/state.py"), Path("other.py")),
        imports={Path("api.py"): (Path(".villani_code/state.py"),),
                 Path(".villani_code/state.py"): (Path("other.py"),)},
    )
    assert [row.target for row in import_closure([Path("api.py")], index)] == [Path("api.py")]
    with pytest.raises(ValueError, match="target"):
        impact_files(Path(".villani_code/state.py"), index)


def test_results_are_deterministic_and_perform_no_io(index, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("selection performed I/O")

    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    reordered = RepoIndex(files=tuple(reversed(index.files)), imports=dict(reversed(list(index.imports.items()))))
    assert impact_files(Path("codec.py"), index, depth=2) == impact_files(Path("codec.py"), reordered, depth=2)
    assert import_closure([Path("api.py")], index) == import_closure([Path("api.py")], reordered)
    assert relevant_files("fix api.py", index) == relevant_files("fix api.py", reordered)
