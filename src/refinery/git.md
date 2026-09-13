# git — commits proposés pour `refinery`

**Aucun agent ne commite.** Ce fichier **propose** ; un humain **exécute**. Voir
[`AGENTS.md`](../../AGENTS.md) § 7.

Append-only : on ajoute une proposition, on ne réécrit pas les précédentes. Une proposition exécutée est
**marquée**, jamais supprimée.

**Rappels de format** — un commit une intention · chemins explicites, jamais `gaa` · message
`refinery: <ce que ça fait>` en minuscules, sans point final · uniquement du travail dont les tests
passent · uniquement `src/refinery/` et `tests/doubles/refinery.py`.

---

## Proposé le 10:09 — la gate d'effet

**Intention** : publier la gate qui retient un edit en `shadow` tant que son effet est dans le bruit.

```sh
ga src/refinery/gate.py \
   src/refinery/test_gate.py
gcmsg "refinery: gate d'effet promouvant sur un écart hors du bruit d'échantillonnage"
```

**Contient** : `Label`, `Effect`, `NodeEvidence`, `Baseline`, `Edit`, `Decision`, `refuse`, `z_score`,
`gate` — dont l'immuabilité mécanique de l'entrée de base et le refus enregistré, jamais fatal.
**Ne contient pas** : `propose`, le double et les deux tests transverses.
**Tests verts** : `src/refinery/test_gate.py` — 20 cas, venv `pithos`, Python 3.12.9.
**Exécuté** : —

---

## Proposé le 10:09 — le plan de raffinement déterministe

**Intention** : publier le plan de raffinement, déterministe et sans aucun appel modèle.

```sh
ga src/refinery/propose.py \
   src/refinery/test_propose.py
gcmsg "refinery: plan de raffinement déterministe routant un fait récurrent vers memory"
```

**Contient** : `RECURRENCE_MIN` et `plan_refinement` — diagnostic construit par le harness, plus petite
entrée utile, preuve limitée aux nœuds qui n'ont pas vérifié.
**Ne contient pas** : le double et les deux tests transverses — proposition suivante.
**Tests verts** : `src/refinery/test_propose.py` — 12 cas, 32 avec `test_gate.py`.
**Exécuté** : —

---

## Proposé le 10:09 — le double, le contrat de frontière et le graphe d'imports

**Intention** : publier le double trivial et les deux tests qui rendent `enabled: false` mécanique.

```sh
ga src/refinery/__init__.py \
   src/refinery/test_double_contract.py \
   src/refinery/test_import_boundaries.py \
   tests/doubles/refinery.py
gcmsg "refinery: double trivial, contrat de frontière et graphe d'imports"
```

**Contient** : `ENABLED = False`, le `Protocol` `Refinery`, le double à deux scénarios scriptables, le
corpus partagé, et le balayage qui vérifie qu'aucun module du socle n'atteint `refinery`.
**Ne contient pas** : le déplacement des deux tests vers `tests/contracts/` et `tests/boundaries/` —
hors de mon périmètre, en attente de dérogation (`STATE.md` § Blocages).
**Tests verts** : `src/refinery` en entier — 72 passed, 1 skipped, venv `pithos`, Python 3.12.9.
**Exécuté** : —

<!-- Gabarit d'une proposition — copie ce bloc, ne le supprime pas.

## Proposé le JJ:MM — <titre court>

**Intention** : une phrase — ce que ce commit fait, et rien d'autre.

```sh
ga src/refinery/<fichier_a>.py \
   tests/doubles/refinery.py
gcmsg "refinery: <ce que ça fait>"
```

**Contient** : …
**Ne contient pas** : …
**Tests verts** : …
**Exécuté** : —

-->
