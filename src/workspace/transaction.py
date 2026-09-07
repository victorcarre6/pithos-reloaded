"""Snapshot d'octets et remplacement atomique d'un fichier existant.

PORTED_FROM: kilocode-main/packages/core/src/file-mutation.ts:144-158
CAS traduit ; verrou unique adapté au socle séquentiel. Staging inspiré de
Prime rlm/repl.py:661-680 ; aucune copie du runtime ni dépôt Git fantôme.
Copyright (c) 2026 Kilo Code, Copyright (c) 2025 opencode — MIT.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock

import journal
from kernel import codeview
from kernel.contracts import Event
from kernel.errors import Cause, PithosError

from .paths import checked_path
from .splice import prepare_splice


_WRITE_LOCK = RLock()


class StaleContentError(PithosError):
    def __init__(self, path: Path):
        super().__init__(Cause.unverifiable, f"stale content: {path}", "target")


def _read(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise PithosError(Cause.invalid_path, "expected regular file", "target")
        content = stream.read(codeview.MAX_SOURCE_BYTES + 1)
    if len(content) > codeview.MAX_SOURCE_BYTES:
        raise PithosError(Cause.invalid_schema, "oversized source", "target")

    return content


class Transaction:
    """Capture à l'entrée ; restaurer explicitement sur verdict rouge, ou sur exception."""

    def __init__(self, target: Path, *, root: Path, view=codeview, trace=journal):
        self.root = root.resolve()
        self.target = target
        self.view = view
        self.trace = trace
        self.before = None
        self.active = False
        self._changed = False
        self.last_plan = None

    def __enter__(self):
        if self.before is not None:
            raise RuntimeError("transaction is single-use")
        self.path = checked_path(self.target, self.root, self.view)
        self.before = _read(self.path)
        self.mode = stat.S_IMODE(self.path.stat().st_mode)
        self.active = True

        return self

    def __exit__(self, exc_type, exc, traceback):
        try:
            if exc is not None and self._changed:
                self.restore()
        except BaseException as restore_error:
            raise BaseExceptionGroup("transaction and restoration failed", [exc, restore_error]) from None
        finally:
            self.active = False

        return False

    def splice(self, function_name: str, new_source: str):
        self._require_active()
        if self.path.suffix != ".py":
            raise PithosError(Cause.invalid_path, "expected Python target", "target")
        self._record("splice", {"function_name": function_name, "new_source": new_source})
        self.last_plan = prepare_splice(self.before, function_name, new_source, target=self.path)
        self.cas_write(self.last_plan.content)

        return self.last_plan.fact

    def cas_write(self, content: bytes) -> None:
        self._require_active()
        if len(content) > codeview.MAX_SOURCE_BYTES:
            raise PithosError(Cause.invalid_schema, "oversized source", "content")
        self._record("write", {"before_hex": self.before.hex(), "after_hex": content.hex()})
        self._replace(content, self.before)

    def restore(self) -> None:
        self._require_active()
        self._replace(self.before, self._current())
        self._changed = False

    def _require_active(self):
        if not self.active:
            raise RuntimeError("transaction is not active")

    def _record(self, operation, payload):
        event = Event(
            ts=datetime.now(timezone.utc).isoformat(),
            v=1,
            type="tool_activity",
            durable=True,
            payload={"operation": operation, "path": str(self.path), **payload},
        )

        # logging
        if self.trace.emit(event) is not True:
            raise PithosError(Cause.unverifiable, "attempt_not_written", "journal")

    def _current(self):
        if checked_path(self.path, self.root, self.view) != self.path:
            raise StaleContentError(self.path)

        return _read(self.path)

    def _replace(self, content, expected):
        # les écritures coopérantes ne s'intercalent pas entre comparaison et rename
        with _WRITE_LOCK:
            if self._current() != expected:
                raise StaleContentError(self.path)
            descriptor, name = tempfile.mkstemp(dir=self.path.parent, prefix=self.path.name + ".", suffix=".tmp")
            temporary = Path(name)
            try:
                with os.fdopen(descriptor, "wb") as stream:
                    os.fchmod(stream.fileno(), self.mode)
                    stream.write(content)
                    stream.flush()
                    os.fsync(stream.fileno())

                # une écriture extérieure pendant le staging doit aussi être refusée
                if self._current() != expected:
                    raise StaleContentError(self.path)
                os.replace(temporary, self.path)
                self._changed = True
            finally:
                temporary.unlink(missing_ok=True)
