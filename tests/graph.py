"""Lecture AST commune ; les politiques de dépendance restent dans chaque corpus de frontière."""

import ast
from pathlib import Path


SRC = Path(__file__).resolve().parents[1] / "src"


def production_paths(root):
    candidates = root.rglob("*.py")
    kept = [path for path in candidates if not path.name.startswith("test_") and path.name != "conftest.py"]

    return sorted(kept)


def production_files(root):
    """Recense récursivement le code livré et refuse un périmètre vide ou absent."""

    paths = production_paths(root)
    assert paths, f"no production files under {root}"

    return paths


def sources(module):
    return production_files(SRC / module)


def scan(root, check):
    """Conserve chaque chemin relatif complet, y compris les __init__.py homonymes."""

    result = {}
    for path in production_files(root):
        relative = path.relative_to(root)
        result[relative] = check(path.read_text(encoding="utf-8"), relative)

    return result


def assert_clean(root, check):
    scanned = scan(root, check)
    issues = {path: errors for path, errors in scanned.items() if errors}
    assert not issues, issues


class Source:
    """Expose imports, appels et alias issus d'un même arbre, sans exécuter le code."""

    def __init__(self, source):
        self.nodes = tuple(ast.walk(ast.parse(source)))
        self.imports = tuple(node for node in self.nodes if isinstance(node, (ast.Import, ast.ImportFrom)))
        self.calls = tuple(node for node in self.nodes if isinstance(node, ast.Call))
        self.attributes = tuple(node for node in self.nodes if isinstance(node, ast.Attribute))
        self.aliases = {}
        for node in self.imports:
            for alias in node.names:
                if isinstance(node, ast.Import):
                    bound = alias.asname or alias.name.partition(".")[0]
                    self.aliases[bound] = alias.name if alias.asname else bound
                elif not node.level:
                    self.aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"

    def imported_names(self):
        names = set()
        for node in self.imports:
            if isinstance(node, ast.Import) or node.module is None:
                names.update(alias.name for alias in node.names)
            else:
                names.add(node.module)

        return names

    def resolve(self, node):
        name = ast.unparse(node)
        prefix, separator, suffix = name.partition(".")
        resolved = self.aliases.get(prefix, prefix)

        return f"{resolved}{separator}{suffix}"


def imported_names(source):
    return Source(source).imported_names()


def imported_roots(source):
    names = imported_names(source)

    return {name.partition(".")[0] for name in names}


def check_imports(source, *, allowed, local, roots=()):
    """Applique une allowlist explicite ; un import relatif ne peut sortir du paquet."""

    errors = []
    for node in source.imports:
        if isinstance(node, ast.ImportFrom) and node.level:
            names = {node.module} if node.module else {alias.name for alias in node.names}
            if node.level != 1 or not names <= local:
                errors.append(f"relative:{node.level}:{sorted(names)}")
            continue
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif node.module in allowed or node.module.partition(".")[0] in roots:
            names = [node.module]
        else:
            names = [f"{node.module}.{alias.name}" for alias in node.names]
        for name in names:
            if name not in allowed and name.partition(".")[0] not in roots:
                errors.append(f"import:{name}")

    return errors


def forbidden_calls(source, names):
    calls = [source.resolve(call.func) for call in source.calls]

    return [name for name in calls if name in names]


def process_calls(source):
    prefixes = ("os.exec", "os.spawn", "os.system", "os.popen", "os.fork")
    calls = [source.resolve(call.func) for call in source.calls]

    return [name for name in calls if name.startswith(prefixes)]
