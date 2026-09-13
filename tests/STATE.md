# STATE — passe transverse

**Statut** : en cours
**Mise à jour** : 13:09

## Prochaine action

Vérifier visuellement http://127.0.0.1:5173 sur trial-44kcg6ig dès qu'un navigateur est accessible : sélection du run, cinq gates, arbre bloqué, métriques et pagination. Le code, les tests de rendu et la lecture HTTP sont livrés ; la suite métier reprend dans src/engine/STATE.md.

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
