"""Identité macOS, issue du SDK local sys/proc_info.h:59-87 et libproc.h:96."""

import ctypes
import hashlib
import os
import struct
import subprocess

from kernel.contracts import Contract, Name, PositiveInt
from kernel.facts import Digest


class ProcessIdentity(Contract):
    pid: PositiveInt
    start_time: Name
    cmd_sha256: Digest


def process_start(pid: int) -> str | None:
    """Lit les secondes et microsecondes de démarrage ; aucun repli moins précis."""

    # proc_bsdinfo : 12 uint32, 48 octets de noms, 6 uint32, puis 2 uint64
    library = ctypes.CDLL("/usr/lib/libproc.dylib")
    query = library.proc_pidinfo
    query.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
    query.restype = ctypes.c_int
    buffer = ctypes.create_string_buffer(136)
    size = query(pid, 3, 0, buffer, len(buffer))  # PROC_PIDTBSDINFO
    if size != len(buffer):
        return None
    seconds, microseconds = struct.unpack_from("=QQ", buffer.raw, 120)

    return f"{seconds}:{microseconds:06d}"


def fingerprint(pid: int) -> ProcessIdentity | None:
    """Atteste un démarrage stable autour de la lecture de la commande complète."""

    start = process_start(pid)
    if start is None:
        return None
    try:
        result = subprocess.run(
            ["/bin/ps", "-ww", "-p", str(pid), "-o", "command="],
            capture_output=True, env={**os.environ, "LC_ALL": "C"}, timeout=1,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    command = result.stdout.strip()
    if result.returncode or not command or process_start(pid) != start:
        return None
    digest = hashlib.sha256(command).hexdigest()

    return ProcessIdentity(pid=pid, start_time=start, cmd_sha256=digest)
