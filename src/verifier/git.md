# git — commits proposés pour `verifier`

**Aucun agent ne commite.** Ce fichier **propose** ; un humain **exécute**. Voir
[`AGENTS.md`](../../AGENTS.md) § 7.

Append-only : on ajoute une proposition, on ne réécrit pas les précédentes. Une proposition exécutée est
**marquée**, jamais supprimée.

**Rappels de format** — un commit une intention · chemins explicites, jamais `gaa` · message
`verifier: <ce que ça fait>` en minuscules, sans point final · uniquement du travail dont les tests passent ·
uniquement `src/verifier/` et `tests/doubles/verifier.py`.

---

_Aucune proposition. Le module n'a pas encore de code._

<!-- Gabarit d'une proposition — copie ce bloc, ne le supprime pas.

## Proposé le JJ:MM — <titre court>

**Intention** : une phrase — ce que ce commit fait, et rien d'autre.

```sh
ga src/verifier/<fichier_a>.py \
   src/verifier/<fichier_b>.py \
   tests/doubles/verifier.py
gcmsg "verifier: <ce que ça fait>"
```

**Contient** : …
**Ne contient pas** : …
**Tests verts** : …
**Exécuté** : —

-->

## Proposé le 06:09 — exécution des invariants fermés

**Intention** : exécuter les invariants sur des copies possédées avec artefacts conservés et résultat typé.

```sh
ga src/verifier/domains.py \
   src/verifier/relations.py \
   src/verifier/models.py \
   src/verifier/runner.py \
   src/verifier/conftest.py \
   src/verifier/test_relations.py \
   src/verifier/test_runner.py
gcmsg "verifier: exécute les invariants fermés sur copies conservées"
```

**Contient** : huit relations exécutables, cinq domaines, admission AST, seed 0, subprocess borné, conservation du triplet de sorties et détection des terminaisons prématurées.
**Ne contient pas** : `schema_conform`, mutation-check, attestation d'effet ni reçu durable.
**Tests verts** : `src/verifier/test_relations.py`, `src/verifier/test_runner.py` — **49 passed in 9.83s**, Python 3.12.9 / venv pithos.
**Exécuté** : —

## Proposé le 06:09 — sensibilité de l'invariant aux mutations

**Intention** : exiger un mutant effectivement tué pour attester la sensibilité de l'invariant.

```sh
ga src/verifier/mutation.py \
   src/verifier/models.py \
   src/verifier/test_mutation.py
gcmsg "verifier: vérifie la sensibilité par cinq mutations ast"
```

**Contient** : transformations isolées et compilables, baseline verte, budget partagé, rejet des faux kills, rapport typé.
**Ne contient pas** : attestation de changement du workspace ni reçu journalisé.
**Tests verts** : `src/verifier/test_mutation.py` — **10 passed in 3.86s**, Python 3.12.9 / venv pithos.
**Exécuté** : —
