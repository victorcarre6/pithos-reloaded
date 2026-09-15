"""Commit local sous verrou de composition ; le reçu durable reste l'autorité d'admission."""

from datetime import datetime, timezone
from functools import partial
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import subprocess
import time
from typing import Protocol, runtime_checkable

import journal
from kernel.contracts import Event
from kernel.errors import Cause, PithosError
from kernel.facts import FileFact, Receipt, RecordKey, RepoFact, SourceFact

from .git import PRELUDE, _environment, _git, checked_repo_path, repo_fact
from .identity import EffectIdentity, transport_key
from .intent import read_ledger, record_intent, record_result


@runtime_checkable
class Finalizer(Protocol):
    def reconcile(self, key: RecordKey, receipt: Receipt, timeout: float) -> RepoFact | None: ...
    def finalize(self, key: RecordKey, receipt: Receipt, timeout: float) -> RepoFact: ...


class GreenFinalizer:
    def __init__(self, repo: Path, *, ledger: Path, events_path: Path, trace=journal,
                 runner=subprocess.run, clock=time.monotonic):
        self.repo = repo.resolve()
        self.ledger = ledger.resolve()
        self.events_path = events_path.resolve()
        if any(path.is_relative_to(self.repo) for path in (self.ledger, self.events_path)):
            raise ValueError("publication evidence must be outside the target repository")
        self.trace, self.runner, self.clock = trace, runner, clock

    def _execute(self, command, *, deadline, **kwargs):
        # même borne pour toutes les commandes ; aucun hook, filtre implicite ou maintenance
        remaining = deadline - self.clock()
        if remaining <= 0:
            raise PithosError(Cause.timeout, "publication deadline exhausted")
        options = ["--literal-pathspecs", "-c", "core.hooksPath=/dev/null",
                   "-c", "commit.gpgsign=false", "-c", "gc.auto=0", "-c", "maintenance.auto=false"]
        command = [command[0], *options, *command[1:]]
        try:
            result = self.runner(command, timeout=remaining, **kwargs)
        except subprocess.TimeoutExpired as error:
            raise PithosError(Cause.timeout, "Git publication effect must be reconciled") from error
        if result.returncode != 0:
            raise PithosError(Cause.unverifiable, f"Git exited {result.returncode}: {result.stderr!r}")

        return result

    def _prepare(self, key, receipt, timeout):
        # les modèles sont revalidés et le reçu est retrouvé dans la trace de verifier
        if isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("publication timeout must be finite and positive")
        deadline = self.clock() + timeout
        runner = partial(self._execute, deadline=deadline)
        key = RecordKey.model_validate_json(key.model_dump_json())
        receipt = Receipt.model_validate_json(receipt.model_dump_json())
        if (receipt.node_id, receipt.attempt, receipt.returncode) != (*key.value[1:3], 0):
            raise ValueError("receipt identity differs from verification")
        found = False
        if self.trace.torn_tail(self.events_path) is not None:
            raise PithosError(Cause.unverifiable, "publication journal has a torn tail")
        # ponytail: scan de la trace de mission ; indexer si son coût mesuré devient significatif
        for event in self.trace.read(self.events_path):
            payload = event.payload
            matching = payload.get("key") == key.model_dump(mode="json")
            if event.type != "validation" or not event.durable or not matching:
                continue
            saved = Receipt.model_validate_json(json.dumps(payload["receipt"]))
            if payload.get("scope") != "node_verification" or payload.get("effect") != "confirmed" or saved != receipt:
                raise PithosError(Cause.unverifiable, "durable receipt does not authorize this publication")
            found = True
        if not found:
            raise PithosError(Cause.unverifiable, "durable verification receipt is missing")

        # la publication est limitée à la tranche mono-fichier attestée
        facts = {type(fact): fact for fact in receipt.facts}
        if len(receipt.facts) != 3 or set(facts) != {FileFact, SourceFact, RepoFact}:
            raise ValueError("publication requires exactly three attested facts")
        file, source, before = facts[FileFact], facts[SourceFact], facts[RepoFact]
        relative = checked_repo_path(source.path, self.repo)
        if source.path != self.repo / relative or source.path.is_symlink():
            raise ValueError("publication requires a canonical source path")
        hashes = (sha256(source.before).hexdigest(), sha256(source.after).hexdigest())
        if file.path != source.path or hashes != (file.sha_before, file.sha_after) or file.n_replacements != 1:
            raise ValueError("publication source does not match the receipt")
        if before.repo != self.repo or not before.complete or source.before == source.after:
            raise ValueError("publication requires an attested repository change")
        if re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", before.head) is None:
            raise ValueError("publication parent must be an exact object identifier")
        changes = before.changes
        if len(changes) != 1 or changes[0].path != Path(relative) or changes[0].origin is not None:
            raise ValueError("publication requires one designated path")
        if changes[0].status not in {" M", "M ", "MM"}:
            raise ValueError("publication only accepts modification of an existing file")
        for cached in ([], ["--cached"]):
            attributes = _git(self.repo, ["check-attr", *cached, "--all", "--", relative], runner=runner)
            if attributes:
                raise PithosError(Cause.unverifiable, "Git attributes could transform the attested source")
        branch = _git(self.repo, ["symbolic-ref", "--quiet", "HEAD"], runner=runner).strip()
        digest = sha256(b"commit\0" + key.model_dump_json().encode()).hexdigest()
        identity = EffectIdentity(result=digest, transport=transport_key())
        intent = {
            "key": key.model_dump(mode="json"),
            "receipt_sha256": sha256(receipt.model_dump_json().encode()).hexdigest(),
            "parent": before.head,
            "branch": branch,
            "path": relative,
        }
        intent["message"] = f"pithos: verified {digest}\n\nreceipt-sha256: {intent['receipt_sha256']}"

        return source, before, identity, intent, runner

    def _record(self, operation, identity, payload):
        # logging : la trace brute précède la projection du registre
        event = Event(ts=datetime.now(timezone.utc).isoformat(), v=1, type="status", durable=True, payload={
            "scope": "broker",
            "operation": operation,
            "result_id": identity.result,
            "transport_id": identity.transport,
            **payload,
        })
        if self.trace.emit(event) is not True:
            raise PithosError(Cause.receipt_not_written, "publication record was not written")

    def _blob(self, head, relative, runner):
        command = ["git", *PRELUDE, "cat-file", "blob", f"{head}:{relative}"]
        result = runner(command, cwd=str(self.repo), env=_environment(), capture_output=True)

        return result.stdout

    def _reconcile(self, source, before, identity, intent, runner):
        # l'index JSON est une projection ; le dépôt observé décide de l'effet réel
        entry = read_ledger(self.ledger, trace=self.trace).get(identity.result)
        if entry is not None and entry.get("intent") != intent:
            raise PithosError(Cause.unverifiable, "publication identity has conflicting evidence")
        relative = intent["path"]
        if source.path.read_bytes() != source.after or self._blob(before.head, relative, runner) != source.before:
            raise PithosError(Cause.unverifiable, "source bytes differ from the attested publication")
        current = repo_fact(self.repo, runner=runner)
        if current.head == before.head:
            if current != before or entry is not None and "result" in entry:
                raise PithosError(Cause.unverifiable, "repository changed before publication")

            return None

        # seul le commit immédiatement issu de cette intention est reconnaissable
        metadata = _git(self.repo, ["show", "-s", "--format=%P%n%B", current.head], runner=runner)
        parent, _, body = metadata.partition("\n")
        paths = _git(self.repo, ["diff-tree", "--no-commit-id", "--name-only", "-r", "-z",
                               before.head, current.head], runner=runner)
        clean = current.complete and not current.changes and not current.diff
        recognized = entry is not None and parent == before.head and body.rstrip("\n") == intent["message"]
        if not clean or not recognized or paths != relative + "\0":
            raise PithosError(Cause.unverifiable, "observed commit is not the intended publication")
        if self._blob(current.head, relative, runner) != source.after:
            raise PithosError(Cause.unverifiable, "committed bytes differ from the receipt")
        result = current.model_dump(mode="json")
        if "result" in entry and entry["result"] != result:
            raise PithosError(Cause.unverifiable, "recorded publication contradicts the repository")
        if "result" not in entry:
            self._record("commit_result", identity, {"key": intent["key"], "repo": result})
            record_result(self.ledger, identity, result, trace=self.trace)

        return current

    def reconcile(self, key: RecordKey, receipt: Receipt, timeout: float) -> RepoFact | None:
        return self._reconcile(*self._prepare(key, receipt, timeout))

    def finalize(self, key: RecordKey, receipt: Receipt, timeout: float) -> RepoFact:
        # interrogation obligatoire même si l'appelant a omis son propre préflight
        prepared = self._prepare(key, receipt, timeout)
        current = self._reconcile(*prepared)
        if current is not None:
            return current
        _, _, identity, intent, runner = prepared
        self._record("commit_intent", identity, intent)
        record_intent(self.ledger, identity, intent, trace=self.trace)
        _git(self.repo, ["commit", "--only", "--cleanup=verbatim", "--no-gpg-sign",
                         "-m", intent["message"], "--", intent["path"]], runner=runner)
        result = self._reconcile(*prepared)
        if result is None:
            raise PithosError(Cause.unverifiable, "Git returned without the intended commit")

        return result
