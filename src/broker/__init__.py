"""La seule sortie de données : Git par subprocess, Telegram par httpx, et rien d'autre.

C'est le point d'application de la contrainte dure n°5 — aucun autre module n'ouvre de socket
sortant, et le graphe d'imports le garde. `broker` rend des faits et envoie des messages ; il ne
connaît pas la boucle.
"""

from pathlib import Path
from typing import Protocol, runtime_checkable

from .git import Change, PullRequest, RepoFact, automerge, commit, open_pr, preflight, repo_fact
from .identity import Effect, EffectIdentity, new_identity, result_key, same_result, transport_key
from .intent import Stage, read_ledger, record_intent, record_result, resume, stage
from .telegram import Command, CommandKind, TelegramRequestRejected, TelegramTransportError
from .telegram import chunks, is_stale, notify, poll, relay, remember_offset, retry_delay, saved_offset

__all__ = [
    "Broker", "Change", "Command", "CommandKind", "Effect", "EffectIdentity", "PullRequest",
    "RepoFact", "Stage", "TelegramRequestRejected", "TelegramTransportError", "automerge",
    "chunks", "commit", "is_stale", "new_identity", "notify", "open_pr", "poll", "preflight",
    "read_ledger", "record_intent", "record_result", "relay", "remember_offset", "repo_fact",
    "result_key", "resume", "retry_delay", "same_result", "saved_offset", "stage",
    "transport_key",
]


@runtime_checkable
class Broker(Protocol):
    """Ce que les modules au-dessus attendent de la frontière sortante — implémentation comme double.

    Les membres sont statiques : la frontière est un module, pas un objet à instancier.
    """

    @staticmethod
    def repo_fact(repo: Path) -> RepoFact: ...

    @staticmethod
    def preflight(repo: Path) -> None: ...

    @staticmethod
    def commit(repo: Path, paths: list[Path], message: str) -> str: ...

    @staticmethod
    def open_pr(repo: Path, branch: str, body: str) -> PullRequest: ...

    @staticmethod
    def automerge(pr: PullRequest) -> None: ...

    @staticmethod
    def notify(text: str, idempotency_key: str) -> bool: ...

    @staticmethod
    def poll(offset: int) -> tuple[list[Command], int]: ...
