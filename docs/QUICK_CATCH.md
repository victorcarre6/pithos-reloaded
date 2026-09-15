# Quick catch — Pithos Reloaded

_Référence courte. Mise à jour : **15:09**. Le périmètre produit reste défini par [PROJECT.md](PROJECT.md)._

## État constaté

**Les onze modules contiennent du code, aucun n’est déclaré fini.** La suite complète est collectable
et verte : **1 602 passed, 3 skipped, 7 warnings en 114,64 s**, dans le venv pyenv `pithos`, **Python 3.12.9**.
Web : **8 tests jsdom et build React/Vite verts**, Node 26.7.0.
Le jalon **« premier vert » avec modèle local est constaté** : trial-25ugxn94 sous unit_projection,
44,898 s, trois gates, un reçu durable et effet confirmé. Le fichier corrigé reste non commité.
Une suite verte sur les corpus existants ne prouve pas la livraison de tous les items des MODULE.md.

| Module | Lignes de code | Cible globale | Lignes physiques | Statut |
|---|---:|---:|---:|---|
| `kernel` | 311 | 380 | 492 | en cours |
| `journal` | 262 | 400 | 446 | en cours |
| `verifier` | 749 | 950 | 974 | en cours |
| `bridge` | 315 | 250 | 517 | en cours |
| `workspace` | 271 | 200 | 398 | en cours |
| `engine` | 1125 | 1050 | 1500 | en cours |
| `campaign` | 562 | 550 | 983 | en cours |
| `lifecycle` | 494 | 250 | 679 | en cours |
| `broker` | 577 | 550 | 943 | bloqué |
| `observatory` | 902 | 550 | 1359 | en cours |
| `refinery` | 112 | 100 | 223 | en cours |
| **Total** | **5680** | | **8514** | |

Mesure : lignes portant du code, hors blancs, commentaires et docstrings AST ; `__init__.py` et
sous-paquets inclus, tests et doubles exclus. Huit modules dépassent leur cible : bridge,
workspace, engine, campaign, lifecycle, broker, observatory et refinery. Leurs STATE portent un **plafond justifié** ;
les cibles numériques n’ont pas changé. Le web d’observatory est livré, sous sa cible distincte de 700 L.

## Dernière implémentation — 15:09

Le dashboard est déclaré terminé pour le moment par l'utilisateur. La nouvelle commande
[mission.py](../experiments/visualizer/README.md#mission-reprenable-et-finalisation-locale--1409)
charge le même arbre à la reprise, appelle walk via flow et finalise les verts avec broker.
Lifecycle détient le verrou jusqu'à l'arrêt confirmé du worker et des gardiens de toutes les gates.
Chaque gate est admise après écriture de sa custody, sous le même propriétaire que la mission ;
un TTL ne permet plus de reprendre le verrou d'un propriétaire vivant. Une course native révélée
par la suite complète est corrigée : les groupes déjà sortis dont le leader est zombie sont
réconciliés sans signal ; une identité inconnue avec un groupe vivant reste refusée.

Preuve intégrée : commit unique après perte d'acquittement, refus restauré, coupure pendant un
invariant réel puis restauration à la reprise, sweep du worker et de la gate après mort du superviseur.
La CLI réelle reprend aussi le vert sans nouvel appel modèle. Git/Prefect/verifier/
workspace/journal/lifecycle réels sur copies, **modèle seul simulé**. Serveur Prefect local explicite
et sans analytics requis pour la CLI. Le nouveau trial réel utilise la nano-étape, sans cette finalisation.

Consolidation du 15:09 : contrats Walker/MissionRunner/GreenFinalizer partagés ; seule la dépendance
Prefect est permise en plus pour flow.py, maintenant soumis au balayage injecté fichier par fichier.
Le [diagnostic de sensibilité](../src/verifier/SENSITIVITY.md) reproduit le refus et une limite :
une projection à branches sur [0, 2] passe aussi sous idempotent. L'extension autorisée le 15:09
ajoute `unit_projection` : les nouveaux essais vérifient la projection exacte sur [0, 1] avec
comparaisons exactes, onze exemples fixes et Hypothesis seedé. Les anciens reçus restent idempotent.
Le rejeu du candidat archivé passe ; aucun ancien fichier ni verdict n'est réécrit.
Le nouveau trial Ollama est également vert : deux appels, 3 350 tokens rapportés, un reçu
`effect: confirmed` et `tree.finalized` vide. La mission composée reste testée avec modèle simulé.

## Socle précédent — 13:09

- **Kernel** : SourceFact porte les octets avant/après bornés et sérialisés sans perte ; RepoFact porte
  les chemins, le diff et une complétude explicite. Kernel valide la forme ; verifier décide de l'accord.
- **Workspace / broker** : snapshots relus pendant la transaction, fait Git canonique. Sans HEAD ou
  avec fichiers non suivis, l'observation Git reste incomplète. Aucun contenu non observé n'est inventé.
- **Verifier** : `run` croise les empreintes, plages, chemins et hunks Git avant la double gate.
  Le reçu est lié aux mêmes faits et n'est rendu qu'après acquittement du journal. Le contrôle des faits
  consomme le même budget. `schema_conform` reste la relation manquante du catalogue, porté à dix choix le 15:09.
- **Engine** : `run_attempt` compose intention durable, transaction, candidat revalidé, faits, gate et reçu.
  Rejet, reçu absent/étranger et échec de publication restaurent les octets ; aucun rejeu de `running`.
  `select.py` conserve la sélection et les dépendances depuis un index fourni par le harness.
- **Bridge** : schéma candidat fermé sur une fonction existante, source bornée, requête et réponse
  intégrales conservées ; **verifier.preflight** bloque les critères inexécutables avant tout appel.
- **Observatory** : collection directe runs/, état publié prioritaire sur les intentions, gates des
  refus et artefacts bornés/paginés. UI locale, contexte, outils et bilan journalier. Rapports de
  vérification et capacité/provenance/durée des nouveaux appels désormais tracés par engine/bridge.
- **Graphify/GVS5H** : notions sélectionnées en parties J/K, sans leurs dépendances. Omissions de
  ContextPacket annoncées et budgétées ; 20 interfaces livrées contrôlées par une table livré/prévu.

L'utilisateur a autorisé la source candidate le 12:09 ; critères et entrées restent sous contrôle du harness.
Le [banc audio](../experiments/visualizer/README.md) vérifie vert, invariant rouge et refus du reçu avec
engine/workspace/verifier/journal réels, bridge/Git simulés. La sonde Ollama réelle a d'abord tronqué à
128 tokens, puis rendu un critère conforme à 358 tokens après consigne explicite et réserve de 1 024.
La fenêtre 16 384 est lue via `ollama show` et transmise avec provenance **asserted**. Cette sonde ne prouve
pas à elle seule la génération candidate ; l'idempotence seule ne prouve pas les bornes audio exactes [0, 1].
Le trial réel `trial-44kcg6ig` a ensuite produit un candidat conforme, refusé sur **tautology** :
5 gates, 0 reçu, rollback exact, 35,021 s, 2 appels et 2 461 tokens rapportés. Le dépôt d'essai est
initialisé (HEAD 57e47c5). Ce résultat ne valide pas encore le jalon « premier vert ».

## Dernière passe transverse

La demande de reprise de `TEMPO.md`, conservée dans le [journal transverse](../tests/STATE.md), a conduit à :

- Un chargeur de doubles partagé entre modules et contrats ; chaque chargement a son état propre.
- Un scanner AST commun, récursif, qui refuse le vide et conserve les chemins complets.
- Des injections permanentes qui appellent les **vrais tests de balayage** sur copies : chaque fichier,
  sous-paquet futur et exception de chemin est éprouvé. Dix contrats détectent une signature divergente.
- Un contrôle des onze en-têtes STATE : mesures, cible, empreinte des sources, date et statut fermé.
  La date `JJ:MM` ne donne pas d’année ; l’empreinte détecte les modifications non reportées.
- Le rôle transverse défini dans [AGENTS.md](../AGENTS.md) § 14, synchronisé dans CLAUDE.md,
  avec reprise dans [tests/STATE.md](../tests/STATE.md) et propositions dans [tests/git.md](../tests/git.md).
- Les documents Markdown rendus versionnables ; caches Python et code tiers restent ignorés.
  **Les 27 caches déjà suivis restent dans l’index** : leur retrait est proposé à l’humain dans tests/git.md.

Les trois skips sont les variantes réelles de tests qui chargent un scénario propre au double
(bridge, campaign, refinery). Sept avertissements subsistent : adaptateur Starlette/httpx et fork
après démarrage de threads. Les tests utilisent des doubles, fichiers temporaires, serveurs HTTP
locaux et processus jetables ; la sonde Ollama citée plus haut est une mesure séparée de cette suite.

## Prochaines étapes métier

1. Conserver le fichier vert de `trial-25ugxn94` pour revue et commit par l'opérateur. Le workspace
   n'est plus un seed : une nouvelle mission composée demande une nouvelle copie initialisée,
   un nouveau `--run` et Prefect local. Les commandes sont dans le [banc](../experiments/visualizer/README.md).
2. Reprendre les frontières documentées : producteur du triplet de baseline, contrat RepoIndex pour
   campaign, lecture JSON tolérante dans journal, propriétaire du polling Telegram côté broker.
3. Continuer les items indépendants depuis les STATE : garde disque `ensure_space` de lifecycle,
   contrat déclaré de sortie pour schema_conform. Les ports verrou/worker et exécuteur de gates
   ont leurs contrats partagés. Le dashboard reste déclaré terminé ; **refinery reste désactivé.**
4. Exécuter les spikes et le jalon réel selon [ROADMAP.md](ROADMAP.md), sans déduire leur succès
   des tests de module. Les cibles non atteintes ne sont pas effacées par le travail transverse.

## Commandes utiles

Dashboard : [commandes de lancement](../README.md#observatoire-local), [URL locale](http://127.0.0.1:5173).
La lecture HTTP du proxy est validée ; aucun screenshot ou essai navigateur n'est revendiqué.

```sh
# environnement imposé
pyenv activate pithos
python -V

# suite entière, sans bytecode ni cache pytest
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -rs -p no:cacheprovider

# compte et vérifie les onze STATE, sans les réécrire
PYTHONDONTWRITEBYTECODE=1 python -m tests.state_check

# balayages soumis à injection, y compris exceptions de chemin
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_boundary_scans.py

# contrats et mutation de signatures
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/contracts
```

Si la sandbox interdit le bind local ou les observations de processus macOS, consigner cet échec
puis utiliser une exécution autorisée ; aucun skip de confort. Aucun agent n’exécute une commande
Git d’écriture. Les propositions de cette passe supposent les implémentations déjà présentes dans
le worktree ; elles ne remplacent pas les propositions propres à chaque module.

`docs/ELN.md` a été fusionné dans [EXPLANATIONS.md](EXPLANATIONS.md), Partie II, par la décision 33.


## Entrée terminal — 13:09

`python src/main.py selftest --case green` lance le banc avec quatre panneaux fixes. Les modes
`probe` et `trial --repo … --seconds …` gardent leurs arguments et prérequis ; `--no-tui` ou une
sortie redirigée garde le JSON seul. Tokens mesurés à réception, tours candidats, opérations du
harness et reçus viennent des traces durables. `Ctrl+C` rend 130 après fermeture transactionnelle.
Voir [les commandes et limites](../experiments/visualizer/README.md#affichage-terminal--1309).


## Contre-preuve résolue — 14:09

La sonde initiale reproduisait un invariant détaché survivant au watchdog (1 failed en 2,22 s).
Après extension autorisée à verifier, le port d'exécution et les gardiens lifecycle ferment ce défaut.
**23 tests ciblés passent en 44,47 s**, avec gates réelles, descendant, mort du superviseur et CLI.
Les preuves négatives restent dans les STATE ; le modèle est simulé dans cette intégration.
