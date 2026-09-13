"""Sélection pure, adaptée d'Ouroboros ouroboros/code_intelligence.py:737-800.

Le graphe résolu vient du harness ; aucun index implicite ni lecture du workspace.
Copyright (c) 2026 Anton Razzhigaev — MIT License.

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

from pathlib import Path

from kernel.codeview import PathClass, classify_repo_path

from .classify import CandidateTarget, RepoIndex, analyze_instruction


def relevant_files(instruction: str, index: RepoIndex) -> tuple[CandidateTarget, ...]:
    """Rend les cibles et raisons du classifieur existant, sans plafond silencieux."""

    index = RepoIndex.model_validate(index.model_dump())
    analysis = analyze_instruction(instruction, index)

    return analysis.candidate_targets


def _indexed_imports(index):
    """Filtre les deux côtés du graphe selon la classification de chemins du kernel."""

    index = RepoIndex.model_validate(index.model_dump())
    allowed = {path for path in index.files if classify_repo_path(path) == PathClass.authoritative}
    edges = {}
    for path in sorted(allowed):
        dependencies = set(index.imports.get(path, ()))
        edges[path] = dependencies & allowed

    return edges


def _closure(targets, edges, depth):
    """Parcourt en largeur, conserve les cibles et enregistre la distance minimale."""

    frontier = set(targets)
    if not frontier <= set(edges):
        raise ValueError("target must be an authoritative indexed path")
    reached = {path: 0 for path in frontier}
    for distance in range(1, depth + 1):
        following = set()
        for path in frontier:
            following.update(edges[path])
        frontier = following - set(reached)
        if not frontier:
            break
        for path in frontier:
            reached[path] = distance

    return reached


def import_closure(targets: list[Path], index: RepoIndex) -> tuple[CandidateTarget, ...]:
    """Rend la fermeture des dépendances présentes dans l'index, cycles inclus une seule fois."""

    edges = _indexed_imports(index)
    reached = _closure(targets, edges, len(edges))
    result = []
    for path, distance in sorted(reached.items()):
        reason = "target" if distance == 0 else f"dependency depth {distance}"
        result.append(CandidateTarget(target=path, reason=reason))

    return tuple(result)


def impact_files(target: Path, index: RepoIndex, *, depth: int = 1) -> tuple[CandidateTarget, ...]:
    """Rend les importeurs de la cible jusqu'à la profondeur explicite, entre 1 et 5."""

    # inversion des imports résolus ; aucune inférence de références dynamiques
    if type(depth) is not int or not 1 <= depth <= 5:
        raise ValueError("impact depth must be an integer between 1 and 5")
    imports = _indexed_imports(index)
    reverse = {path: set() for path in imports}
    for path, dependencies in imports.items():
        for dependency in dependencies:
            reverse[dependency].add(path)

    # la cible reste présente même si personne ne l'importe
    reached = _closure([target], reverse, depth)
    result = []
    for path, distance in sorted(reached.items()):
        reason = "target" if distance == 0 else f"imports depth {distance}"
        result.append(CandidateTarget(target=path, reason=reason))

    return tuple(result)
