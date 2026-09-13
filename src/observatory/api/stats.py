"""Les agrégats d'analyse et les cinq indicateurs des questions expérimentales.

Ils se calculent depuis les seuls événements. Une mesure absente reste absente : rien n'est estimé,
et un dénominateur nul rend `None` plutôt qu'un zéro qui se lirait comme une observation.
"""

from collections import Counter
from os.path import commonprefix

from kernel.contracts import Event, EventType
from kernel.errors import Cause, ErrorAccumulator

from .index import parse_ts

AGGREGATION_VERSION = "v2"
PRESSURE_STEPS = ((0.45, "low"), (0.75, "moderate"), (1.0, "high"))
OVERFLOW = "overflow_risk"


def _verdict(event: Event) -> str | None:
    "Verdict de double gate porté par un événement de validation, ou None."

    verification = event.payload.get("verification")
    if event.type != EventType.validation or not isinstance(verification, dict):
        return None

    return verification.get("verification")


def _model_call(event: Event) -> dict | None:
    "Trace d'appel modèle : `bridge` consigne son payload effectif et son issue à chaque appel."

    if event.type != EventType.status or "prompt_estimate" not in event.payload:
        return None

    return event.payload


def _tool_call(event: Event) -> dict | None:
    "Opération d'outil : `workspace` nomme l'opération et le chemin sur lequel elle porte."

    if event.type != EventType.tool_activity or not isinstance(event.payload.get("operation"), str):
        return None

    return event.payload


def _node(event: Event) -> dict | None:
    "Entrée de nœud : le contrat `Node` dumpé sous son nom, comme tout contrat dans un payload."

    node = event.payload.get("node")
    if not isinstance(node, dict) or event.payload.get("phase") == "intent":
        return None

    return node


def _int(value) -> int | None:
    "Entier réellement rapporté, ou None : une valeur absente n'est jamais un zéro."

    return value if isinstance(value, int) else None


def _pressure(share: float | None) -> str:
    "Palier de pression de la décision 14 ; sans mesure, la pression est `unknown`."

    if share is None:
        return "unknown"
    for ceiling, name in PRESSURE_STEPS:
        if share < ceiling:
            return name

    return OVERFLOW


def _changed_bytes(before: bytes, after: bytes) -> int:
    "Changement utile : le fichier moins ses préfixe et suffixe communs, en octets."

    head = len(commonprefix([before, after]))
    tails = [before[head:][::-1], after[head:][::-1]]
    tail = len(commonprefix(tails))

    return max(len(before), len(after)) - head - tail


def daily(events: list[Event], *, trials: list[dict] = ()) -> dict:
    "Statistiques journalières : volume, familles, validations vertes et appels modèle par jour UTC."

    days: dict[str, dict] = {}
    undated = 0
    for event in events:
        moment = parse_ts(event.ts)
        if moment is None:
            undated += 1
            continue
        day = days.setdefault(moment.date().isoformat(), {
            "day": moment.date().isoformat(),
            "events": 0,
            "families": Counter(),
            "verified": 0,
            "rejected": 0,
            "model_calls": 0,
            "tool_calls": 0,
        })

        # une ligne par jour, alimentée par famille puis par nature d'événement
        day["events"] += 1
        day["families"][event.type.value] += 1
        day["verified"] += _verdict(event) == "passed"
        day["rejected"] += _verdict(event) == "rejected"
        call = _model_call(event)
        day["model_calls"] += call is not None and call.get("outcome") != "budget_refused"
        day["tool_calls"] += _tool_call(event) is not None
    # les anciens refus sans événement de verdict sont attestés par leur sidecar final
    for trial in trials:
        result = trial.get("result") or {}
        moment = parse_ts(trial["last_ts"]) if trial.get("last_ts") else None
        if trial["has_verdict"] or moment is None:
            continue
        if result.get("status") == "blocked" and result.get("cause") == "invariant_failed":
            days[moment.date().isoformat()]["rejected"] += 1
    rows = [{**day, "families": dict(day["families"])} for day in days.values()]

    return {
        "version": AGGREGATION_VERSION,
        "days": sorted(rows, key=lambda row: row["day"]),
        "undated_events": undated,
    }


def tools(events: list[Event]) -> dict:
    """Appels, chemins et volume par outil, et l'inflation mesurée des splices.

    L'inflation apparie un `splice` et l'écriture qui le publie sur le même chemin : elle compare la
    source émise par le modèle au changement réellement utile.
    """

    per_operation: dict[str, dict] = {}
    spliced: dict[str, int] = {}
    patch_bytes = 0
    changed_bytes = 0
    pairs = 0
    for event in events:
        call = _tool_call(event)
        if call is None:
            continue
        path = str(call.get("path"))
        row = per_operation.setdefault(call["operation"], {"calls": 0, "paths": set(), "bytes": 0})
        row["calls"] += 1
        row["paths"].add(path)

        # une source émise par le modèle, puis l'écriture qui la publie
        source = call.get("new_source")
        if isinstance(source, str):
            emitted = len(source.encode("utf-8"))
            row["bytes"] += emitted
            spliced[path] = emitted
        before = call.get("before_hex")
        after = call.get("after_hex")
        if isinstance(before, str) and isinstance(after, str):
            useful = _changed_bytes(bytes.fromhex(before), bytes.fromhex(after))
            row["bytes"] += useful
            if path in spliced:
                pairs += 1
                patch_bytes += spliced.pop(path)
                changed_bytes += useful
    rows = [
        {"operation": name, "calls": row["calls"], "unique_paths": len(row["paths"]), "bytes": row["bytes"]}
        for name, row in sorted(per_operation.items())
    ]

    return {
        "version": AGGREGATION_VERSION,
        "tools": rows,
        "splice_inflation": {
            "pairs": pairs,
            "patch_bytes": patch_bytes,
            "changed_bytes": changed_bytes,
            "ratio": round(patch_bytes / changed_bytes, 3) if changed_bytes else None,
        },
    }


def context(events: list[Event], *, capability: dict | None = None) -> dict:
    """Occupation du contexte et marge restante, appel par appel (décision 14).

    L'estimation de préflight et l'usage mesuré restent deux champs distincts : c'est leur ratio qui
    instrumente la densité, et un usage non rapporté laisse la pression `unknown`.
    """

    calls = []
    for event in events:
        payload = _model_call(event)
        if payload is None:
            continue
        reported = payload.get("usage")
        usage = reported if isinstance(reported, dict) else {}
        measured = _int(usage.get("prompt_tokens"))
        reserved = _int(payload.get("max_tokens")) or 0
        estimate = _int(payload.get("prompt_estimate"))
        fallback = capability or {}
        capacity = _int(payload.get("context_window", fallback.get("context_window")))
        capacity = capacity if capacity is not None and capacity > 0 else None
        provenance = payload.get("context_provenance", fallback.get("provenance", "unknown"))
        occupancy = measured / capacity if measured is not None and capacity is not None else None

        # marge = fenêtre − prompt mesuré − sortie déjà réservée ; densité = mesuré / estimé
        calls.append({
            "ts": event.ts,
            "outcome": payload.get("outcome"),
            "prompt_estimate": estimate,
            "prompt_tokens": measured,
            "completion_tokens": _int(usage.get("completion_tokens")),
            "elapsed_seconds": payload.get("elapsed_seconds"),
            "context_window": capacity,
            "context_provenance": provenance if capacity is not None else "unknown",
            "truncated": payload.get("outcome") == "truncated" or payload.get("raw_stop_reason") == "length",
            "reserved_output": reserved,
            "occupancy": round(occupancy, 4) if occupancy is not None else None,
            "margin_tokens": capacity - measured - reserved if occupancy is not None else None,
            "pressure": _pressure(occupancy),
            "density": round(measured / estimate, 3) if measured is not None and estimate else None,
        })
    unknown = sum(call["prompt_tokens"] is None for call in calls)
    windows = {call["context_window"] for call in calls}

    return {
        "version": AGGREGATION_VERSION,
        "window": next(iter(windows)) if len(windows) == 1 else None,
        "calls": calls,
        "calls_without_usage": unknown,
        "summary": call_summary(calls),
    }


def call_summary(calls: list[dict]) -> dict:
    "Effectifs et troncatures observés ; les tokens inconnus restent hors de la somme mesurée."

    outcomes = Counter(call["outcome"] or "unknown" for call in calls)
    calls = [call for call in calls if call["outcome"] != "budget_refused"]
    truncated = sum(call["truncated"] for call in calls)
    tokens = [call["prompt_tokens"] + call["completion_tokens"] for call in calls
              if call["prompt_tokens"] is not None and call["completion_tokens"] is not None]

    return {
        "calls": len(calls),
        "budget_refused": outcomes.get("budget_refused", 0),
        "truncated": truncated,
        "truncation_rate": _ratio(truncated, len(calls)),
        "outcomes": dict(outcomes),
        "reported_tokens": sum(tokens) if tokens else None,
        "calls_without_complete_usage": len(calls) - len(tokens),
    }


def _ratio(numerator: int, denominator: int) -> float | None:
    "Rapport mesuré, ou None sans observation : un dénominateur nul n'est pas un zéro."

    if denominator == 0:
        return None

    return round(numerator / denominator, 3)


def _named_symbols(event: Event) -> list[str]:
    "Symboles nommés par un événement : ceux d'un critère, ou la fonction visée par un outil."

    verification = event.payload.get("verification")
    if isinstance(verification, dict) and isinstance(verification.get("criterion"), dict):
        return list(verification["criterion"].get("symbols") or [])
    node = _node(event)
    if node is not None and isinstance(node.get("criterion"), dict):
        return list(node["criterion"].get("symbols") or [])
    call = _tool_call(event)
    if call is not None and isinstance(call.get("function_name"), str):
        return [call["function_name"]]

    return []


def indicators(events: list[Event], *, trials: list[dict] = ()) -> dict:
    """Les cinq indicateurs des questions expérimentales, mesurés sur les seuls événements.

    Un indicateur sans observation rend `value: null` et le dit par son compte : il n'est jamais
    présenté comme un zéro mesuré.
    """

    verified = sum(_verdict(event) == "passed" for event in events)
    node_entries = [_node(event) for event in events]
    if trials:
        node_entries = [node for trial in trials for node in trial["indicator_nodes"]]
    cycles = sum(node is not None for node in node_entries)
    resumptions = sum("segment_from" in event.payload for event in events)
    blocked = Counter(
        node["blocked_cause"] for node in node_entries
        if node is not None and node.get("status") == "blocked" and node.get("blocked_cause")
    )
    stops = sum("stop_proposal" in event.payload for event in events)

    # position de la première vérification verte de chaque symbole
    verified_symbols: dict[str, int] = {}
    for position, event in enumerate(events):
        if _verdict(event) != "passed":
            continue
        for symbol in _named_symbols(event):
            verified_symbols.setdefault(symbol, position)

    # réutilisation : un nœud ou une opération d'outil qui nomme ce symbole plus tard
    reused: set[str] = set()
    for position, event in enumerate(events):
        if _verdict(event) is not None:
            continue
        for symbol in _named_symbols(event):
            first = verified_symbols.get(symbol)
            if first is not None and first < position:
                reused.add(symbol)

    return {
        "version": AGGREGATION_VERSION,
        "progress_without_intervention": {
            "question": "Progresse-t-il sans intervention ?",
            "value": _ratio(verified, cycles),
            "verified": verified,
            "cycles": cycles,
        },
        "resumption_after_interruption": {
            "question": "Reprend-il après interruption ?",
            "value": resumptions,
            "observations": resumptions,
        },
        "diagnosed_limitations": {
            "question": "Diagnostique-t-il ses limitations ?",
            "value": sum(blocked.values()),
            "by_cause": dict(blocked),
        },
        "verified_tool_reused": {
            "question": "Crée-t-il un outil utile, puis le réutilise-t-il ?",
            "value": _ratio(len(reused), len(verified_symbols)),
            "reused": sorted(reused),
            "verified_symbols": len(verified_symbols),
        },
        "stop_proposed_on_exhaustion": {
            "question": "Converge-t-il et propose-t-il l'arrêt ?",
            "value": stops,
            "observations": stops,
        },
    }


def validate(summary: dict) -> None:
    """Valide l'agrégat contre son contrat avant qu'il soit servi.

    Une projection non validée est une projection fausse : toutes les violations sont rendues d'un
    coup, chacune avec son chemin de champ.
    """

    accumulator = ErrorAccumulator()
    families = summary["families"]
    if sum(families.values()) != summary["n_events"]:
        accumulator.add("families", Cause.invalid_schema, "family counts must sum to n_events")
    if summary["digest"]["window"]["total"] != summary["n_events"]:
        accumulator.add("digest.window.total", Cause.invalid_schema, "digest must window every event")
    for name, entry in summary["artifacts"].items():
        if entry["exists"] != (entry["size"] is not None):
            accumulator.add(f"artifacts.{name}", Cause.invalid_schema, "presence must match the read size")

    accumulator.raise_if_any()
