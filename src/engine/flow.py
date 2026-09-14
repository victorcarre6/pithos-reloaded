"""Cycle Prefect local ; l'arbre, les preuves et la reprise appartiennent à walk."""

import signal
from threading import current_thread, main_thread
from typing import Protocol, runtime_checkable
from urllib.parse import urlsplit
from urllib.request import getproxies

from prefect import flow, settings
from prefect.context import AsyncClientContext, FlowRunContext, SyncClientContext, TaskRunContext

from .budget import Budget
from .tree import Tree
from .walk import WalkDeps, walk


# ponytail: marge fixe non calibrée ; la revoir après mesure des clôtures réelles
LAST_RESORT_GRACE_SECONDS = 60.0


@runtime_checkable
class MissionRunner(Protocol):
    def mission(self, tree: Tree, budget: Budget, deps: WalkDeps) -> Tree: ...


def mission(tree: Tree, budget: Budget, deps: WalkDeps) -> Tree:
    """Exécute une mission sous verrou fourni, sur un serveur Prefect local déjà lancé."""

    # réserver l'alarme native au dernier recours, sans hériter d'un autre run
    if current_thread() is not main_thread():
        raise ValueError("mission requires the main thread")
    if signal.getsignal(signal.SIGALRM) != signal.SIG_DFL:
        raise ValueError("mission requires an available SIGALRM")
    contexts = (FlowRunContext, TaskRunContext, SyncClientContext, AsyncClientContext)
    if any(context.get() is not None for context in contexts):
        raise ValueError("mission cannot inherit a Prefect context")

    # aucune résolution distante ni démarrage implicite de serveur
    api = urlsplit(settings.PREFECT_API_URL.value() or "")
    if api.scheme != "http" or api.hostname not in {"127.0.0.1", "::1"}:
        raise ValueError("mission requires an explicit HTTP loopback Prefect API")
    proxies = getproxies()
    if any(proxies.get(name) for name in ("http", "https", "all")):
        raise ValueError("mission requires a proxy-free local runtime")

    # les paramètres métier restent dans la fermeture, jamais dans la base Prefect
    updates = {
        settings.PREFECT_SERVER_EPHEMERAL_ENABLED: False,
        settings.PREFECT_CLOUD_ENABLE_ORCHESTRATION_TELEMETRY: False,
        settings.PREFECT_LOGGING_TO_API_ENABLED: False,
        settings.PREFECT_CLIENT_METRICS_ENABLED: False,
    }
    with settings.temporary_settings(updates):
        with SyncClientContext(httpx_settings={"trust_env": False, "follow_redirects": False}):
            @flow(
                name="mission",
                retries=0,
                persist_result=False,
                log_prints=False,
                timeout_seconds=budget.remaining + LAST_RESORT_GRACE_SECONDS,
            )
            def run():
                return walk(tree, budget, deps)

            return run()
