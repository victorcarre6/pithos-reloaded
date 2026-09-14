"""Rejeu des arbres fournis au constructeur ; aucune dépendance exécutée."""

from engine.tree import Tree
from engine.dump import parse, render


class MemoryEngine:
    def __init__(self, trees):
        self.trees = [Tree.model_validate_json(tree.model_dump_json()) for tree in trees]

    def run_attempt(self, tree, node_id, budget, deps, *, tree_path, artifact_root,
                    system, instruction, attempt) -> Tree:
        scripted = self.trees.pop(0)

        return Tree.model_validate_json(scripted.model_dump_json())

    def walk(self, tree, budget, deps) -> Tree:
        scripted = self.trees.pop(0)

        return Tree.model_validate_json(scripted.model_dump_json())


class MemoryFinalizer:
    """Publication scénarisée par identité logique ; aucun Git ni filesystem."""

    def __init__(self, results):
        self.results = list(results)
        self.recorded = {}
        self.calls = []

    def reconcile(self, key, receipt, timeout):
        self.calls.append(("reconcile", key, receipt, timeout))

        return self.recorded.get(key)

    def finalize(self, key, receipt, timeout):
        self.calls.append(("finalize", key, receipt, timeout))
        if key not in self.recorded:
            self.recorded[key] = self.results.pop(0)

        return self.recorded[key]


class MemoryContextArchive:
    """Même sérialisation que CONTEXT.md, conservée en mémoire sans filesystem."""

    def __init__(self):
        self.files = {}

    def dump(self, section, *, path):
        self.files[path] = self.files.get(path, "") + render(section)

    def read(self, mission_id, *, path):
        return parse(self.files.get(path, ""), mission_id)
