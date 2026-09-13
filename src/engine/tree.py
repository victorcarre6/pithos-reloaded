"""État du domaine ; dispositions liées au résultat, sans ledger d'arbre parallèle.

Adaptation de ouroboros/ouroboros/task_tree_ledger.py:108-168,384-433.
"""

import json
from hashlib import sha256
from typing import Literal

from pydantic import Field, StrictInt, model_validator

from kernel.contracts import Contract, Name, Node
from kernel.facts import Digest


class ChildDisposition(Contract):
    parent_id: Name
    child_id: Name
    disposition: Literal["integrated", "irrelevant", "deferred"]
    result_sha256: Digest


def result_sha256(node: Node) -> str:
    """Identifie le résultat structurel d'un nœud ; ne remplace pas un reçu d'exécution."""

    content = json.dumps(node.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))

    return sha256(content.encode("utf-8")).hexdigest()


class Tree(Contract):
    mission_id: Name
    nodes: tuple[Node, ...]
    cap_children: StrictInt = Field(gt=0)
    dispositions: tuple[ChildDisposition, ...] = ()

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
            if disposition.result_sha256 == result_sha256(child):
                current[child.id] = disposition

        return tuple(current.values())
