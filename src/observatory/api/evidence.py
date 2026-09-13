"""Projection des sidecars d'essai ; aucune exécution, aucun verdict ou reçu créé ici."""

import json
from hashlib import sha256
from pathlib import Path

from kernel.contracts import Node

MAX_ARTIFACT_BYTES = 2_000_000
ROOT_FILES = {"result.json", "tree.json", "CONTEXT.md"}
GATE_FILES = {"meta.json", "result.json", "candidate.py", "invariant.py", "stdout.txt", "stderr.txt", "counterexample.txt"}


def safe_path(root: Path, relative: str) -> Path:
    "Résout un fichier contenu dans l'essai, sans suivre de lien symbolique."

    path = Path(relative)
    if path.is_absolute() or not path.parts or ".." in path.parts or root.is_symlink():
        raise ValueError("unsafe_path")
    target = root
    for part in path.parts:
        target = target / part
        if target.is_symlink():
            raise ValueError("unsafe_path")
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("unsafe_path")

    return target


def read_text(root: Path, relative: str) -> str:
    "Lit au plus 2 Mo ; un dépassement reste explicite au lieu de tronquer silencieusement."

    path = safe_path(root, relative)
    with path.open("rb") as handle:
        content = handle.read(MAX_ARTIFACT_BYTES + 1)
    if len(content) > MAX_ARTIFACT_BYTES:
        raise ValueError("artifact_too_large")

    return content.decode("utf-8")


def read_object(root: Path, relative: str, anomalies: list[str]) -> dict | None:
    "Lit un sidecar objet ; l'absence est permise, une corruption est signalée."

    try:
        value = json.loads(read_text(root, relative))
        if not isinstance(value, dict):
            raise ValueError("expected_object")
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as failure:
        anomalies.append(f"{relative}:{type(failure).__name__}:{failure}")

        return None

    return value


def artifact_names(root: Path) -> list[str]:
    "Artefacts publiés par le runner, y compris ceux d'une vérification refusée."

    names = sorted(ROOT_FILES)
    for directory in sorted(root.glob("invariant-*")):
        if not directory.is_dir() or directory.is_symlink():
            continue
        names.extend(f"{directory.name}/{name}" for name in sorted(GATE_FILES) if (directory / name).exists())

    return names


def trial_projection(root: Path, events: list) -> dict:
    "Rapproche l'état publié et les preuves historiques, avec la provenance des rôles inférés."

    anomalies = []
    result = read_object(root, "result.json", anomalies)
    tree = read_object(root, "tree.json", anomalies)
    nodes = []
    try:
        raw_nodes = tree.get("nodes", []) if tree is not None else []
        if not isinstance(raw_nodes, list):
            raise ValueError("expected_nodes_list")
        nodes = [Node.model_validate(node) for node in raw_nodes]
    except (ValueError, TypeError) as failure:
        anomalies.append(f"tree.json:invalid_nodes:{failure}")

    # seules les intentions qui concordent avec l'état publié expliquent son issue
    reason = None
    published = {node.id: node.status.value for node in nodes}
    receipts = []
    reports = []
    hashes: dict[str, set[str]] = {}
    for event in events:
        payload = event.payload
        if payload.get("scope") == "engine" and published.get(payload.get("node_id")) == payload.get("operation"):
            reason = payload.get("detail")
        if event.durable and event.type.value == "validation" and isinstance(payload.get("receipt"), dict):
            receipts.append(payload["receipt"])
        if payload.get("operation") == "verification_report":
            reports.append({"ts": event.ts, "key": payload.get("key"), "verification": payload.get("verification")})
        if payload.get("operation") != "write":
            continue
        for role in ("before", "after"):
            encoded = payload.get(f"{role}_hex")
            if not isinstance(encoded, str):
                continue
            try:
                source = bytes.fromhex(encoded).decode("utf-8-sig").encode("utf-8")
                digest = sha256(source).hexdigest()
                hashes.setdefault(digest, set()).add(role)
            except ValueError:
                anomalies.append(f"invalid_source_hex:{event.ts}:{role}")

    # l'empreinte rattache une exécution à une source ; elle ne nomme pas un opérateur de mutation
    gates = []
    for name in artifact_names(root):
        if not name.endswith("/meta.json"):
            continue
        metadata = read_object(root, name, anomalies)
        if metadata is None:
            continue
        roles = hashes.get(metadata.get("source_sha256"), set())
        role = next(iter(roles)) if len(roles) == 1 else "variant"
        gates.append({
            "path": str(Path(name).parent),
            "role": role,
            "role_provenance": "source_sha256" if len(roles) == 1 else "unassigned",
            "metadata": metadata,
        })
    order = {"before": 0, "after": 1, "variant": 2}
    gates.sort(key=lambda gate: (order[gate["role"]], gate["path"]))

    return {
        "result": result,
        "nodes": [node.model_dump(mode="json") for node in nodes],
        "reason": reason,
        "receipt_count": len(receipts),
        "receipts": receipts,
        "gates": gates,
        "reports": reports,
        "anomalies": anomalies,
        "state_source": "tree.json" if tree is not None else "events",
    }
