"""Telegram bidirectionnel : notifications sortantes, polling, allowlist, cinq commandes.

Deux erreurs typées, jamais confondues : une réponse négative explicite du service n'est pas une
panne de transport. Le backoff est **partagé** par le notifier et le poller — deux backoffs
indépendants se désynchronisent et martèlent le service.
"""

import os
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path

import httpx
import journal
from journal.redact import REDACTED
from kernel.contracts import Contract, Event, EventType, PositiveInt
from pydantic import Field, StrictInt

from .intent import read_ledger

API_ENV = "PITHOS_TELEGRAM_API"
TOKEN_ENV = "PITHOS_TELEGRAM_TOKEN"
CHAT_ENV = "PITHOS_TELEGRAM_CHAT"
ALLOWLIST_ENV = "PITHOS_TELEGRAM_ALLOWLIST"
DEFAULT_API = "https://api.telegram.org"
# la limite de l'API est en unités UTF-16 : un emoji en compte deux
TEXT_LIMIT = 4096
POLL_TIMEOUT_SEC = 20
CALL_TIMEOUT_SEC = 25
RETRY_INITIAL_SEC = 5
RETRY_MAX_SEC = 60
OFFSET_KEY = "offset"

# état partagé du module : la cadence dégradée, et les clés déjà envoyées dans ce processus
delay = 0.0
sent: dict[str, int] = {}


class CommandKind(StrEnum):
    status = "status"
    latest = "latest"
    pause = "pause"
    stop = "stop"
    answer = "answer"


KINDS = {f"/{kind.value}": kind for kind in CommandKind}


class Command(Contract):
    """Une commande entrante recevable ; `date` est ce qui permet de la dater d'une mission."""

    kind: CommandKind
    update_id: PositiveInt
    chat_id: StrictInt
    sender: StrictInt
    date: StrictInt = Field(ge=0)
    argument: str


class TelegramRequestRejected(RuntimeError):
    """Réponse négative explicite du service — le transport, lui, a fonctionné."""

    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = int(status_code or 0)

    @property
    def transient(self) -> bool:
        return self.status_code == 429 or self.status_code >= 500


class TelegramTransportError(RuntimeError):
    """Aucune réponse exploitable n'est parvenue : on ne sait rien de l'effet."""


def note_failure() -> None:
    "Un tour dégradé de plus : le délai part de l'initial, puis double jusqu'au plafond."

    global delay

    delay = RETRY_INITIAL_SEC if delay == 0 else min(delay * 2, RETRY_MAX_SEC)


def note_success() -> None:
    "Tout tour réussi, d'où qu'il vienne, remet la cadence à l'initial."

    global delay

    delay = 0.0


def retry_delay() -> float:
    "Ce qu'il faut attendre avant la prochaine tentative, poller et notifier confondus."

    return delay or RETRY_INITIAL_SEC


def u16len(value: str) -> int:
    "Longueur au sens de Telegram : des unités UTF-16, pas des points de code."

    return sum(2 if ord(char) > 0xFFFF else 1 for char in value)


def _prefix_u16(value: str, budget: int) -> str:
    "Le plus long préfixe tenant dans le budget, coupé sur une frontière de point de code."

    used = 0
    index = 0
    while index < len(value):
        width = 2 if ord(value[index]) > 0xFFFF else 1
        if used + width > budget:
            break
        used += width
        index += 1

    return value[:index]


def chunks(text: str, limit: int = TEXT_LIMIT) -> list[str]:
    """Découpe le texte en messages d'au plus `limit` unités UTF-16, sans rien perdre.

    La coupe cherche d'abord un saut de ligne dans la fenêtre ; à défaut elle tombe sur la
    frontière d'unité, qui ne coupe jamais un point de code en deux.
    """

    pieces = []
    rest = text
    while u16len(rest) > limit:
        window = _prefix_u16(rest, limit)
        cut = window.rfind("\n") + 1
        head = window[:cut] if cut > 0 else window
        pieces.append(head)
        rest = rest[len(head):]
    pieces.append(rest)

    return pieces


def _token() -> str:
    return os.environ.get(TOKEN_ENV, "")


def _endpoint(method: str) -> str:
    "Route de l'API ; `PITHOS_TELEGRAM_API` la déplace pour un banc, jamais en production."

    base = os.environ.get(API_ENV) or DEFAULT_API

    return f"{base.rstrip('/')}/bot{_token()}/{method}"


def _scrubbed(text: str) -> str:
    "Retire le jeton du texte : Telegram renvoie parfois l'URL qui le porte dans sa description."

    token = _token()

    return text.replace(token, REDACTED) if token else text


def allowed_senders() -> frozenset[int]:
    "Les identifiants autorisés à commander ; une allowlist vide n'autorise personne."

    listed = os.environ.get(ALLOWLIST_ENV, "").split(",")
    digits = [entry.strip() for entry in listed if entry.strip().isdigit()]

    return frozenset(int(entry) for entry in digits)


def _record(fact: dict) -> None:
    "Consigne l'effet sortant, rédigé : ces JSONL ne sont jamais effacés."

    scrubbed, _ = journal.redact(fact)
    journal.emit(Event(
        ts=datetime.now(timezone.utc).isoformat(),
        v=1,
        type=EventType.status,
        durable=True,
        payload=scrubbed,
    ))


def _call(method: str, payload: dict) -> dict:
    "Un POST bloquant vers l'API ; le rejet explicite et la panne de transport restent distincts."

    try:
        with httpx.Client(timeout=CALL_TIMEOUT_SEC) as client:
            answer = client.post(_endpoint(method), json=payload)
        body = answer.json()
    except httpx.HTTPError as failure:
        note_failure()
        raise TelegramTransportError(f"{method}: transport failed ({type(failure).__name__})") from None
    except ValueError:
        note_failure()
        raise TelegramTransportError(f"{method}: response is not json") from None

    if not isinstance(body, dict):
        note_failure()
        raise TelegramTransportError(f"{method}: response is not an object")

    if answer.status_code >= 400 or not body.get("ok"):
        description = _scrubbed(str(body.get("description") or ""))
        rejection = TelegramRequestRejected(f"{method}: {description}", answer.status_code)
        if rejection.transient:
            note_failure()
        raise rejection

    note_success()

    return body


def notify(text: str, idempotency_key: str) -> bool:
    """Envoie le texte au chat de campagne ; un rejeu de la même clé ne renvoie rien.

    Rend `False` sur toute issue négative : la distinction entre rejet explicite et panne de
    transport vit dans la trace, jamais dans le booléen.
    """

    if idempotency_key in sent:
        return True

    pieces = [piece for piece in chunks(text) if piece.strip()]
    chat = os.environ.get(CHAT_ENV, "")
    try:
        for piece in pieces:
            _call("sendMessage", {"chat_id": chat, "text": piece})
    except (TelegramRequestRejected, TelegramTransportError) as failure:
        _record({
            "method": "sendMessage",
            "outcome": type(failure).__name__,
            "description": str(failure),
            "idempotency_key": idempotency_key,
        })

        return False

    sent[idempotency_key] = len(pieces)
    _record({
        "method": "sendMessage",
        "outcome": "sent",
        "chunks": len(pieces),
        "idempotency_key": idempotency_key,
    })

    return True


def _command(update: dict) -> Command | None:
    "Rend la commande d'une update, ou `None` quand elle n'en porte pas une recevable."

    message = update.get("message") or {}
    text = str(message.get("text") or "").strip()
    word, _, argument = text.partition(" ")
    kind = KINDS.get(word.split("@")[0])
    if kind is None:
        return None

    # allowlist : une commande venue d'ailleurs est ignorée, et cette ignorance est journalisée
    sender = int((message.get("from") or {}).get("id") or 0)
    if sender not in allowed_senders():
        _record({"method": "getUpdates", "outcome": "ignored", "sender": sender, "command": kind.value})

        return None

    return Command(
        kind=kind,
        update_id=update["update_id"],
        chat_id=int((message.get("chat") or {}).get("id") or 0),
        sender=sender,
        date=int(message.get("date") or 0),
        argument=argument.strip(),
    )


def poll(offset: int) -> tuple[list[Command], int]:
    "Rend les commandes recevables et l'offset suivant ; toute update lue est consommée."

    body = _call("getUpdates", {"offset": offset, "timeout": POLL_TIMEOUT_SEC})
    updates = body.get("result") or []
    commands = [command for command in map(_command, updates) if command is not None]
    highest = max([int(update.get("update_id") or 0) for update in updates], default=offset - 1)

    return commands, max(offset, highest + 1)


def saved_offset(path: Path, *, trace=journal) -> int:
    "L'offset survivant au redémarrage : une commande déjà traitée n'est jamais rejouée."

    return int(read_ledger(path, trace=trace).get(OFFSET_KEY, 0))


def remember_offset(path: Path, offset: int, *, trace=journal) -> None:
    "Persiste l'offset atteint, sous le verrou du journal."

    trace.update_json_locked(path, lambda state: {**state, OFFSET_KEY: offset})


def is_stale(command: Command, mission_started_at: int) -> bool:
    "Vrai quand la commande précède la mission courante — un `/stop` tardif ne vise pas la suivante."

    return command.date < mission_started_at


def relay(command: Command, controller) -> str | None:
    """Émet le signal d'une commande de contrôle et rend le verdict du contrôleur.

    `/pause` interrompt, `/stop` va jusqu'à la sortie. `broker` ne touche jamais l'arbre : il
    n'appelle que l'`InterruptController`.
    """

    if command.kind is CommandKind.pause:
        return controller.register_interrupt()
    if command.kind is not CommandKind.stop:
        return None

    verdict = controller.register_interrupt()
    while verdict != "exit":
        verdict = controller.register_interrupt()

    return verdict
