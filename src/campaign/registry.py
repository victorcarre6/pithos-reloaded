"""Le registre d'outils : la famille `skill` du magasin, vue sous l'angle de l'appelabilité.

Un verdict est lié à l'empreinte du contenu qu'il gouverne : il périme dès que les octets bougent.
Le compteur et la gate lisent **la même** primitive d'empreinte — c'est sa seule raison d'être.

PORTED_FROM: villani-code-main/villani_code/autonomous.py:53-60,1014-1042 (MIT)
PORTED_FROM: ouroboros-main/ouroboros/tools/registry.py:1566-1571,1605-1616,1862-2005 (Apache-2.0)
"""

from enum import StrEnum
from hashlib import sha256
from typing import Mapping

from pydantic import Field

from kernel.contracts import Contract, Name
from kernel.facts import Digest


class TaskLifecycle(StrEnum):
    """Les sept états d'une tâche du registre ; « échoué » ne dit pas s'il faut réessayer."""

    pending = "pending"
    running = "running"
    passed = "passed"
    failed = "failed"        # vérifié rouge : ne pas réessayer tel quel
    blocked = "blocked"      # rien à tenter tant que la cause tient
    retryable = "retryable"  # transitoire : une tentative reste due
    exhausted = "exhausted"  # les tentatives dues ont été prises


FAILURES = (TaskLifecycle.failed, TaskLifecycle.blocked, TaskLifecycle.exhausted)


class Surface(StrEnum):
    tools = "tools"
    mcp = "mcp"


class OmissionReason(StrEnum):
    module_load_failed = "module_load_failed"    # un module qui échoue omet TOUS ses outils
    not_passed = "not_passed"                    # la tâche n'a pas atteint son verdict vert
    stale_fingerprint = "stale_fingerprint"      # les octets attestés ont bougé depuis


class Omission(Contract):
    """Ce qui manque à la surface projetée, avec la raison typée de son absence."""

    surface: Surface
    reason: OmissionReason
    subject: Name
    detail: str


class ToolEntry(Contract):
    """Un outil du registre : où l'appeler, et sur quels octets son verdict a été rendu."""

    key: Name
    module: Name
    call: Name
    digests: dict[Name, Digest] = Field(min_length=1)
    lifecycle: TaskLifecycle


def fingerprint(digests: Mapping[str, Digest]) -> Digest:
    "Empreinte stable d'un ensemble de fichiers attestés — la primitive que gate et compteur partagent."

    canonical = "".join(f"{name}:{digests[name]}\n" for name in sorted(digests))

    return sha256(canonical.encode("utf-8")).hexdigest()


def diverged(entry: ToolEntry, current: Mapping[str, Digest]) -> list[str]:
    "Nomme les fichiers attestés dont l'octet courant n'est plus celui du verdict, disparition comprise."

    return [name for name, digest in entry.digests.items() if current.get(name) != digest]


def is_satisfied(entry: ToolEntry, current: Mapping[str, Digest]) -> bool:
    "La satisfaction tombe dès que l'empreinte des fichiers de l'entrée n'est plus celle du verdict."

    attested = {name: current[name] for name in entry.digests if name in current}

    return fingerprint(attested) == fingerprint(entry.digests)


class Projection(Contract):
    """La surface d'outils réellement appelable, et la raison typée de chaque absence."""

    available: list[ToolEntry]
    omissions: list[Omission]


def project(entries: list[ToolEntry], current: Mapping[str, Digest],
            failed_modules: Mapping[str, str]) -> Projection:
    """Projette la surface appelable ; un module qui échoue à l'import omet **tous** ses outils.

    L'ordre des gardes est celui des causes : l'import d'abord, le verdict ensuite, l'empreinte enfin.
    """

    available = []
    omissions = []
    for entry in entries:
        load_error = failed_modules.get(entry.module)
        if load_error is not None:
            omissions.append(Omission(surface=Surface.tools, reason=OmissionReason.module_load_failed,
                                      subject=entry.key, detail=load_error))
        elif entry.lifecycle is not TaskLifecycle.passed:
            omissions.append(Omission(surface=Surface.tools, reason=OmissionReason.not_passed,
                                      subject=entry.key, detail=entry.lifecycle.value))
        elif not is_satisfied(entry, current):
            log_content = ", ".join(diverged(entry, current))
            omissions.append(Omission(surface=Surface.tools, reason=OmissionReason.stale_fingerprint,
                                      subject=entry.key, detail=log_content))
        else:
            available.append(entry)

    return Projection(available=available, omissions=omissions)
