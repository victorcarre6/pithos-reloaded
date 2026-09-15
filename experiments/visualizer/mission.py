"""Mission audio reprenable : worker lifecycle, flow local et commit vert via broker."""

import argparse
from functools import partial
from hashlib import sha256
import json
from pathlib import Path
import signal
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

import bridge
import broker
import journal
import verifier
from engine.attempt import Deps
from engine.budget import Budget
from engine.tree import Tree, publish
from engine.walk import WalkDeps
from experiments.visualizer.run import INSTRUCTION, SEED, SYSTEM, projection_criterion
from kernel.contracts import Node, Relation
from lifecycle.execution import MissionProcess, run_command
from lifecycle.lock import RunLock
from workspace import Workspace


def execute(repo, output, budget):
    """Relit une mission sous verrou déjà détenu, puis appelle son unique enveloppe flow."""

    from engine.flow import mission

    # identité liée au répertoire de preuves ; une reprise ne crée aucun nouvel arbre
    journal.bind(output / "events.jsonl", output / "live.log")
    tree_path = output / "tree.json"
    mission_id = "audio-" + sha256(str(output).encode()).hexdigest()[:16]
    target = repo / "audio_visualizer.py"
    criterion = projection_criterion()
    if tree_path.exists():
        tree = Tree.model_validate_json(tree_path.read_bytes())
        valid = len(tree.nodes) == 1 and tree.mission_id == mission_id and tree.cap_children == 1
        if not valid or tree.nodes[0].target != target:
            raise ValueError("persisted mission differs from this experiment")
        # les anciennes preuves gardent leur relation ; aucune migration de reçu
        persisted = tree.nodes[0].criterion
        legacy = criterion.model_copy(update={"relation": Relation.idempotent})
        if persisted not in (criterion, legacy):
            raise ValueError("persisted mission differs from this experiment")
    else:
        if target.read_bytes() != SEED.read_bytes():
            raise ValueError("a new mission requires the unchanged experiment seed")
        node = Node(id="clamp-level", parent_id=None, depth=0, target=target, criterion=criterion,
                    status="pending", blocked_cause=None)
        tree = Tree(mission_id=mission_id, nodes=(node,), cap_children=1)
    publish(tree, tree, tree_path, journal)

    # aucune sonde modèle pour simplement réconcilier ou finaliser une preuve existante
    capability = bridge.Capability(bridge.Provenance.unprobeable, 0, False, "no new attempt requested")
    admissible = any(node.status in {"pending", "budget_limited"} for node in tree.nodes)
    if admissible and budget.can_start:
        capability = bridge.probe()
    attempt = Deps(Workspace(repo), bridge, verifier, journal, partial(broker.repo_fact, repo), capability)
    finalizer = broker.GreenFinalizer(repo, ledger=output / "effects.json", events_path=output / "events.jsonl")
    deps = WalkDeps(attempt, finalizer, tree_path, output / "events.jsonl", output,
                    SYSTEM.read_text(), INSTRUCTION)
    with verifier.execution_scope(run_command):
        mission(tree, budget, deps)


def launch(repo, output, seconds, *, worker=execute):
    """Exécute ou reprend le banc ; toutes les missions du dépôt partagent leur custody."""

    # chemins canoniques et preuves hors dépôt ; aucun git d'écriture dans le parent
    repo, output = repo.resolve(), output.resolve()
    if ROOT.is_relative_to(repo) or not (repo / ".git").is_dir():
        raise ValueError("a dedicated initialized Git repository is required")
    control = repo.with_name(f".{repo.name}.pithos")
    if control.is_symlink():
        raise ValueError("custody directory must not be a symbolic link")
    if output.is_relative_to(repo) or control.is_relative_to(output) or output.is_relative_to(control):
        raise ValueError("mission evidence and custody must be separate and outside the repository")
    budget = Budget(seconds)
    output.mkdir(parents=True, exist_ok=True)
    control.mkdir(exist_ok=True)
    journal.bind(control / "events.jsonl", control / "live.log")
    lock = RunLock(control / "run.lock", max_seconds=seconds + 60)
    process = MissionProcess(lock, events_path=control / "events.jsonl")
    process.run(partial(worker, repo, output, budget), budget.deadline + 60)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True, help="répertoire stable de preuves à créer ou reprendre")
    parser.add_argument("--seconds", type=float, default=180)
    args = parser.parse_args(argv)

    def interrupt(signum, frame):
        raise KeyboardInterrupt

    previous = signal.signal(signal.SIGTERM, interrupt)
    try:
        launch(args.repo, args.run, args.seconds)
    except KeyboardInterrupt:
        report, code = {"status": "interrupted", "run": str(args.run.resolve())}, 130
    except Exception as error:
        report = {"status": "error", "error": type(error).__name__, "detail": str(error), "run": str(args.run.resolve())}
        code = 1
    else:
        tree = Tree.model_validate_json((args.run / "tree.json").read_bytes())
        report = {
            "status": tree.nodes[0].status.value,
            "finalized": len(tree.finalized),
            "criterion": tree.nodes[0].criterion.model_dump(mode="json"),
            "run": str(args.run.resolve()),
        }
        code = 0 if tree.finalized else 1
    finally:
        signal.signal(signal.SIGTERM, previous)
    content = json.dumps(report, ensure_ascii=False)
    print(content)

    return code


if __name__ == "__main__":
    raise SystemExit(main())
