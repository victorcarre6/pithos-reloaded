"""Un POST bloquant vers la route locale : une requête, une réponse complète, pas de streaming."""

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from urllib.parse import urlparse

import httpx
import journal
from kernel.contracts import Event, EventType

from .revalidate import schema_sha256

DEFAULT_URL = "http://127.0.0.1:11434"
URL_ENV = "PITHOS_OLLAMA_URL"
MODEL = "pithos/ling-3.0-tiny:8b-16k"
SCHEMA_NAME = "criterion"
# un local lent n'est pas une panne ; la borne murale de la mission reste prioritaire
TIMEOUT_SEC = 300.0
# mesuré par un tiers sur la famille `ling`, versionné comme donnée et non redécouvert
SAMPLING = {"temperature": 0.3, "top_p": 0.95, "top_k": 20}
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
THINK_CLOSE = "</think>"
CHARS_PER_TOKEN = 4
BODY_EXCERPT_CHARS = 500


class Outcome(StrEnum):
    completed = "completed"
    truncated = "truncated"
    unknown_stop = "unknown_stop"
    transport_error = "transport_error"
    budget_refused = "budget_refused"


@dataclass(frozen=True, slots=True)
class Deadline:
    "Ce qu'un appel a le droit de consommer : une borne murale et une place de sortie réservée."

    seconds: float
    context_window: int
    reserved_output: int


@dataclass(frozen=True, slots=True)
class RawResponse:
    """Résultat discriminé d'un appel — jamais un `None` surchargé.

    `content` n'est renseigné que sur `completed` ; le corps complet vit dans la trace.
    """

    outcome: Outcome
    content: str
    thinking: str
    raw_stop_reason: str
    usage: dict
    prompt_estimate: int


def normalize_base_url(url: str) -> str:
    "Ajoute `/v1` de façon idempotente et refuse toute route hors loopback (contrainte n°5)."

    cleaned = url.rstrip("/")
    host = urlparse(cleaned).hostname
    if host not in LOOPBACK_HOSTS:
        raise ValueError(f"bridge: route hors loopback refusée — {url}")

    return cleaned if cleaned.endswith("/v1") else f"{cleaned}/v1"


def base_url() -> str:
    "Route locale courante ; `PITHOS_OLLAMA_URL` la déplace pour un banc, jamais hors loopback."

    return normalize_base_url(os.environ.get(URL_ENV) or DEFAULT_URL)


def estimate_tokens(text: str) -> int:
    "Estimation de préflight, explicitement distincte de l'usage mesuré rendu par la route."

    return len(text) // CHARS_PER_TOKEN + 1


def build_payload(schema: dict, system: str, user: str, deadline: Deadline) -> dict:
    "Le point d'insertion de `response_format` : mode strict exigé, jamais préféré."

    return {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": deadline.reserved_output,
        "stream": False,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": SCHEMA_NAME, "schema": schema, "strict": True},
        },
        **SAMPLING,
    }


def _split_thinking(message: dict) -> tuple[str, str]:
    "Sépare le raisonnement du contenu exploitable ; rien n'est jamais extrait du raisonnement."

    thinking = message.get("reasoning_content") or message.get("reasoning") or ""
    content = message.get("content") or ""

    if THINK_CLOSE in content:
        reasoned, _, content = content.partition(THINK_CLOSE)
        thinking = f"{thinking}{reasoned}"

    return content.strip(), thinking


def _record(payload: dict, response: RawResponse, excerpt: str) -> None:
    "Consigne le payload effectif et l'issue : c'est ce qui rend le taux de rejet mesurable."

    fact = {
        "endpoint": f"{base_url()}/chat/completions",
        "model": payload["model"],
        "schema_sha256": schema_sha256(payload["response_format"]["json_schema"]["schema"]),
        "max_tokens": payload["max_tokens"],
        "sampling": dict(SAMPLING),
        "outcome": response.outcome.value,
        "raw_stop_reason": response.raw_stop_reason,
        "prompt_estimate": response.prompt_estimate,
        "usage": response.usage,
        "body_excerpt": excerpt[:BODY_EXCERPT_CHARS],
    }

    journal.emit(Event(
        ts=datetime.now(timezone.utc).isoformat(),
        v=1,
        type=EventType.status,
        durable=True,
        payload=fact,
    ))


def call(schema: dict, system: str, user: str, deadline: Deadline) -> RawResponse:
    """Un POST bloquant. Une requête, une réponse complète. Pas de streaming.

    Aucun repli sur la contrainte de décodage, aucun retry implicite : l'issue typée suffit.
    """

    estimate = estimate_tokens(system) + estimate_tokens(user)
    payload = build_payload(schema, system, user, deadline)

    # la place de la sortie est réservée AVANT l'appel : un contrat qui ne rentre pas ne part pas
    if estimate + deadline.reserved_output > deadline.context_window:
        refused = RawResponse(Outcome.budget_refused, "", "", "", {}, estimate)
        _record(payload, refused, "")

        return refused

    timeout = min(deadline.seconds, TIMEOUT_SEC)
    try:
        with httpx.Client(timeout=timeout, transport=httpx.HTTPTransport(retries=0)) as client:
            answer = client.post(f"{base_url()}/chat/completions", json=payload)
            answer.raise_for_status()
            body = answer.json()
    except (httpx.HTTPError, ValueError) as failure:
        failed = RawResponse(Outcome.transport_error, "", "", "", {}, estimate)
        _record(payload, failed, f"{type(failure).__name__}: {failure}")

        return failed

    choice = (body.get("choices") or [{}])[0]
    content, thinking = _split_thinking(choice.get("message") or {})
    raw_stop_reason = str(choice.get("finish_reason") or "")
    outcome = {"stop": Outcome.completed, "length": Outcome.truncated}.get(raw_stop_reason, Outcome.unknown_stop)

    # une génération tronquée n'est pas une génération terminée : rien d'exploitable n'en sort
    exploitable = content if outcome is Outcome.completed else ""
    response = RawResponse(outcome, exploitable, thinking, raw_stop_reason, body.get("usage") or {}, estimate)
    _record(payload, response, content)

    return response
