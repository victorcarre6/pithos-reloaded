# STATE — passe transverse

**Statut** : en cours
**Mise à jour** : 15:09

## Prochaine action

La projection exacte et la correction de custody sont livrées. Reprendre le chantier indépendant lifecycle/disk.ensure_space depuis son STATE ; conserver les contrôles natifs du zombie et des groupes vivants illisibles dans la suite complète.

## Critères de livraison

- [x] Suite entière collectable et exécutée dans Python 3.12.9 / pithos.
- [x] Chargeur unique de doubles partagé par tests de module et contrats.
- [x] Scanner commun récursif, non vide, sans collision de basenames ; injections du balayage.
- [x] Contrôle mécanique des en-têtes STATE et mesure explicite des lignes.
- [x] Protocole de passe transverse et contrôles de fin de module inscrits dans AGENTS.
- [x] Ignorés Git corrigés ; retrait des caches suivis proposé avec chemins explicites.
- [x] TEMPO et documentation actualisés avec résultats et limites.

## Journal

### 11:09 — état initial

Demande utilisateur : adapter tout TEMPO en autonomie. Le périmètre est transverse ;
les implémentations métier existantes et leurs cases de livraison sont préservées.
Python mesuré : 3.12.9, préfixe `/Users/victorcarre/.pyenv/versions/pithos`.
Suite dans la sandbox : **2 failed, 1173 passed, 3 skipped, 40 errors en 23,98 s**.
Les serveurs HTTP locaux sont refusés par la sandbox et les empreintes macOS sont
indisponibles. Relance hors sandbox demandée avec justification ciblée.
Le worktree était déjà modifié avant cette passe, dont les déplacements des tests
transverses et les trois `__init__.py` manquants ; ils ne sont pas réattribués à cette passe.

### 11:09 — mesure hors sandbox et mutualisation

Suite initiale hors sandbox : **1 215 passed, 3 skipped, 7 warnings en 33,90 s**.
Les avertissements concernent l'adaptateur Starlette/httpx et les forks après démarrage
de threads, pas une campagne réelle. Aucun environnement ni dépendance modifiés.

Le chargeur a été remplacé par `tests/support.py`, exposé par les fixtures racine.
Le kernel de verifier garde son scope session requis par ses fixtures de reçu.
Tests de contrat + engine/workspace après mutualisation : **266 passed, 3 skipped en 3,20 s**.
Scanner et corpus des onze frontières : **189 passed en 0,77 s**.
Les nouveaux tests ont d'abord échoué à la collecte, faute des helpers non encore écrits.
Après implémentation : **38 passed en 0,68 s** pour helpers et injections du balayage.
Chaque test de frontière réel est appelé sur une copie, puis une violation est injectée
successivement dans chaque fichier, avec un nouveau sous-paquet et son `__init__.py`.
Le code du worktree n'est jamais muté par ces sondes.
**Niveau de preuve : 5** pour les contrats ; détection AST exercée sur copies réelles.

## Arbitrages

- Cibles numériques conservées. Mesure choisie : lignes portant du code hors blancs,
  commentaires et docstrings, avec total physique séparé. Tests/doubles hors production.
- Aucun module déclaré fini sur simple succès de suite. Les preuves restent au niveau observé.
- Aucune commande Git d'écriture. Les opérations d'index sont proposées dans `tests/git.md`.

### 11:09 — états mesurés et dérives détectées

Le test des vrais en-têtes a d’abord échoué sur les onze modules : formats et empreintes absents.
Après mise à jour, les contrôles passent. Deux sondes supplémentaires ont rougi : la date `1:9`
était acceptée et une carte de cibles vide donnait un succès vide. Les deux sont corrigées.
Le format `JJ:MM` n’indique aucune année : le contrôle valide le calendrier, pas une ancienneté
impossible à inférer. L’empreinte repère les modifications même sans changement de nombre de lignes.

**352 passed, 3 skipped en 4,40 s** pour les frontières, neuf contrats, injections et helpers.
Les neuf contrats détectent désormais une signature divergente par un test permanent ; les doubles
sont chargés à neuf et les mutations mémoire sont annulées par pytest.
Les six dépassements de cible subsistent après exclusion des commentaires/docstrings ; le constat
TEMPO « entièrement de la documentation » ne vaut pas pour la production globale actuelle.
Les plafonds justifiés et les cibles numériques sont distincts ; aucun code métier n’a été raccourci.
`AGENTS.md` définit le rôle transverse et garde les décisions produit intactes ; son miroir
`CLAUDE.md` est synchronisé conformément au journal EXPLANATIONS.
**Niveau de preuve : 5** pour les contrats, 2 pour la conformité des mesures documentaires.

### 11:09 — dernières sondes et livraison

Première suite complète après adaptation : **1283 passed, 3 skipped, 7 warnings en 34,80 s**.
La revue des exceptions a ensuite révélé trois erreurs par basename : `nested/codeview.py`,
`nested/runner.py`, `nested/flow.py` héritaient des permissions du fichier racine. Les **trois tests
rouges** ont précédé leur correction par chemin relatif complet ; **25 sondes vertes en 0,71 s**.
Suite complète finale hors sandbox : **1 286 passed, 3 skipped, 7 warnings en 34,59 s**, Python **3.12.9 / pithos**.

Skips conservés : `test_bridge_double.py` (frontière réelle sans file à charger),
`test_campaign_double.py` et `test_refinery_double.py` (politiques réelles sans scénario à charger).
Aucun skip ajouté. Sept avertissements non masqués : adaptateur Starlette/httpx et fork après threads.
Mesures des onze STATE conformes ; protocole AGENTS/CLAUDE identique. TEMPO garde ses observations
initiales puis la résolution point par point. QUICK_CATCH ne présente plus le premier vert comme
l’unique manque du produit. Aucune case métier cochée, aucun MODULE modifié par cette passe.

**Niveau de preuve : 5** pour les contrats et corpus sur doubles ; les tests de processus et HTTP
constatent des effets locaux mais ne démontrent aucune campagne/Ollama. Le statut `fini` de ce
fichier qualifie uniquement la livraison du travail transverse autorisé, avec commandes d’index
préparées pour l’humain conformément à AGENTS § 7, pas exécutées.

## Opérations Git laissées à l’humain

| Quoi | État | Action exacte |
|---|---|---|
| 27 caches encore suivis | Préparation terminée, index inchangé | Lot « arrêter de suivre les caches Python » dans tests/git.md |
| Documentation désormais visible | Non mise en index | Lots « mémoire du dépôt » et « documents de référence existants » |
| Code métier préexistant non suivi | Conservé hors propositions transverses | Relire les src/*/git.md avant de composer un snapshot complet |

### 11:09 — contrôle final documentaire et filesystem

`python -m tests.state_check` rend 0 pour les onze modules et affiche désormais les empreintes
à recopier avec les comptes. `git diff --check` est vert ; le contrôle des fichiers non suivis
inclus dans cette passe ne trouve aucun espace de fin de ligne. Aucun lien Markdown relatif cassé
parmi TEMPO, AGENTS/CLAUDE, tests/STATE, tests/git, les documents docs et les STATE de module.
AGENTS et CLAUDE sont identiques octet par octet. Les **27 pyc suivis sont identiques à HEAD**,
et les 27 commandes proposées nomment chacune leur fichier une seule fois.
**Niveau de preuve : 3** pour la comparaison d’octets ; aucune modification de l’index observée
ni effectuée par cette passe.

### 12:09 — validation transverse des unités métier successives

Les agents de module ont été repris successivement dans cette session : faits kernel, producteur
workspace, producteur broker, gate verifier, sélection engine. Les preuves et résultats négatifs
appartiennent à leurs STATE ; aucun statut fini n'a été attribué aux onze modules.

Adaptations partagées : le contrat de signature verifier inclut `run` et le Protocol `Verifier` ;
sa frontière autorise `re` stdlib pour lire les coordonnées des hunks sans I/O. Le mutant de signature
et les injections de balayage existants restent verts. README a été corrigé : « aucune implémentation »
était obsolète, la référence courte donne désormais le détail mesuré de la livraison.

**Suite finale : 1 367 passed, 3 skipped, 7 warnings en 37,10 s** dans pithos / Python 3.12.9.
Relance broker après refus du bind local dans la sandbox : **114 passed en 1,99 s**. Aucune suppression
de test, skip supplémentaire ou installation. Mesure : **4 410 lignes de code, 6 904 physiques** ;
les onze en-têtes passent, six dépassements restent justifiés sans relever les cibles.
Aucun bytecode suivi changé, aucun Git d'écriture. Propositions ci-après et dans chaque module.
**Niveau de preuve : 5** pour les contrats ; aucune campagne ni validation réelle du modèle local.

### 13:09 — validation finale du banc audio

Suite complète dans **pithos / Python 3.12.9** : **1 402 passed, 3 skipped, 7 warnings en 40,64 s**.
La suite intermédiaire après run_attempt avait rendu **1 397 passed, 3 skipped, 7 warnings en 37,46 s**.
Les cinq tests ajoutés relisent effets disque, reçus et artefacts du banc ; aucun nouveau skip.
Skips : variantes réelles non scénarisables bridge/campaign/refinery. Warnings Starlette/httpx et
fork après threads conservés. Les onze mesures STATE passent : **4 570 code, 7 106 physiques**.
Aucune dépendance installée ni commande Git d'écriture. Aucun module déclaré fini.
**Niveau de preuve : 5** sur contrats et composition ; la sonde de critère Ollama, mesurée séparément,
atteint le niveau 6 pour ce seul appel. Le premier trial réel attend le HEAD du dépôt dédié.

La passe partagée ajoute le contrat NanoEngine, inclut preflight dans le contrat Verifier et publie
les cinq régressions du banc. AGENTS/CLAUDE/PROJECT portent l'amendement approuvé du code candidat.
Le statut fini de ce fichier qualifie cette livraison transverse ; le trial et le marcheur ne le sont pas.

### 13:09 — contrôle final de livraison

`git diff --check` passe. Les 21 fichiers nouveaux/documentaires relus n'ont ni espace de fin de
ligne ni lien relatif cassé ; AGENTS et CLAUDE sont identiques. Les **27 pyc suivis sont inchangés**
par rapport à HEAD. Les **17 rapports** conservés sous runs sont des JSON lisibles. La copie du seed
est exacte et son dépôt reste non initialisé. Aucun index, commit, branche ni dépôt tiers modifié.
Propositions prêtes dans les git.md de module, tests et experiments/visualizer ; aucune exécutée.
**Niveau de preuve : 3** pour les comparaisons d'octets et les fichiers, 2 pour le format JSON.

### 13:09 — chantier observabilité et références autorisé

L'utilisateur demande d'exécuter les recommandations de la revue : raccord réel du banc, dashboard,
indicateurs GVS5H, omissions visibles et contrôle documentaire Graphify. Travail par modules successifs,
puis intégration transverse ; aucune commande Git d'écriture. Le dépôt d'essai a été initialisé par
l'humain (HEAD 57e47c5), puis le trial-44kcg6ig a été rejeté sur tautology en 35,02 s et restauré.
Les sept pyc désormais modifiés étaient déjà présents au démarrage de ce chantier ; ne pas les restaurer.

Critères :
- [TODO] Le trial apparaît avec son nœud, son rejet, ses cinq gates, son rollback et l'absence de reçu.
- [TODO] Le web local porte la navigation de v1, des vues de preuves et des tests de rendu/rafraîchissement.
- [TODO] Les métriques distinguent troncatures, erreurs, progression attestée et données absentes.
- [TODO] Le contexte rendu annonce ses omissions ; le marqueur consomme son budget estimé.
- [TODO] Un contrôle documentaire distingue livré/prévu et détecte une signature livrée divergente.
- [TODO] Les références retenues sont cataloguées avec leurs limites ; documentation et git.md à jour.

État initial : 94 tests observatory passent (1 warning). La lecture réelle des 7 événements produit
0 nœud, 0 rejet, aucune cause ; l'index runs/ échoue faute de sous-répertoire missions/. Aucune UI web
dans Reloaded. Le résultat négatif constitue le cas de validation, pas une raison de modifier la gate.

### 13:09 — observabilité intégrée, vérification finale

- [DONE] Trial historique projeté : nœud bloqué, cause tautology, cinq gates, aucun reçu, rollback.
- [DONE] Dashboard local rebranché : catalogue, arbre, preuves, contexte, timeline et artefacts paginés.
- [DONE] Troncatures, préflight, erreurs, états publiés et capacités de provenance explicite séparés.
- [DONE] Rapports de verifier conservés avant décision ; refus d'écriture testé avec restauration.
- [DONE] Notices d'omission comptées dans le budget et sans fuite des contenus exclus.
- [DONE] Contrôle de 20 interfaces livrées sur 11 modules, plus deux interfaces prévues non exigées.
- [DONE] Références J/K cataloguées, documentation et propositions Git préparées.
- [TODO] Inspection visuelle dans un navigateur : CUA ne fournit aucun navigateur ni application.

Avant intégration de l'entrée TUI parallèle : **1 426 passed, 3 skipped, 7 warnings en 41,28 s**.
Sur le dépôt commun avec cette entrée : **1 444 passed, 3 skipped, 7 warnings en 43,83 s**,
Python **3.12.9 / pithos**, sans bytecode ni cache pytest. Skips : variantes réelles des contrats
bridge/campaign/refinery sans chargement de scénario ; warnings Starlette/httpx et six forks après threads.
Web : **8 tests jsdom**, typage et build Vite verts sous Node **26.7.0**, npm **11.19.0**.
Le contrôle des onze STATE passe : **4 858 code, 7 482 physiques**, hors web et entrées src racine.

Lecture HTTP réelle via le proxy 5173 vers l'API 8823 : ready=true, 7 événements historiques,
5 gates, 0 reçu, 2 appels, 2 461 tokens rapportés et 0 troncature. Le nouveau selftest-wo3aa7e5
porte un rapport de vérification durable ; les anciens essais ne sont pas réécrits.
Le fichier actif retrouve le SHA 40818e8d40d125b69d8e75dff8fcaab1040dace8d87e7e06b9d8362fba577bf5.
Les deux serveurs écoutent uniquement 127.0.0.1. Les dépendances restent déclarées et verrouillées.

**Niveau 5** sur contrats/doubles, **4** pour les scénarios jsdom, **6 limité à la lecture HTTP,
aux artefacts et au filesystem locaux**. Aucun rendu navigateur ni nouvelle campagne Ollama revendiqué.
Le marcheur complet, le branchement de ContextPacket et la garde de non-progrès restent à construire.
Les travaux parallèles de TUI et les sept pyc déjà modifiés sont conservés ; aucune commande Git d'écriture.

### 13:09 — documents et propositions contrôlés

Neuf propositions append-only ajoutées aux git.md d'observatory, engine, bridge, tests et du banc.
Les **61 chemins** proposés existent, sans blanc final. Le contrôle des liens a trouvé une référence
historique vers TEMPO.md désormais absent : QUICK_CATCH pointe vers le journal transverse qui conserve
cette demande. Aucun document historique ni preuve brute recréé ou supprimé.
Après correction du commentaire d'autorité dans render.py : **19 tests de projection/documentation
passent en 0,34 s** ; lignes inchangées, empreinte observatory actualisée, onze STATE et diff conformes.
Ce contrôle documentaire ne remplace pas la vérification visuelle encore ouverte.

### 14:09 — support partagé de GreenFinalize et de la composition lifecycle

La demande explicite portant sur broker et la composition lifecycle nécessite leurs contrats et
leurs tests d'intégration communs. L'ajustement des frontières est limité aux nouveaux fichiers
et aux imports stdlib time/math/functools ; aucun import métier interdit ni accès réseau supplémentaire
n'est autorisé. Les doubles broker/lifecycle ont leurs tests de signature avec dérive injectée.
La production engine reste intacte ; ses blocages de composition sont résolus par les preuves du banc.

Unités vérifiées : broker **1 534 passed, 3 skipped, 7 warnings en 60,35 s** sur suite racine ;
lifecycle **1 545 passed, 3 skipped, 7 warnings en 61,72 s**. Le nouveau test intégré a rougi à
la collecte avant mission.py, puis donné 2 passed en 19,11 s. Avec coupure et superviseur mort :
**46 passed en 29,70 s** sur intégration/lifecycle/contrat. Suite finale en cours après conservation
des issues du worker. Les résultats négatifs et mesures détaillées restent dans les STATE de module.
**Niveau de preuve : 5 pour la mission complète**, modèle seul simulé ; aucun essai Ollama ajouté.

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


### 14:09 — admission opérateur suspendue

La CLI mission ferme désormais l'admission avant création de preuves/worker tant que les groupes
verifier ne sont pas possédés. Les scénarios contrôlés d'intégration restent accessibles par injection
du worker de test ; ils ne sont pas une autorisation d'essai réel. Plan de correction après accord :
port d'exécution des commandes de gate dans verifier, fourni par lifecycle depuis la composition ;
aucun import lifecycle dans verifier, aucune modification des critères ni des reçus. Enregistrement
avant admission et sortie confirmée de chaque groupe, y compris après disparition du worker.

### 14:09 — état sûr en attente d'extension de périmètre

Après suspension de l'entrée opérateur : suite complète **1 549 passed, 3 skipped, 7 warnings en
89,05 s**, pithos/Python 3.12.9. Le nouveau test constate le refus AVANT création de preuves ou
worker. STATE et diff-check verts. Cette suite ne résout pas la sonde négative du groupe détaché
(1 failed en 2,22 s) : la composition reste suspendue et l'accord src/verifier reste en attente.
GreenFinalizer demeure livrable indépendamment ; les propositions de composition restent suspendues.

### 14:09 — extension custody autorisée, intégration en cours

L'utilisateur répond « Continue en autonomie » à la demande explicite d'extension à verifier :
le raccordement de ses groupes de processus est autorisé. Réutilisation du superviseur lifecycle
et de son pipe : chaque gate a un gardien enregistré avant admission, sous le même propriétaire
que le worker. Verifier conserve commandes, artefacts et verdicts via un port contextuel.

Preuves intermédiaires : 2 erreurs de collecte avant publication des ports ; ensuite **42 passed
in 4.43s** (runner, port et frontière verifier). Custody native : **1 failed, 9 passed in 5.60s** ;
le timeout conservait la requête IPC contenant un Path dans le détail JSON de sortie. Le résultat
terminal est désormais distinct de la requête ; nouvelle vérification en cours. La CLI reste fermée
jusqu'à la preuve d'interruption d'une gate réelle et de récupération après mort du superviseur.
**Niveau de preuve** : 5 pour le port ; validation native de la composition encore incomplète.

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

### 15:09 — refus tautology reproduit, consolidation des frontières en cours

Rejeu exact des sources et du critère archivés de trial-44kcg6ig : **rejected / tautology**, avant
rouge, après vert, trois mutants survivants. Les **44 fichiers historiques sont inchangés** par
comparaison SHA-256 avant/après. Nouvelles preuves conservées dans
/private/tmp/pithos-sensitivity-kvhdkqos/verdict.json et ses cinq répertoires d'invariants.

Le corpus réduit compare trois représentations : min/max [0,1] est rejeté ; les versions à branches
[0,1] et [0,2] passent toutes deux rouge-avant/vert-après/kill. La gate prouve seulement l'idempotence
et une sensibilité à son inventaire AST, pas les bornes exactes. Aucun opérateur opportuniste ni
assouplissement de gate n'est ajouté. `test_sensitivity.py` et mutations : **14 passed in 5.53s**.

La consolidation transverse prévue reprend ensuite les ports Walker, MissionRunner et GreenFinalizer.
La sonde de balayage sur chaque fichier, sans sa dispense flow.py, rend **1 failed, 10 passed,
14 deselected in 0.90s** : le vrai scanner accepte socket dans flow.py. Correction ciblée : seul
Prefect est permis en plus dans ce fichier ; les autres interdits persistent. Les contrats vérifient
noms, ordre, nature positionnelle/keyword-only et valeurs par défaut, avec mutations sur chaque port.
Premier passage : **2 failed, 44 passed in 3.91s**, le test oubliait le RepoFact exigé par le double
broker ; fixture corrigée avec le double kernel. Aucun code métier modifié sur ce nouveau chantier.
**Niveau de preuve : 5** pour les contrats ; scripts d'invariants réels et défaut AST reproduit.

### 15:09 — sensibilité et contrats partagés livrés

**164 passed in 22.32s** sur verifier, contrats engine et frontières injectées. Suite complète
**1 568 passed, 3 skipped, 7 warnings en 103,09 s**, Python **3.12.9 / pithos**, sans bytecode ni cache pytest, hors sandbox.
Les trois skips restent tests/contracts/test_bridge_double.py:77, test_campaign_double.py:170 et
 test_refinery_double.py:82 (variantes réelles sans scénario). Warnings existants : Starlette/httpx
et six forks après threads. Contrôle des onze STATE et diff-check verts.

La reproduction exacte conserve les 44 fichiers du trial. Le corpus autonome teste la survie des
mutants du clamp compact et l'acceptation de deux écritures à branches, dont une projection [0,2].
Aucun opérateur de mutation ajouté, aucun critère ni gate modifié ; la preuve produit n'est pas
élargie par cette livraison. `src/verifier/SENSITIVITY.md` expose les résultats et leurs limites.

Les contrats partagés couvrent désormais NanoEngine, Walker, MissionRunner et GreenFinalizer.
La dérive de chaque méthode et des paramètres keyword-only est détectée ; les doubles de walk et
mission ne font aucune I/O et rendent un arbre indépendant. Le scanner n'exempte plus flow.py :
seul Prefect y est autorisé en plus, avec une injection effective dans chaque fichier du module.
Les tests locaux engine restent en place ; aucune implémentation métier voisine n'est modifiée.

Une préférence optionnelle a été demandée sur la preuve de projection exacte. Sans changement de
périmètre décidé, le banc reste celui de PROJECT.md. Aucun essai Ollama supplémentaire, commit,
push ni suppression de données. Propositions ajoutées dans verifier/git.md et tests/git.md.
**Niveau de preuve : 5** sur contrats ; 4 pour les invariants exécutés sur copies contrôlées.

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
