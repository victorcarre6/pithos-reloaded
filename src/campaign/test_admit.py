"""L'admission déclarative : toutes les violations en une fois, chacune avec son chemin de champ."""

import pytest

from campaign.admit import ARGUMENT_ROOT, FORBIDDEN, Err, Ok, Proposal, Violation, admit
from kernel.errors import Cause


VALID = {
    "name": "read_csv",
    "title": "read a csv file into rows",
    "description": "a tool that parses a csv file and returns its rows",
    "evidence": ["mission-3 asked twice for csv parsing"],
    "blast_radius": "file",
    "source": "model",
    "module": "tools.csv",
    "call": "read",
    "arguments": ["path", "delimiter"],
    "template": "read_csv --path {{args.path}} --delimiter {{args.delimiter}}",
    "criterion": None,
}


def paths(verdict):
    return sorted(violation.field_path for violation in verdict.violations)


def test_a_well_formed_proposal_is_admitted():
    verdict = admit(dict(VALID))

    assert isinstance(verdict, Ok)
    assert isinstance(verdict.value, Proposal)
    assert verdict.value.name == "read_csv"


def test_a_proposal_with_three_defects_yields_three_violations_and_three_paths():
    verdict = admit({**VALID, "name": "Read CSV!", "module": "os.path", "evidence": []})

    assert isinstance(verdict, Err)
    assert paths(verdict) == ["evidence", "module", "name"]
    assert all(violation.detail for violation in verdict.violations)


def test_the_shape_and_the_rules_are_reported_in_the_same_pass():
    broken = {key: value for key, value in VALID.items() if key != "call"}
    verdict = admit({**broken, "name": "1bad"})

    assert paths(verdict) == ["call", "name"]


@pytest.mark.parametrize("character", sorted(FORBIDDEN - {"{", "}"}))
def test_no_shell_metacharacter_survives_in_a_tool_name(character):
    verdict = admit({**VALID, "name": f"read{character}csv"})

    assert isinstance(verdict, Err)
    assert paths(verdict) == ["name"]


@pytest.mark.parametrize("template", [
    "read_csv {{ $(rm -rf /) }}",
    "read_csv {{ `id` }}",
    "read_csv {{ 1 + 1 }}",
    "read_csv {{args.path | sh}}",
    "read_csv {{}}",
    "read_csv {{args.path.suffix}}",
    "read_csv {{args}}",
    "read_csv {{env.HOME}}",
])
def test_an_evaluable_or_open_placeholder_is_refused(template):
    verdict = admit({**VALID, "template": template})

    assert isinstance(verdict, Err)
    assert paths(verdict) == ["template.0"]


def test_a_placeholder_must_name_an_argument_the_proposal_declares():
    verdict = admit({**VALID, "template": "read_csv --path {{args.undeclared}}"})

    assert paths(verdict) == ["template.0"]
    assert "undeclared" in verdict.violations[0].detail


def test_every_open_placeholder_is_reported_not_only_the_first():
    verdict = admit({**VALID, "template": "{{ $(id) }} then {{ `id` }} then {{args.path}}"})

    assert paths(verdict) == ["template.0", "template.1"]


@pytest.mark.parametrize("template", [
    "read_csv; rm -rf /", "read_csv && id", "read_csv `id`", "read_csv $HOME",
    "read_csv > /etc/passwd", "read_csv {args.path}", "read_csv }}",
])
def test_a_template_carries_no_shell_metacharacter_outside_its_placeholders(template):
    verdict = admit({**VALID, "template": template})

    assert paths(verdict) == ["template"]


@pytest.mark.parametrize("module", ["os.path", "subprocess", "tools", ".tools.csv", "Tools.Csv"])
def test_a_module_outside_the_allowed_prefixes_is_refused(module):
    verdict = admit({**VALID, "module": module})

    assert paths(verdict) == ["module"]


def test_a_proposal_without_evidence_does_not_exist():
    # une opportunité sans preuve n'existe pas : la règle vient de la source, pas de nous
    verdict = admit({**VALID, "evidence": []})

    assert paths(verdict) == ["evidence"]


def test_a_violation_carries_a_closed_cause_and_survives_json():
    verdict = admit({**VALID, "name": "no"})
    violation = verdict.violations[0]

    assert isinstance(violation.cause, Cause)
    assert Violation.model_validate_json(violation.model_dump_json()) == violation


def test_admit_never_reads_a_field_it_cannot_type():
    verdict = admit({"name": 7, "module": [], "template": {}, "arguments": "path"})

    assert isinstance(verdict, Err)
    assert "name" in paths(verdict)


def test_the_argument_root_is_the_only_one_the_grammar_opens():
    assert ARGUMENT_ROOT == "args"


@pytest.mark.parametrize("argument", ["path;id", "PATH", "1st", "a b", "x" * 65, "path.suffix"])
def test_a_declared_argument_obeys_the_same_closed_alphabet(argument):
    verdict = admit({**VALID, "arguments": [argument], "template": "read_csv"})

    assert "arguments.0" in paths(verdict)


def test_an_illegal_argument_name_is_refused_by_the_template_grammar_too():
    # sans la grammaire fermée, un argument déclaré ferait passer n'importe quel contenu d'accolades
    verdict = admit({**VALID, "arguments": ["path;id"], "template": "read_csv {{args.path;id}}"})

    assert paths(verdict) == ["arguments.0", "template.0"]


def test_a_foreign_root_is_refused_even_when_it_names_a_declared_argument():
    # sans la racine fermée, `{{env.path}}` passerait au seul motif que `path` est déclaré
    verdict = admit({**VALID, "template": "read_csv {{env.path}}"})

    assert paths(verdict) == ["template.0"]
    assert ARGUMENT_ROOT in verdict.violations[0].detail
