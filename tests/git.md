# git — commits proposés pour la passe transverse

**Aucun agent ne commite.** Ce fichier **propose** ; un humain **exécute**. Voir
[`AGENTS.md`](../AGENTS.md) § 7.

⚠️ **Cet emplacement est une extension du § 7, à arbitrer** !
→ `AGENTS.md` § 7 range les propositions dans `src/<module>/git.md`. Le travail ci-dessous n'appartient
à **aucun module** : il peuple `tests/boundaries/` et `tests/contracts/`, que le § 11 exige et qu'aucun
agent de module n'a le droit d'écrire. Faute de foyer, la proposition est ici. Si l'auteur préfère un
autre emplacement, la déplacer — le contenu ne change pas.

Append-only, comme les onze autres : on ajoute, on ne réécrit pas. Une proposition exécutée est
**marquée**, jamais supprimée.

---

## Proposé le 10:09 — rendre la suite du dépôt collectable

**Intention** : donner à `kernel`, `engine` et `lifecycle` le `__init__.py` que les huit autres ont.

```sh
ga src/kernel/__init__.py \
   src/engine/__init__.py \
   src/lifecycle/__init__.py
gcmsg "socle: paquets réguliers pour kernel, engine et lifecycle"
```

**Contient** : trois `__init__.py` qui ne réexportent rien. Sans eux, huit `test_import_boundaries.py`
et sept `test_double_contract.py` entrent en collision de nom de module et `pytest` à la racine
**échoue à la collecte**.
**Ne contient pas** : le déplacement des tests — proposition suivante.
**Tests verts** : `pytest -q` à la racine, 1 157 passed avant l'ajout des tests transverses manquants.
**Exécuté** : —

---

## Proposé le 10:09 — peupler tests/boundaries/ et tests/contracts/

**Intention** : déplacer les quinze tests transverses à l'emplacement qu'`AGENTS.md` § 11 leur assigne.

```sh
# six des quinze fichiers déplacés étaient SUIVIS : la suppression doit être mise en index
git rm --cached src/kernel/test_double_contract.py src/kernel/test_import_boundaries.py \
                src/verifier/test_double_contract.py src/verifier/test_import_boundaries.py \
                src/workspace/test_double_contract.py src/workspace/test_import_boundaries.py
ga tests/conftest.py \
   tests/contracts/ \
   tests/boundaries/
gcmsg "tests: frontières et contrats à l'emplacement exigé par AGENTS.md § 11"
```

**Contient** : les 15 fichiers déplacés et renommés à un nom unique, `tests/conftest.py` (le chargeur
de doubles, écrit une fois au lieu d'être réécrit dans chaque module), `tests/contracts/conftest.py`
(les événements typés du corpus), et cinq corrections d'arithmétique de chemin rendues nécessaires par
le déplacement — `broker` et `engine` dérivaient leur racine de `parents[1]`.
**Corrige aussi** : un test d'`engine` devenu **vert par vacuité** (il balayait un répertoire sans
code), et un dict indexé par *basename* qui rendait `observatory/__init__.py` invisible à son propre
test de frontière — `observatory/api/__init__.py` l'écrasait. Le motif est corrigé dans les cinq tests
qui le partageaient.
**Ne contient pas** : les cinq tests transverses manquants — proposition suivante.
**Tests verts** : `pytest -q` à la racine → 1 186 passed, 2 skipped.
**Exécuté** : —

---

## Proposé le 10:09 — les cinq tests transverses qui manquaient

**Intention** : compléter le § 11 pour les trois modules sans frontière et les deux doubles sans contrat.

```sh
ga tests/boundaries/test_journal.py \
   tests/boundaries/test_bridge.py \
   tests/boundaries/test_lifecycle.py \
   tests/contracts/test_journal_double.py \
   tests/contracts/test_bridge_double.py
gcmsg "tests: frontières de journal, bridge et lifecycle, contrats de journal et bridge"
```

**Contient** : les trois graphes d'imports manquants — dont celui qui tient la **deuxième règle du
§ 3**, `bridge` n'importe jamais `engine` — et les deux corpus de contrat manquants. Le corpus de
`bridge` exclut explicitement le transport : `call` et `probe` parlent à un serveur, et leur borne au
loopback est testée par `src/bridge/test_client.py`.
**Ne contient pas** : les mises à jour de `STATE.md` et de `QUICK_CATCH.md` — proposition suivante.
**Tests verts** : `pytest -q` à la racine → **1 215 passed, 3 skipped**, venv `pithos`, Python 3.12.9.
**Exécuté** : —

---

## Proposé le 10:09 — remettre la mémoire du dépôt d'aplomb

**Intention** : faire dire aux documents de reprise ce que la mesure dit, et non ce qu'ils supposaient.

```sh
ga docs/QUICK_CATCH.md \
   src/*/STATE.md
gcmsg "docs: état de reprise et quick catch alignés sur la mesure du 10:09"
```

**Contient** : `QUICK_CATCH.md`, qui annonçait *« aucune ligne de code écrite »* pour 4 916 L livrées ;
les onze `STATE.md` avec leur entrée de journal de la passe ; la résolution des douze blocages
d'emplacement ; et cinq en-têtes corrigés à la mesure — `kernel`, `verifier`, `workspace`, `engine` et
`lifecycle` portaient `Lignes : 0` et le statut `non commencé` avec du code vert.
**Ne contient pas** : aucune case de « Fini quand » n'a été cochée à la place d'un agent de module. La
passe n'a observé que ce qu'elle a mesuré.
**Tests verts** : sans objet — aucun code touché. Liens relatifs vérifiés : aucun cassé.
**Exécuté** : —

---

## Point d'hygiène signalé, non corrigé

**27 fichiers `__pycache__/*.pyc` sont suivis par git** et `.gitignore` ne les couvre pas. La passe les
a effacés en nettoyant l'arbre, puis **restaurés à l'octet près** depuis `HEAD` — l'arbre est intact.

Ce n'est pas au périmètre de cette passe de le corriger, mais c'est un vrai défaut : un `.pyc` suivi
change à chaque exécution de test et pollue tout diff. La forme qui le règle :

```gitignore
__pycache__/
*.py[cod]
```

suivie d'un `git rm -r --cached` sur les 27 fichiers. **À arbitrer par l'auteur**, comme le point ouvert
de `.gitignore` sur `docs/` et `resources/` déjà consigné dans `QUICK_CATCH.md`.


---

## 11:09 — foyer officialisé et propositions actualisées

AGENTS § 14 donne désormais ce foyer à la passe transverse et autorise ses fichiers documentaires.
Les propositions du 10:09 restent comme historique **non exécuté**. Les lots suivants remplacent
leurs listes de fichiers pour les chemins communs : ne pas exécuter les deux séries successivement.
Les suppressions de tests locaux et les paquets réguliers proviennent de la passe précédente ;
ils sont inclus explicitement pour que les tests partagés soient reprenables.

**Précondition de revue** : la suite a été testée sur le worktree complet, qui contient déjà beaucoup
de code métier non suivi. Les lots ci-dessous ne mettent pas ce code métier en index : ses propositions
restent dans `src/<module>/git.md`. Ils ne sont donc pas, à eux seuls, un snapshot complet clonable.
Relire et ordonner les propositions des modules avant de créer l’historique ; aucune de ces commandes
n’a été exécutée par l’agent. L’ajout de `.gitignore` du lot d’hygiène rend les documents ajoutables.

## Proposé le 11:09 — preuves des frontières partagées

**Intention** : rendre les tests de frontière du dépôt non vacuement verts.

```sh
git rm --cached -- src/kernel/test_double_contract.py \
   src/kernel/test_import_boundaries.py \
   src/verifier/test_double_contract.py \
   src/verifier/test_import_boundaries.py \
   src/workspace/test_double_contract.py \
   src/workspace/test_import_boundaries.py
ga conftest.py \
   tests/__init__.py \
   tests/conftest.py \
   tests/support.py \
   tests/test_support.py \
   tests/graph.py \
   tests/test_graph.py \
   tests/test_boundary_scans.py \
   tests/boundaries/test_bridge.py \
   tests/boundaries/test_broker.py \
   tests/boundaries/test_campaign.py \
   tests/boundaries/test_engine.py \
   tests/boundaries/test_journal.py \
   tests/boundaries/test_kernel.py \
   tests/boundaries/test_lifecycle.py \
   tests/boundaries/test_observatory.py \
   tests/boundaries/test_refinery.py \
   tests/boundaries/test_verifier.py \
   tests/boundaries/test_workspace.py \
   tests/contracts/conftest.py \
   tests/contracts/test_bridge_double.py \
   tests/contracts/test_broker_double.py \
   tests/contracts/test_campaign_double.py \
   tests/contracts/test_journal_double.py \
   tests/contracts/test_kernel_double.py \
   tests/contracts/test_observatory_double.py \
   tests/contracts/test_refinery_double.py \
   tests/contracts/test_verifier_double.py \
   tests/contracts/test_workspace_double.py \
   src/kernel/__init__.py \
   src/engine/__init__.py \
   src/lifecycle/__init__.py \
   src/journal/conftest.py \
   src/verifier/conftest.py \
   src/bridge/conftest.py \
   src/workspace/conftest.py \
   src/engine/conftest.py \
   src/campaign/conftest.py \
   src/lifecycle/conftest.py \
   src/broker/conftest.py \
   src/observatory/conftest.py
gcmsg "tests: prouver les frontières partagées par injection"
```

**Contient** : paquets et migration préexistants, chargeur frais commun, fixtures spécifiques conservées,
scanner récursif non vide, politiques de chaque module, chemins complets, corpus de signatures et
leurs mutants. Les injections travaillent seulement sur copies et doubles isolés.
**Ne contient pas** : implémentations métier, métrique documentaire, modifications d’index des caches.
**Tests verts** : suite entière Python 3.12.9 / pithos — 1 286 passed, 3 skipped, 7 warnings en 34,59 s ; les trois skips concernent
les variantes réelles des scénarios propres aux doubles. Les 25 sondes de balayage passent.
**Exécuté** : —

## Proposé le 11:09 — mémoire du dépôt contrôlée par mesure

**Intention** : détecter mécaniquement les en-têtes de reprise périmés.

```sh
ga tests/state_check.py \
   tests/test_state_check.py \
   AGENTS.md \
   CLAUDE.md \
   TEMPO.md \
   docs/QUICK_CATCH.md \
   docs/ROADMAP.md \
   docs/EXPLANATIONS.md \
   src/kernel/STATE.md \
   src/journal/STATE.md \
   src/verifier/STATE.md \
   src/bridge/STATE.md \
   src/workspace/STATE.md \
   src/engine/STATE.md \
   src/campaign/STATE.md \
   src/lifecycle/STATE.md \
   src/broker/STATE.md \
   src/observatory/STATE.md \
   src/refinery/STATE.md \
   tests/STATE.md \
   tests/git.md
gcmsg "tests: contrôler les états de reprise par mesure et empreinte"
```

**Contient** : comptage AST/tokenize, validation des champs et plafonds, onze en-têtes actualisés,
historique préservé, rôle transverse AGENTS/CLAUDE, TEMPO annoté, reprise et documentation courantes.
**Ne contient pas** : changement de cible numérique, statut fini attribué à un module, code métier.
**Tests verts** : `tests/test_state_check.py` et suite complète — 1 286 passed, 3 skipped, 7 warnings en 34,59 s ;
`PYTHONDONTWRITEBYTECODE=1 python -m tests.state_check` valide les onze modules.
**Exécuté** : —

## Proposé le 11:09 — arrêter de suivre les caches Python

**Intention** : retirer les caches Python de l’index en conservant les fichiers sur disque.

```sh
git rm --cached -- src/bridge/__pycache__/__init__.cpython-312.pyc \
   src/bridge/__pycache__/client.cpython-312.pyc \
   src/bridge/__pycache__/conftest.cpython-312-pytest-8.4.2.pyc \
   src/bridge/__pycache__/probe.cpython-312.pyc \
   src/bridge/__pycache__/revalidate.cpython-312.pyc \
   src/bridge/__pycache__/schema.cpython-312.pyc \
   src/bridge/__pycache__/test_client.cpython-312-pytest-8.4.2.pyc \
   src/bridge/__pycache__/test_interface.cpython-312-pytest-8.4.2.pyc \
   src/bridge/__pycache__/test_probe.cpython-312-pytest-8.4.2.pyc \
   src/bridge/__pycache__/test_revalidate.cpython-312-pytest-8.4.2.pyc \
   src/bridge/__pycache__/test_schema.cpython-312-pytest-8.4.2.pyc \
   src/journal/__pycache__/__init__.cpython-312.pyc \
   src/journal/__pycache__/conftest.cpython-312-pytest-8.4.2.pyc \
   src/journal/__pycache__/read.cpython-312.pyc \
   src/journal/__pycache__/redact.cpython-312.pyc \
   src/journal/__pycache__/test_interface.cpython-312-pytest-8.4.2.pyc \
   src/journal/__pycache__/test_read.cpython-312-pytest-8.4.2.pyc \
   src/journal/__pycache__/test_redact.cpython-312-pytest-8.4.2.pyc \
   src/journal/__pycache__/test_write.cpython-312-pytest-8.4.2.pyc \
   src/journal/__pycache__/write.cpython-312.pyc \
   src/kernel/__pycache__/codeview.cpython-312.pyc \
   src/kernel/__pycache__/contracts.cpython-312.pyc \
   src/kernel/__pycache__/errors.cpython-312.pyc \
   src/kernel/__pycache__/facts.cpython-312.pyc \
   tests/doubles/__pycache__/bridge.cpython-312.pyc \
   tests/doubles/__pycache__/journal.cpython-312.pyc \
   tests/doubles/__pycache__/kernel.cpython-312.pyc
ga .gitignore
gcmsg "repo: retirer les caches python de l’index"
```

**Contient** : les 27 chemins exacts encore suivis ; `__pycache__/` et `*.py[cod]` ignorés ; documents
Markdown de docs/resources désormais visibles, code tiers toujours ignoré.
**Ne contient pas** : suppression de fichiers du filesystem, ajout de documents ou de dépôts tiers.
**Tests verts** : suite complète sans bytecode — 1 286 passed, 3 skipped, 7 warnings en 34,59 s ; aucune différence des
27 caches suivis après les tests. Les effets de cette commande d’index restent **non exécutés**.
**Exécuté** : —

## Proposé le 11:09 — inclure les documents de référence existants

**Intention** : rendre les documents de référence existants disponibles au prochain clone.

```sh
ga docs/PROJECT.md \
   docs/ARCHITECTURE.md \
   resources/IMPORT_REPORT.md \
   resources/MANIFEST.md \
   resources/kilocode.md \
   resources/langfuse.md \
   resources/openhands.md \
   resources/ouroboros.md \
   resources/pi.md \
   resources/prime-agent.md \
   resources/swe-agent.md \
   resources/unsloth.md \
   resources/villani.md
gcmsg "docs: inclure le cadrage et les références markdown existants"
```

**Contient** : PROJECT, ARCHITECTURE et les onze Markdown de resources, rendus visibles par le lot
précédent. Leur contenu préexistant n’est pas réécrit par cette passe. Les trois documents de reprise
mis à jour font partie du lot « mémoire du dépôt ».
**Ne contient pas** : code des neuf dépôts tiers, données brutes, dépendances installées.
**Tests verts** : les documents n’ajoutent aucun code exécuté ; suite complète verte ci-dessus,
liens relatifs contrôlés. La vérité historique de chaque référence n’est pas réauditée ici.
**Exécuté** : —

## Proposé le 12:09 — contrat partagé de la gate de faits

**Intention** : éprouver l'interface complète de verifier dans les contrôles transverses.

```sh
ga tests/contracts/test_verifier_double.py \
   tests/boundaries/test_verifier.py
gcmsg "tests: couvre le contrat de vérification des faits"
```

**Contient** : signatures de run et Protocol Verifier ; autorisation stdlib re dans la frontière.
**Prérequis** : proposition verifier du 12:09 et faits canoniques kernel avec producteurs.
**Tests verts** : 134 tests verifier/contrat/frontière ; suite complète 1 367 passed, 3 skipped,
7 warnings en 37,10 s. Les injections du balayage et la mutation de signature restent vertes.
**Exécuté** : —

## Proposé le 12:09 — reprise documentaire après la chaîne de faits

**Intention** : rendre l'état livré et la prochaine définition produit explicites.

```sh
ga README.md \
   docs/QUICK_CATCH.md \
   docs/ROADMAP.md \
   docs/EXPLANATIONS.md \
   tests/STATE.md \
   tests/git.md
gcmsg "docs: actualise la reprise après la gate de faits"
```

**Contient** : état README corrigé, mesures et preuve finale, journal des résultats négatifs,
prochaines étapes et arbitrage de source candidate en attente. Les STATE métier sont proposés dans leurs modules.
**Ne contient pas** : changement du cadrage PROJECT, réponse implicite à l'arbitrage ni campagne réelle.
**Tests verts** : suite complète 1 367 passed, 3 skipped, 7 warnings en 37,10 s ; onze en-têtes mesurés,
whitespace contrôlé ; bytecodes suivis inchangés. Aucun test supplémentaire pour ces textes seuls.
**Exécuté** : —

## Proposé le 13:09 — éprouver les contrats de la nano-étape

**Intention** : Contrôler les frontières publiées par la nano-étape et vérifier le banc sur disque.

```sh
ga tests/contracts/test_engine_double.py \
   tests/contracts/test_verifier_double.py \
   tests/test_visualizer_trial.py
gcmsg "tests: éprouve la nano-étape et son banc audio"
```

**Contient** : Contrat NanoEngine avec mutation de signature, preflight dans Verifier, trois scénarios de fichiers/reçus et deux refus de dépôt cible. Prérequis : lots métier et banc audio.
**Tests verts** : tests/contracts/test_engine_double.py, tests/contracts/test_verifier_double.py, tests/test_visualizer_trial.py. Suite complète **1 402 passed, 3 skipped, 7 warnings en 40,64 s** dans Python 3.12.9/pithos.
**Exécuté** : —

## Proposé le 13:09 — consigner le cadrage audio approuvé

**Intention** : Rendre la décision de code candidat et la reprise du banc audio explicites.

```sh
ga AGENTS.md \
   CLAUDE.md \
   .gitignore \
   README.md \
   docs/PROJECT.md \
   docs/QUICK_CATCH.md \
   docs/ROADMAP.md \
   docs/EXPLANATIONS.md \
   tests/STATE.md \
   tests/git.md
gcmsg "docs: consigne le banc audio et le code candidat autorisé"
```

**Contient** : Amendement utilisateur du 12:09, preuves et limites, prochaines commandes humaines ; runs et workspace ignorés sans suppression. Les propositions antérieures restent historiques et doivent être composées avant staging des mêmes fichiers.
**Tests verts** : Suite complète et tests.state_check ; AGENTS/CLAUDE comparés octet par octet. Suite complète **1 402 passed, 3 skipped, 7 warnings en 40,64 s** dans Python 3.12.9/pithos.
**Exécuté** : —


## Proposé le 13:09 — vérifier les nouvelles frontières de lecture

**Intention** : Contrôler le contrat publié par la collection directe des essais.

```sh
ga tests/boundaries/test_bridge.py \
   tests/boundaries/test_observatory.py \
   tests/contracts/test_observatory_double.py
gcmsg "tests: contrôle les frontières de la projection des essais"
```

**Contient** : Contrat build_run_index et snapshot de flatten_tree, dépendances stdlib explicites pour télémétrie et lecture des sidecars ; interdits métier conservés. Prérequis : lots bridge et observatory.
**Tests verts** : tests/boundaries/test_bridge.py, tests/boundaries/test_observatory.py, tests/contracts/test_observatory_double.py. Suite complète : **1 444 passed, 3 skipped, 7 warnings en 43,83 s**, Python 3.12.9/pithos ; contrôle des onze STATE vert.
**Exécuté** : —


## Proposé le 13:09 — contrôler les interfaces documentées

**Intention** : Détecter les signatures livrées qui divergent de la documentation.

```sh
ga tests/doc_check.py \
   tests/test_doc_check.py \
   docs/ARCHITECTURE.md
gcmsg "tests: contrôle les interfaces documentées livrées"
```

**Contient** : Inventaire explicite livré/prévu, analyse AST sans eval, contrôle des noms, de l'ordre et de l'obligation des paramètres. Vingt interfaces livrées couvrent onze modules ; types et valeurs par défaut restent hors du contrôle.
**Tests verts** : tests/test_doc_check.py : 8 tests, signatures divergentes et inventaire vide refusés. Suite complète : **1 444 passed, 3 skipped, 7 warnings en 43,83 s**, Python 3.12.9/pithos ; contrôle des onze STATE vert.
**Exécuté** : —


## Proposé le 13:09 — documenter la livraison de l'observatoire

**Intention** : Rendre la livraison observabilité reprenable avec ses preuves.

```sh
ga README.md \
   docs/QUICK_CATCH.md \
   docs/ROADMAP.md \
   docs/EXPLANATIONS.md \
   resources/GVS5H.md \
   resources/graphify.md \
   resources/IMPORT_REPORT.md \
   resources/MANIFEST.md \
   tests/STATE.md \
   tests/git.md
gcmsg "docs: consigne les preuves de l'observatoire"
```

**Contient** : Commandes locales, résultat réel négatif, limites de preuve, décisions J/K et références relues. Aucun dépôt tiers ni artefact brut inclus. Les documents partagés portent aussi les travaux antérieurs et l'entrée TUI : composer leurs propositions avant staging.
**Tests verts** : Contrôle des interfaces et des STATE, revue des liens et du diff ; huit tests web et build verts. Suite complète : **1 444 passed, 3 skipped, 7 warnings en 43,83 s**, Python 3.12.9/pithos ; contrôle des onze STATE vert.
**Exécuté** : —
