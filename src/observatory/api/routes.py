"""Routes de lecture : catalogue et détail séparés, manifeste d'artefacts, digest par famille.

Le processus est distinct du harness et n'écrit jamais. L'adresse de bind est une **constante** :
aucun chemin de code, aucune variable d'environnement ne peut l'ouvrir ailleurs que sur la loopback.
"""

from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from kernel.contracts import Event, Node

from . import stats
from .evidence import artifact_names, read_text, safe_path, trial_projection
from .index import EVENTS_NAME, Index, build_index, build_run_index, families, mission_events
from .index import parse_ts, refresh, segments
from .render import flatten_tree, status_text, window

HOST = "127.0.0.1"
PORT = 8823
LOGS_ROOT = Path.home() / "logs" / "pithos2"
DIGEST_EVENTS = 25
MAX_PAGE = 500
# un horodatage illisible ne se place pas au hasard : il passe en fin de tri
UNDATED = datetime(9999, 12, 31, tzinfo=timezone.utc)

app = FastAPI(title="Pithos observatory", version=stats.AGGREGATION_VERSION)
_index: Index | None = None


def bind(logs_root: Path) -> Index:
    "Fixe la racine de logs servie et reconstruit l'index depuis le disque. Lecture seule."

    global _index

    _index = build_index(logs_root)

    return _index


def bind_runs(runs_root: Path) -> Index:
    "Sert une collection d'essais explicitement choisie."

    global _index

    _index = build_run_index(runs_root)

    return _index


def _current() -> Index:
    "Index courant, rafraîchi par `mtime` ; une panne de suivi laisse l'index servi tel quel."

    if _index is None:
        bind(LOGS_ROOT)
    refresh(_index)

    return _index


def _freshness(index: Index) -> dict:
    "Fraîcheur visible sur chaque réponse : quand l'index a été bâti, relu, et ce qui a échoué."

    return {
        "built_at": index.built_at,
        "refreshed_at": index.refreshed_at,
        "watch_error": index.watch_error,
        "missions": len(index.rows),
    }


def _row(index: Index, mission_id: str):
    "Ligne de catalogue d'une mission indexée ; un identifiant inconnu ne devient jamais un chemin."

    row = index.rows.get(mission_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"unknown mission: {mission_id}")

    return row


def _size(path: Path) -> int | None:
    "Taille d'un artefact, ou None quand il n'est pas lisible. Aucune ouverture de fichier."

    try:
        return path.stat().st_size
    except OSError:
        return None


def _artifacts(index: Index, mission_id: str, events: list[Event]) -> dict:
    "Manifeste des artefacts : chemin, présence et taille — jamais le contenu."

    mission_dir = index.missions_root / mission_id
    paths = segments(mission_dir) + [mission_dir / name for name in artifact_names(mission_dir)]

    # les artefacts d'invariant sont ceux que les reçus nomment, et eux seuls
    for event in events:
        receipt = event.payload.get("receipt")
        if isinstance(receipt, dict) and isinstance(receipt.get("artifact_path"), str):
            paths.append(Path(receipt["artifact_path"]))

    manifest = {}
    for path in paths:
        key = str(path.relative_to(mission_dir)) if path.is_relative_to(mission_dir) else str(path)
        try:
            safe = safe_path(mission_dir, key)
            size = _size(safe)
        except ValueError:
            size = None
        manifest[key] = {"path": str(path), "exists": size is not None, "size": size}

    return manifest


def _scoped_events(index: Index, mission_id: str | None) -> list[Event]:
    "Événements du périmètre demandé : une mission nommée, ou tout le catalogue, dans l'ordre."

    if mission_id is not None:
        _row(index, mission_id)

        return mission_events(index, mission_id)[0]

    collected = []
    for name in index.rows:
        collected.extend(mission_events(index, name)[0])
    collected.sort(key=lambda event: parse_ts(event.ts) or UNDATED)

    return collected


@app.get("/ready")
def ready():
    "Readiness servie depuis ce qui a réellement été indexé, jamais depuis le spawn du processus."

    index = _current()

    return {
        "ready": index.watch_error is None,
        "logs_root": str(index.logs_root),
        "freshness": _freshness(index),
    }


@app.get("/missions")
def missions(limit: int = Query(25, ge=1, le=MAX_PAGE), offset: int = Query(0, ge=0)):
    "Catalogue : il ne charge jamais les événements d'une mission, seulement leur comptage."

    index = _current()
    rows = sorted(index.rows.values(), key=lambda row: row.last_ts or "", reverse=True)
    selected, omission = window(rows, limit, offset)

    return {
        "missions": selected,
        "window": omission,
        "has_more": omission["below"] > 0,
        "freshness": _freshness(index),
    }


@app.get("/missions/{mission_id}")
def mission(mission_id: str):
    "Détail d'une mission : comptage par famille, digest borné, artefacts et rendu texte compact."

    index = _current()
    row = _row(index, mission_id)
    mission_dir = index.missions_root / mission_id
    events, read_anomalies = mission_events(index, mission_id)
    tail = max(len(events) - DIGEST_EVENTS, 0)
    selected, omission = window(events, DIGEST_EVENTS, tail)
    observed = trial_projection(mission_dir, events)
    snapshot = tuple(Node.model_validate(node) for node in observed["nodes"])
    nodes, tree_anomalies = flatten_tree(events, snapshot=snapshot)

    # le détail compte ce qu'il vient de lire ; le catalogue peut être en retard, il le dit
    summary = {
        "mission_id": mission_id,
        "n_events": len(events),
        "families": families(events),
        "first_ts": row.first_ts,
        "last_ts": row.last_ts,
        "segments": row.segments,
        "anomalies": list(read_anomalies) + tree_anomalies,
        "digest": {
            "events": [event.model_dump(mode="json") for event in selected],
            "window": {"path": str(mission_dir / EVENTS_NAME), **omission},
        },
        "artifacts": _artifacts(index, mission_id, events),
        "trial": observed,
        "context": stats.context(events, capability=(observed["result"] or {}).get("capability")),
        "status_text": status_text(row, nodes),
        "freshness": _freshness(index),
    }
    stats.validate(summary)

    return summary


@app.get("/missions/{mission_id}/tree")
def tree(mission_id: str, limit: int = Query(200, ge=1, le=MAX_PAGE), offset: int = Query(0, ge=0)):
    "Arbre aplati en lignes : parenté conservée, durées séparées, anomalies montrées."

    index = _current()
    _row(index, mission_id)
    events, read_anomalies = mission_events(index, mission_id)
    observed = trial_projection(index.missions_root / mission_id, events)
    snapshot = tuple(Node.model_validate(node) for node in observed["nodes"])
    rows, tree_anomalies = flatten_tree(events, snapshot=snapshot)
    selected, omission = window(rows, limit, offset)

    return {
        "nodes": selected,
        "window": omission,
        "anomalies": list(read_anomalies) + tree_anomalies + observed["anomalies"],
        "freshness": _freshness(index),
    }


@app.get("/missions/{mission_id}/artifacts")
def artifacts(mission_id: str):
    "Manifeste d'artefacts d'une mission : présence et taille, servis tels quels."

    index = _current()
    _row(index, mission_id)
    events, _ = mission_events(index, mission_id)

    return {"artifacts": _artifacts(index, mission_id, events), "freshness": _freshness(index)}


@app.get("/stats/daily")
def stats_daily(mission: str | None = None):
    "Statistiques journalières, sur une mission nommée ou sur tout le catalogue."

    index = _current()

    return stats.daily(_scoped_events(index, mission), trials=_trials(index, mission))


@app.get("/stats/tools")
def stats_tools(mission: str | None = None):
    "Appels, chemins et volume par outil, et l'inflation mesurée des splices."

    index = _current()

    return stats.tools(_scoped_events(index, mission))


@app.get("/stats/context")
def stats_context(mission: str | None = None):
    "Occupation du contexte et marge restante, appel par appel."

    index = _current()

    names = [mission] if mission is not None else list(index.rows)
    calls = []
    for name in names:
        _row(index, name)
        events, _ = mission_events(index, name)
        observed = trial_projection(index.missions_root / name, events)
        capability = (observed["result"] or {}).get("capability")
        report = stats.context(events, capability=capability)
        calls.extend({"mission_id": name, **call} for call in report["calls"])

    return {"version": stats.AGGREGATION_VERSION, "calls": calls, "summary": stats.call_summary(calls)}


@app.get("/stats/attempts")
def stats_attempts():
    "Bilan séparé par mode : un selftest ou une probe n'est jamais un succès du modèle réel."

    index = _current()
    groups = {}
    for trial in _trials(index, None):
        result = trial["result"] or {}
        mode = result.get("mode", "unknown")
        group = groups.setdefault(mode, {
            "runs": 0,
            "with_state": 0,
            "admission_errors": 0,
            "with_receipt": 0,
            "restored": 0,
            "unchanged": 0,
            "by_cause": {},
        })
        group["runs"] += 1
        group["with_state"] += bool(trial["nodes"])
        group["admission_errors"] += bool(result.get("error")) and not trial["nodes"]
        group["with_receipt"] += trial["receipt_count"] > 0
        group["restored"] += result.get("restored") is True
        before = result.get("before_sha256")
        group["unchanged"] += before is not None and before == result.get("after_sha256")
        cause = result.get("cause")
        if cause:
            group["by_cause"][cause] = group["by_cause"].get(cause, 0) + 1

    return {"version": stats.AGGREGATION_VERSION, "by_mode": groups, "freshness": _freshness(index)}


@app.get("/indicators")
def indicators(mission: str | None = None):
    "Les cinq indicateurs des questions expérimentales, sans terminal."

    index = _current()

    return stats.indicators(_scoped_events(index, mission), trials=_trials(index, mission))


def _trials(index: Index, mission_id: str | None) -> list[dict]:
    "Projections indépendantes par essai, sans créer d'événement rétrospectif."

    names = [mission_id] if mission_id is not None else list(index.rows)
    observed = []
    for name in names:
        _row(index, name)
        events, _ = mission_events(index, name)
        trial = trial_projection(index.missions_root / name, events)
        trial["last_ts"] = index.rows[name].last_ts
        trial["has_verdict"] = any(stats._verdict(event) is not None for event in events)
        trial["indicator_nodes"] = trial["nodes"] if trial["state_source"] == "tree.json" else [stats._node(event) for event in events]
        observed.append(trial)

    return observed


@app.get("/missions/{mission_id}/artifact")
def artifact(mission_id: str, path: str, limit: int = Query(200, ge=1, le=MAX_PAGE), offset: int = Query(0, ge=0)):
    "Aperçu texte borné d'un artefact connu ; jamais un chemin du workspace ou un lien sortant."

    index = _current()
    _row(index, mission_id)
    root = index.missions_root / mission_id
    if path not in artifact_names(root):
        raise HTTPException(status_code=404, detail="unknown artifact")
    try:
        content = read_text(root, path)
    except (OSError, ValueError) as failure:
        code = 413 if str(failure) == "artifact_too_large" else 404
        raise HTTPException(status_code=code, detail=str(failure)) from failure
    selected, omission = window(content.splitlines(), limit, offset)

    return {"path": path, "text": "\n".join(selected), "window": omission}


@app.get("/missions/{mission_id}/events")
def events_page(mission_id: str, limit: int = Query(100, ge=1, le=MAX_PAGE), offset: int = Query(0, ge=0)):
    "Page de journal lue par son propriétaire, avec omissions explicites."

    index = _current()
    _row(index, mission_id)
    events, anomalies = mission_events(index, mission_id)
    selected, omission = window(events, limit, offset)

    return {"events": selected, "window": omission, "anomalies": anomalies}


def serve() -> None:
    "Sert l'observatoire sur la loopback. `HOST` est une constante, jamais un réglage."

    uvicorn.run(app, host=HOST, port=PORT)
