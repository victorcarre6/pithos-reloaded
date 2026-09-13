from pathlib import Path

import pytest

from tests.state_check import check_state, count_source, measure, module_targets


@pytest.mark.parametrize("source,expected", [
    ('"""module\ndoc"""\n# comment\n\nx = 1  # inline\n', 1),
    ('def f():\n    """contract"""\n\n    return 1\n', 2),
    ('class C:\n    """contract"""\n    async def f(self):\n        """contract"""\n        return 1\n', 3),
    ('text = """data\n# not a comment\nend"""\n', 3),
    ('"""doc"""; x = 1\n', 1),
    ('@decorator\ndef f():\n    return {\n        "a": 1,\n    }\n', 5),
])
def test_code_count_excludes_only_comments_blanks_and_real_docstrings(source, expected):
    code, physical = count_source(source)
    assert code == expected
    assert physical == len(source.splitlines())


def test_measure_includes_subpackages_but_not_tests_or_doubles(tmp_path):
    (tmp_path / "api").mkdir()
    (tmp_path / "__init__.py").write_text('"""exports"""\n')
    (tmp_path / "api/__init__.py").write_text("x = 1\n")
    (tmp_path / "test_ignored.py").write_text("x = 1\n" * 20)
    (tmp_path / "conftest.py").write_text("x = 1\n" * 20)
    before = measure(tmp_path)
    assert before.code == 1
    assert before.physical == 2
    (tmp_path / "api/__init__.py").write_text("x = 2\n")
    assert measure(tmp_path).sha256 != before.sha256


def state_text(measured):
    return (
        "# STATE\n\n"
        "**Statut** : en cours\n"
        "**Mise à jour** : 11:09\n"
        f"**Lignes** : {measured.code} code / 10 cible · {measured.physical} physiques\n"
        f"**Empreinte** : {measured.sha256}\n\n"
        "## Prochaine action\nVérifier le prochain invariant.\n\n"
        "## Journal\nAnciennes mesures conservées.\n"
    )


@pytest.fixture
def module(tmp_path):
    (tmp_path / "work.py").write_text("x = 1\n")
    measured = measure(tmp_path)
    (tmp_path / "STATE.md").write_text(state_text(measured))

    return tmp_path


def test_current_header_is_accepted(module):
    assert check_state(module, 10) == []


@pytest.mark.parametrize("old,new,expected", [
    ("en cours", "non commencé", "statut"),
    ("11:09", "—", "date"),
    ("11:09", "31:02", "date"),
    ("11:09", "1:9", "date"),
    ("1 code", "0 code", "lignes"),
    ("10 cible", "11 cible", "cible"),
    ("1 physiques", "3 physiques", "physiques"),
    ("en cours", "terminé peut-être", "statut"),
])
def test_stale_or_invalid_headers_fail(module, old, new, expected):
    path = module / "STATE.md"
    path.write_text(path.read_text().replace(old, new, 1))
    assert any(expected in error for error in check_state(module, 10))


def test_same_line_count_does_not_hide_stale_state(module):
    (module / "work.py").write_text("x = 2\n")
    assert any("empreinte" in error for error in check_state(module, 10))


def test_excess_requires_a_bounded_written_justification(module):
    path = module / "STATE.md"
    source = state_text(measure(module)).replace("10 cible", "0 cible")
    path.write_text(source)
    assert any("dépassement" in error for error in check_state(module, 0))
    source += "\n**Plafond justifié** : 1 code\n**Justification** : contrat public nécessaire, corpus mesuré.\n"
    path.write_text(source)
    assert check_state(module, 0) == []
    path.write_text(source.replace("1 code\n**Justification", "0 code\n**Justification"))
    assert any("plafond" in error for error in check_state(module, 0))


def test_targets_come_from_canonical_module_table(tmp_path):
    path = tmp_path / "AGENTS.md"
    path.write_text("| 1 | `kernel` | contrats | — | ~380 L |\n| 6 | `engine` | arbre | 1-5 | ~1 050 L |\n")
    assert module_targets(path) == {"kernel": 380, "engine": 1050}


def test_missing_module_table_is_not_a_vacuous_success(tmp_path):
    path = tmp_path / "AGENTS.md"
    path.write_text("# No module table\n")
    with pytest.raises(ValueError, match="cibles"):
        module_targets(path)


def test_repository_state_headers_match_current_production():
    root = Path(__file__).resolve().parents[1]
    targets = module_targets(root / "AGENTS.md")
    assert len(targets) == 11
    errors = {}
    for module, target in targets.items():
        found = check_state(root / "src" / module, target)
        if found:
            errors[module] = found
    assert errors == {}
