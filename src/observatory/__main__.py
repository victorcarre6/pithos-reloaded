"""Démarre uniquement le lecteur HTTP local, dans un processus distinct du harness."""

from argparse import ArgumentParser
from pathlib import Path

from .api.routes import LOGS_ROOT, bind, bind_runs, serve


def main():
    "Choisit explicitement la disposition des traces ; l'adresse reste 127.0.0.1."

    parser = ArgumentParser(description=__doc__)
    roots = parser.add_mutually_exclusive_group()
    roots.add_argument("--runs-root", type=Path, help="collection directe d'essais visualizer")
    roots.add_argument("--logs-root", type=Path, default=LOGS_ROOT, help="racine contenant missions/")
    args = parser.parse_args()
    if args.runs_root is not None:
        bind_runs(args.runs_root.resolve())
    else:
        bind(args.logs_root.resolve())
    serve()


if __name__ == "__main__":
    main()
