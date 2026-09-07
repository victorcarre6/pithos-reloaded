"""Filesystem d'octets en mémoire ; mêmes gardes pures, aucune I/O ni symlink."""

from pathlib import Path
from posixpath import normpath

from kernel.codeview import BINARY_SUFFIXES, MAX_SNIPPET_BYTES, MAX_SNIPPET_LINES, MAX_SOURCE_BYTES
from kernel.codeview import PathClass, classify_repo_path
from kernel.errors import Cause, PithosError
from workspace import StaleContentError, prepare_splice
from workspace.paths import normalized_target


class MemoryWorkspace:
    def __init__(self, root, files):
        self.root = Path(normpath(str(root)))
        self.files = {self._canonical(Path(path)): bytes(raw) for path, raw in files.items()}

    def _canonical(self, target):
        normalized = normalized_target(target, self.root)

        return Path(normpath(str(normalized)))

    def _path(self, target):
        path = self._canonical(target)
        if not path.is_relative_to(self.root):
            raise PithosError(Cause.invalid_path, "target escapes workspace", "target")
        if classify_repo_path(path.relative_to(self.root)) != PathClass.authoritative:
            raise PithosError(Cause.invalid_path, "target is not authoritative", "target")

        return path

    def _read(self, path):
        if path not in self.files:
            raise FileNotFoundError(path)
        content = self.files[path]
        if len(content) > MAX_SOURCE_BYTES:
            raise PithosError(Cause.invalid_schema, "oversized source", "target")

        return content

    def transaction(self, target):
        return MemoryTransaction(self, target)

    def splice(self, target, function_name, new_source):
        with self.transaction(target) as transaction:
            return transaction.splice(function_name, new_source)

    def project(self, target, start, end):
        path = self._path(target)
        if path not in self.files:
            raise FileNotFoundError(path)
        raw = self.files[path]
        head = raw[:4096]
        controls = sum(byte < 9 or 13 < byte < 32 for byte in head)
        binary = b"\0" in head or head.startswith((b"\xff\xfe", b"\xfe\xff"))
        if path.suffix.lower() in BINARY_SUFFIXES or binary or (head and controls / len(head) > 0.3):
            raise PithosError(Cause.invalid_path, "binary projection refused", "target")
        if start < 1 or end < start:
            raise ValueError("invalid inclusive line range")
        lines = raw[:MAX_SNIPPET_BYTES].splitlines(keepends=True)
        end = min(end, start - 1 + MAX_SNIPPET_LINES)
        selected = b"".join(lines[start - 1:end]).decode("utf-8", errors="replace")
        bounded = selected.encode("utf-8")[:MAX_SNIPPET_BYTES]

        return bounded.decode("utf-8", errors="ignore")


class MemoryTransaction:
    def __init__(self, workspace, target):
        self.workspace = workspace
        self.target = target
        self.before = None
        self.last_plan = None
        self.active = False
        self.changed = False

    def __enter__(self):
        if self.before is not None:
            raise RuntimeError("transaction is single-use")
        self.path = self.workspace._path(self.target)
        self.before = self.workspace._read(self.path)
        self.active = True

        return self

    def __exit__(self, exc_type, exc, traceback):
        try:
            if exc is not None and self.changed:
                self.restore()
        except BaseException as restore_error:
            raise BaseExceptionGroup("transaction and restoration failed", [exc, restore_error]) from None
        finally:
            self.active = False

        return False

    def _require_active(self):
        if not self.active:
            raise RuntimeError("transaction is not active")

    def splice(self, function_name, new_source):
        self._require_active()
        if self.path.suffix != ".py":
            raise PithosError(Cause.invalid_path, "expected Python target", "target")
        self.last_plan = prepare_splice(self.before, function_name, new_source, target=self.path)
        self.cas_write(self.last_plan.content)

        return self.last_plan.fact

    def cas_write(self, content):
        self._require_active()
        if len(content) > MAX_SOURCE_BYTES:
            raise PithosError(Cause.invalid_schema, "oversized source", "content")
        if self.workspace._read(self.path) != self.before:
            raise StaleContentError(self.path)
        self.workspace.files[self.path] = bytes(content)
        self.changed = True

    def restore(self):
        self._require_active()
        self.workspace._read(self.path)
        self.workspace.files[self.path] = self.before
        self.changed = False
