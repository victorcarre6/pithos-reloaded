"""Contrôle documentaire inspiré de Graphify, limité aux interfaces explicitement livrées."""

import ast
import importlib
import inspect

HEADING = "## Interfaces observables — 13:09"


def rows(text):
    "Lit la table de contrat, sans confondre objectifs de module et livraison."

    if HEADING not in text:
        raise ValueError("missing interface inventory")
    section = text.split(HEADING, 1)[1].split("\n## ", 1)[0]
    entries = []
    for line in section.splitlines():
        cells = [cell.strip().strip("`") for cell in line.split("|")[1:-1]]
        if len(cells) == 3 and cells[0] in {"livré", "prévu"}:
            entries.append(tuple(cells))
    if not entries:
        raise ValueError("empty interface inventory")

    return entries


def check(entries):
    "Compare noms, ordre, modes de passage et présence des valeurs par défaut, sans exécuter les fonctions."

    issues = []
    for status, module_name, documented in entries:
        if status == "prévu":
            continue
        try:
            node = ast.parse(f"def {documented}: ...").body[0]
            module = importlib.import_module(module_name)
            function = getattr(module, node.name)
            parameters = inspect.signature(function).parameters.values()
            actual = [(param.name, param.kind, param.default is not inspect.Parameter.empty) for param in parameters]
        except (SyntaxError, AttributeError, ImportError, TypeError, ValueError) as failure:
            issues.append(f"{module_name}.{documented}: {failure}")
            continue

        # une signature décrite reste un AST : aucune expression du document n'est évaluée
        args = node.args
        positional = args.posonlyargs + args.args
        required = len(positional) - len(args.defaults)
        expected = []
        for position, param in enumerate(positional):
            kind = inspect.Parameter.POSITIONAL_ONLY if position < len(args.posonlyargs) else inspect.Parameter.POSITIONAL_OR_KEYWORD
            expected.append((param.arg, kind, position >= required))
        if args.vararg is not None:
            expected.append((args.vararg.arg, inspect.Parameter.VAR_POSITIONAL, False))
        for param, default in zip(args.kwonlyargs, args.kw_defaults):
            expected.append((param.arg, inspect.Parameter.KEYWORD_ONLY, default is not None))
        if args.kwarg is not None:
            expected.append((args.kwarg.arg, inspect.Parameter.VAR_KEYWORD, False))
        if actual != expected:
            issues.append(f"{module_name}.{documented}: signature differs: {actual}")

    return issues
