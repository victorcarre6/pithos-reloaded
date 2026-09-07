"""Rendu fixe des invariants de la décision 2, sur une copie appartenant au verifier."""

import ast
from pathlib import Path
from textwrap import indent

from kernel.contracts import Criterion, Domain, Relation
from kernel.errors import Cause, PithosError

from .domains import DOMAIN_CODE


SEED = 0
BODIES = {
    Relation.round_trip: "assert g(f(deepcopy(x))) == x",
    Relation.idempotent: "first = f(deepcopy(x))\nassert f(deepcopy(first)) == first",
    Relation.commutes_with: "assert f(g(deepcopy(x))) == g(f(deepcopy(x)))",
    Relation.preserves: "assert g(f(deepcopy(x))) == g(deepcopy(x))",
    Relation.invariant_under: "assert f(g(deepcopy(x))) == f(deepcopy(x))",
    Relation.monotone: "if x <= y:\n    assert f(deepcopy(x)) <= f(deepcopy(y))",
    Relation.total: "f(deepcopy(x))",
    Relation.raises_on: (
        "try:\n    f(deepcopy(x))\nexcept Exception as error:\n"
        "    assert type(error) is g\nelse:\n    raise AssertionError('expected exception')"
    ),
}


def body_nodes(definition):
    """Liste le corps direct d'une fonction, sans entrer dans les définitions imbriquées."""

    pending = list(reversed(definition.body))
    nodes = []
    while pending:
        node = pending.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        nodes.append(node)
        children = list(ast.iter_child_nodes(node))
        pending.extend(reversed(children))

    return nodes


def admit(criterion: Criterion, source: str) -> None:
    """Vérifie les définitions et l'appel unaire sans exécuter ni lire la cible."""

    # revalidation des collections mutables du modèle pydantic
    criterion = Criterion.model_validate(criterion.model_dump())
    if len(source.encode("utf-8")) > 2_000_000:
        raise PithosError(Cause.invalid_schema, "source_too_large", "source")
    tree = ast.parse(source)
    kinds = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    for index, name in enumerate(criterion.symbols):
        definitions = [node for node in tree.body if isinstance(node, kinds) and node.name == name]
        if len(definitions) != 1:
            raise PithosError(Cause.invalid_symbol, "missing_or_duplicate_symbol", name)
        definition = definitions[0]
        for statement in tree.body:
            if isinstance(statement, kinds):
                continue
            for node in ast.walk(statement):
                if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)) and node.id == name:
                    raise PithosError(Cause.invalid_symbol, "rebound_symbol", name)
                if isinstance(node, ast.alias):
                    imported = node.asname if node.asname is not None else node.name.split(".")[0]
                    if imported in {name, "*"}:
                        raise PithosError(Cause.invalid_symbol, "rebound_symbol", name)

        # exception déclarée ou fonction synchrone acceptant exactement un argument fourni
        if criterion.relation == Relation.raises_on and index == 1:
            if not isinstance(definition, ast.ClassDef):
                raise PithosError(Cause.invalid_symbol, "exception_class_required", name)
            continue
        if not isinstance(definition, ast.FunctionDef) or definition.decorator_list:
            raise PithosError(Cause.invalid_symbol, "plain_function_required", name)
        args = definition.args
        positional = len(args.posonlyargs) + len(args.args)
        required = positional - len(args.defaults)
        keyword_required = any(value is None for value in args.kw_defaults)
        if required > 1 or (positional < 1 and args.vararg is None) or keyword_required:
            raise PithosError(Cause.invalid_symbol, "unary_call_required", name)
        if any(isinstance(node, (ast.Yield, ast.YieldFrom)) for node in body_nodes(definition)):
            raise PithosError(Cause.invalid_symbol, "generator_not_supported", name)


def render(criterion: Criterion, target: Path) -> str:
    """Rend un script autonome ; target doit désigner la copie créée par le runner."""

    # choix fermés ; schéma de sortie et ordre partiel restent explicites
    criterion = Criterion.model_validate(criterion.model_dump())
    if criterion.relation == Relation.schema_conform:
        raise PithosError(Cause.unverifiable, "schema_binding_missing", "relation")
    if criterion.relation == Relation.monotone and criterion.domain not in {Domain.small_ints, Domain.floats_finite}:
        raise PithosError(Cause.unverifiable, "unordered_domain", "domain")
    bindings = f"f = candidate[{criterion.symbols[0]!r}]\n"
    if len(criterion.symbols) == 2:
        bindings += f"g = candidate[{criterion.symbols[1]!r}]\n"
    if criterion.relation == Relation.raises_on:
        bindings += "assert isinstance(g, type) and issubclass(g, Exception)\n"
    arguments = "x=strategy, y=strategy" if criterion.relation == Relation.monotone else "x=strategy"
    parameters = "x, y" if criterion.relation == Relation.monotone else "x"
    body = indent(BODIES[criterion.relation], "    ")
    strategy = DOMAIN_CODE[criterion.domain]

    # le rapport terminal distingue un vrai passage d'un exit prématuré du candidat
    script = (
        "# invariant rendu par verifier ; conserver avec la copie candidate\n"
        "import json\nimport runpy\nimport traceback\nfrom copy import deepcopy\nfrom pathlib import Path\n"
        "from hypothesis import given, settings, seed, strategies as st\n"
        "from hypothesis.errors import HypothesisException\n"
        f"candidate = runpy.run_path({str(target)!r})\n{bindings}"
        f"strategy = {strategy}\n"
        f"@seed({SEED})\n"
        "@settings(max_examples=100, deadline=None, database=None, report_multiple_bugs=False)\n"
        f"@given({arguments})\ndef invariant({parameters}):\n{body}\n"
        "status = 'passed'\ncode = 0\ntry:\n    invariant()\n"
        "except HypothesisException:\n    status = 'tool_error'\n    code = 70\n    traceback.print_exc()\n"
        "except Exception as error:\n    status = 'failed'\n    code = 20\n    traceback.print_exc()\n"
        "    with Path(__file__).with_name('counterexample.txt').open('x', encoding='utf-8') as stream:\n"
        "        stream.write('\\n'.join(getattr(error, '__notes__', ())))\n"
        "with Path(__file__).with_name('result.json').open('x', encoding='utf-8') as stream:\n"
        "    stream.write(json.dumps({'check': status}))\n"
        "raise SystemExit(code)\n"
    )

    return script
