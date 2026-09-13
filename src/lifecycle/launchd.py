"""Admission des réveils, adaptée de prime-agent/core/cron-jobs.ts:1591-1640."""

from pathlib import Path

import journal

from .lock import LockPort, LockState, record


def claim_tick(tick_id: str, *, lock: LockPort, events_path: Path, trace=journal) -> bool:
    """Consomme le tick avant livraison ; le gagnant garde le verrou jusqu'à release."""

    # un réveil occupé est consommé, sans attendre ni arrêter son propriétaire
    if lock.acquire() == LockState.unavailable:
        record(trace, "tick_skipped", tick_id=tick_id)

        return False

    # lecture par démarrage, sous le verrou commun à toutes les missions
    admitted = False
    try:
        if trace.torn_tail(events_path) is not None:
            return False
        for event in trace.read(events_path):
            payload = event.payload
            if payload.get("scope") != "lifecycle":
                continue
            consumed = payload.get("operation") in {"tick_claimed", "tick_skipped"}
            if consumed and payload.get("tick_id") == tick_id:
                return False

        # logging : True atteste la persistance, pas l'exécution de la mission
        admitted = record(trace, "tick_claimed", tick_id=tick_id)
    except OSError:
        return False
    finally:
        if not admitted:
            lock.release()

    return admitted
