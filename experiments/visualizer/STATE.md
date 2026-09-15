# STATE — banc audio

**Statut** : en cours
**Mise à jour** : 15:09

## Prochaine action

Premier vert livré dans trial-25ugxn94 : conserver le fichier workspace corrigé pour revue et commit par l’opérateur. Avant une mission composée Ollama, vérifier la disponibilité d’un nouveau dépôt initialisé avec le seed intact et utiliser un nouveau --run ; ne pas réinitialiser le workspace vert.

## Avancement

- [DONE] Cadrage inspiré du visualiseur : fonction scalaire compatible avec le catalogue actuel.
- [DONE] Exécuteur transactionnel réutilisable dans engine, schéma candidat dans bridge.
- [DONE] Régressions avec effets disque réels : vert, invariant rouge, refus du reçu.
- [DONE] Sonde structurée sur le modèle Ollama prévu, sans changer son installation.
- [DONE] Copie exacte du seed prête pour le dépôt Git dédié ; commandes humaines préparées.
- [DONE] Nano-étape avec génération candidate et observations Git réelles : rejet tautology conservé.
- [DONE] Marcheur/flow, finalisation Git et reprise sous lifecycle : modèle seul simulé dans le test intégré.

- [DONE] Relation unit_projection : bornes exactes, contre-exemples et reprise des anciens critères.
- [DONE] Premier vert Ollama trial-25ugxn94 : reçu durable, effet confirmé, fichier conservé.

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

### 14:09 — commande de mission reprenable

Test d'abord : collecte rouge, mission.py absent (**1 error en 0,15 s**). Après composition :
**2 passed en 19,11 s**. Après ajout coupure et orphelin : suite intégration/lifecycle/contrat
**46 passed en 29,70 s**. Le serveur Prefect temporaire est local et sans analytics ; le modèle
est le seul composant simulé. Tous les Git d'écriture des tests portent sur tmp_path.

- Vert : source modifiée, reçu durable, HEAD nouveau propre, deux commits au total (seed + vert).
- Acquittement perdu : arbre passed non finalisé après commit ; reprise sur même --run sans
  sonde/candidat supplémentaire, un seul reçu et un seul commit de finalisation.
- Rouge : aucun reçu ni commit, retour exact aux octets seed.
- Coupure OS après splice : running et candidat constatés ; reprise sans modèle, restauration
  exacte et blocage interrupted. La coupure ne fabrique aucun reçu.
- Parent tué : le worker orphelin est moissonné avant l'admission suivante.

La commande historique trial reste une tentative sans commit. La nouvelle mission est explicitement
un cycle walk/flow avec commit local via broker, sans push, PR ou Telegram. Le modèle local et le
serveur Prefect de l'opérateur n'ont pas été sollicités ; trial-44kcg6ig reste un refus tautology.
**Niveau de preuve : 5 pour la mission complète**, 6 limité aux composants locaux réellement utilisés.

### 14:09 — livraison intégrée vérifiée

Suite complète finale : **1 548 passed, 3 skipped, 7 warnings en 87,81 s**, Python **3.12.9 / pithos**,
hors sandbox. Les trois skips existants restent bridge:77, campaign:170, refinery:82 (scénarios
propres aux doubles) ; warnings Starlette/httpx et les six anciens forks après threads.
Contrôle des onze STATE et `git diff --check` verts. Aucun paquet installé, aucun Git d'écriture
sur le harness ou le dépôt de campagne, aucun service opérateur sollicité, dashboard intact.
Les effets Git réels sont limités aux dépôts temporaires des tests. Le test d'intégration garde
le modèle simulé : le premier vert Ollama reste à démontrer, trial-44kcg6ig demeure négatif.
**Niveau de preuve : 5 pour la mission complète**, **6 limité aux composants locaux** effectivement
exercés. La commande et la reprise sur même --run sont décrites dans experiments/visualizer/README.md.

### 14:09 — contre-preuve finale : groupe d'invariant détaché

La revue de src/verifier/runner.py:113 constate start_new_session=True. La sonde jetable
/private/tmp/test_pithos_detached.py reproduit ce lancement sous MissionProcess : **1 failed en
2,22 s**, le groupe d'invariant survit à la coupure du worker. La sonde nettoie ensuite explicitement
son groupe ; aucun processus de ce diagnostic n'est laissé en marche.

Cette contre-preuve limite la suite verte précédente : le scénario cut suspendait verifier.run
avant le spawn réel et ne couvrait pas ses groupes séparés. Le groupe du worker et ses descendants
restant dans ce groupe sont bien récoltés ; l'arrêt de tous les groupes du verifier n'est PAS prouvé.
La composition n'est donc pas prête pour un essai opérateur. GreenFinalizer reste vérifié indépendamment.

Correction requise : admission durable et récolte des groupes séparés d'invariants, sans modifier
les critères, les entrées, les gates ou l'autorité du reçu. Le port de lancement correspondant manque
à verifier. L'extension du périmètre à src/verifier a été demandée à l'utilisateur conformément à
AGENTS.md § 6 ; aucune production verifier n'a été modifiée avant sa réponse.
**Niveau de preuve : 4 pour ce défaut reproduit** ; la preuve positive d'arrêt global est retirée.

### 14:09 — état sûr en attente d'extension de périmètre

Après suspension de l'entrée opérateur : suite complète **1 549 passed, 3 skipped, 7 warnings en
89,05 s**, pithos/Python 3.12.9. Le nouveau test constate le refus AVANT création de preuves ou
worker. STATE et diff-check verts. Cette suite ne résout pas la sonde négative du groupe détaché
(1 failed en 2,22 s) : la composition reste suspendue et l'accord src/verifier reste en attente.
GreenFinalizer demeure livrable indépendamment ; les propositions de composition restent suspendues.

### 14:09 — gates sous custody, contre-preuve traitée

Le port contextuel verifier couvre baseline, candidat et mutants. Le superviseur lance un gardien
par gate, écrit sa custody avant admission, puis récolte son groupe sous la plus petite deadline.
Worker et gardiens ont le même propriétaire ; sa disparition permet leur sweep par le détenteur
suivant du verrou. Le runner garde l'autorité sur le rapport, les codes 0/20 et le reçu.
Aucun nouveau protocole réseau ni dépendance ; l'IPC réutilise le pipe du worker.

Résultats intermédiaires conservés : **20 passed in 5.62s** (lifecycle/frontière), puis **2 failed,
11 passed in 34.78s**. La gate réelle était arrêtée mais le worker recevait encore un retour à la
deadline globale : il pouvait restaurer avant la coupure. Le superviseur ne répond plus après cette
borne. L'autre rouge révélait une injection de signature sur une copie différente du double ; le
contrôle reçoit désormais l'instance mutée. Relance : **1 failed, 23 passed in 42.68s** ; tous les
scénarios intégrés passent, le seul rouge est un NameError dans le nouveau test d'admission (assertions
placées dans le mauvais test, corrigées avant la reprise). Aucun résultat négatif n'est effacé.

La CLI est réouverte après les preuves de vraie gate coupée et d'orphelin récupéré ; vérification de
son entrée réelle en cours, puis suite complète. L'isolation reste celle des groupes gérés par le
harness ; elle ne confine pas un programme hostile créant lui-même une session.
**Niveau de preuve : 5 pour la mission complète** (modèle simulé), **6 pour les effets locaux** observés.

### 14:09 — custody des gates livrée et mission réouverte

L'autorisation est confirmée explicitement : « Oui, étendre à verifier ». Les critères, les entrées,
les gates et l'autorité du reçu restent inchangés. Seul le lancement passe par le port sous custody.

- Tests ciblés : **23 passed in 44.47s**. Chaque invariant produit correspond à un gardien admis
  dans la custody commune. Journal refusé : aucun programme de gate lancé.
- Deadline globale pendant la gate réelle : son programme et son descendant sont arrêtés ; le
  candidat et running sont constatés, puis le walk suivant restaure les octets sans appel modèle.
- Superviseur tué pendant une gate réelle : sweep du worker et du gardien avant admission suivante ;
  aucune custody active, aucun descendant encore exécuté et verrou libéré.
- CLI réelle sur le même --run vert : résultat passed/finalized=1, un seul reçu et un seul commit
  de finalisation. Acquittement perdu et refus restent couverts sans double commit ni reçu indu.

Suite complète, Python **3.12.9 / pithos**, sans bytecode ni cache pytest, hors sandbox : **1 556 passed, 3 skipped, 7 warnings en 100,50 s**.
Les skips sont tests/contracts/test_bridge_double.py:77, test_campaign_double.py:170 et
 test_refinery_double.py:82 : variantes réelles sans scénario à charger. Warnings existants :
Starlette/httpx et six occurrences de fork après threads. Contrôle des onze STATE et diff-check verts.
Aucun Git d'écriture sur le harness ou le dépôt opérateur ; les commits de test portent uniquement
sur les dépôts jetables. Aucun nouveau trial Ollama : trial-44kcg6ig reste refusé sur tautology.
Les suspensions de composition du 14:09 sont levées ; leurs contre-preuves restent archivées.

**Niveau de preuve : 5 pour la mission complète**, modèle simulé ; **6 pour les effets locaux**
Git/Prefect/verifier/workspace/journal/lifecycle réellement observés. Les groupes gérés par le harness
ne sont pas une sandbox de code hostile. Le dashboard demeure déclaré terminé pour le moment.

### 15:09 — projection exacte autorisée, test initial rouge

L’utilisateur demande maintenant la projection exacte sur [0, 1]. Le chantier ajoute une relation
fermée unit_projection, sans borne ni tolérance fournie par le modèle. Les nouvelles missions
l’utilisent ; les reprises conservent leur critère et les anciens reçus ne sont pas requalifiés.
Le premier test kernel échoue comme attendu : relation absente du catalogue (1 failed,
81 deselected, 0,15 s). Implémentation et vérifications en cours.
**Niveau de preuve atteint** : 1 à ce point de reprise.

### 15:09 — projection exacte vérifiée, essai local en cours

Validation ciblée : 108 tests kernel/projection en 3,88 s ; 400 tests kernel/verifier,
contrats/frontières et trial en 31,12 s ; 8 tests trial/mission en 46,27 s, dont reprise
idempotent historique, reçu unit_projection, rollback [0, 2] et custody réelle.
Suite complète : 1 600 passed, 3 skipped, 8 warnings en 114,44 s, Python 3.12.9 / pithos.
Un avertissement ajouté par le test (domain copié comme str plutôt qu'enum) a été corrigé ;
la vérification finale reste à consigner. Les trois skips sont les scénarios réservés aux
doubles bridge/campaign/refinery ; les sept avertissements antérieurs restent distincts.

Rejeu archivé : projection-replay-6k9y5dc3, avant rouge/après vert/mutant tué, 44 fichiers
historiques inchangés par SHA-256, aucun reçu et aucun appel Ollama dans ce rejeu.
Le dépôt opérateur est propre et identique au seed. La première lecture Ollama a été refusée
par la sandbox (operation not permitted) ; la lecture autorisée confirme num_ctx 16384.
Une nouvelle tentative trial --seconds 180 est lancée sous unit_projection ; ne pas en
déduire le verdict avant lecture de son result.json. Aucun Git d'écriture exécuté par l'agent.
**Niveau de preuve atteint** : 5 pour les contrats ; runtime de mission réel avec modèle simulé.

### 15:09 — premier vert réel sous unit_projection

Le nouveau trial-25ugxn94 utilise tous les composants réels, Ollama inclus : **passed** en
44,89811025001109 s pour la tentative, deux appels et 3 350 tokens rapportés (1 227 + 2 123).
Configuration num_ctx 16384 relue par ollama show ; provenance de la capacité toujours asserted.

Relecture indépendante des preuves : exactement trois résultats de gates failed/failed/passed,
un seul reçu durable lié à unit_projection avec effect confirmed, arbre passed, fichier cible
modifié et SHA-256 correspondant au rapport. Avant :
40818e8d40d125b69d8e75dff8fcaab1040dace8d87e7e06b9d8362fba577bf5 ; après :
2699717e89232fcd6ae0eee5395eb8122e67d2ffe9b3f39c9439f83c065f1b29.
La correction produite est max(0.0, min(1.0, level)). Les 44 fichiers du trial-44kcg6ig
restent inchangés, empreintes de nouveau comparées après l'essai.

Le fichier vert est conservé dans experiments/visualizer/workspace/audio_visualizer.py ;
aucun commit, push ni autre Git d'écriture exécuté par l'agent. Ce trial ne passe pas par
Prefect/GreenFinalizer : tree.finalized reste vide. Pour une future mission composée, préparer
un nouveau dépôt seed et un nouveau --run ; ne pas réinitialiser le workspace vert.
**Niveau de preuve atteint** : 6 pour cette nano-étape réelle, vérification finie du contrat
de projection ; pas de preuve universelle ni de finalisation de mission réelle.

### 15:09 — contre-preuve lors de la vérification finale

La seconde suite complète rend **1 failed, 1 599 passed, 3 skipped, 7 warnings en 115,87 s**.
Échec exact : tests/test_visualizer_mission.py::test_dead_supervisor_is_swept_before_admitting_another_worker,
RuntimeError unresolved mission custody à la reprise. Le même test passait dans la première suite
et le corpus ciblé ; l'intermittence doit être expliquée avant clôture. Preuves conservées dans
pytest-191/test_dead_supervisor_is_swept_0 sous le tmpdir système. L'avertissement Pydantic
ajouté par le test est bien résolu. Le trial réel vert et ses reçus restent valides et inchangés.

### 15:09 — course de custody corrigée et corpus ciblé vert

Les **64 tests lifecycle, mission composée, contrat et frontière passent en 55,26 s**.
Le test natif reproduit la fenêtre zombie sans attente artificielle de récolte ; le groupe
vivant à empreinte illisible reste refusé sans signal. La suite complète est relancée.
Production lifecycle réduite à 494 lignes de code / 679 physiques, sans changement de cible.

### 15:09 — livraison finale de la projection exacte

Suite finale : **1 602 passed, 3 skipped, 7 warnings en 114,64 s**, Python **3.12.9 / pyenv pithos**,
sans bytecode ni cache pytest. Contrôle des onze STATE et revue du diff verts. Les skips
restent les variantes réelles des scénarios réservés aux doubles bridge (ligne 79), campaign
(ligne 170) et refinery (ligne 82). Les avertissements restants sont Starlette/httpx et six
forks après démarrage de threads. Aucun test supprimé ou marqué skip pour rendre la suite verte.

Les contre-preuves précédentes sont conservées : critère absent, avertissement Pydantic,
échec intermittent de reprise et reproduction native du zombie. Leurs corrections sont vérifiées.
Le trial-25ugxn94 prouve la nano-étape réelle sous unit_projection ; sa correction reste non
commitée. Les reprises idempotent gardent leur critère et leur reçu historiques.

Mesures finales : kernel 311 code / 492 physiques ; verifier 749 / 974 ; lifecycle 494 / 679.
Total des onze modules : 5 680 lignes de code / 8 514 physiques. Aucune dépendance ajoutée.
**Niveau de preuve atteint** : 5 pour les contrats partagés ; 6 pour le trial Ollama décrit
ci-dessus et les observations natives de processus, sans prétendre à une preuve universelle.
