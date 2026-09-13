"""Git et `gh` par subprocess : un prélude fixe, des arguments validés, un fait typé.

Le dépôt de campagne est écrit par un modèle : aucune commande ne prend de glob, et tout argument
qui atteint la CLI a été validé ici même.
"""

import json
import os
import re
import subprocess
from pathlib import Path

from kernel.contracts import Contract, Name, PositiveInt
from kernel.errors import Cause, PithosError
from kernel.facts import RepoChange as Change, RepoFact
from pydantic import ValidationError

# prélude déterministe : ni verrou optionnel, ni fsmonitor, ni réécriture de fin de ligne
PRELUDE = [
    "--no-optional-locks",
    "-c", "core.autocrlf=false",
    "-c", "core.fsmonitor=false",
    "-c", "core.quotepath=false",
]
STATUS_CODES = frozenset(" MADRCUT?!")
RENAME_CODES = frozenset("RC")
REF_GRAMMAR = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
TITLE_MAX_CHARS = 72
CHECK_SUCCESS = "SUCCESS"


class PullRequest(Contract):
    repo: Path
    number: PositiveInt
    url: Name
    branch: Name
    head_sha: Name


def checked_repo_path(path: Path, repo: Path) -> str:
    "Rend le chemin relatif au dépôt, en refusant ce qui en sort ou ce qui pilote la CLI."

    text = str(path)
    root = repo.resolve()
    candidate = (root / path).resolve()
    inside = candidate == root or root in candidate.parents
    if "\0" in text or text.startswith("-") or not inside:
        raise PithosError(Cause.invalid_path, f"path escapes the repository: {text!r}", "paths")

    return candidate.relative_to(root).as_posix()


def checked_ref(ref: str) -> str:
    "Rend le nom de branche, en refusant tout ce que Git lirait comme autre chose qu'un nom."

    refusable = not REF_GRAMMAR.match(ref) or ".." in ref or ref.endswith(".lock")
    if refusable:
        raise PithosError(Cause.invalid_symbol, f"not a branch name: {ref!r}", "branch")

    return ref


def checked_text(text: str, field: str) -> str:
    "Rend le texte destiné à un argument de la CLI, non vide et sans octet nul."

    if not text.strip() or "\0" in text:
        raise PithosError(Cause.invalid_schema, f"empty or nul-bearing {field}", field)

    return text


def _environment() -> dict:
    "Environnement explicite : aucun prompt interactif, sortie en C, secrets d'hôte hérités."

    inherited = ("PATH", "HOME", "GH_TOKEN", "GITHUB_TOKEN")
    passed = {name: os.environ[name] for name in inherited if name in os.environ}

    return {**passed, "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C"}


def _checked_output(command: list[str], repo: Path, *, runner) -> str:
    "Exécute la commande dans le dépôt et rend sa sortie, ou lève en portant `stderr`."

    completed = runner(command, cwd=str(repo), env=_environment(), capture_output=True, text=True)
    if completed.returncode != 0:
        detail = f"{' '.join(command[:3])} exited {completed.returncode}: {completed.stderr.strip()}"
        raise PithosError(Cause.unverifiable, detail, command[0])

    return completed.stdout


def _git(repo: Path, args: list[str], *, runner) -> str:
    return _checked_output(["git", *PRELUDE, *args], repo, runner=runner)


def _gh(repo: Path, args: list[str], *, runner) -> str:
    return _checked_output(["gh", *args], repo, runner=runner)


def _head(repo: Path, *, runner) -> str:
    "Sha de tête, vide tant que le dépôt n'a aucun commit — un dépôt neuf n'est pas une panne."

    command = ["git", *PRELUDE, "rev-parse", "--quiet", "--verify", "HEAD"]
    completed = runner(command, cwd=str(repo), env=_environment(), capture_output=True, text=True)

    return completed.stdout.strip()


def _entry(record: str) -> tuple[str, str]:
    "Sépare les deux codes d'état du chemin, en refusant toute entrée hors grammaire."

    readable = len(record) > 3 and record[2] == " " and set(record[:2]) <= STATUS_CODES
    if not readable:
        raise PithosError(Cause.invalid_schema, f"malformed porcelain entry: {record!r}", "status")

    return record[:2], record[3:]


def parse_status(raw: str) -> list[Change]:
    """Rend un changement par entrée de `--porcelain=v1 -z`, les deux côtés d'un rename compris.

    Une entrée illisible lève : un silence ferait passer un fichier modifié pour un dépôt propre.
    """

    if raw and not raw.endswith("\0"):
        raise PithosError(Cause.invalid_schema, "truncated porcelain output", "status")
    records = raw.split("\0")
    if records and records[-1] == "":
        records.pop()

    # une entrée, puis son chemin d'origine quand l'état est un rename ou une copie
    changes = []
    index = 0
    while index < len(records):
        status, path = _entry(records[index])
        origin = None
        if set(status) & RENAME_CODES:
            index += 1
            if index >= len(records) or not records[index]:
                raise PithosError(Cause.invalid_schema, f"rename without origin: {status!r}", "status")
            origin = Path(records[index])
        try:
            change = Change(status=status, path=Path(path), origin=origin)
        except ValidationError as error:
            raise PithosError(Cause.invalid_schema, str(error), "status") from error
        changes.append(change)
        index += 1

    return changes


def repo_fact(repo: Path, *, runner=subprocess.run) -> RepoFact:
    "Le fait typé que `verifier` consomme : sha de tête, entrées de statut, diff binaire complet."

    head = _head(repo, runner=runner)
    raw_status = _git(repo, ["status", "--porcelain=v1", "-z", "-uall"], runner=runner)
    diff_args = ["diff", "--no-ext-diff", "--no-textconv", "--binary", head]
    diff = _git(repo, diff_args, runner=runner) if head else ""
    changes = parse_status(raw_status)
    untracked = any(change.status == "??" for change in changes)
    complete = bool(head) and not untracked

    return RepoFact(repo=repo.resolve(), head=head, changes=changes, diff=diff, complete=complete)


def preflight(repo: Path, *, runner=subprocess.run) -> None:
    "Refuse un dépôt sale, en nommant les fichiers en cause plutôt qu'un décompte."

    fact = repo_fact(repo, runner=runner)
    if fact.changes:
        listed = ", ".join(str(change.path) for change in fact.changes)
        raise PithosError(Cause.invariant_failed, f"repository is dirty: {listed}", "repo")


def commit(repo: Path, paths: list[Path], message: str, *, runner=subprocess.run) -> str:
    """Commite exclusivement les chemins désignés et rend le sha produit.

    Aucun glob, aucun `-A` : seuls les fichiers explicitement nommés atteignent l'historique.
    """

    # validation complète avant la première exécution
    relatives = [checked_repo_path(path, repo) for path in paths]
    subject = checked_text(message, "message")
    if not relatives:
        raise PithosError(Cause.invalid_path, "commit requires at least one path", "paths")

    _git(repo, ["add", "--", *relatives], runner=runner)
    _git(repo, ["commit", "-m", subject, "--", *relatives], runner=runner)

    return _head(repo, runner=runner)


def open_pr(repo: Path, branch: str, body: str, *, runner=subprocess.run) -> PullRequest:
    "Ouvre la PR de la branche et rend son identité relue chez l'hôte, jamais celle espérée."

    ref = checked_ref(branch)
    text = checked_text(body, "body")
    title = text.strip().splitlines()[0][:TITLE_MAX_CHARS]

    _gh(repo, ["pr", "create", "--head", ref, "--title", title, "--body", text], runner=runner)
    fields = "number,url,headRefName,headRefOid"
    view = _decoded(_gh(repo, ["pr", "view", ref, "--json", fields], runner=runner))

    return PullRequest(
        repo=repo,
        number=view["number"],
        url=view["url"],
        branch=view["headRefName"],
        head_sha=view["headRefOid"],
    )


def automerge(pr: PullRequest, *, runner=subprocess.run) -> None:
    """Active l'auto-merge, et seulement sur un rollup de checks entièrement vert.

    La gate est relue chez l'hôte à l'appel : un verdict vert passé en argument ne prouverait que
    ce que l'appelant a bien voulu dire.
    """

    number = str(pr.number)
    view = _decoded(_gh(pr.repo, ["pr", "view", number, "--json", "statusCheckRollup"], runner=runner))
    rollup = view.get("statusCheckRollup") or []
    conclusions = {str(check.get("conclusion") or check.get("state") or "") for check in rollup}
    if conclusions != {CHECK_SUCCESS}:
        raise PithosError(Cause.invariant_failed, f"gate is not green: {sorted(conclusions)}", "pr")

    _gh(pr.repo, ["pr", "merge", number, "--auto", "--squash"], runner=runner)


def _decoded(raw: str) -> dict:
    "Rend l'objet JSON rendu par `gh`, en refusant toute autre forme."

    try:
        payload = json.loads(raw)
    except ValueError:
        raise PithosError(Cause.invalid_schema, f"gh returned invalid json: {raw[:120]!r}", "gh") from None
    if not isinstance(payload, dict):
        raise PithosError(Cause.invalid_schema, "gh returned a non-object payload", "gh")

    return payload
