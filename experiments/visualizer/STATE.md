# STATE — banc audio

**Statut** : en cours
**Mise à jour** : 13:09

## Prochaine action

Examiner la sensibilité du critère idempotent sur trial-44kcg6ig : ses trois variantes passent,
donc aucun reçu n'est autorisé. Conserver cet essai et traiter toute évolution du catalogue dans
verifier après lecture de son contrat. Le marcheur avec réconciliation reprend dans engine/STATE.md ;
le dépôt d'essai possède déjà son HEAD et ne doit pas être réinitialisé.

## Avancement

- [DONE] Cadrage inspiré du visualiseur : fonction scalaire compatible avec le catalogue actuel.
- [DONE] Exécuteur transactionnel réutilisable dans engine, schéma candidat dans bridge.
- [DONE] Régressions avec effets disque réels : vert, invariant rouge, refus du reçu.
- [DONE] Sonde structurée sur le modèle Ollama prévu, sans changer son installation.
- [DONE] Copie exacte du seed prête pour le dépôt Git dédié ; commandes humaines préparées.
- [DONE] Nano-étape avec génération candidate et observations Git réelles : rejet tautology conservé.
- [TODO] Marcheur complet et reprise après interruption : suite dans engine/STATE.md.

## Journal

### 12:09 — trois trajectoires sur copies

Les composants engine, workspace, verifier et journal sont réels. Le modèle rend une réponse scénarisée ;
Git est un double qui décrit le diff des octets effectivement relus. Aucun dépôt Git créé.

| Cas | Répertoire sous runs/ | Résultat | Durée mesurée |
|---|---|---|---:|
| vert | selftest-6p3i74o8 | passed, fichier modifié, reçu écrit | 0,568 s |
| invariant rouge | selftest-9y_zhkhg | blocked / invariant_failed, octets restaurés, aucun reçu | 0,367 s |
| refus du reçu | selftest-6xmb9fyx | blocked / receipt_not_written, octets restaurés, aucun reçu | 0,607 s |

SHA avant : `40818e8d40d125b69d8e75dff8fcaab1040dace8d87e7e06b9d8362fba577bf5`.
SHA après vert : `ac2d9e018da6892817a21bef7b16ffb69d31da3c840e371f4896a308db5c1462`.
Les deux échecs retrouvent exactement le SHA avant. Le vert et le refus du reçu ont chacun trois
artefacts de gate : seed rouge, candidat vert, mutant rouge. Ce constat ne prouve que l'idempotence,
pas la conformité complète à l'intervalle audio attendu.
**Niveau de preuve : 5** pour cette composition avec doubles ; effets fichiers effectivement observés.

### 13:09 — modèle local et preuve négative conservée

La sonde sans fenêtre a refusé le démarrage dans le sandbox (`probe-hl_m8m7f`), puis hors sandbox
(`probe-nm_07u0h`). Le diagnostic HTTP conservé dans ce second répertoire constate un statut 200
et le modèle attendu dans la liste ; aucune métadonnée de fenêtre n'y figure.
La commande `ollama show pithos/ling-3.0-tiny:8b-16k --parameters` rend `num_ctx 16384`.
Cette valeur est transmise explicitement par PITHOS_CONTEXT_WINDOW, avec provenance asserted.

Premier appel réel (`probe-41ado4z2`) : **truncated**, 128 tokens générés entièrement dans le thinking,
contenu inexploitable vide. Après consigne explicite et réserve de 1 024 tokens, toujours sous 60 s,
`probe-z20hc14z` rend **completed / stop**, un Criterion revalidé et **358 tokens de completion**,
223 tokens de prompt (581 au total, usage rendu par la route). Les deux requêtes et réponses restent
dans leurs journaux. Aucun taux de fiabilité n'est extrapolé depuis cette observation.
**Niveau de preuve : 6 pour cette sonde de critère uniquement**, fenêtre asserted ; aucune génération
de fonction réelle ni nano-étape complète avec Ollama encore démontrée.

### 13:09 — régressions permanentes

`tests/test_visualizer_trial.py` : **5 passed en 3,01 s**. Les tests relisent indépendamment fichiers,
reçus et artefacts de gate ; ils refusent aussi le harness et un répertoire sans Git avant appel modèle.
Chaque invocation conserve un nouveau répertoire de preuves. Suite complète de clôture en cours.

## Blocages

| Quoi | Pourquoi | Ce qui débloquerait |
|---|---|---|
| Premier HEAD du dépôt d'essai | AGENTS § 7 interdit toute commande Git d'écriture par l'agent | Résolu le 13:09 par l'opérateur : HEAD 57e47c5 ; trial-44kcg6ig exécuté ensuite, aucune réinitialisation nécessaire |
| Fenêtre absente de /v1/models | Pas de contexte deviné par bridge | Résolu : num_ctx lu via ollama show, transmis comme asserted ; sonde réelle verte |
| Sortie de sonde tronquée | 128 tokens consommés par le thinking | Résolu : consigne explicite et réserve 1 024 ; 358 tokens observés, stop et schéma conforme |

### 13:09 — validation finale du banc audio

Suite complète dans **pithos / Python 3.12.9** : **1 402 passed, 3 skipped, 7 warnings en 40,64 s**.
La suite intermédiaire après run_attempt avait rendu **1 397 passed, 3 skipped, 7 warnings en 37,46 s**.
Les cinq tests ajoutés relisent effets disque, reçus et artefacts du banc ; aucun nouveau skip.
Skips : variantes réelles non scénarisables bridge/campaign/refinery. Warnings Starlette/httpx et
fork après threads conservés. Les onze mesures STATE passent : **4 570 code, 7 106 physiques**.
Aucune dépendance installée ni commande Git d'écriture. Aucun module déclaré fini.
**Niveau de preuve : 5** sur contrats et composition ; la sonde de critère Ollama, mesurée séparément,
atteint le niveau 6 pour ce seul appel. Le premier trial réel attend le HEAD du dépôt dédié.

### 13:09 — contrôle final de livraison

`git diff --check` passe. Les 21 fichiers nouveaux/documentaires relus n'ont ni espace de fin de
ligne ni lien relatif cassé ; AGENTS et CLAUDE sont identiques. Les **27 pyc suivis sont inchangés**
par rapport à HEAD. Les **17 rapports** conservés sous runs sont des JSON lisibles. La copie du seed
est exacte et son dépôt reste non initialisé. Aucun index, commit, branche ni dépôt tiers modifié.
Propositions prêtes dans les git.md de module, tests et experiments/visualizer ; aucune exécutée.
**Niveau de preuve : 3** pour les comparaisons d'octets et les fichiers, 2 pour le format JSON.


### 13:09 — entrée Pithos et TUI préparés

Demande explicite : ajouter `src/main.py` avec les arguments du banc et des panneaux fixes.
Le point d'entrée et `src/tui.py` sont préparés sur copie, avec parseur partagé dans run.py.
Les panneaux relisent les traces ; les compteurs ne doublonnent pas l'usage bridge/engine.
Aucune dépendance ajoutée, aucune implémentation métier ni commande Git d'écriture.

Tests d'abord : collecte rouge attendue faute du module tui ; première copie corrigée car le filtre
workspace avait aussi omis src/workspace. Première passe : **2 failed, 19 passed en 5,66 s**, les espaces
internes des titres étaient remplacés par des traits. Après correction : **21 passed en 5,59 s**.
Avec le test de vrai SIGINT en pseudo-terminal : **22 passed en 6,08 s**, Python 3.12.9/pithos.
Le signal arrive après une modification effectivement relue ; les octets initiaux sont retrouvés,
result.json est durable, le processus rend 130 et le curseur est restauré. Bridge reste scénarisé.
**Niveau de preuve : 5** pour le banc ; **6** limité au pseudo-terminal, signal et filesystem locaux.

Suite complète sur copie dans la sandbox : **3 failed, 1387 passed, 3 skipped, 40 errors en 34,18 s**.
Les 40 erreurs sont des binds HTTP locaux interdits ; deux échecs lifecycle concernent les empreintes
macOS indisponibles. Le troisième (`tests/test_state_check.py::test_repository_state_headers_match_current_production`)
concerne l'en-tête engine de la copie, pendant un chantier parallèle. Le contrôle STATE de cette copie
signale 652/904 déclarées contre 673/930 mesurées et une empreinte périmée. Aucun résultat supprimé.
Le dépôt courant a depuis un nouvel en-tête engine ; la validation finale doit s'y faire après intégration.

**Prochaine action pour cette entrée** : exécuter la suite complète hors sandbox sur le dépôt courant,
puis tests.state_check, revue du diff et ajout de la proposition git.md si les contrôles passent.
La prochaine action métier en tête de ce STATE reste distincte du lanceur.


### 13:09 — entrée TUI livrée et vérifiée dans le dépôt courant

L'intégration conserve les changements parallèles des autres modules. La première suite hors sandbox
sur le dépôt courant rend **1 443 passed, 3 skipped, 7 warnings en 44,64 s**. Les onze en-têtes STATE
passent ; l'écart engine constaté sur l'ancienne copie est résolu dans le chantier parallèle.

La revue finale a ajouté un dernier prélèvement de l'état avant fermeture de l'écran, suivi d'un résumé
sur stderr en terminal interactif : les tokens reçus juste avant la fin d'un run restent visibles.
Le test retient le rafraîchissement périodique puis publie l'usage ; les 120 tokens de la fixture sont
retrouvés dans la dernière frame et dans le résumé. **23 tests ciblés passent en 6,21 s**.

**Suite finale : 1 444 passed, 3 skipped, 7 warnings en 44,62 s**, Python **3.12.9 / pithos**,
sans bytecode ni cache pytest. Skips : variantes réelles bridge/campaign/refinery sans scénario de double.
Avertissements : Starlette/httpx et six forks après threads. Aucun skip ajouté par ce chantier.
`python -m tests.state_check` passe pour les onze modules ; `git diff --check` passe.
Les dix fichiers ajoutés/modifiés sont relus, sans blancs finaux. Les fichiers d'entrée hors modules
comptent **10 code / 19 physiques pour src/main.py**, **219 code / 262 physiques pour src/tui.py**.

La relecture du trial historique `trial-44kcg6ig` donne 2 appels, 1 tour candidat, 499 tokens d'entrée,
1 962 de sortie, 2 461 au total, 2 activités outils et 0 reçu. Il s'agit d'une projection des preuves
existantes, pas d'un nouvel essai Ollama. Le nouveau TUI est vérifié avec modèle scénarisé et vrai PTY.
**Niveau de preuve : 5** pour l'intégration ; **6** limité au terminal, SIGINT et filesystem locaux.

**État de cette entrée : livré.** Commande de reprise opérateur :
`PYTHONDONTWRITEBYTECODE=1 python src/main.py selftest --case green` ; pour l'essai réel,
reprendre les prérequis et la commande `trial` du README. Le marcheur et sa réconciliation restent
les prochaines actions métier d'engine. Le statut du banc n'est pas requalifié par cette livraison UI.
Les propositions de commit sont ajoutées à git.md ; aucune exécutée, aucune preuve supprimée.

### 13:09 — trial réel relu dans le dashboard

Le HEAD 57e47c5 a été créé par l'opérateur avant trial-44kcg6ig. Engine, workspace, verifier,
journal, bridge et les observations Git sont réels dans cet essai : **blocked / invariant_failed /
tautology**, **35,021147958992515 s**, **0 reçu**. Le candidat borne le niveau avec min/max ;
l'invariant passe après splice, mais les trois variantes passent aussi. Ce refus démontre
l'insuffisante sensibilité de la validation ; il ne démontre pas que le candidat est faux.

Les cinq gates et sept événements restent intacts. SHA avant/après :
40818e8d40d125b69d8e75dff8fcaab1040dace8d87e7e06b9d8362fba577bf5.
Deux appels rapportent 2 461 tokens, sans troncature ; fenêtre 16 384 de provenance asserted.
Le dashboard http://127.0.0.1:5173 expose état, gates, contexte, timeline et artefacts en lecture seule.
Lecture HTTP réelle vérifiée, mais contrôle visuel non obtenu faute de navigateur accessible.

Suite commune **1 444 passed, 3 skipped, 7 warnings en 43,83 s**, Python 3.12.9/pithos ;
huit tests web et build verts. **Niveau 6 pour la relecture des effets de cet essai réel**,
sans nouveau trial Ollama, premier vert réel ni marcheur complet revendiqué.


### 13:09 — documentation TUI regroupée dans src

À la demande explicite de l'utilisateur, création de `src/TUI.md` et `src/GIT.md`.
TUI.md décrit les commandes, panneaux, sources des métriques, sorties et interruption,
avec les limites et preuves de la livraison. GIT.md reprend la proposition du banc comme
un seul lot, ajoute les deux documents et conserve l'historique précédent.
Contenu, blocs Markdown et liens locaux vérifiés. Les mesures de tests citées sont celles
archivées à la livraison ; aucune nouvelle suite métier lancée pour ces documents.
**Niveau de preuve : 2** pour les contrôles documentaires. Aucun code ni index Git modifié.
**Prochaine action documentaire** : consulter src/TUI.md pour lancer le banc ; l'opérateur
relit src/GIT.md et les fichiers complets avant toute mise en version.
