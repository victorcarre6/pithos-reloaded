# git — commits proposés pour `engine`

**Aucun agent ne commite.** Ce fichier **propose** ; un humain **exécute**. Voir
[`AGENTS.md`](../../AGENTS.md) § 7.

Append-only : on ajoute une proposition, on ne réécrit pas les précédentes. Une proposition exécutée est
**marquée**, jamais supprimée.

**Rappels de format** — un commit une intention · chemins explicites, jamais `gaa` · message
`engine: <ce que ça fait>` en minuscules, sans point final · uniquement du travail dont les tests passent ·
uniquement `src/engine/` et `tests/doubles/engine.py`.

---

_Aucune proposition. Le module n'a pas encore de code._

<!-- Gabarit d'une proposition — copie ce bloc, ne le supprime pas.

## Proposé le JJ:MM — <titre court>

**Intention** : une phrase — ce que ce commit fait, et rien d'autre.

```sh
ga src/engine/<fichier_a>.py \
   src/engine/<fichier_b>.py \
   tests/doubles/engine.py
gcmsg "engine: <ce que ça fait>"
```

**Contient** : …
**Ne contient pas** : …
**Tests verts** : …
**Exécuté** : —

-->

## Proposé le 10:09 — admission du contexte sous budget

**Intention** : produire un inventaire de contexte qui refuse les données périmées et le débordement irréductible.

```sh
ga src/engine/context.py \
   src/engine/test_context.py \
   src/engine/conftest.py
gcmsg "engine: admettre le contexte par empreintes et éviction fifo"
```

**Contient** : inventaire typé intégral, raisons exclusives, paliers, FIFO, passations liées aux empreintes.
**Ne contient pas** : sélection des fichiers, écriture de CONTEXT.md et raccordement au marcheur.
**Tests verts** : `src/engine/test_context.py` — inclus dans les 29 tests verts budget/contexte du 10:09.
**Exécuté** : —

## Proposé le 10:09 — budget monotone

**Intention** : réserver la fin de la borne murale à la finalisation.

```sh
ga src/engine/budget.py \
   src/engine/test_budget.py
gcmsg "engine: fermer l'admission dans la réserve de finalisation"
```

**Contient** : deadline à ancre unique, temps restant, temps dépensable, validation des durées.
**Ne contient pas** : finalisation du marcheur et adaptateur Prefect.
**Tests verts** : `src/engine/test_budget.py` — inclus dans les 29 tests verts budget/contexte du 10:09.
**Exécuté** : —

## Proposé le 10:09 — scission bornée de l'arbre

**Intention** : publier une scission complète ou un blocage mécanique sous contrôle de concurrence.

```sh
ga src/engine/tree.py \
   src/engine/walk.py \
   src/engine/test_tree.py
gcmsg "engine: borner et persister les scissions de l'arbre"
```

**Contient** : validation du graphe, profondeur 3, `cap_children`, intention durable, CAS de publication,
blocages `memory`, dispositions structurelles du parent liées au hash de l'enfant.
**Ne contient pas** : exécution, attestation de l'effet, finalisation et fonction `walk` complète.
**Tests verts** : `src/engine/test_tree.py` — inclus dans les **55 verts en 0,25 s** de la suite engine.
**Exécuté** : —

## Proposé le 10:09 — doublons de contexte contradictoires

**Intention** : empêcher un élément optionnel de masquer un élément obligatoire homonyme.

```sh
ga src/engine/context.py \
   src/engine/test_context.py
gcmsg "engine: refuser les doublons de contexte contradictoires"
```

**Contient** : comparaison des doublons et test de régression rouge puis vert.
**Ne contient pas** : changement de la politique FIFO.
**Tests verts** : `src/engine/test_context.py` — inclus dans les **55 verts en 0,25 s** de la suite engine.
**Exécuté** : —

## État des propositions le 10:09 — consolidation avant exécution humaine

Les propositions sont restées **non exécutées**. Les deux propositions concernant le
contexte se regroupent en la première, avec la correction du doublon incluse dans les
fichiers actuels. Ne pas tenter deux commits successifs des mêmes fichiers inchangés.
La proposition « scission bornée de l'arbre » est **remplacée** par celle ci-dessous :
`walk.py` importe maintenant le classifieur, les deux doivent être publiés ensemble.
La proposition budget reste indépendante et applicable telle quelle.

## Proposé le 10:09 — décomposition déterministe vérifiée

**Intention** : dériver et publier des enfants bornés pour un nœud sans critère.

```sh
ga src/engine/classify.py \
   src/engine/tree.py \
   src/engine/walk.py \
   src/engine/test_classify.py \
   src/engine/test_tree.py \
   src/engine/test_import_boundaries.py \
   src/engine/MODULE.md \
   src/engine/STATE.md \
   src/engine/git.md
gcmsg "engine: décomposer les nœuds par classification déterministe bornée"
```

**Contient** : arbre validé, classifieur branché et tracé, scission complète ou blocage,
CAS, intentions conservées, dispositions structurelles, contrôles de frontière locaux,
point de reprise et blocages de contrat. Dépend du `conftest.py` de la proposition contexte.
**Ne contient pas** : marcheur exécutant, finalisation, baseline, `select.py`, `dump.py`, Prefect,
ni double du futur contrat d'exécution.
**Tests verts** : `src/engine` — **81 tests en 0,30 s**, Python **3.12.9**, venv **pithos** ;
`git diff --check -- src/engine tests/doubles/engine.py` vert.
**Exécuté** : —

## Proposé le 12:09 — sélection déterministe du contexte

**Intention** : sélectionner les fichiers pertinents et leurs relations d'import avec une raison explicite.

```sh
ga src/engine/classify.py \
   src/engine/select.py \
   src/engine/test_select.py \
   src/engine/MODULE.md \
   src/engine/STATE.md \
   src/engine/git.md
gcmsg "engine: sélectionne le contexte depuis les imports indexés"
```

**Contient** : RepoIndex avec imports résolus injectés, pertinence issue du classifieur, fermeture des dépendances et importeurs, profondeur explicite, cycles et exclusion runtime, notice MIT.
**Ne contient pas** : producteur de l'index, walk exécutant, dump de contexte, Prefect.
**Tests verts** : 96 tests engine/frontière en 0,33 s ; suite globale 1 365 passed, 3 skipped, 7 warnings en 38,19 s.
**Exécuté** : —

## Proposé le 13:09 — exécuter une nano-étape transactionnelle

**Intention** : Publier le vert uniquement après validation des faits et reçu durable, avec restauration sur exception.

```sh
ga src/engine/attempt.py \
   src/engine/test_attempt.py \
   tests/doubles/engine.py \
   src/engine/MODULE.md \
   src/engine/STATE.md \
   src/engine/git.md
gcmsg "engine: exécute une nano-étape avec reçu durable"
```

**Contient** : Deps et NanoEngine, intention/CAS, transaction, admission, candidat, faits, gate, reçu et publication. Le marcheur complet reste ouvert. Prérequis : lots bridge candidat et verifier preflight.
**Tests verts** : src/engine/test_attempt.py, tests/contracts/test_engine_double.py, tests/boundaries/test_engine.py. Suite complète **1 402 passed, 3 skipped, 7 warnings en 40,64 s** dans Python 3.12.9/pithos.
**Exécuté** : —
