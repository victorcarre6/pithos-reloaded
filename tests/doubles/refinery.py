"""Double de la politique d'auto-amélioration : trivial, le module étant en bout de chaîne et éteint.

Deux scénarios se scriptent en assignant un attribut du module : `plan` donne le plan que rendra
`plan_refinement`, et `decision` force le verdict de `gate`. Sans script, le double ne propose rien et
ne promeut rien — un double qui promeut par défaut ferait passer une gate que personne n'a mesurée.

`refuse` est importée telle quelle : c'est une fonction pure, et la réimplémenter aurait créé un second
jeu de règles d'immuabilité.
"""

from campaign.store import Store

from refinery.gate import Baseline, Decision, Edit, Effect, Label, refuse

ENABLED = False

plan: list[Edit] = []
decision: Decision | None = None


def reset() -> None:
    "Vide le plan scripté et rétablit le verdict de `gate` à son défaut : rien ne bouge."

    global decision

    plan.clear()
    decision = None


def plan_refinement(state: Store, baseline: Baseline) -> list[Edit]:
    "Rend le plan scripté par le test, et rien d'autre : le double ne diagnostique pas."

    return list(plan)


def gate(edit: Edit, before: Baseline, after: Baseline) -> Decision:
    "Rend le verdict forcé, sinon `held` — un edit refusé le reste, même dans un double."

    reason = refuse(edit)
    if reason:
        return Decision(effect=Effect.refused, label=Label.shadow, version=edit.version,
                        evidence=edit.evidence, detail=reason)

    if decision is not None:
        return decision

    return Decision(effect=Effect.held, label=Label.shadow, version=edit.version,
                    evidence=edit.evidence, detail="the double never promotes on its own")
