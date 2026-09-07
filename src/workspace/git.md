# git — commits proposés pour `workspace`

**Aucun agent ne commite.** Ce fichier **propose** ; un humain **exécute**. Voir
[`AGENTS.md`](../../AGENTS.md) § 7.

Append-only : on ajoute une proposition, on ne réécrit pas les précédentes. Une proposition exécutée est
**marquée**, jamais supprimée.

**Rappels de format** — un commit une intention · chemins explicites, jamais `gaa` · message
`workspace: <ce que ça fait>` en minuscules, sans point final · uniquement du travail dont les tests passent ·
uniquement `src/workspace/` et `tests/doubles/workspace.py`.

---

_Aucune proposition. Le module n'a pas encore de code._

<!-- Gabarit d'une proposition — copie ce bloc, ne le supprime pas.

## Proposé le JJ:MM — <titre court>

**Intention** : une phrase — ce que ce commit fait, et rien d'autre.

```sh
ga src/workspace/<fichier_a>.py \
   src/workspace/<fichier_b>.py \
   tests/doubles/workspace.py
gcmsg "workspace: <ce que ça fait>"
```

**Contient** : …
**Ne contient pas** : …
**Tests verts** : …
**Exécuté** : —

-->

## Proposé le 07:09 — préparation pure du splice

**Intention** : refuser un remplacement de fonction invalide avant toute écriture.

```sh
ga src/workspace/splice.py \
   src/workspace/test_splice.py \
   src/workspace/STATE.md \
   src/workspace/git.md
gcmsg "workspace: valide le splice ast avant écriture"
```

**Contient** : plan typé, compilation sans exécution, empreintes et bilan.
**Tests verts** : `src/workspace/test_splice.py` — 37 tests, Python 3.12.9 / pithos.
**Exécuté** : —

## Proposé le 07:09 — écritures transactionnelles confinées

**Intention** : appliquer une fonction validée sans écraser un snapshot périmé.

```sh
ga src/workspace/__init__.py \
   src/workspace/paths.py \
   src/workspace/transaction.py \
   src/workspace/splice.py \
   src/workspace/conftest.py \
   src/workspace/test_splice.py \
   src/workspace/test_transaction.py \
   src/workspace/test_paths.py \
   src/workspace/STATE.md \
   src/workspace/git.md
gcmsg "workspace: applique le splice avec cas et rollback exact"
```

**Contient** : chemin canonique, six gardes, rollback, conservation préalable via journal,
corrections de l'encodage et des décorateurs parenthésés.
**Tests verts** : `src/workspace` — 79 tests, Python 3.12.9 / pithos.
**Exécuté** : —

## Proposé le 07:09 — socle workspace complet dans le périmètre autorisé

**Priorité** : cette proposition consolidée remplace, pour exécution, les deux
propositions précédentes restées non exécutées. Leurs résultats historiques restent
conservés. Aucun fichier n'a été stagé par l'agent.

**Intention** : publier le remplacement transactionnel vérifiable d'une fonction existante.

```sh
ga src/workspace/__init__.py \
   src/workspace/paths.py \
   src/workspace/protocol.py \
   src/workspace/splice.py \
   src/workspace/transaction.py \
   src/workspace/conftest.py \
   src/workspace/test_splice.py \
   src/workspace/test_transaction.py \
   src/workspace/test_paths.py \
   src/workspace/test_double_contract.py \
   src/workspace/test_import_boundaries.py \
   tests/doubles/workspace.py \
   src/workspace/MODULE.md \
   src/workspace/STATE.md \
   src/workspace/git.md
gcmsg "workspace: publie le splice transactionnel avec preuves et double"
```

**Contient** : six gardes, canonicalisation, préservation des octets, CAS, rollback,
traces préalables, modèles/Protocols, double mémoire et contrôles de frontière.
**Tests verts** : `src/workspace` — **119 passed in 0.27s**, Python 3.12.9 / pithos.
**Preuve supplémentaire** : splice puis restauration réelle ; empreintes et événements
conservés dans l'artefact référencé par STATE.md, niveau 5.
**Limite** : placement final des deux tests partagés à autoriser ; cette proposition
ne stage aucun chemin hors du périmètre actuel. Mettre à jour la proposition après
ces déplacements autorisés, si elle n'a pas déjà été exécutée.
**Exécuté** : —
