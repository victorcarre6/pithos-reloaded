"""Double de la politique : un magasin en mémoire, sans fichier ni journal, et un `admit` pilotable.

Quatre scénarios se scriptent en assignant un attribut du module, parce que ce sont ceux que la
frontière doit savoir jouer : `malformed` reçoit une entrée que `load` doit ignorer sans lever,
`verdicts` pilote `admit` proposition par proposition, `redundancy` force le verdict de `dedup`, et
`stop` force celui de `should_stop`.

Les fonctions de politique pures — `rank`, `derive`, et la dédup non forcée — sont importées telles
quelles : un double les réimplémenterait à l'identique, et en aurait fait une seconde politique.
"""

from campaign.admit import Err, Ok, Proposal, Violation
from campaign.propose import Redundancy, dedup as real_dedup, derive, rank  # politiques pures
from campaign.stop import StopProposal, should_stop as real_should_stop
from campaign.store import ALIVE, CLIP, Entry, Family, Store
from kernel.errors import Cause

entries: dict[Family, dict[str, Entry]] = {family: {} for family in ALIVE}
malformed: dict[Family, dict[str, dict]] = {family: {} for family in ALIVE}
ignored: list[str] = []
verdicts: dict[str, object] = {}
redundancy: Redundancy | None = None
stop: StopProposal | None = None


def reset() -> None:
    "Vide le magasin en mémoire et rétablit les quatre scénarios scriptables à leur valeur nominale."

    global redundancy, stop

    for family in ALIVE:
        entries[family].clear()
        malformed[family].clear()
    ignored.clear()
    verdicts.clear()
    redundancy = None
    stop = None


def bind(path=None, *, trace=None) -> None:
    "Accepte la liaison sans rien ouvrir : le double n'a ni fichier ni journal."


def load() -> Store:
    "Rend le magasin en mémoire. NE LÈVE JAMAIS : une entrée mal formée est ignorée avec sa raison."

    state = Store(entries={family: dict(entries[family]) for family in ALIVE})
    for family in ALIVE:
        for key, raw in malformed[family].items():
            try:
                state.entries[family][key] = Entry.model_validate({**raw, "key": key, "family": family})
            except ValueError as error:
                ignored.append(f"{family.value}:{key}: {error}".replace("\n", " "))

    return state


def put(family: Family, key: str, entry: Entry) -> None:
    "Écrit l'entrée en mémoire ; une clé déjà présente garde sa création et voit sa version montée."

    previous = entries[family].get(key)
    version = previous.version + 1 if previous else 1
    created_at = previous.created_at if previous else entry.created_at
    entries[family][key] = entry.model_copy(update={"key": key, "family": family, "version": version,
                                                    "created_at": created_at})


def render_compact(family: Family, budget: int) -> str:
    "Même forme bornée que le magasin réel : un en-tête compté, des lignes, puis ce qui est omis."

    records = load().entries[family]
    header = f"{family}: {len(records)}"
    marker = f"  - +{len(records)} more"
    available = budget - len(marker) - 1

    lines = [header]
    used = len(header)
    for entry in records.values():
        line = f"  - [{family}:{entry.key}] {entry.title} (v{entry.version}, {entry.source}): {entry.content[:CLIP]}"
        if used + len(line) + 1 > available:
            break
        lines.append(line)
        used += len(line) + 1

    omitted = len(records) - len(lines) + 1
    if omitted:
        lines.append(f"  - +{omitted} more")

    return "\n".join(lines)


def admit(proposal: dict) -> Ok[Proposal] | Err[list[Violation]]:
    "Rend le verdict scripté pour cette proposition, ou juge sur la seule forme du contrat."

    scripted = verdicts.get(proposal.get("name"))
    if scripted is not None:
        return scripted

    try:
        return Ok(Proposal.model_validate(proposal))
    except ValueError as error:
        return Err([Violation(field_path="proposal", cause=Cause.invalid_schema, detail=str(error))])


def dedup(proposal: Proposal, state: Store) -> Redundancy | None:
    "Rend la redondance forcée par le test, sinon la même décision mécanique que la politique réelle."

    if redundancy is not None:
        return redundancy

    return real_dedup(proposal, state)


def should_stop(state: Store) -> StopProposal | None:
    "Rend la proposition d'arrêt forcée par le test, sinon celle que la politique réelle rendrait."

    if stop is not None:
        return stop

    return real_should_stop(state)
