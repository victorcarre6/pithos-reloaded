"""Préparation pure : une fonction exacte, compilation, bilan avant toute écriture.

Villani : state_tooling.py:44-86,236-291 ; patch_apply.py:330-333.
Copie libre accordée dans resources/MANIFEST.md ; enveloppes strictes adaptées.
"""

import ast
import difflib
import io
import re
import tokenize
from hashlib import sha256
from pathlib import Path

from kernel.codeview import MAX_SOURCE_BYTES
from kernel.contracts import Contract
from kernel.errors import Cause, PithosError
from kernel.facts import FileFact


class SplicePlan(Contract):
    content: bytes
    fact: FileFact
    diff: str
    lines_added: int


def _require_utf8(raw):
    encoding, _ = tokenize.detect_encoding(io.BytesIO(raw).readline)
    if encoding not in {"utf-8", "utf-8-sig"}:
        raise ValueError("expected UTF-8 source")


def _signature(node):
    args = node.args
    keywords = [(arg.arg, value is None) for arg, value in zip(args.kwonlyargs, args.kw_defaults)]

    return (type(node), len(args.posonlyargs), [arg.arg for arg in args.args],
            len(args.defaults), keywords, args.vararg is not None, args.kwarg is not None)


def prepare_splice(before: bytes, function_name: str, new_source: str, *, target: Path) -> SplicePlan:
    """Rend les octets candidats et leur fait ; ne lit, n'écrit et n'exécute rien."""

    # enveloppe complète seulement ; aucune extraction dans une réponse en prose
    source = new_source.strip("\r\n")
    fenced = re.fullmatch(r"```(?:python)?\r?\n(.*?)\r?\n```", source, re.DOTALL)
    if fenced:
        source = fenced.group(1)
    numbered = [re.fullmatch(r"(\d+): (.*)", line) for line in source.splitlines()]
    if numbered and all(numbered):
        numbers = [int(match.group(1)) for match in numbered]
        if numbers == list(range(numbers[0], numbers[0] + len(numbers))):
            source = "\n".join(match.group(2) for match in numbered)

    # un seul def de module ; annotations et décorateurs restent inertes
    try:
        if max(len(before), len(source.encode("utf-8"))) > MAX_SOURCE_BYTES:
            raise ValueError("oversized source")
        tree = ast.parse(source, filename=str(target))
        kinds = (ast.FunctionDef, ast.AsyncFunctionDef)
        if len(tree.body) != 1 or not isinstance(tree.body[0], kinds):
            raise ValueError("expected exactly one module def")
        replacement = tree.body[0]
        if replacement.name != function_name:
            raise ValueError("function name mismatch")
    except (SyntaxError, ValueError, UnicodeError) as error:
        raise PithosError(Cause.invalid_schema, str(error), "new_source") from error

    # signature appelable inchangée ; valeurs par défaut et annotations modifiables
    try:
        _require_utf8(before)
        original = ast.parse(before, filename=str(target))
    except (SyntaxError, ValueError) as error:
        raise PithosError(Cause.invalid_schema, str(error), "target") from error
    definitions = [node for node in original.body if getattr(node, "name", None) == function_name]
    if len(definitions) != 1 or not isinstance(definitions[0], kinds):
        raise PithosError(Cause.invalid_symbol, "expected one existing module function", "function_name")
    previous = definitions[0]
    if _signature(previous) != _signature(replacement):
        detail = f"incompatible signatures: {function_name}({ast.unparse(previous.args)}) -> {function_name}({ast.unparse(replacement.args)})"
        raise PithosError(Cause.invalid_schema, detail, "new_source")

    # plage inclusive avec décorateurs ; les octets hors plage ne sont pas décodés
    starts = [previous.lineno] + [node.lineno for node in previous.decorator_list]
    start, end = min(starts), previous.end_lineno
    bom = b"\xef\xbb\xbf" if before.startswith(b"\xef\xbb\xbf") else b""
    lines = before[len(bom):].splitlines(keepends=True)
    if previous.decorator_list:
        while start > 1 and not lines[start - 1].startswith(b"@"):
            start -= 1
    old = b"".join(lines[start - 1:end])
    newline = re.search(rb"\r\n|\r|\n", old)
    ending = newline.group() if newline else b"\n"
    normalized = source.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")
    inserted = normalized.encode("utf-8").replace(b"\n", ending)
    if old.endswith((b"\n", b"\r")):
        inserted += ending
    content = bom + b"".join(lines[:start - 1]) + inserted + b"".join(lines[end:])

    # même compilateur que py_compile, sans fichier .pyc ni exécution du code objet
    try:
        if len(content) > MAX_SOURCE_BYTES:
            raise ValueError("oversized spliced source")
        _require_utf8(content)
        compile(content, str(target), "exec", dont_inherit=True)
    except (SyntaxError, ValueError) as error:
        detail = f"file={target} validator=compile exception={type(error).__name__}: {error}; repair this function"
        raise PithosError(Cause.invalid_schema, detail, "new_source") from error
    if content == before:
        raise PithosError(Cause.invariant_failed, "unchanged source: n_replacements=0", "new_source")

    # bilan fondé sur les octets exacts, distinct de toute décision de vérification
    fact = FileFact(
        path=target,
        sha_before=sha256(before).hexdigest(),
        sha_after=sha256(content).hexdigest(),
        spliced_range=(start, end),
        n_replacements=1,
    )
    diff_lines = difflib.diff_bytes(difflib.unified_diff, before.splitlines(True), content.splitlines(True))
    diff = b"".join(diff_lines).decode("utf-8", errors="replace")
    lines_added = len(inserted.splitlines()) - (end - start + 1)

    return SplicePlan(content=content, fact=fact, diff=diff, lines_added=lines_added)
