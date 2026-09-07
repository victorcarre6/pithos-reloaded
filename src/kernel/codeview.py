"""Lecture structurelle Python, sans exécution, index ni sélection de contexte.

Villani : villani_code/utils.py:22-27 (copie libre, resources/MANIFEST.md).
PORTED_FROM: kilocode-main/packages/opencode/src/tool/read.ts:146-195
Détection adaptée : UTF-16/32 est binaire pour notre lecteur UTF-8.
Copyright (c) 2026 Kilo Code, Copyright (c) 2025 opencode — MIT.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import ast
from enum import StrEnum
from pathlib import Path

from .contracts import Contract
from .errors import Cause, PithosError


MAX_SOURCE_BYTES = 2_000_000
MAX_SNIPPET_BYTES = 8_000
MAX_SNIPPET_LINES = 40
BINARY_SUFFIXES = {
    ".zip", ".tar", ".gz", ".exe", ".dll", ".so", ".class", ".jar", ".war",
    ".7z", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods",
    ".odp", ".bin", ".dat", ".obj", ".o", ".a", ".lib", ".wasm", ".pyc", ".pyo",
}
EDITOR_DIRS = {".vscode", ".idea"}
RUNTIME_DIRS = {
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".ipynb_checkpoints", ".venv", "venv", ".villani_code",
}
GENERATED_DIRS = {"build", "dist", "node_modules"}


class PathClass(StrEnum):
    vcs_internal = "vcs_internal"
    editor_artifact = "editor_artifact"
    runtime_artifact = "runtime_artifact"
    generated = "generated"
    authoritative = "authoritative"


class Symbol(Contract):
    name: str
    arity: int
    posonly: list[str]
    kwonly: list[str]
    defaults: dict[str, str]
    annotations: dict[str, str]
    vararg: str | None
    kwarg: str | None


def _module(path: Path) -> ast.Module:
    """Parse un module Python borné sans l'importer."""

    # langage et taille explicites ; aucune approximation par regex
    if path.suffix != ".py":
        detail = f"structural_unavailable:{path.suffix}"
        raise PithosError(Cause.invalid_schema, detail, "target")
    with path.open("rb") as stream:
        raw = stream.read(MAX_SOURCE_BYTES + 1)
    if len(raw) > MAX_SOURCE_BYTES:
        raise PithosError(Cause.invalid_schema, "oversized source", "target")

    return ast.parse(raw, filename=str(path))


def symbols(path: Path) -> list[Symbol]:
    """Décrit les fonctions du module ; arity compte toutes les positions déclarées."""

    # définitions exportables, sans méthodes ni fonctions imbriquées
    result = []
    for node in _module(path).body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        args = node.args
        positional = args.posonlyargs + args.args

        # défauts absents distincts d'un défaut littéral None
        default_args = positional[len(positional) - len(args.defaults):]
        defaults = {arg.arg: ast.unparse(value) for arg, value in zip(default_args, args.defaults)}
        for arg, value in zip(args.kwonlyargs, args.kw_defaults):
            if value is not None:
                defaults[arg.arg] = ast.unparse(value)

        # annotations textuelles uniquement ; aucune évaluation
        vararg = args.vararg
        kwarg = args.kwarg
        annotated_args = positional + args.kwonlyargs
        annotated_args.extend(arg for arg in (vararg, kwarg) if arg is not None)
        annotations = {}
        for arg in annotated_args:
            if arg.annotation is not None:
                annotations[arg.arg] = ast.unparse(arg.annotation)
        if node.returns is not None:
            annotations["return"] = ast.unparse(node.returns)
        result.append(Symbol(
            name=node.name,
            arity=len(positional),
            posonly=[arg.arg for arg in args.posonlyargs],
            kwonly=[arg.arg for arg in args.kwonlyargs],
            defaults=defaults,
            annotations=annotations,
            vararg=vararg.arg if vararg is not None else None,
            kwarg=kwarg.arg if kwarg is not None else None,
        ))

    return result


def module_defs(path: Path) -> list[str]:
    """Liste fonctions et classes de premier niveau, dans l'ordre source."""

    definitions = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    names = [node.name for node in _module(path).body if isinstance(node, definitions)]

    return names


def snippet(path: Path, start: int, end: int) -> str:
    """Extrait des lignes 1-based inclusives du préfixe de 8 000 octets, au plus 40."""

    # borne appliquée à la lecture, même pour une ligne de plusieurs mégaoctets
    if start < 1 or end < start:
        raise ValueError("invalid inclusive line range")
    with path.open("rb") as stream:
        raw = stream.read(MAX_SNIPPET_BYTES)
    lines = raw.splitlines(keepends=True)
    end = min(end, start - 1 + MAX_SNIPPET_LINES)
    selected = b"".join(lines[start - 1:end])

    # une substitution UTF-8 peut augmenter la taille ; borner aussi la sortie
    text = selected.decode("utf-8", errors="replace")
    bounded = text.encode("utf-8")[:MAX_SNIPPET_BYTES]

    return bounded.decode("utf-8", errors="ignore")


def is_binary(path: Path) -> bool:
    """Détecte un binaire par extension ou sur les 4 096 premiers octets."""

    # extension, bom, nul, puis proportion stricte de contrôles
    if path.suffix.lower() in BINARY_SUFFIXES:
        return True
    with path.open("rb") as stream:
        raw = stream.read(4096)
    if raw.startswith((b"\xff\xfe", b"\xfe\xff", b"\x00\x00\xfe\xff")) or b"\x00" in raw:
        return True
    controls = sum(byte < 9 or 13 < byte < 32 for byte in raw)

    return bool(raw) and controls / len(raw) > 0.3


def is_path_within(child: Path, parent: Path) -> bool:
    """Vérifie le confinement après résolution des liens et des segments parents."""

    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError:
        return False

    return True


def classify_repo_path(path: Path) -> PathClass:
    """Classe un chemin relatif lexical ; refuse les chemins sensibles ou indéterminés."""

    # seules les adresses relatives au dépôt sont classifiables sans racine
    parts = set(path.parts)
    if path.is_absolute() or not parts or ".." in parts:
        raise PithosError(Cause.invalid_path, "expected a repository-relative path", "target")

    # précédence de Villani ; environnements exclus comme artefacts runtime
    suffix = path.suffix.lower()
    if ".git" in parts:
        return PathClass.vcs_internal
    if path.name in {".DS_Store", "Thumbs.db"} or parts & EDITOR_DIRS:
        return PathClass.editor_artifact
    if suffix in {".pyc", ".pyo", ".pyd"} or parts & RUNTIME_DIRS:
        return PathClass.runtime_artifact
    if parts & GENERATED_DIRS:
        return PathClass.generated

    # aucune classe de repli ne rend un secret authoritative
    sensitive_suffix = suffix in {".key", ".pem", ".p12", ".pfx", ".crt", ".cer"}
    sensitive_names = ("token", "secret", "credential", "private_key", "api_key", "password", "passwd")
    name = path.name.lower()
    sensitive_name = any(word in name for word in sensitive_names)
    sensitive_json = suffix == ".json" and sensitive_name
    if sensitive_suffix or sensitive_json or any(part.startswith(".") for part in parts):
        raise PithosError(Cause.invalid_path, "sensitive or unclassified path", "target")

    return PathClass.authoritative
