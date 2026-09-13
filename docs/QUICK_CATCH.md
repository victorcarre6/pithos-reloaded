# Quick catch — Pithos Reloaded

_Référence courte. Mise à jour : **13:09**. Le périmètre produit reste défini par [PROJECT.md](PROJECT.md)._

## État constaté

**Les onze modules contiennent du code, aucun n’est déclaré fini.** La suite complète est collectable
et verte : **1 444 passed, 3 skipped, 7 warnings en 43,83 s**, dans le venv pyenv `pithos`, **Python 3.12.9**.
Web : **8 tests jsdom et build React/Vite verts**, Node 26.7.0.
Une nano-étape passe avec bridge/Git simulés ; le jalon **« premier vert » avec modèle local reste à démontrer**.
Une suite verte sur les corpus existants ne prouve pas la livraison de tous les items des MODULE.md.

| Module | Lignes de code | Cible globale | Lignes physiques | Statut |
|---|---:|---:|---:|---|
| `kernel` | 307 | 380 | 488 | en cours |
| `journal` | 262 | 400 | 446 | en cours |
| `verifier` | 715 | 950 | 925 | en cours |
| `bridge` | 315 | 250 | 517 | en cours |
| `workspace` | 271 | 200 | 398 | en cours |
| `engine` | 673 | 1050 | 930 | en cours |
| `campaign` | 562 | 550 | 983 | en cours |
| `lifecycle` | 325 | 250 | 464 | en cours |
| `broker` | 414 | 550 | 749 | bloqué |
| `observatory` | 902 | 550 | 1359 | en cours |
| `refinery` | 112 | 100 | 223 | en cours |
| **Total** | **4858** | | **7482** | |

Mesure : lignes portant du code, hors blancs, commentaires et docstrings AST ; `__init__.py` et
sous-paquets inclus, tests et doubles exclus. Six modules dépassent encore leur cible : bridge,
workspace, campaign, lifecycle, observatory et refinery. Leurs STATE portent un **plafond justifié** ;
les cibles numériques n’ont pas changé. Le web d’observatory est livré, sous sa cible distincte de 700 L.

## Dernière implémentation — 13:09

- **Kernel** : SourceFact porte les octets avant/après bornés et sérialisés sans perte ; RepoFact porte
  les chemins, le diff et une complétude explicite. Kernel valide la forme ; verifier décide de l'accord.
- **Workspace / broker** : snapshots relus pendant la transaction, fait Git canonique. Sans HEAD ou
  avec fichiers non suivis, l'observation Git reste incomplète. Aucun contenu non observé n'est inventé.
- **Verifier** : `run` croise les empreintes, plages, chemins et hunks Git avant la double gate.
  Le reçu est lié aux mêmes faits et n'est rendu qu'après acquittement du journal. Le contrôle des faits
  consomme le même budget. `schema_conform` reste la neuvième relation manquante.
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

1. Examiner la sensibilité du critère à partir des variantes survivantes du trial conservé. Composer le marcheur
   complet autour de `run_attempt` : reprise/réconciliation, finalisation des verts et baseline de mission.
   Détails : [engine/STATE.md](../src/engine/STATE.md). `dump.py` reste un item indépendant.
2. Reprendre les frontières documentées : producteur du triplet de baseline, contrat RepoIndex pour
   campaign, lecture JSON tolérante dans journal, propriétaire du polling Telegram côté broker.
3. Continuer les items indépendants depuis les STATE : garde disque `ensure_space` de lifecycle,
   validation visuelle d’observatory (navigateur indisponible à l'agent), listes métier encore ouvertes. Le contrat NanoEngine est testé ;
   le contrat complet du marcheur et celui de lifecycle restent à publier. **Refinery reste désactivé.**
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
