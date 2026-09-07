"""Subprocess sur copie possédée ; inspiration Villani benchmark/verifier.py:39-137.

Copie libre accordée dans resources/MANIFEST.md ; pas de shell ni lecture du workspace.
"""

import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

from kernel.contracts import Criterion
from kernel.errors import PithosError

from .models import ExecutionResult
from .relations import SEED, admit, render


def compact_failure_output(output: str, max_lines: int = 24, max_chars: int = 1800) -> str:
    """Borne tête et queue ; adapté de Villani planning.py:403-411, sans perdre la queue."""

    # réduction indépendante en lignes puis caractères
    if max_lines < 3 or max_chars < 7:
        raise ValueError("diagnostic budget too small")
    lines = [line.rstrip() for line in output.splitlines() if line.strip()]
    if len(lines) > max_lines:
        head = max_lines // 2
        tail = max_lines - head - 1
        lines = lines[:head] + ["..."] + lines[-tail:]
    text = "\n".join(lines)
    if len(text) > max_chars:
        head = (max_chars - 5) // 2
        tail = max_chars - 5 - head
        text = text[:head] + "\n...\n" + text[-tail:]

    return text


def _write_new(path, text):
    with path.open("x", encoding="utf-8", newline="") as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())


def _preview(path):
    with path.open("rb") as stream:
        size = os.fstat(stream.fileno()).st_size
        head = stream.read(4096)
        if size > 4096:
            stream.seek(max(4096, size - 4096))
            head += b"\n...\n" + stream.read(4096)
    text = head.decode("utf-8", errors="replace")

    return compact_failure_output(text), size


def execute(criterion: Criterion, source: str, *, artifact_root: Path, timeout: float) -> ExecutionResult:
    """Exécute une source fournie en mémoire et conserve tous ses artefacts, échec compris."""

    # admission avant création de fichier ou de processus
    if isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be positive and finite")
    started = time.monotonic()
    try:
        admit(criterion, source)
        render(criterion, Path("candidate.py"))
    except (PithosError, SyntaxError, ValueError) as error:
        return ExecutionResult(
            execution="invalid",
            check="not_run",
            returncode=None,
            artifact_path=None,
            diagnostic=compact_failure_output(str(error)),
            duration=time.monotonic() - started,
        )

    # création exclusive : aucun artefact précédent n'est réécrit
    artifact = None
    returncode = None
    execution = "tool_error"
    check = "not_run"
    diagnostic = ""
    counterexample = ""
    sizes = {"stdout": 0, "stderr": 0}
    try:
        directory = Path(tempfile.mkdtemp(prefix="invariant-", dir=artifact_root.absolute()))
        candidate = directory / "candidate.py"
        _write_new(candidate, source)
        artifact = directory / "invariant.py"
        script = render(criterion, candidate)
        _write_new(artifact, script)

        # sorties vers fichiers : aucun pipe détenu par un descendant ne bloque wait
        command = [sys.executable, "-I", "-B", str(artifact)]
        environment = {"HYPOTHESIS_STORAGE_DIRECTORY": str(directory / "hypothesis")}
        with (directory / "stdout.txt").open("xb") as stdout, (directory / "stderr.txt").open("xb") as stderr:
            remaining = timeout - (time.monotonic() - started)
            if remaining <= 0:
                raise subprocess.TimeoutExpired(command, timeout)
            process = subprocess.Popen(
                command,
                cwd=directory,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                start_new_session=True,
            )
            try:
                returncode = process.wait(timeout=remaining)
            finally:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
                for stream in (stdout, stderr):
                    stream.flush()
                    os.fsync(stream.fileno())

        # seule une terminaison attestée du squelette fixe peut être verte ou rouge
        with (directory / "result.json").open("rb") as stream:
            report = json.loads(stream.read(1024))
        if report == {"check": "passed"} and returncode == 0:
            execution = "completed"
            check = "passed"
        elif report == {"check": "failed"} and returncode == 20:
            counterexample, _ = _preview(directory / "counterexample.txt")
            execution = "completed"
            check = "failed"
    except subprocess.TimeoutExpired:
        execution = "timed_out"
        diagnostic = "invariant timeout"
    except (OSError, ValueError, AttributeError) as error:
        diagnostic = str(error)

    # lecture bornée des seuls fichiers créés ici ; les octets complets restent sur disque
    if artifact is not None:
        for name in sizes:
            try:
                preview, sizes[name] = _preview(artifact.parent / f"{name}.txt")
                diagnostic += "\n" + preview
            except OSError as error:
                execution, check = "tool_error", "not_run"
                diagnostic += f"\n{error}"
    result = ExecutionResult(
        execution=execution,
        check=check,
        returncode=returncode,
        artifact_path=artifact,
        diagnostic=compact_failure_output(diagnostic),
        duration=time.monotonic() - started,
        counterexample=counterexample,
        seed=SEED,
        stdout_bytes=sizes["stdout"],
        stderr_bytes=sizes["stderr"],
    )

    # métadonnées durables avant de rendre un résultat exploitable
    if artifact is not None:
        try:
            metadata = result.model_dump(mode="json")
            metadata["criterion"] = criterion.model_dump(mode="json")
            metadata["source_sha256"] = hashlib.sha256(source.encode("utf-8")).hexdigest()
            metadata["python"] = sys.version
            text = json.dumps(metadata, ensure_ascii=False)
            _write_new(artifact.parent / "meta.json", text)
        except OSError as error:
            values = result.model_dump()
            diagnostic = f"{result.diagnostic}\nmetadata_error: {error}"
            values.update(execution="tool_error", check="not_run", diagnostic=compact_failure_output(diagnostic))
            result = ExecutionResult(**values)

    return result
