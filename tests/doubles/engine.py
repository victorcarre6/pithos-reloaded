"""Rejeu des arbres fournis au constructeur ; aucune dépendance exécutée."""

from engine.tree import Tree


class MemoryEngine:
    def __init__(self, trees):
        self.trees = [Tree.model_validate_json(tree.model_dump_json()) for tree in trees]

    def run_attempt(self, tree, node_id, budget, deps, *, tree_path, artifact_root,
                    system, instruction, attempt) -> Tree:
        scripted = self.trees.pop(0)

        return Tree.model_validate_json(scripted.model_dump_json())
