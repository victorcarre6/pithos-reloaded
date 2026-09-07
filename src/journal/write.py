"""Écriture durable : une ligne JSONL, sa projection `live.log`, un read-modify-write verrouillé."""

import fcntl
import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from kernel.contracts import Event, EventType

from .read import TornTail, generation_signature, next_event_id, torn_tail

LOCK_NAME = ".journal.lock"
LOCK_TIMEOUT_SEC = 4.0
LOCK_POLL_SEC = 0.01
PRIVATE_FILE_MODE = 0o600

_events_path: Path | None = None
_live_path: Path | None = None
_lock_path: Path | None = None
_next_id = 1


def _segment_path(base: Path, index: int) -> Path:
    "Chemin du segment n° `index` d'un journal ; l'index 0 est le fichier d'origine."

    if index == 0:
        return base

    return base.with_name(f"{base.stem}.{index}{base.suffix}")


def _segment_link(previous: Path, torn: TornTail) -> Event:
    "Ouverture d'un segment lié : d'où il vient, et le fragment resté lisible derrière lui."

    payload = {
        "segment_from": previous.name,
        "torn_offset": torn.offset,
        "torn_bytes": torn.n_bytes,
        "generation": generation_signature(previous),
    }

    return Event(
        ts=datetime.now(timezone.utc).isoformat(),
        v=1,
        type=EventType.status,
        durable=True,
        payload=payload,
    )


def bind(events_path: Path, live_path: Path) -> None:
    """Fixe les deux sorties de la mission et reprend la numérotation des événements.

    Une queue déchirée n'est pas réparée : la reprise ouvre le segment suivant, dont le premier
    événement porte le lien vers le fragment laissé lisible.
    """

    global _events_path, _live_path, _lock_path, _next_id

    # dernier segment ouvert pour ce journal — celui auquel une reprise s'ajoute
    index = 0
    while _segment_path(events_path, index + 1).exists():
        index += 1
    active = _segment_path(events_path, index)

    _live_path = live_path
    _lock_path = live_path.with_name(LOCK_NAME)
    _events_path = active
    _next_id = next_event_id(active)

    torn = torn_tail(active)
    if torn is not None:
        _events_path = _segment_path(events_path, index + 1)
        emit(_segment_link(active, torn))


def _acquire(timeout_sec: float) -> int | None:
    "Prend le verrou global unique du journal, ou rend None — indisponible, ou délai expiré."

    if _lock_path is None:
        return None

    try:
        lock_fd = os.open(str(_lock_path), os.O_WRONLY | os.O_CREAT, PRIVATE_FILE_MODE)
    except OSError:
        return None

    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

            return lock_fd
        except OSError:
            time.sleep(LOCK_POLL_SEC)
    os.close(lock_fd)

    return None


def _release(lock_fd: int) -> None:
    "Rend le verrou global et referme son descripteur."

    fcntl.flock(lock_fd, fcntl.LOCK_UN)
    os.close(lock_fd)


def _open_append(path: Path) -> int:
    "Ouvre un fichier en append, son répertoire créé au besoin, en mode privé."

    path.parent.mkdir(parents=True, exist_ok=True)

    return os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, PRIVATE_FILE_MODE)


def _write_once(fd: int, data: bytes) -> bool:
    "Écrit en une seule syscall ; une écriture partielle est un échec, jamais un succès."

    return os.write(fd, data) == len(data)


def _projection(row: dict) -> bytes:
    "Ligne unique suivable en `tail -F`, qui déclare le payload qu'elle omet (décision 29)."

    liveness = "durable" if row["durable"] else "ephemeral"
    log_content = (
        f"{row['ts']} #{row['event_id']} {row['type']} [{liveness}] "
        f"(payload omitted: {len(row['payload'])} keys)\n"
    )

    return log_content.encode("utf-8")


def emit(event: Event) -> bool:
    """Écrit la ligne JSONL complète puis sa projection d'une ligne dans `live.log`.

    Ne lève jamais : une panne rend `False`, et c'est l'absence du reçu constatée après coup qui
    retire l'attestation.
    """

    global _next_id

    if _events_path is None:
        return False

    # sérialisation et ouvertures d'abord : après ce bloc, seule une panne disque reste possible
    try:
        row = event.model_dump(mode="json")
        row["event_id"] = _next_id
        jsonl_line = (json.dumps(row, ensure_ascii=False) + "\n").encode("utf-8")
        live_line = _projection(row)
        live_fd = _open_append(_live_path)
        events_fd = _open_append(_events_path)
    except (OSError, TypeError, ValueError):
        return False

    # la ligne JSONL est la preuve ; l'échec de la projection ne retire pas une preuve écrite
    written = False
    lock_fd = _acquire(LOCK_TIMEOUT_SEC)
    try:
        if lock_fd is not None and _write_once(events_fd, jsonl_line):
            os.fsync(events_fd)
            written = True
            _write_once(live_fd, live_line)
    except OSError:
        pass
    finally:
        if lock_fd is not None:
            _release(lock_fd)
        os.close(events_fd)
        os.close(live_fd)

    if written:
        _next_id += 1

    return written


def _read_json(path: Path) -> dict:
    "Lit le dict JSON courant ; un fichier absent est un dict vide, un fichier corrompu lève."

    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}

    return json.loads(content)


def _write_json_atomic(path: Path, payload: dict) -> None:
    "Publie par temporaire sibling puis `os.replace` : un SIGKILL laisse l'original intact."

    path.parent.mkdir(parents=True, exist_ok=True)
    content = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    tmp = path.with_name(f".{path.name}.tmp.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex[:8]}")

    # bits de permission préservés : os.replace crée un nouvel inode
    mode = PRIVATE_FILE_MODE
    if path.exists():
        mode = path.stat().st_mode & 0o7777

    try:
        fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        try:
            if not _write_once(fd, content):
                raise OSError(f"journal: écriture partielle de {tmp}")
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(tmp, path)
    except OSError:
        tmp.unlink(missing_ok=True)
        raise


def update_json_locked(path: Path, fn: Callable[[dict], dict]) -> None:
    """Read-modify-write sous un seul verrou tenu, relecture du disque DANS le verrou.

    Lève `TimeoutError` sur échec de verrou : continuer sans verrou réintroduirait silencieusement
    la perte de mise à jour que cette fonction supprime.
    """

    lock_fd = _acquire(LOCK_TIMEOUT_SEC)
    if lock_fd is None:
        raise TimeoutError(f"journal: verrou global indisponible pour {path}")

    try:
        current = _read_json(path)
        _write_json_atomic(path, fn(current))
    finally:
        _release(lock_fd)
