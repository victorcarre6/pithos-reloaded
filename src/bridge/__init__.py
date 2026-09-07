"""La frontière modèle : tout ce que le modèle peut émettre est défini ici.

C'est le point d'application de la contrainte dure n°1 — aucun littéral produit par le modèle
n'atteint l'exécution. La politique de retry est métier et vit dans `engine`, jamais ici.
"""

from pydantic import BaseModel
from typing import Protocol, runtime_checkable

from .client import Deadline, Outcome, RawResponse, call
from .probe import Capability, Provenance, probe
from .revalidate import Err, ErrorCode, Ok, revalidate
from .schema import normalize_schema

__all__ = [
    "Bridge", "Capability", "Deadline", "Err", "ErrorCode", "Ok", "Outcome", "Provenance",
    "RawResponse", "call", "normalize_schema", "probe", "revalidate",
]


@runtime_checkable
class Bridge(Protocol):
    """Ce que `engine` attend de la frontière modèle — implémentation comme double.

    Les membres sont statiques : la frontière est un module, pas un objet à instancier.
    """

    @staticmethod
    def normalize_schema(model: type[BaseModel]) -> dict: ...

    @staticmethod
    def call(schema: dict, system: str, user: str, deadline: Deadline) -> RawResponse: ...

    @staticmethod
    def revalidate(raw: str, schema: dict, model: type[BaseModel]) -> Ok[BaseModel] | Err[ErrorCode]: ...

    @staticmethod
    def probe() -> Capability: ...
