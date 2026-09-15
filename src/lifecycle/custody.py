"""Readiness observable, bornée même lorsque la probe ne rend pas la main.

Adapté de unsloth/studio/backend/cloudflare_tunnel.py:507-555 : disponibilité
observée et état de sortie confirmé. La probe locale ne doit pas créer d'enfants.
"""

import math
import multiprocessing
import os
import signal
import subprocess
import time
from collections.abc import Callable
from enum import StrEnum
from pathlib import Path
from typing import Literal

import journal
from kernel.contracts import Contract, Name, PositiveInt

from .lock import record
from .process import ProcessIdentity, fingerprint, process_start


# Notions portées de ouroboros/process_custody.py:233-280,496-575.
# MIT License
# Copyright (c) 2026 Anton Razzhigaev
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


class OwnedProcess(Contract):
    process: ProcessIdentity
    owner_pid: PositiveInt
    owner_start: Name
    process_scope: Literal["task", "session", "daemon"]


class IdentityMismatch(RuntimeError):
    """L'identité observée n'autorise aucun signal sur le groupe demandé."""


def _group_running(pid, deadline):
    result = subprocess.run(
        ["/bin/ps", "-axo", "pgid=,stat="],
        capture_output=True, text=True, check=True,
        timeout=max(0.001, deadline - time.monotonic()),
    )
    rows = [line.split() for line in result.stdout.splitlines()]
    members = [row for row in rows if row[0] == str(pid)]

    return any(not row[1].startswith("Z") for row in members)


def kill_group(pid: int, *, expected: ProcessIdentity) -> None:
    """Arrête un groupe attesté ; sans identité concordante, aucun signal n'est envoyé."""

    # appariement immédiat ; jamais de repli vers un simple kill du parent
    if pid != expected.pid:
        raise IdentityMismatch("pid differs from the admission identity")
    current = fingerprint(pid)
    if current != expected:
        # un zombie n'a plus d'empreinte ; constater la sortie n'autorise aucun signal
        if current is None and not _group_running(pid, time.monotonic() + 1):
            return
        raise IdentityMismatch("process identity is unknown or changed")
    if pid <= 1 or os.getpgid(pid) != pid or pid == os.getpgrp():
        raise IdentityMismatch("target must lead a separate process group")
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        return

    # confirmation de tout le groupe ; les zombies sont déjà sortis
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        if not _group_running(pid, deadline):
            return
        time.sleep(0.01)
    raise TimeoutError("process group exit not confirmed")


def active_processes(events_path: Path, trace=journal) -> dict[ProcessIdentity, OwnedProcess]:
    """Projette la custody ; une trace partielle ne prouve jamais l'absence d'orphelins."""

    # projection par démarrage ; les événements bruts ne sont jamais réécrits
    active = {}
    if trace.torn_tail(events_path) is not None:
        raise ValueError("custody journal has a torn tail")
    for event in trace.read(events_path):
        payload = event.payload
        if payload.get("scope") != "lifecycle":
            continue
        operation = payload.get("operation")
        if operation not in {"process_started", "process_stopped"}:
            continue
        if not event.durable:
            raise ValueError("custody transition is not durable")
        try:
            identity = ProcessIdentity.model_validate(payload["process"])
            if operation == "process_stopped":
                active.pop(identity, None)
                continue
            entry = OwnedProcess(
                process=identity,
                owner_pid=payload["owner_pid"],
                owner_start=payload["owner_start"],
                process_scope=payload["process_scope"],
            )
        except (KeyError, ValueError, TypeError) as error:
            raise ValueError("custody journal contains an invalid identity") from error
        active[identity] = entry

    return active


def sweep_orphans(*, events_path: Path, trace=journal) -> list[int]:
    """Moissonne les empreintes actives dont le propriétaire est prouvé disparu."""

    try:
        active = active_processes(events_path, trace)
    except ValueError:
        return []

    # génération différente seule insuffisante : le propriétaire doit être mort
    stopped = []
    for identity, entry in active.items():
        if entry.process_scope == "daemon":
            continue
        try:
            os.kill(entry.owner_pid, 0)
        except ProcessLookupError:
            dead = True
        except PermissionError:
            continue
        else:
            observed = process_start(entry.owner_pid)
            dead = observed is not None and observed != entry.owner_start
        if not dead:
            continue
        observed = fingerprint(identity.pid)
        if observed is not None and observed != identity:
            continue

        # logging : une panne empêche l'effet, un échec reste actif et reprenable
        data = identity.model_dump(mode="json")
        if not record(trace, "process_stopping", process=data):
            continue
        try:
            kill_group(identity.pid, expected=identity)
        except (IdentityMismatch, OSError, TimeoutError, subprocess.SubprocessError) as error:
            record(trace, "process_stop_failed", process=data, error=str(error))
            continue
        record(trace, "process_stopped", process=data)
        stopped.append(identity.pid)

    return stopped


class Readiness(StrEnum):
    ready = "ready"
    timeout = "timeout"
    failed = "failed"


def wait_ready(probe: Callable[[], bool], deadline: float) -> Readiness:
    """Attend une probe en processus jetable jusqu'à une deadline monotone absolue."""

    # aucune probe lancée après expiration ou avec une deadline non finie
    if not math.isfinite(deadline):
        raise ValueError("deadline must be finite")
    if time.monotonic() >= deadline:
        return Readiness.timeout
    context = multiprocessing.get_context("fork")
    reader, writer = context.Pipe(duplex=False)

    def observe():
        reader.close()
        try:
            while time.monotonic() < deadline:
                if probe() is True:
                    writer.send(Readiness.ready)

                    return
                time.sleep(0.01)
        except Exception:
            writer.send(Readiness.failed)
        finally:
            writer.close()

    # le parent reste capable d'arrêter une probe bloquée
    child = context.Process(target=observe)
    result = Readiness.timeout
    try:
        child.start()
        writer.close()
        remaining = max(0, deadline - time.monotonic())
        if reader.poll(remaining):
            try:
                observed = reader.recv()
                if time.monotonic() < deadline:
                    result = observed
            except EOFError:
                pass
    finally:
        reader.close()
        writer.close()
        if child.pid is not None:
            child.join(timeout=0)
            if child.is_alive():
                child.kill()
            child.join(timeout=0.5)
            if child.is_alive():
                raise TimeoutError("readiness probe exit not confirmed")
            child.close()

    return result
