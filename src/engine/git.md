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


## Proposé le 13:09 — conserver chaque rapport de vérification

**Intention** : Conserver le verdict du verifier avant toute décision de publication.

```sh
ga src/engine/attempt.py \
   src/engine/test_attempt.py \
   src/engine/MODULE.md \
   src/engine/STATE.md \
   src/engine/git.md
gcmsg "engine: conserve les rapports de vérification avant décision"
```

**Contient** : Événement durable verification_report avec RecordKey, sans facts ni reçu synthétique ; restauration lorsque sa trace échoue. Transmission de la provenance de capacité au Deadline de l'appel. Prérequis : proposition run_attempt.
**Tests verts** : src/engine/test_attempt.py, tests/contracts/test_engine_double.py, tests/boundaries/test_engine.py ; rapport relu dans selftest-wo3aa7e5. Suite complète : **1 444 passed, 3 skipped, 7 warnings en 43,83 s**, Python 3.12.9/pithos ; contrôle des onze STATE vert.
**Exécuté** : —


## Proposé le 13:09 — annoncer les omissions dans leur budget

**Intention** : Rendre les omissions visibles dans le contexte sans dépasser son budget.

```sh
ga src/engine/context.py \
   src/engine/test_context.py
gcmsg "engine: budgète la notice des omissions de contexte"
```

**Contient** : Comptes par raison fermée, séparateur compris dans le coût estimé, recalcul après chaque éviction FIFO, aucune fuite du texte exclu. Décision et preuves dans MODULE.md/STATE.md du lot précédent. Branchement au marcheur encore prévu.
**Tests verts** : src/engine/test_context.py ; 116 tests engine/contrat/frontière lors de l'incrément. Suite complète : **1 444 passed, 3 skipped, 7 warnings en 43,83 s**, Python 3.12.9/pithos ; contrôle des onze STATE vert.
**Exécuté** : —

## Proposé le 14:09 — reprendre les missions depuis leurs preuves durables

**Intention** : Exécuter un walk reprenable dont les résultats verts sont finalisés par identité logique.

```sh
ga src/engine/walk.py \
   src/engine/recovery.py \
   src/engine/attempt.py \
   src/engine/tree.py \
   src/engine/test_walk.py \
   src/engine/test_recovery.py \
   src/engine/test_attempt.py \
   tests/doubles/engine.py \
   src/engine/MODULE.md \
   src/engine/STATE.md \
   src/engine/git.md
gcmsg "engine: reprend les missions depuis leurs preuves durables"
```

**Contient** : WalkDeps/Walker et GreenFinalizer, identités de tentative persistées, snapshots avant effet,
réconciliation sans inférence, restauration du candidat connu, finalisation interrogée avant rejeu,
dispositions liées aux reçus, baseline de clôture et admission du contexte courant. Double scénarisé,
contrôles de signatures et scénarios de coupure inclus. Cas nominal à deux verts successifs testé.
**Ne contient pas** : Adaptateur Git réel, enveloppe lifecycle/Prefect, projection CONTEXT.md ; leurs
contrats et prochaines actions sont explicités dans MODULE.md/STATE.md. Aucun changement du dashboard.
**Tests verts** : **152 passed** sur src/engine, tests/contracts/test_engine_double.py et
tests/boundaries/test_engine.py ; suite complète **1480 passed, 3 skipped, 7 warnings en 43,90 s**,
Python 3.12.9/pithos. Contrôle des onze STATE et git diff --check verts. **Niveau 5 sur doubles**.
**Exécuté** : —

## Proposé le 14:09 — reprendre une mission avec sa passation vérifiée

**Intention** : Reprendre une mission avec une passation vérifiée sous empreintes fraîches.

**État courant** : la proposition walk ci-dessus n'a pas été exécutée. Les fichiers partagés contiennent
maintenant le raccordement à dump.py. Utiliser **ce lot complet à la place du lot walk seul** pour l'état
actuel ; ne pas exécuter successivement les deux propositions. L'ancienne reste conservée comme historique.

```sh
ga src/engine/walk.py \
   src/engine/recovery.py \
   src/engine/attempt.py \
   src/engine/tree.py \
   src/engine/dump.py \
   src/engine/test_walk.py \
   src/engine/test_recovery.py \
   src/engine/test_attempt.py \
   src/engine/test_dump.py \
   tests/doubles/engine.py \
   src/engine/MODULE.md \
   src/engine/STATE.md \
   src/engine/git.md
gcmsg "engine: reprend les missions avec une passation vérifiée"
```

**Contient** : unité walk précédente, passation append-only par tentative, empreintes après restauration,
relecture validée, sélection ou exclusion jusqu'au prompt bridge, double mémoire et contrat mordant.
Le JSON complet préserve les anciens contenus ; seule la projection déterministe admise est réinjectée.
**Ne contient pas** : adaptateur Git réel, enveloppe Prefect/lifecycle, modification du dashboard.
**Tests verts** : **172 passed** sur src/engine, contrat NanoEngine et frontière ; suite complète
**1500 passed, 3 skipped, 7 warnings en 44,03 s**, Python 3.12.9/pithos ; onze STATE et diff-check verts.
**Exécuté** : —

## Proposé le 14:09 — enveloppe Prefect locale

**Intention** : Exécuter une mission sous un cycle Prefect local sans déplacer l'autorité métier.

**Historique observé** : les lots walk et passation ont été exécutés par l'humain : eb028ee puis
daee504, worktree propre au démarrage de cette unité. Les anciennes propositions restent historiques.

```sh
ga src/engine/flow.py \
   src/engine/test_flow.py \
   tests/doubles/engine.py \
   src/engine/MODULE.md \
   src/engine/STATE.md \
   src/engine/git.md
gcmsg "engine: enveloppe les missions dans prefect local"
```

**Contient** : entrée mission à appel unique, contrat MissionRunner, double, budget conservé,
paramètres métier absents de Prefect, résultat non persisté, garde locale des connexions, timeout
de secours natif et tests du SDK réel isolés dans un interpréteur dédié. Aucun retry Prefect.
**Ne contient pas** : adaptateur GreenFinalizer réel, serveur de production, verrou/watchdog lifecycle
ou placement transverse des contrats. Ces besoins restent explicités dans STATE.md.
**Tests verts** : corpus engine/contrat/frontière **185 passed en 11,31 s** avant ajout de la garde locale
de flow ; dernier test_flow sans serveur **13 passed, 1 deselected en 1,19 s** ; coexistence avec les
vrais forks lifecycle après isolation **30 passed en 11,46 s**. Suite complète finale **1514 passed,
3 skipped, 7 warnings en 55,93 s**, Python 3.12.9/pithos. Onze STATE et diff-check verts.
**Preuve** : niveau 5 pour le métier sur doubles ; niveau 6 limité au runtime Prefect local.
**Exécuté** : —
