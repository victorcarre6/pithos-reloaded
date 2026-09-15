"""Worker spawn sous verrou, admis après custody durable et récolté sous deadline."""

from collections.abc import Callable
from functools import partial
import math
import multiprocessing
import os
from pathlib import Path
import signal
import subprocess
import time
from typing import Protocol, runtime_checkable

import journal

from .custody import active_processes, kill_group, sweep_orphans
from .lock import LockPort, LockState, record
from .process import fingerprint, process_start


@runtime_checkable
class MissionProcessPort(Protocol):
    def run(self, task: Callable[[], None], deadline: float) -> None: ...


_connection = None


def run_command(command: list[str], *, directory: Path,
                environment: dict[str, str], timeout: float) -> int:
    """Demande au superviseur une commande du harness sous custody et deadline communes."""

    if _connection is None:
        raise OSError("command custody requires a mission worker")
    if isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("command timeout must be finite and positive")
    request = (command, directory, environment, time.monotonic() + timeout)
    _connection.send(("command", request))
    outcome, result = _connection.recv()
    if outcome == "timeout":
        raise subprocess.TimeoutExpired(command, timeout)
    if outcome != "result" or type(result) is not int:
        raise OSError(f"command custody failed: {result}")

    return result


def _command(command, directory, environment):
    # le programme rejoint le groupe du gardien déjà enregistré, sans créer une autre session
    with (directory / "stdout.txt").open("ab") as stdout, (directory / "stderr.txt").open("ab") as stderr:
        process = subprocess.Popen(command, cwd=directory, env=environment, stdin=subprocess.DEVNULL,
                                   stdout=stdout, stderr=stderr)
        returncode = process.wait()
        for stream in (stdout, stderr):
            stream.flush()
            os.fsync(stream.fileno())

    return returncode


def _worker(connection, task):
    global _connection

    # le leader reste vivant pour permettre une récolte du groupe après le résultat
    os.setsid()
    try:
        connection.send("ready")
        if connection.recv() != "admit":
            return
        _connection = connection
        try:
            result = ("result", task())
        except BaseException as error:
            result = ("error", f"{type(error).__name__}: {error}")
        connection.send(result)
        connection.recv()
    except EOFError:
        pass
    finally:
        # le parent disparu ferme le pipe ; aucun descendant n'est abandonné
        os.killpg(os.getpid(), signal.SIGKILL)


class MissionProcess:
    def __init__(self, lock: LockPort, *, events_path: Path, trace=journal):
        self.lock, self.events_path, self.trace = lock, events_path, trace

    def run(self, task: Callable[[], None], deadline: float) -> None:
        """Exécute une fonction de composition importable dans un processus principal neuf."""

        # le temps d'initialisation fait partie de la même borne que le worker
        if isinstance(deadline, bool) or not math.isfinite(deadline):
            raise ValueError("worker deadline must be finite")
        if deadline <= time.monotonic():
            raise TimeoutError("worker deadline exhausted")
        if self.lock.acquire() not in {LockState.held, LockState.stale_reclaimed}:
            raise RuntimeError("mission lock unavailable")
        try:
            # la custody est commune aux missions qui partagent ce verrou
            sweep_orphans(events_path=self.events_path, trace=self.trace)
            active = active_processes(self.events_path, self.trace)
            if any(entry.process_scope != "daemon" for entry in active.values()):
                raise RuntimeError("unresolved mission custody")
            self._execute(task, deadline, "session")
        finally:
            active = active_processes(self.events_path, self.trace)
            if not any(entry.process_scope != "daemon" for entry in active.values()):
                self.lock.release()

    def _execute(self, task, deadline, scope):
        # même admission et même récolte pour le worker et chaque gardien de commande
        child, identity, reader, writer = None, None, None, None
        recorded = False
        outcome, result = "not_admitted", None
        try:
            if not math.isfinite(deadline) or time.monotonic() >= deadline:
                raise TimeoutError("worker deadline exhausted")
            owner = process_start(os.getpid())
            if owner is None:
                raise RuntimeError("mission owner identity unavailable")
            context = multiprocessing.get_context("spawn")
            reader, writer = context.Pipe()
            child = context.Process(target=_worker, args=(writer, task))
            child.start()
            writer.close()
            if not reader.poll(max(0, deadline - time.monotonic())) or reader.recv() != "ready":
                raise TimeoutError("worker startup deadline exhausted")
            identity = fingerprint(child.pid)
            if identity is None or os.getpgid(child.pid) != child.pid:
                raise RuntimeError("worker custody identity unavailable")
            recorded = record(self.trace, "process_started", process=identity.model_dump(mode="json"),
                              owner_pid=os.getpid(), owner_start=owner, process_scope=scope)
            if not recorded:
                raise RuntimeError("worker custody was not written")
            if time.monotonic() >= deadline:
                raise TimeoutError("worker admission deadline exhausted")
            reader.send("admit")
            outcome = "unknown"

            # interruption douce pour restaurer ; la borne OS reste le dernier recours
            try:
                while True:
                    if not reader.poll(max(0, deadline - time.monotonic())):
                        raise TimeoutError("worker hard deadline exhausted; mission must be reconciled")
                    kind, payload = reader.recv()
                    if kind != "command":
                        result = payload
                        break
                    command, directory, environment, requested = payload
                    command_task = partial(_command, command, directory, environment)
                    try:
                        value = self._execute(command_task, min(deadline, requested), "task")
                        reply = ("result", value)
                    except TimeoutError:
                        reply = ("timeout", None)
                    except RuntimeError as error:
                        reply = ("error", str(error))
                    # une sortie inconnue interdit toute nouvelle commande, même après erreur de gate
                    active = active_processes(self.events_path, self.trace)
                    if any(entry.process_scope == "task" for entry in active.values()):
                        raise RuntimeError("command group exit not confirmed")
                    if time.monotonic() >= deadline:
                        raise TimeoutError("worker hard deadline exhausted; mission must be reconciled")
                    reader.send(reply)
            except KeyboardInterrupt:
                if fingerprint(child.pid) == identity:
                    os.kill(child.pid, signal.SIGINT)
                reader.poll(max(0, min(60, deadline - time.monotonic())))
                raise
            outcome = "completed" if kind == "result" else "failed"
            if kind != "result":
                raise RuntimeError(result)
        finally:
            # aucune libération du verrou avant confirmation de sortie du groupe
            try:
                if child is not None and child.pid is not None:
                    child.join(timeout=0)
                    if identity is None:
                        # avant admission, seul le worker existe et n'a produit aucun effet métier
                        child.kill()
                    else:
                        kill_group(child.pid, expected=identity)
                    child.join(timeout=2)
                    if child.is_alive():
                        raise TimeoutError("worker exit not confirmed")
                    if recorded:
                        if not record(self.trace, "process_stopped", process=identity.model_dump(mode="json"),
                                      outcome=outcome, detail=result):
                            raise RuntimeError("worker exit record unavailable")
                    child.close()
            finally:
                if reader is not None:
                    reader.close()
                if writer is not None:
                    writer.close()

        return result
