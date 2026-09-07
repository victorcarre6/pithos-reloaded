"""Un chemin canonique commun à l'édition et à la projection.

Villani state_tooling.py:177-207 : déquote et séparateurs, sans le lstrip('./')
qui effacerait un échappement. Prédicats partagés du kernel, injectables.
"""

from pathlib import Path

from kernel.codeview import PathClass
from kernel.errors import Cause, PithosError
from kernel.protocol import CodeView


def normalized_target(target: Path, root: Path) -> Path:
    raw = str(target).strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        raw = raw[1:-1].strip()

    return root / Path(raw.replace("\\", "/"))


def checked_path(target: Path, root: Path, view: CodeView) -> Path:
    path = normalized_target(target, root)

    # confinement puis politique sur l'adresse réellement utilisée
    try:
        resolved = path.resolve()
        if not view.is_path_within(resolved, root):
            raise ValueError("target escapes workspace")
        relative = resolved.relative_to(root)
        if view.classify_repo_path(relative) != PathClass.authoritative:
            raise ValueError("target is not authoritative")
    except (ValueError, RuntimeError) as error:
        raise PithosError(Cause.invalid_path, str(error), "target") from error

    return resolved
