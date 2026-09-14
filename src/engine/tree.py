"""État du domaine ; dispositions liées au résultat, sans ledger d'arbre parallèle.

Adaptation de ouroboros/ouroboros/task_tree_ledger.py:108-168,384-433.
"""

import json
from hashlib import sha256
from typing import Literal

from pydantic import Field, StrictInt, model_validator

from kernel.contracts import Contract, Name, Node, PositiveInt
from kernel.facts import Digest, Receipt, RepoFact


class StateNotWrittenError(RuntimeError):
    """L'état observé ne peut pas être publié durablement."""


class StateConflictError(StateNotWrittenError):
    """Un autre instantané a remplacé celui que l'appelant avait observé."""


def publish(tree, updated, tree_path, journal):
    """Publie uniquement si l'instantané observé reste courant."""

    def compare(current):
        if current != {} and Tree.model_validate_json(json.dumps(current)) != tree:
            raise StateConflictError("tree changed since observation")

        return updated.model_dump(mode="json")

    journal.update_json_locked(tree_path, compare)


class ChildDisposition(Contract):
    parent_id: Name
    child_id: Name
    disposition: Literal["integrated", "irrelevant", "deferred"]
    result_sha256: Digest


def result_sha256(node: Node, receipt: Receipt | None = None) -> str:
    """Identifie le résultat du nœud, reçu compris lorsqu'il existe."""

    values = node.model_dump(mode="json")
    if receipt is not None:
        values["receipt"] = receipt.model_dump(mode="json")
    content = json.dumps(values, sort_keys=True, separators=(",", ":"))

    return sha256(content.encode("utf-8")).hexdigest()


class Tree(Contract):
    mission_id: Name
    nodes: tuple[Node, ...]
    cap_children: StrictInt = Field(gt=0)
    dispositions: tuple[ChildDisposition, ...] = ()
    attempts: dict[Name, PositiveInt] = Field(default_factory=dict)
    receipts: dict[Name, Receipt] = Field(default_factory=dict)
    finalized: dict[Name, RepoFact] = Field(default_factory=dict)

    @model_validator(mode="after")
    def consistent_graph(self):
        # unicité, parenté et profondeur excluent les cycles sans parcours récursif
        by_id = {node.id: node for node in self.nodes}
        if len(by_id) != len(self.nodes):
            raise ValueError("node ids must be unique")
        widths = {}
        for node in self.nodes:
            if node.parent_id is None:
                continue
            parent = by_id.get(node.parent_id)
            if parent is None or parent.depth + 1 != node.depth:
                raise ValueError("missing parent or inconsistent depth")
            widths[parent.id] = widths.get(parent.id, 0) + 1
        if any(width > self.cap_children for width in widths.values()):
            raise ValueError("child count exceeds cap_children")

        # chaque résultat reste attaché à la tentative réclamée dans l'arbre
        if not self.attempts.keys() <= by_id.keys():
            raise ValueError("attempt requires an existing node")
        for node_id, receipt in self.receipts.items():
            if receipt.node_id != node_id or receipt.attempt != self.attempts.get(node_id):
                raise ValueError("receipt does not match the claimed attempt")
        if not self.finalized.keys() <= self.receipts.keys():
            raise ValueError("finalization requires a receipt")
        for repo in self.finalized.values():
            if not repo.complete or not repo.head or repo.changes or repo.diff:
                raise ValueError("finalization requires a complete clean repository")

        # une disposition historique reste conservée, même quand son hash est périmé
        for disposition in self.dispositions:
            child = by_id.get(disposition.child_id)
            if child is None or child.parent_id != disposition.parent_id:
                raise ValueError("disposition requires an existing parent-child edge")

        return self

    def current_dispositions(self) -> tuple[ChildDisposition, ...]:
        """Rend la dernière disposition de chaque enfant dont le résultat n'a pas changé."""

        by_id = {node.id: node for node in self.nodes}
        current = {}
        for disposition in self.dispositions:
            child = by_id[disposition.child_id]
            if disposition.result_sha256 == result_sha256(child, self.receipts.get(child.id)):
                current[child.id] = disposition

        return tuple(current.values())
