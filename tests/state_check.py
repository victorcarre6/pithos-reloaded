"""Mesures et contrôle des en-têtes : python -m tests.state_check, sans écriture."""

import ast
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
from io import StringIO
from pathlib import Path
import re
import tokenize

from tests.graph import production_paths


@dataclass(frozen=True)
class Measurement:
    code: int
    physical: int
    sha256: str


def count_source(source):
    """Compte les lignes physiques portant du code, hors blancs, commentaires et docstrings AST."""

    # positions AST en octets utf-8, positions tokenize en caractères
    lines = source.splitlines()
    docstrings = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) or not node.body:
            continue
        first = node.body[0]
        if not isinstance(first, ast.Expr) or not isinstance(first.value, ast.Constant) or not isinstance(first.value.value, str):
            continue
        start_line = lines[first.lineno - 1].encode("utf-8")
        end_line = lines[first.end_lineno - 1].encode("utf-8")
        start_column = len(start_line[:first.col_offset].decode("utf-8"))
        end_column = len(end_line[:first.end_col_offset].decode("utf-8"))
        docstrings.append(((first.lineno, start_column), (first.end_lineno, end_column)))

    # un littéral multiligne affecté à une variable reste du code, même s'il contient #
    ignored = {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER}
    occupied = set()
    for token in tokenize.generate_tokens(StringIO(source).readline):
        if token.type in ignored:
            continue
        if any(start <= token.start and token.end <= end for start, end in docstrings):
            continue
        for number in range(token.start[0], token.end[0] + 1):
            if number <= len(lines) and lines[number - 1].strip():
                occupied.add(number)

    return len(occupied), len(lines)


def measure(root):
    """Mesure la production du module, __init__.py et sous-paquets inclus, tests exclus."""

    code = 0
    physical = 0
    digest = sha256()
    for path in production_paths(root):
        raw = path.read_bytes()
        file_code, file_physical = count_source(raw.decode("utf-8"))
        code += file_code
        physical += file_physical
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(raw)
        digest.update(b"\0")

    return Measurement(code, physical, digest.hexdigest())


def module_targets(path):
    """Lit les cibles globales de la carte des modules dans AGENTS.md."""

    pattern = r"^\|\s*\d+\s*\|\s*`(\w+)`\s*\|[^\n]*?\|\s*~([\d ]+) L"
    pairs = re.findall(pattern, path.read_text(), re.MULTILINE)
    if not pairs:
        raise ValueError("table des cibles absente ou illisible")

    return {name: int(number.replace(" ", "")) for name, number in pairs}


def check_state(root, target):
    """Vérifie les mesures, la date et les incohérences observables, sans inférer un statut métier."""

    measured = measure(root)
    content = (root / "STATE.md").read_text()
    header = content.split("\n## ", 1)[0]
    fields = dict(re.findall(r"^\*\*(.+?)\*\*\s*:\s*(.+)$", header, re.MULTILINE))
    errors = []
    status = fields.get("Statut")
    if status not in {"non commencé", "en cours", "bloqué", "fini"}:
        errors.append("statut absent ou non fermé")
    if status == "non commencé" and measured.code:
        errors.append("statut non commencé malgré la présence de code")
    try:
        stamp = fields.get("Mise à jour", "")
        if not re.fullmatch(r"\d{2}:\d{2}", stamp):
            raise ValueError("JJ:MM requis")
        day, month = stamp.split(":")
        # sans année dans JJ:MM, seule la validité calendaire est vérifiable
        date(2000, int(month), int(day))
    except ValueError:
        errors.append("date absente ou invalide, JJ:MM requis")

    # comparaison indépendante des deux unités et de l'empreinte de tous les fichiers
    counts = re.fullmatch(r"(\d+) code / (\d+) cible · (\d+) physiques", fields.get("Lignes", ""))
    if counts is None:
        errors.append("lignes : format code / cible · physiques requis")
    else:
        code, declared_target, physical = map(int, counts.groups())
        if code != measured.code:
            errors.append(f"lignes : {code} déclarées, {measured.code} mesurées")
        if declared_target != target:
            errors.append(f"cible : {declared_target} déclarée, {target} dans AGENTS.md")
        if physical != measured.physical:
            errors.append(f"physiques : {physical} déclarées, {measured.physical} mesurées")
    if fields.get("Empreinte") != measured.sha256:
        errors.append("empreinte de production périmée ou absente")

    # une justification ne vaut que jusqu'au plafond explicitement mesuré
    if measured.code > target:
        ceiling = re.findall(r"^\*\*Plafond justifié\*\* : (\d+) code$", content, re.MULTILINE)
        reasons = re.findall(r"^\*\*Justification\*\* : (.+)$", content, re.MULTILINE)
        if not ceiling or not reasons:
            errors.append("dépassement sans plafond ni justification écrite")
        elif measured.code > int(ceiling[-1]):
            errors.append("plafond justifié dépassé")

    return errors


def main():
    root = Path(__file__).resolve().parents[1]
    errors = []
    targets = module_targets(root / "AGENTS.md")
    documented = {path.parent.name for path in (root / "src").glob("*/MODULE.md")}
    if documented != set(targets):
        errors.append("la carte des cibles ne couvre pas exactement les MODULE.md")
    for name, target in targets.items():
        module = root / "src" / name
        measured = measure(module)
        row = f"{name:12} {measured.code:4} code / {target:4} cible | {measured.physical:4} physiques"
        print(row)
        stamp = f"             empreinte {measured.sha256}"
        print(stamp)
        for error in check_state(module, target):
            errors.append(f"{name}: {error}")
    for error in errors:
        print(error)

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
