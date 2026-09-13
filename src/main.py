"""Entrée Pithos : les commandes du banc audio avec suivi terminal dynamique."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

from experiments.visualizer.run import main as run
from tui import Dashboard


def main(argv=None):
    return run(argv, display=Dashboard)


if __name__ == "__main__":
    raise SystemExit(main())
