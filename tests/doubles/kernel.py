"""Constructeurs valides et codeview mémoire ; aucun accès au disque ni exécution."""

import ast
from pathlib import Path
from posixpath import normpath

from kernel.codeview import BINARY_SUFFIXES, MAX_SNIPPET_BYTES, MAX_SNIPPET_LINES, MAX_SOURCE_BYTES
from kernel.codeview import Symbol, classify_repo_path
from kernel.contracts import Criterion, Event, Node
from kernel.errors import Cause, PithosError
from kernel.facts import FileFact, Receipt


def criterion(**changes):
    values = {"relation": "total", "symbols": ["f"], "domain": "small_ints"}
    values.update(changes)

    return Criterion(**values)


def node(**changes):
    values = {
        "id": "node-1",
        "parent_id": None,
        "depth": 0,
        "target": Path("tool.py"),
        "criterion": criterion(),
        "status": "pending",
        "blocked_cause": None,
    }
    values.update(changes)

    return Node(**values)


def event(**changes):
    values = {
        "ts": "2026-09-06T00:00:00Z",
        "v": 1,
        "type": "validation",
        "durable": True,
        "payload": {},
    }
    values.update(changes)

    return Event(**values)


def file_fact(**changes):
    values = {
        "path": Path("tool.py"),
        "sha_before": "a" * 64,
        "sha_after": "b" * 64,
        "spliced_range": (1, 1),
        "n_replacements": 1,
    }
    values.update(changes)

    return FileFact(**values)


def receipt(**changes):
    values = {
        "node_id": "node-1",
        "attempt": 1,
        "returncode": 0,
        "artifact_path": Path("invariant.py"),
        "facts": [file_fact()],
    }
    values.update(changes)

    return Receipt(**values)


class MemoryCodeView:
    """Lit des sources en mémoire ; ce filesystem virtuel ne contient pas de symlinks."""

    classify_repo_path = staticmethod(classify_repo_path)  # prédicat public pur, sans état simulé

    def __init__(self, sources):
        self.sources = {Path(path): source for path, source in sources.items()}

    def _raw(self, path):
        if path not in self.sources:
            raise FileNotFoundError(path)
        source = self.sources[path]

        return source.encode("utf-8") if isinstance(source, str) else source

    def _tree(self, path):
        if path.suffix != ".py":
            detail = f"structural_unavailable:{path.suffix}"
            raise PithosError(Cause.invalid_schema, detail, "target")
        raw = self._raw(path)
        if len(raw) > MAX_SOURCE_BYTES:
            raise PithosError(Cause.invalid_schema, "oversized source", "target")

        return ast.parse(raw)

    def symbols(self, path):
        # lecture indépendante des définitions en mémoire
        result = []
        for definition in self._tree(path).body:
            if not isinstance(definition, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            args = definition.args
            vararg = args.vararg
            kwarg = args.kwarg
            positional = args.posonlyargs + args.args

            # défauts des positions et des paramètres nommés
            defaults = {}
            offset = len(positional) - len(args.defaults)
            for index, value in enumerate(args.defaults):
                name = positional[offset + index].arg
                defaults[name] = ast.unparse(value)
            for index, arg in enumerate(args.kwonlyargs):
                value = args.kw_defaults[index]
                if value is not None:
                    defaults[arg.arg] = ast.unparse(value)
            parameters = positional + args.kwonlyargs
            parameters.extend(arg for arg in (vararg, kwarg) if arg is not None)

            # projection d'annotations sans évaluation
            annotations = {}
            for arg in parameters:
                if arg.annotation is not None:
                    annotations[arg.arg] = ast.unparse(arg.annotation)
            if definition.returns is not None:
                annotations["return"] = ast.unparse(definition.returns)
            result.append(Symbol(
                name=definition.name,
                arity=len(positional),
                posonly=[arg.arg for arg in args.posonlyargs],
                kwonly=[arg.arg for arg in args.kwonlyargs],
                defaults=defaults,
                annotations=annotations,
                vararg=vararg.arg if vararg is not None else None,
                kwarg=kwarg.arg if kwarg is not None else None,
            ))

        return result

    def module_defs(self, path):
        kinds = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        names = [node.name for node in self._tree(path).body if isinstance(node, kinds)]

        return names

    def snippet(self, path, start, end):
        if start < 1 or end < start:
            raise ValueError("invalid inclusive line range")
        raw = self._raw(path)[:MAX_SNIPPET_BYTES]
        lines = raw.splitlines(keepends=True)
        end = min(end, start - 1 + MAX_SNIPPET_LINES)
        selected = b"".join(lines[start - 1:end])
        text = selected.decode("utf-8", errors="replace")
        bounded = text.encode("utf-8")[:MAX_SNIPPET_BYTES]

        return bounded.decode("utf-8", errors="ignore")

    def is_binary(self, path):
        if path.suffix.lower() in BINARY_SUFFIXES:
            return True
        raw = self._raw(path)[:4096]
        if raw.startswith((b"\xff\xfe", b"\xfe\xff", b"\x00\x00\xfe\xff")) or b"\0" in raw:
            return True
        controls = sum(byte < 9 or 13 < byte < 32 for byte in raw)

        return bool(raw) and controls / len(raw) > 0.3

    def is_path_within(self, child, parent):
        normalized = Path(normpath(str(child)))

        return normalized.is_relative_to(Path(normpath(str(parent))))
