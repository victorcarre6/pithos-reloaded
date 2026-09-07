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

## État des propositions — 07:09

Les trois propositions ci-dessous décrivent l'état final vérifié et **remplacent pour exécution** les
propositions précédentes, laissées dans ce journal. Aucune n'a été exécutée. Elles s'appliquent dans cet
ordre ; les contrats kernel et l'interface journal sont des prérequis publiés par leurs propres agents.

### 1 — scripts d'invariants conservés

**Intention** : exécuter les relations fermées sur des copies dont les preuves restent relisibles.

```sh
ga src/verifier/domains.py \
   src/verifier/relations.py \
   src/verifier/models.py \
   src/verifier/runner.py \
   src/verifier/conftest.py \
   src/verifier/test_relations.py \
   src/verifier/test_runner.py
gcmsg "verifier: exécute les invariants sur des copies conservées"
```

**Contient** : huit relations, cinq domaines, admission AST, seed fixe, shrinking, subprocess borné,
artefacts exclusifs et métadonnées, résultat typé ; correction des portées imbriquées et symboles remplacés.
**Tests verts** : `src/verifier/test_relations.py`, `src/verifier/test_runner.py`, inclus dans les
**108 passed in 20.09s** de `src/verifier` sous Python 3.12.9 / venv pithos.
**Exécuté** : —

### 2 — double gate de sensibilité

**Intention** : exiger le rouge avant, le vert après puis un mutant effectivement tué.

```sh
ga src/verifier/mutation.py \
   src/verifier/gates.py \
   src/verifier/test_mutation.py \
   src/verifier/test_gates.py
gcmsg "verifier: exige la double gate de sensibilité"
```

**Contient** : cinq mutations compilables à un site, budget partagé, refus d'une baseline verte ou d'une
tautologie, pannes distinctes des kills ; verdict limité à la vérification des sources.
**Tests verts** : `src/verifier/test_mutation.py`, `src/verifier/test_gates.py`, inclus dans les
**108 passed in 20.09s** de `src/verifier` sous Python 3.12.9 / venv pithos.
**Exécuté** : —

### 3 — frontière publique avec reçu acquitté

**Intention** : publier une frontière de vérification dont le reçu dépend de l'acquittement du journal.

```sh
ga src/verifier/__init__.py \
   src/verifier/protocol.py \
   src/verifier/receipt.py \
   tests/doubles/verifier.py \
   src/verifier/test_receipt.py \
   src/verifier/test_double_contract.py \
   src/verifier/test_import_boundaries.py \
   src/verifier/MODULE.md \
   src/verifier/STATE.md \
   src/verifier/git.md
gcmsg "verifier: publie la frontière avec reçu acquitté"
```

**Contient** : `SourceVerifier`, double déterministe, identité typée, émission sur journal injecté, test
`emit=False`, contrôles d'import et d'I/O locaux, documentation des raccordements kernel encore bloqués.
**Ne contient pas** : `run(criterion, facts)` complet, `schema_conform`, transition de nœud, gate hermétique,
ni déplacement hors du périmètre autorisé. Le reçu courant porte `effect=unproven` dans sa trace.
**Tests verts** : `src/verifier/test_receipt.py`, `src/verifier/test_double_contract.py`,
`src/verifier/test_import_boundaries.py`, inclus dans les **108 passed in 20.09s** de `src/verifier`
sous Python 3.12.9 / venv pithos. Preuve autonome conservée :
`/private/tmp/pithos-verifier-proof-c74qv4ng/`, codes mesurés **20 → 0 → 20**.
**Exécuté** : —

## Actualisation prioritaire — 07:09 — code déjà intégré dans 46a18fe

Au contrôle final, le commit **`46a18fe` — `arborescence modules`** est apparu dans l'historique.
`git diff` confirme que les neuf fichiers de production, le double, tous les tests et `MODULE.md`
correspondent déjà à ce commit. **Aucune commande Git en écriture n'a été lancée par cet agent.**

Les propositions 1 et 2 sont donc **sans objet pour exécution : contenu intégré dans 46a18fe**.
La proposition 3 est **partiellement intégrée dans 46a18fe** ; seuls les derniers ajouts de reprise
ci-dessous restent à enregistrer. Ne pas réexécuter les anciennes listes de fichiers.

## Proposé le 07:09 — état vérifié des raccordements restants

**Intention** : conserver l'état de reprise vérifié du verifier en attendant les faits kernel manquants.

```sh
ga src/verifier/STATE.md \
   src/verifier/git.md
gcmsg "verifier: consigne la validation et les raccordements restants"
```

**Contient** : les 108 tests verts, les preuves négatives corrigées, la mesure de 739 lignes, les chemins
des artefacts autonomes et les contrats nécessaires à la suite ; actualisation après intégration du code.
**Tests verts** : **108 passed in 20.09s**, Python 3.12.9 / venv pithos ; code inchangé depuis ce contrôle.
**Vérification de forme** : les 21 fichiers relus par `git diff --no-index --check` sans diagnostic.
**Exécuté** : —
