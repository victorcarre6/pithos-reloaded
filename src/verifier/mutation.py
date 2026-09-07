"""Mutations AST à un seul site ; un échec d'outillage n'est jamais un kill."""

import ast
from copy import deepcopy
from pathlib import Path
import time
from typing import Iterator

from kernel.contracts import Criterion

from .models import KillReport, MutationAttempt
from .relations import body_nodes
from .runner import execute


MAX_MUTANTS = 64


class AtNode(ast.NodeTransformer):
    def __init__(self, target):
        self.target = target

    def visit(self, node):
        if node is self.target:
            return self.replace(node)

        return super().visit(node)


class ReturnNone(AtNode):
    name = "return_none"

    @staticmethod
    def accepts(node):
        return isinstance(node, ast.Return) and node.value is not None

    def replace(self, node):
        return ast.Return(value=ast.Constant(value=None))


class InvertIf(AtNode):
    name = "invert_if"

    @staticmethod
    def accepts(node):
        return isinstance(node, ast.If)

    def replace(self, node):
        node.test = ast.UnaryOp(op=ast.Not(), operand=node.test)

        return node


class SwapArithmetic(AtNode):
    name = "swap_arithmetic"
    pairs = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.FloorDiv, ast.FloorDiv: ast.Mult, ast.Div: ast.Mult}

    @classmethod
    def accepts(cls, node):
        return isinstance(node, ast.BinOp) and type(node.op) in cls.pairs

    def replace(self, node):
        node.op = self.pairs[type(node.op)]()

        return node


class FlipCompare(AtNode):
    name = "flip_compare"
    pairs = {ast.Lt: ast.Gt, ast.Gt: ast.Lt, ast.LtE: ast.GtE, ast.GtE: ast.LtE, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}

    @classmethod
    def accepts(cls, node):
        return isinstance(node, ast.Compare) and type(node.ops[0]) in cls.pairs

    def replace(self, node):
        node.ops[0] = self.pairs[type(node.ops[0])]()

        return node


class ShiftNumber(AtNode):
    name = "shift_number"

    @staticmethod
    def accepts(node):
        return isinstance(node, ast.Constant) and isinstance(node.value, (int, float))

    def replace(self, node):
        value = not node.value if isinstance(node.value, bool) else node.value + 1

        return ast.Constant(value=value)


OPERATORS = (ReturnNone, InvertIf, SwapArithmetic, FlipCompare, ShiftNumber)


def mutants(source: str) -> Iterator[tuple[str, str]]:
    """Produit des mutations distinctes, compilables, dans les corps de fonctions uniquement."""

    # inventaire stable ; ni annotations, ni paramètres, ni constantes du module
    tree = ast.parse(source)
    original = ast.unparse(tree)
    seen = {original}
    nodes = []
    for definition in tree.body:
        if isinstance(definition, ast.FunctionDef):
            nodes.extend(body_nodes(definition))

    # chaque transformation repart d'une copie complète de l'ast original
    for operator in OPERATORS:
        for node in nodes:
            if not operator.accepts(node):
                continue
            memo = {}
            copied = deepcopy(tree, memo)
            changed = operator(memo[id(node)]).visit(copied)
            rendered = ast.unparse(ast.fix_missing_locations(changed))
            if rendered in seen:
                continue
            compile(rendered, "<mutant>", "exec")  # validation seule ; cet objet code n'est jamais exécuté
            seen.add(rendered)
            name = f"{operator.name}:{node.lineno}:{node.col_offset}"
            yield name, rendered


def kill_check(criterion: Criterion, source: str, *, artifact_root: Path, timeout: float) -> KillReport:
    """Exige une baseline verte puis un kill effectif sous un budget mural partagé."""

    # un invariant déjà rouge ne peut attribuer aucun échec à une mutation
    started = time.monotonic()
    baseline = execute(criterion, source, artifact_root=artifact_root, timeout=timeout)
    attempts = []
    status, reason = "blocked", "baseline_not_green"
    if baseline.check == "passed":
        reason = "no_mutants"
        for index, (name, mutated) in enumerate(mutants(source)):
            remaining = timeout - (time.monotonic() - started)
            if remaining <= 0:
                status, reason = "blocked", "budget_exhausted"
                break
            if index >= MAX_MUTANTS:
                status, reason = "blocked", "mutant_limit"
                break
            result = execute(criterion, mutated, artifact_root=artifact_root, timeout=remaining)
            attempts.append(MutationAttempt(operator=name, result=result))
            if result.check == "not_run":
                status, reason = "blocked", "execution_failure"
                break
            if result.check == "failed":
                status, reason = "killed", "killed"
                break
            status, reason = "survived", "survived"

    return KillReport(status=status, reason=reason, baseline=baseline, attempts=tuple(attempts))
