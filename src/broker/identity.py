"""Identité d'un effet sortant : le résultat est déterministe, le transport est renouvelé.

Décision 30 — un push ou un message rejoué après un échec de transport porte **la même** identité de
résultat et une identité de transport **neuve**. Il ne compte pas deux fois.
"""

import hashlib
import uuid
from enum import StrEnum

from kernel.contracts import Contract, Name, PositiveInt
from kernel.facts import Digest


class Effect(StrEnum):
    commit = "commit"
    pull_request = "pull_request"
    automerge = "automerge"
    notify = "notify"


class EffectIdentity(Contract):
    """Les deux identités d'une tentative ; `transport` est exclu de toute comparaison."""

    result: Digest
    transport: Name


def result_key(mission: Name, node: Name, attempt: PositiveInt, effect: Effect) -> str:
    "Empreinte déterministe de (mission, nœud, tentative, effet), stable d'un rejeu à l'autre."

    # séparateur nul : deux axes concaténés ne peuvent pas produire la même empreinte
    axes = "\0".join([mission, node, str(attempt), Effect(effect).value])

    return hashlib.sha256(axes.encode()).hexdigest()


def transport_key() -> str:
    "Identité de transport, neuve à chaque tentative et jamais comparée."

    return uuid.uuid4().hex


def new_identity(mission: Name, node: Name, attempt: PositiveInt, effect: Effect) -> EffectIdentity:
    "L'identité d'une tentative : le résultat qu'elle vise, et le transport qu'elle emprunte."

    return EffectIdentity(result=result_key(mission, node, attempt, effect), transport=transport_key())


def same_result(left: EffectIdentity, right: EffectIdentity) -> bool:
    "Vrai quand les deux tentatives visent le même résultat, quel que soit leur transport."

    return left.result == right.result
