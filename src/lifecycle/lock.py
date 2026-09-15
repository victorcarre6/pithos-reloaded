"""Verrou local ; chaque génération retirée reste une archive non remplaçable.

Adapté de prime-agent/packages/coding-agent/src/core/session-lease.ts:160-324
et langfuse/worker/src/utils/RedisLock.ts:55-148. Aucun heartbeat ni breaker.
"""

import json
import math
import os
import time
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Protocol, runtime_checkable
from uuid import uuid4

import journal
from kernel.contracts import Event

from .process import process_start


class LockState(StrEnum):
    held = "held"
    unavailable = "unavailable"
    stale_reclaimed = "stale_reclaimed"


@runtime_checkable
class LockPort(Protocol):
    def acquire(self) -> LockState: ...
    def release(self) -> None: ...


def record(trace, operation: str, **payload) -> bool:
    """Persiste un événement de cycle de vie avant de rendre l'effet admissible."""

    event = Event(
        ts=datetime.now(timezone.utc).isoformat(),
        v=1,
        type="status",
        durable=True,
        payload={"scope": "lifecycle", "operation": operation, **payload},
    )

    return trace.emit(event)


class RunLock:
    """Accorde held/stale_reclaimed ; unavailable interdit toute délivrance."""

    def __init__(self, path: Path, *, max_seconds: float, trace=journal,
                 clock=time.monotonic, identity=process_start):
        if not math.isfinite(max_seconds) or max_seconds <= 0:
            raise ValueError("max_seconds must be finite and positive")
        self.path = path
        self.max_seconds = max_seconds
        self.trace = trace
        self.clock = clock
        self.identity = identity
        self.token = None

    def _owner(self):
        """Refuse tout état partiel ou non conforme avant de choisir un chemin."""

        owner = json.loads((self.path / "owner.json").read_bytes())
        token = owner["token"]
        if not isinstance(token, str) or len(token) != 32:
            raise ValueError("invalid token")
        if any(character not in "0123456789abcdef" for character in token):
            raise ValueError("invalid token")
        if type(owner["pid"]) is not int or owner["pid"] <= 0:
            raise ValueError("invalid pid")
        if not isinstance(owner["start_time"], str) or not owner["start_time"]:
            raise ValueError("missing start identity")
        if not math.isfinite(owner["created"]):
            raise ValueError("invalid creation time")

        return owner

    def acquire(self) -> LockState:
        """Tente une acquisition ; toute observation inconnue ferme l'admission."""

        # pas d'identité héritée : un fork doit mesurer son propre processus
        pid = os.getpid()
        start = self.identity(pid)
        if not start or self.token is not None:
            return LockState.unavailable
        state = LockState.held
        try:
            # mkdir arbitre l'admission ; un writer interrompu reste indisponible
            try:
                self.path.mkdir(mode=0o700)
            except FileExistsError:
                owner = self._owner()
                try:
                    os.kill(owner["pid"], 0)
                except ProcessLookupError:
                    stale = True
                else:
                    observed = self.identity(owner["pid"])
                    if not observed:
                        return LockState.unavailable
                    stale = observed != owner["start_time"]
                if not stale:
                    return LockState.unavailable

                # l'intention doit être durable même si le processus meurt après rename
                if not record(self.trace, "lock_reclaiming", previous=owner):
                    return LockState.unavailable

                # même destination pour release et reprise ; jamais supprimée
                retired = self.path.with_name(f"{self.path.name}.retired-{owner['token']}")
                self.path.rename(retired)
                if not record(self.trace, "lock_reclaimed", previous=owner, archive=str(retired)):
                    return LockState.unavailable
                self.path.mkdir(mode=0o700)
                state = LockState.stale_reclaimed

            # publication durable du propriétaire avant d'accorder le verrou
            token = uuid4().hex
            owner = {
                "token": token,
                "pid": pid,
                "start_time": start,
                "created": self.clock(),
            }
            content = json.dumps(owner)
            with (self.path / "owner.json").open("x", encoding="utf-8") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            self.token = token
        except (OSError, ValueError, KeyError, TypeError):
            return LockState.unavailable

        return state

    def release(self) -> None:
        """Retire uniquement sa génération, de façon idempotente."""

        if self.token is None:
            return
        try:
            owner = self._owner()
            if owner["token"] != self.token or owner["pid"] != os.getpid():
                return
            retired = self.path.with_name(f"{self.path.name}.retired-{self.token}")
            self.path.rename(retired)
            self.token = None
        except (OSError, ValueError, KeyError, TypeError):
            return
