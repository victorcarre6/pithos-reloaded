"""Le plan de raffinement : déterministe, zéro appel modèle — l'appel modèle est un dernier recours.

Trois étapes, dans cet ordre : **diagnostiquer**, **modifier la plus petite entrée utile**, puis rejouer
et enregistrer. La troisième appartient à `engine` ; les deux premières sont ici.

La table de routage se réduit à une ligne au socle : un **fait** récurrent va en `memory`. Les deux
autres destinations de la source — procédure vers `skill`, délégation vers `subagent` — n'ont pas de
consommateur tant que le mode agentic est différé.

PORTED_FROM: prime-agent-main/prime-agent-runtime/src/rlm/harness.py:705-720 (MIT)
"""

from campaign.store import Family, Store

from .gate import Baseline, Edit


RECURRENCE_MIN = 3  # en deçà, une entrée n'est pas encore un fait récurrent


def plan_refinement(state: Store, baseline: Baseline) -> list[Edit]:
    """Rend le plan déterministe : même magasin et même baseline rendent exactement le même plan.

    Une mission qui n'a rien raté ne produit aucun edit — on ne réécrit pas un harness qui tient.
    """

    failed = [node for node in baseline.nodes if node.verification != "accepted"]
    if not failed:
        return []

    # diagnostic : construit par le harness, jamais par le modèle
    diagnosis = f"{len(failed)}/{baseline.attempted} nodes did not verify in {baseline.mission_id}"

    # la plus petite entrée utile : le fait le plus récurrent, la clé départageant les ex æquo
    recurring = [entry for entry in state.entries[Family.memory].values() if entry.version >= RECURRENCE_MIN]
    ordered = sorted(recurring, key=lambda entry: (-entry.version, entry.key))
    if not ordered:
        fresh = Edit(family=Family.memory, key=f"mission-{baseline.mission_id}", version=1,
                     content=diagnosis, evidence=failed)

        return [fresh]

    target = ordered[0]
    revised = Edit(family=Family.memory, key=target.key, version=target.version + 1,
                   content=f"{target.content}\n{diagnosis}", evidence=failed)

    return [revised]
