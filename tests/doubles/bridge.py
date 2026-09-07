"""Faux fournisseur scénarisé : une file de réponses, aucun Ollama.

`engine` s'en sert pour éprouver sa politique de retry. On charge la file avec `script(...)` et on
la remplit avec les quatre fabriques ci-dessous, qui couvrent les six cas que la frontière doit
savoir rendre : réponse conforme, `invalid_json`, `schema_violation`, troncature, timeout, et une
réponse que le transport accepte mais que la revalidation locale rejette.
"""

import json

from bridge.client import Deadline, Outcome, RawResponse
from bridge.probe import Capability, Provenance
from bridge.revalidate import revalidate  # fonctions pures : un double en divergerait sans rien
from bridge.schema import normalize_schema  # prouver de plus

queue: list[RawResponse] = []
calls: list[dict] = []
capability = Capability(Provenance.confirmed, 16384, True, "")


def reset() -> None:
    "Vide la file et les appels observés, et rétablit une capacité utilisable."

    global capability

    queue.clear()
    calls.clear()
    capability = Capability(Provenance.confirmed, 16384, True, "")


def script(*responses: RawResponse) -> None:
    "Charge la file des réponses que les prochains appels rendront, dans cet ordre."

    queue.extend(responses)


def conformant(payload: dict) -> RawResponse:
    "Une génération terminée dont le contenu revalide."

    return RawResponse(Outcome.completed, json.dumps(payload), "", "stop", {}, 0)


def malformed(raw: str) -> RawResponse:
    "Une génération terminée que le transport a acceptée et que la revalidation rejettera."

    return RawResponse(Outcome.completed, raw, "", "stop", {}, 0)


def truncated() -> RawResponse:
    "Une génération coupée sur la borne de sortie : rien d'exploitable n'en sort."

    return RawResponse(Outcome.truncated, "", "", "length", {}, 0)


def transport_error() -> RawResponse:
    "Une route indisponible ou un dépassement d'attente."

    return RawResponse(Outcome.transport_error, "", "", "", {}, 0)


def call(schema: dict, system: str, user: str, deadline: Deadline) -> RawResponse:
    "Rend la prochaine réponse scriptée ; une file vide est une route indisponible."

    calls.append({"schema": schema, "system": system, "user": user, "deadline": deadline})
    if not queue:
        return transport_error()

    return queue.pop(0)


def probe() -> Capability:
    "Rend la capacité configurée, sans toucher au réseau."

    return capability
