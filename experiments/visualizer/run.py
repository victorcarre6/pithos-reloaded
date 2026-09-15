"""Banc audio local : régression sur copies, sonde Ollama, ou tentative sur dépôt dédié."""

import argparse
from contextlib import nullcontext
from dataclasses import asdict
from difflib import unified_diff
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

import bridge
import broker
import journal
import verifier
from engine.attempt import Deps, run_attempt
from engine.budget import Budget
from engine.tree import Tree
from kernel.contracts import Criterion, Node
from workspace import Workspace


SEED = HERE / "seed" / "audio_visualizer.py"
SYSTEM = ROOT / "src" / "bridge" / "prompt" / "candidate.md"
INSTRUCTION = "Project the finite audio level to [0, 1]. Preserve the signature; propose only clamp_level."
REFERENCE = (
    "def clamp_level(level):\n"
    "    return max(0.0, min(1.0, level))\n"
)


def projection_criterion():
    """Fixe le contrat des nouveaux essais, indépendamment de la réponse du modèle."""

    return Criterion(relation="unit_projection", symbols=["clamp_level"], domain="floats_finite")


def exercise(repo, output, deps, seconds):
    """Exerce la même nano-étape avec les ports fournis et mesure ses effets sur disque."""

    # données du banc, jamais décidées par le modèle
    target = repo / "audio_visualizer.py"
    before = target.read_bytes()
    criterion = projection_criterion()
    node = Node(id="clamp-level", parent_id=None, depth=0, target=target, criterion=criterion,
                status="pending", blocked_cause=None)
    tree = Tree(mission_id=output.name, nodes=(node,), cap_children=1)
    budget = Budget(seconds)
    result = run_attempt(tree, node.id, budget, deps, tree_path=output / "tree.json",
                         artifact_root=output, system=SYSTEM.read_text(), instruction=INSTRUCTION, attempt=1)

    # mesures depuis les fichiers effectivement relus et le journal durable
    after = target.read_bytes()
    events = list(journal.read(output / "events.jsonl"))
    receipts = [event.payload for event in events if event.type == "validation"]
    state = result.nodes[0]
    report = {
        "status": state.status.value,
        "cause": state.blocked_cause,
        "before_sha256": sha256(before).hexdigest(),
        "after_sha256": sha256(after).hexdigest(),
        "changed": before != after,
        "restored": before == after,
        "receipt_written": bool(receipts),
        "elapsed_seconds": budget.elapsed,
        "capability": asdict(deps.capability),
        "criterion": criterion.model_dump(mode="json"),
        "proof_scope": "exact projection onto [0, 1] on harness-generated finite floats; no universal proof",
    }

    return report


def selftest(output, case):
    """Exécute workspace, verifier et journal réels avec bridge/Git explicitement simulés."""

    from tests.support import load_double

    # copie neuve du seed ; les essais précédents restent intacts
    repo = output / "workspace"
    repo.mkdir()
    target = repo / "audio_visualizer.py"
    before = SEED.read_bytes()
    target.write_bytes(before)
    model = load_double("bridge")
    source = "def clamp_level(level):\n    return max(0.0, min(2.0, level))\n" if case == "rejected" else REFERENCE
    model.script(model.conformant({"function_name": "clamp_level", "new_source": source}))
    git = load_double("broker")
    git.complete = True

    def observe():
        # observation simulée : aucun dépôt Git n'est créé par ce mode
        current = target.read_bytes()
        git.changes = []
        git.diff = ""
        if current != before:
            git.changes = [broker.Change(status=" M", path=Path(target.name), origin=None)]
            lines = unified_diff(before.decode().splitlines(keepends=True), current.decode().splitlines(keepends=True),
                                 fromfile=f"a/{target.name}", tofile=f"b/{target.name}")
            header = f"diff --git a/{target.name} b/{target.name}\n"
            git.diff = header + "".join(lines)

        return git.repo_fact(repo)

    real_emit = journal.emit

    def emit(event):
        if case == "receipt_refused" and event.type == "validation":
            return False

        return real_emit(event)

    # seule la panne demandée est injectée ; les autres écritures passent par journal
    with patch.object(journal, "emit", emit):
        deps = Deps(Workspace(repo), model, verifier, journal, observe, model.capability)
        report = exercise(repo, output, deps, 30)
    expected = report["status"] == "passed" and report["changed"] and report["receipt_written"]
    if case != "green":
        expected = report["status"] == "blocked" and report["restored"] and not report["receipt_written"]
    if case == "receipt_refused":
        expected = expected and report["cause"] == "receipt_not_written"
    report.update(mode="selftest", case=case, checks_passed=expected,
                  components={"engine": "real", "workspace": "real", "verifier": "real",
                              "journal": "real; receipt rejection injected" if case == "receipt_refused" else "real",
                              "bridge": "scripted", "git": "simulated"})

    return report


def trial(repo, output, seconds):
    """Utilise le modèle et Git réels sur un dépôt dédié déjà préparé par l'opérateur."""

    repo = repo.resolve()
    if ROOT.is_relative_to(repo) or not (repo / ".git").exists():
        raise ValueError("a dedicated initialized Git repository is required")
    target = repo / "audio_visualizer.py"
    if target.read_bytes() != SEED.read_bytes():
        raise ValueError("the target must contain the unchanged experiment seed")
    capability = bridge.probe()
    deps = Deps(Workspace(repo), bridge, verifier, journal, lambda: broker.repo_fact(repo), capability)
    report = exercise(repo, output, deps, seconds)
    report.update(mode="trial", components={name: "real" for name in ("engine", "workspace", "verifier", "journal", "bridge", "git")})

    return report


def build_parser():
    """Expose les mêmes arguments au banc historique et à l'entrée Pithos."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-tui", action="store_true", help="désactiver l'affichage dynamique")
    commands = parser.add_subparsers(dest="mode", required=True)
    regression = commands.add_parser("selftest")
    regression.add_argument("--case", choices=("green", "rejected", "receipt_refused"), default="green")
    probe = commands.add_parser("probe")
    actual = commands.add_parser("trial")
    actual.add_argument("--repo", type=Path, required=True)
    actual.add_argument("--seconds", type=float, default=180)
    for command in (regression, probe, actual):
        command.add_argument("--no-tui", action="store_true", default=argparse.SUPPRESS,
                             help="désactiver l'affichage dynamique")

    return parser


def main(argv=None, *, display=None):
    """Lance un essai, conserve son rapport et ferme l'affichage avant le JSON final."""

    parser = build_parser()
    args = parser.parse_args(argv)

    # répertoire exclusif et événements append-only, même en cas d'échec du banc
    runs = HERE / "runs"
    runs.mkdir(exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix=f"{args.mode}-", dir=runs))
    journal.bind(output / "events.jsonl", output / "live.log")
    presentation = nullcontext()
    if display is not None and not args.no_tui:
        presentation = display(args, output)
    with presentation:
        try:
            if args.mode == "selftest":
                report = selftest(output, args.case)
            elif args.mode == "probe":
                capability = bridge.probe()
                report = {"mode": "probe", "capability": asdict(capability), "usable": capability.usable}
            else:
                report = trial(args.repo, output, args.seconds)
        except KeyboardInterrupt:
            report = {"mode": args.mode, "status": "interrupted", "error": "KeyboardInterrupt"}
        except Exception as error:
            report = {"mode": args.mode, "error": type(error).__name__, "detail": str(error)}
        report["evidence_directory"] = str(output)
        serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        with (output / "result.json").open("x") as stream:
            stream.write(serialized)
            stream.flush()
            os.fsync(stream.fileno())

    # sortie stable pour les scripts, après restauration du terminal
    print(serialized, end="")
    if report.get("status") == "interrupted":
        return 130
    success = report.get("checks_passed") or report.get("usable") or report.get("status") == "passed"

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
