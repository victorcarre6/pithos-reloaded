"""Chargement des doubles : une instance indépendante à chaque appel, aucune cache partagée."""

import importlib.util
from pathlib import Path


DOUBLES_DIR = Path(__file__).resolve().parent / "doubles"


def load_double(name):
    """Charge le double demandé sans enregistrer son état mutable dans sys.modules."""

    spec = importlib.util.spec_from_file_location(f"doubles_{name}", DOUBLES_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module
