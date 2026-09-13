"""Double du broker : un dépôt Git simulé et un Telegram en mémoire. Rien ne quitte la machine.

Trois scénarios se scriptent en assignant un attribut du module, parce que ce sont exactement les
trois que la frontière doit savoir jouer : `changes` donne un dépôt sale au prochain `repo_fact`,
`transport_down = True` fait échouer un envoi, et `green = False` refuse l'auto-merge.
"""

from pathlib import Path

from broker.git import Change, PullRequest, RepoFact
from broker.telegram import Command
from kernel.errors import Cause, PithosError
from kernel.facts import FileFact

files: dict[Path, str] = {}
history: list[dict] = []
changes: list[Change] = []
pulls: list[PullRequest] = []
merged: list[PullRequest] = []
outgoing: list[tuple[str, str]] = []
incoming: list[Command] = []
head = "0" * 40
diff = ""
complete = False
green = True
transport_down = False


def reset() -> None:
    "Vide l'état accumulé et rétablit les trois scénarios simulables à leur valeur nominale."

    global head, diff, complete, green, transport_down

    for accumulated in (files, history, changes, pulls, merged, outgoing, incoming):
        accumulated.clear()
    head = "0" * 40
    diff = ""
    complete = False
    green = True
    transport_down = False


def agree_with(fact: FileFact, *, repo: Path | None = None) -> None:
    """Prépare le chemin modifié ; une cible absolue exige la racine explicite du dépôt."""

    path = fact.path
    if path.is_absolute():
        if repo is None:
            raise ValueError("absolute file facts require a repository root")
        path = path.relative_to(repo)
    changes[:] = [Change(status=" M", path=path, origin=None)]


def contradict(fact: FileFact) -> None:
    "Prépare un fait de dépôt qui **contredit** le `FileFact` : rien n'a bougé dans le dépôt."

    changes.clear()


def repo_fact(repo: Path) -> RepoFact:
    "Rend l'état simulé du dépôt, sans jamais lancer `git`."

    return RepoFact(repo=repo, head=head, changes=list(changes), diff=diff, complete=complete)


def preflight(repo: Path) -> None:
    "Refuse un dépôt sale en nommant les fichiers en cause, comme l'implémentation."

    if changes:
        listed = ", ".join(str(change.path) for change in changes)
        raise PithosError(Cause.invariant_failed, f"repository is dirty: {listed}", "repo")


def commit(repo: Path, paths: list[Path], message: str) -> str:
    "Historise un commit ne portant que les chemins désignés, et rend son sha simulé."

    global head

    published = [str(path) for path in paths]
    history.append({"paths": published, "message": message})
    head = f"{len(history):040d}"

    # ce qui vient d'être commité cesse d'être sale ; le reste le demeure
    changes[:] = [change for change in changes if str(change.path) not in published]

    return head


def open_pr(repo: Path, branch: str, body: str) -> PullRequest:
    "Ouvre une PR simulée et rend son identité, numérotée par ordre d'ouverture."

    number = len(pulls) + 1
    pull = PullRequest(
        repo=repo,
        number=number,
        url=f"https://example.invalid/pr/{number}",
        branch=branch,
        head_sha=head,
    )
    pulls.append(pull)

    return pull


def automerge(pr: PullRequest) -> None:
    "Ne fusionne que sur gate verte ; sinon lève la même cause que l'implémentation."

    if not green:
        raise PithosError(Cause.invariant_failed, "gate is not green", "pr")

    merged.append(pr)


def notify(text: str, idempotency_key: str) -> bool:
    "Envoie en mémoire ; une clé déjà envoyée ne compte pas deux fois, une panne ne compte pas."

    if idempotency_key in {key for _, key in outgoing}:
        return True
    if transport_down:
        return False

    outgoing.append((text, idempotency_key))

    return True


def poll(offset: int) -> tuple[list[Command], int]:
    "Rend les commandes en file à partir de l'offset, et l'offset suivant."

    fresh = [command for command in incoming if command.update_id >= offset]
    highest = max([command.update_id for command in fresh], default=offset - 1)

    return fresh, max(offset, highest + 1)
