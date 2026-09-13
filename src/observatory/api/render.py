"""Aplatissement d'arbre et rendu texte compact : une seule vue, trois transports.

Le statut vient des événements publiés, puis du snapshot courant lorsqu'il est fourni.
Les intentions ne font pas autorité ; une durée absente du snapshot reste inconnue.
"""

from kernel.contracts import Contract, Event, Node

from .index import MissionRow, parse_ts

NODE_KEY = "node"
LABEL_CHARS = 80
PREVIEW_NODES = 10


class TreeRow(Contract):
    """Une ligne d'arbre aplati : parenté conservée, durées séparées, anomalies portées."""

    node_id: str
    parent_id: str | None
    depth: int
    status: str
    label: str
    target: str
    n_entries: int
    own_ms: int | None
    subtree_ms: int | None
    anomalies: tuple[str, ...]


def label(node: Node) -> str:
    "Libellé borné dérivé du critère et de la cible ; l'arbre reste lisible sans champ dédié."

    if node.criterion is None:
        text = str(node.target)
    else:
        symbols = ", ".join(node.criterion.symbols)
        text = f"{node.criterion.relation.value}({symbols}) · {node.target}"

    return text if len(text) <= LABEL_CHARS else f"{text[:LABEL_CHARS - 1]}…"


def node_entries(events: list[Event]) -> tuple[list, list[str]]:
    "Entrées de nœud du flux : un payload portant un `node` conforme au contrat de `kernel`."

    entries = []
    anomalies = []
    for event in events:
        if event.payload.get("phase") == "intent":
            continue
        raw = event.payload.get(NODE_KEY)
        if not isinstance(raw, dict):
            continue
        try:
            node = Node.model_validate(raw)
        except ValueError:
            anomalies.append(f"invalid_node:{event.ts}")
            continue
        entries.append((node, parse_ts(event.ts)))

    return entries, anomalies


def _collect(entries: list) -> tuple[dict, list[str], list[str]]:
    """Regroupe les entrées par identifiant ; la première fixe la parenté, la dernière le statut.

    Un identifiant dupliqué ne crée jamais un second nœud — il produit un graphe multiparent qui
    explose au parcours.
    """

    states: dict[str, dict] = {}
    order: list[str] = []
    anomalies: list[str] = []
    for node, moment in entries:
        state = states.get(node.id)
        if state is None:
            state = {"first": node, "last": node, "stamps": [], "n": 0}
            states[node.id] = state
            order.append(node.id)
        elif node.parent_id != state["first"].parent_id:
            anomalies.append(f"duplicate_id:{node.id}")
        state["last"] = node
        state["n"] += 1
        if moment is not None:
            state["stamps"].append(moment)

    return states, order, anomalies


def _spans(states: dict, children: dict, order: list[str]) -> dict:
    """Enveloppe temporelle de chaque sous-arbre, agrégée en remontant.

    C'est `max(fin) − min(début)`, jamais une somme de durées concurrentes.
    """

    spans: dict[str, tuple | None] = {}
    for node_id in reversed(order):
        stamps = states[node_id]["stamps"]
        starts = [stamps[0]] if stamps else []
        ends = [stamps[-1]] if stamps else []

        # bornes des enfants déjà agrégés — l'ordre inverse du parcours les garantit vues
        for child_id in children.get(node_id, []):
            child_span = spans.get(child_id)
            if child_span is not None:
                starts.append(child_span[0])
                ends.append(child_span[1])
        spans[node_id] = (min(starts), max(ends)) if starts else None

    return spans


def _milliseconds(start, end) -> int:
    "Écart en millisecondes, rendu tel quel : une valeur négative est une anomalie à montrer."

    return int((end - start).total_seconds() * 1000)


def flatten_tree(events: list[Event], *, snapshot: tuple[Node, ...] = ()) -> tuple[list[TreeRow], list[str]]:
    """Aplatit l'arbre en lignes, parenté et profondeur de parcours conservées.

    Résiste aux identifiants dupliqués, aux parents inconnus et aux cycles : chaque nœud vu paraît
    exactement une fois, et ce qui a été redressé est déclaré.
    """

    entries, anomalies = node_entries(events)
    entries.extend((node, None) for node in snapshot)
    states, order, collisions = _collect(entries)
    anomalies.extend(collisions)

    # parenté résolue : un parent inconnu fait une racine, et le dit
    children: dict[str | None, list[str]] = {}
    roots = []
    for node_id in order:
        parent_id = states[node_id]["first"].parent_id
        if parent_id is None:
            roots.append(node_id)
        elif parent_id not in states:
            anomalies.append(f"orphan:{node_id}")
            roots.append(node_id)
        else:
            children.setdefault(parent_id, []).append(node_id)

    # parcours itératif avec ensemble `visited` : un cycle ne fait pas boucler la vue
    visited: set[str] = set()
    walk = []
    stack = [(node_id, 0) for node_id in reversed(roots)]
    while stack:
        node_id, depth = stack.pop()
        if node_id in visited:
            continue
        visited.add(node_id)
        walk.append((node_id, depth))
        stack.extend((child_id, depth + 1) for child_id in reversed(children.get(node_id, [])))

    # un nœud jamais atteint depuis une racine est montré à plat, jamais tu
    for node_id in order:
        if node_id not in visited:
            anomalies.append(f"unreachable:{node_id}")
            walk.append((node_id, 0))

    spans = _spans(states, children, [node_id for node_id, _ in walk])
    rows = []
    for node_id, depth in walk:
        state = states[node_id]
        node = state["last"]
        stamps = state["stamps"]
        span = spans[node_id]
        own_ms = _milliseconds(stamps[0], stamps[-1]) if stamps else None
        row_anomalies = [anomaly for anomaly in anomalies if anomaly.endswith(f":{node_id}")]
        if own_ms is not None and own_ms < 0:
            row_anomalies.append(f"negative_duration:{node_id}")
        if node.depth != depth:
            row_anomalies.append(f"depth_mismatch:{node_id}")
        rows.append(TreeRow(
            node_id=node_id,
            parent_id=state["first"].parent_id,
            depth=depth,
            status=node.status.value,
            label=label(node),
            target=str(node.target),
            n_entries=state["n"],
            own_ms=own_ms,
            subtree_ms=_milliseconds(span[0], span[1]) if span is not None else None,
            anomalies=tuple(row_anomalies),
        ))

    return rows, anomalies


def window(rows: list, limit: int, offset: int) -> tuple[list, dict]:
    "Fenêtre d'une projection partielle, qui déclare toujours ce qu'elle omet (décision 29)."

    total = len(rows)
    start = min(max(offset, 0), total)
    selected = rows[start:start + limit]

    omission = {
        "total": total,
        "above": start,
        "below": total - start - len(selected),
    }

    return selected, omission


def status_text(row: MissionRow, rows: list[TreeRow]) -> str:
    """Rendu texte compact de l'état d'une mission, réutilisé par le CLI, Telegram et le web.

    Ce qui n'a pas été observé est dit `unavailable` ; rien n'y est estimé.
    """

    families = ", ".join(f"{name}={total}" for name, total in sorted(row.families.items()))
    statuses = ", ".join(f"{tree_row.node_id}:{tree_row.status}" for tree_row in rows[:PREVIEW_NODES])
    anomalies = list(row.anomalies) + [anomaly for tree_row in rows for anomaly in tree_row.anomalies]
    lines = [
        f"mission: {row.mission_id}",
        f"events: {row.n_events} in {row.segments} segment(s)",
        f"window: {row.first_ts or 'unavailable'} → {row.last_ts or 'unavailable'}",
        f"families: {families or 'unavailable'}",
        f"nodes: {len(rows)}",
    ]

    # aperçu borné des nœuds, puis les anomalies conservées telles quelles
    if statuses:
        lines.append(f"node_status: {statuses}")
    if len(rows) > PREVIEW_NODES:
        lines.append(f"node_status_omitted: {len(rows) - PREVIEW_NODES}")
    lines.append(f"anomalies: {', '.join(anomalies) if anomalies else 'none'}")
    log_content = "\n".join(lines)

    return log_content
