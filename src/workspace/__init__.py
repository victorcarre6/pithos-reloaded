"""Autorité filesystem : racine explicite, fonction existante et fait mesuré."""

from pathlib import Path

import journal
from kernel import codeview
from kernel.errors import Cause, PithosError
from kernel.facts import FileFact

from .paths import checked_path
from .protocol import TransactionPort, WorkspacePort
from .splice import SplicePlan, prepare_splice
from .transaction import StaleContentError, Transaction


class Workspace:
    def __init__(self, root: Path, *, view=codeview, trace=journal):
        self.root = root.resolve()
        self.view = view
        self.trace = trace

    def transaction(self, target: Path) -> Transaction:
        return Transaction(target, root=self.root, view=self.view, trace=self.trace)

    def splice(self, target: Path, function_name: str, new_source: str) -> FileFact:
        with self.transaction(target) as transaction:
            return transaction.splice(function_name, new_source)

    def project(self, target: Path, start: int, end: int) -> str:
        path = checked_path(target, self.root, self.view)
        if self.view.is_binary(path):
            raise PithosError(Cause.invalid_path, "binary projection refused", "target")

        return self.view.snippet(path, start, end)


def splice(target: Path, function_name: str, new_source: str, *, root: Path, view=codeview, trace=journal) -> FileFact:
    return Workspace(root, view=view, trace=trace).splice(target, function_name, new_source)
