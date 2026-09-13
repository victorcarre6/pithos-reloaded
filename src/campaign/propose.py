"""La redondance en deux temps, le classement par axes nommés, et le filet déterministe.

**Aucun appel modèle n'entre dans une décision de politique** — et la redondance en est une. La dédup
sémantique à choix fermé, fail-open, respecterait pourtant la contrainte n°1 à la lettre : elle est
écartée quand même.

PORTED_FROM: kilocode-main/packages/kilo-memory/src/recall/topics.ts:21,26-96 (Apache-2.0)
PORTED_FROM: ouroboros-main/ouroboros/improvement_backlog.py:285-374 (Apache-2.0)
"""

import json
import re
import unicodedata
from datetime import datetime, timezone
from difflib import SequenceMatcher
from enum import StrEnum
from hashlib import sha256

from pydantic import Field
from typing import Annotated

from kernel.contracts import Contract, Criterion, Name, PositiveInt
from kernel.facts import Digest

from . import store
from .admit import BlastRadius, Proposal
from .store import ALIVE, Entry, Family, Source


LEXICAL_OVERLAP = 0.6   # part des termes de la proposition déjà couverts par une entrée
SEQUENCE_RATIO = 0.8    # similarité de surface, pour une reformulation quasi identique
TERMS_MAX = 24
RELATED_MIN = 4         # en dessous, un préfixe partagé n'est plus un indice de la même racine
RELATED_DRIFT = 3       # au delà, ce n'est plus une forme fléchie mais un autre mot
DERIVE_AFTER = 3

TOKEN_PATTERN = re.compile(r"[^\W_][\w.\-]+", re.UNICODE)
SEPARATOR_PATTERN = re.compile(r"[_.\-]+")

AXES = ("blast_radius", "evidence", "source", "name")
BLAST_ORDER = (BlastRadius.file, BlastRadius.module, BlastRadius.repo)
SOURCE_ORDER = (Source.model, Source.derived)


class Stage(StrEnum):
    lexical = "lexical"    # à la proposition, sur les mots
    contract = "contract"  # dès que le critère existe, sur l'empreinte


class Redundancy(Contract):
    """Le doublon constaté : à quel temps, contre quelle entrée, et combien de fois déjà."""

    stage: Stage
    key: Name
    detail: str
    count: PositiveInt


class SignalKind(StrEnum):
    todo = "todo"
    untested = "untested"
    undocumented = "undocumented"


class Signal(Contract):
    """Un fait déterministe relevé sur le dépôt ; jamais un jugement."""

    kind: SignalKind
    path: Name
    symbol: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$")]


def terms(text: str) -> list[str]:
    """Termes d'un texte : le composé entier, puis chacune de ses parties, sans doublon.

    `read_csv` donne `read_csv`, `read` et `csv`, pour qu'un composé et ses morceaux se rencontrent.
    """

    normalized = unicodedata.normalize("NFKC", text)
    collected = []
    for token in TOKEN_PATTERN.findall(normalized):
        compound = SEPARATOR_PATTERN.sub("_", token).strip("_").lower()
        pieces = [piece.lower() for piece in SEPARATOR_PATTERN.split(token) if piece]
        for term in [compound, *pieces]:
            if term and term not in collected:
                collected.append(term)

    return collected[:TERMS_MAX]


def related(left: str, right: str) -> bool:
    "Deux termes de même racine, sans règle de désuffixation propre à une langue."

    if left == right:
        return True

    shared = min(len(left), len(right))

    return (shared >= RELATED_MIN and abs(len(left) - len(right)) <= RELATED_DRIFT
            and (left.startswith(right) or right.startswith(left)))


def overlap(wanted: list[str], covered: list[str]) -> float:
    "Part des termes de la proposition qu'une entrée couvre déjà, formes fléchies comprises."

    if not wanted:
        return 0.0

    matched = [term for term in wanted if any(related(term, other) for other in covered)]

    return len(matched) / len(wanted)


def contract_fingerprint(criterion: Criterion | None) -> Digest | str:
    "Empreinte stable du contrat `{relation, symbols, domain}`, canonicalisée avant comparaison."

    if criterion is None:
        return ""

    canonical = json.dumps(criterion.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)

    return sha256(canonical.encode("utf-8")).hexdigest()


def dedup(proposal: Proposal, state: store.Store) -> Redundancy | None:
    """Rejette un doublon en deux temps, **sans aucun appel modèle**.

    Le temps 2 tranche là où le lexical est aveugle : deux formulations différentes qui produisent le
    même contrat sont le même outil. Le prix est nommé — ce doublon-là se découvre tard.
    """

    fingerprint = contract_fingerprint(proposal.criterion)
    spoken = f"{proposal.title} {proposal.description}"
    wanted = terms(spoken)

    for family in ALIVE:
        for key, entry in state.entries[family].items():
            written = f"{entry.title} {entry.content}"
            if fingerprint and entry.reference.get("contract") == fingerprint:
                return Redundancy(stage=Stage.contract, key=key, detail=fingerprint, count=entry.version)

            ratio = overlap(wanted, terms(written))
            surface = SequenceMatcher(None, spoken, written).ratio()
            if ratio >= LEXICAL_OVERLAP or surface >= SEQUENCE_RATIO:
                log_content = f"overlap={ratio:.2f} surface={surface:.2f}"

                return Redundancy(stage=Stage.lexical, key=key, detail=log_content, count=entry.version)

    return None


def remember(proposal: Proposal, redundancy: Redundancy) -> None:
    """Compte la récurrence au lieu de la jeter : un doublon rejeté trois fois est un signal.

    Le compte est la **version** de l'entrée `memory`, que le magasin incrémente à chaque écriture.
    """

    now = datetime.now(timezone.utc).isoformat()
    seen = Entry(
        key=redundancy.key,
        family=Family.memory,
        title=proposal.title,
        content=proposal.description,
        source=proposal.source,
        version=1,
        created_at=now,
        updated_at=now,
        reference={"stage": redundancy.stage.value, "detail": redundancy.detail},
    )
    store.put(Family.memory, redundancy.key, seen)


def axes(proposal: Proposal) -> tuple:
    "Le tuple de classement, un axe nommé par position — aucun scalaire pondéré, aucun score."

    return (
        BLAST_ORDER.index(proposal.blast_radius),
        -len(proposal.evidence),
        SOURCE_ORDER.index(proposal.source),
        proposal.name,
    )


def rank(proposals: list[Proposal]) -> list[Proposal]:
    "Classe par tuple lexicographique : chaque départage est attribuable à un axe de `AXES`."

    return sorted(proposals, key=axes)


def derive(signals: list[Signal], rejections: int) -> list[Proposal]:
    """Filet déterministe : il ne se déclenche **qu'après trois rejets consécutifs**.

    Le backlog ouvert est le sujet d'étude — si le harness dérivait toutes les propositions, la
    question « crée-t-il un outil utile, puis le réutilise-t-il ? » perdrait son sujet.
    """

    if rejections < DERIVE_AFTER:
        return []

    derived = []
    for signal in signals:
        kind = signal.kind.value
        derived.append(Proposal(
            name=f"{kind}_{signal.symbol}"[:64],
            title=f"address the {kind} on {signal.symbol}",
            description=f"a {kind} signal was found on {signal.symbol} in {signal.path}",
            evidence=[f"{kind} in {signal.path}"],
            blast_radius=BlastRadius.file,
            source=Source.derived,
            module=f"tools.{signal.symbol}",
            call="run",
            arguments=[],
            template=f"{kind}_{signal.symbol}"[:64],
            criterion=None,
        ))

    return rank(derived)


def counters(state: store.Store) -> dict[Source, int]:
    "Compte les entrées par provenance : le filet devient lui-même une mesure de ce que le modèle rate."

    tally = {source: 0 for source in Source}
    for family in ALIVE:
        for entry in state.entries[family].values():
            tally[entry.source] += 1

    return tally
