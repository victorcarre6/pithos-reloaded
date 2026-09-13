"""L'écriture de la couche `managed` de la config MCP — celle que le runtime possède (décision 7).

Un serveur `stdio` est un **exécutable et une liste d'arguments exacte** : pas de shell, pas d'env,
pas de cwd. Rien de ce qui est écrit ici n'est une chaîne qu'un interpréteur relira.

PORTED_FROM: villani-code-main/villani_code/mcp.py:27-35 (MIT)
PORTED_FROM: ouroboros-main/ouroboros/mcp_client.py:230-250 (Apache-2.0)
"""

from pathlib import Path

import journal

from .registry import Projection


LAYER = "managed"


def managed_layer(projection: Projection, interpreter: str) -> dict:
    "Rend la couche `managed` : un serveur par outil réellement appelable, et rien d'autre."

    servers = {
        entry.key: {"command": interpreter, "args": ["-m", entry.module, "--call", entry.call]}
        for entry in projection.available
    }

    return {"layer": LAYER, "mcpServers": servers}


def write_managed(path: Path, projection: Projection, interpreter: str, *, trace=journal) -> None:
    "Remplace le fichier en entier sous le verrou : cette couche a un propriétaire, et c'est nous."

    layer = managed_layer(projection, interpreter)
    trace.update_json_locked(path, lambda data: layer)
