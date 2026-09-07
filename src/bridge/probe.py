"""Trois contrôles d'avant-campagne : la fenêtre est lue, le schéma est éprouvé, sinon on refuse."""

import os
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import httpx
from kernel.contracts import Criterion

from .client import Deadline, Outcome, base_url, call
from .revalidate import Ok, revalidate
from .schema import normalize_schema

WINDOW_ENV = "PITHOS_CONTEXT_WINDOW"
MODELS_TIMEOUT_SEC = 5.0
PROBE_TIMEOUT_SEC = 60.0
PROBE_OUTPUT_TOKENS = 128
PROMPT_PATH = Path(__file__).parent / "prompt" / "ling.md"
PROBE_TASK = "Name the relation stating that the function `parse` is total over small integers."


class Provenance(StrEnum):
    confirmed = "confirmed"
    asserted = "asserted"
    unprobeable = "unprobeable"


@dataclass(frozen=True, slots=True)
class Capability:
    "Ce que la route a prouvé savoir faire ; `usable` est fail-closed."

    provenance: Provenance
    context_window: int
    schema_honored: bool
    detail: str

    @property
    def usable(self) -> bool:
        return self.provenance is not Provenance.unprobeable and self.schema_honored


def system_prompt() -> str:
    "Le prompt système est une donnée versionnée, jamais une constante enfouie dans le code."

    return PROMPT_PATH.read_text(encoding="utf-8")


def read_window() -> tuple[Provenance, int]:
    "Lit `n_ctx_train` sur `/v1/models` ; à défaut, l'aveu explicite de l'opérateur, sinon rien."

    try:
        with httpx.Client(timeout=MODELS_TIMEOUT_SEC, transport=httpx.HTTPTransport(retries=0)) as client:
            answer = client.get(f"{base_url()}/models")
            answer.raise_for_status()
            models = answer.json().get("data") or []
    except (httpx.HTTPError, ValueError):
        models = []

    for model in models:
        meta = model.get("meta") or {}
        window = meta.get("n_ctx_train") or model.get("context_window") or 0
        if window:
            return Provenance.confirmed, int(window)

    acknowledged = os.environ.get(WINDOW_ENV, "")
    if acknowledged.isdigit() and int(acknowledged) > 0:
        return Provenance.asserted, int(acknowledged)

    return Provenance.unprobeable, 0


def probe() -> Capability:
    """Trois contrôles avant campagne, dans l'ordre où ils peuvent échouer.

    La fenêtre est lue et non supposée ; un vrai `Criterion` est envoyé ; sa réponse doit revalider.
    """

    provenance, window = read_window()
    if provenance is Provenance.unprobeable:
        return Capability(provenance, 0, False, "n_ctx_train illisible sur /v1/models")

    schema = normalize_schema(Criterion)
    deadline = Deadline(PROBE_TIMEOUT_SEC, window, PROBE_OUTPUT_TOKENS)
    response = call(schema, system_prompt(), PROBE_TASK, deadline)
    if response.outcome is not Outcome.completed:
        return Capability(provenance, window, False, f"appel de sonde: {response.outcome.value}")

    verdict = revalidate(response.content, schema, Criterion)
    if not isinstance(verdict, Ok):
        return Capability(provenance, window, False, f"revalidation: {verdict.code.value}")

    return Capability(provenance, window, True, "")
