# STATE — `observatory`

**Statut** : en cours
**Mise à jour** : 13:09
**Lignes** : 902 code / 550 cible · 1359 physiques
**Empreinte** : 8f34e824dac0cd91557efe1b2ad3ec137102408c845caafdd386ffb82301a437

## Prochaine action

Obtenir la vérification visuelle de http://127.0.0.1:5173 sur trial-44kcg6ig quand un navigateur sera accessible. Les tests de rendu, le build et la lecture HTTP sont verts ; ne pas les renommer en validation visuelle. Puis qualifier les indicateurs de mission au branchement du marcheur complet.

## Avancement

- [x] L'index est reconstruit **au démarrage depuis le disque**, sans collecteur, et suivi par `mtime`.
- [x] Catalogue et détail sont deux routes distinctes — le catalogue ne charge pas les détails.
- [x] Une queue déchirée en fin de JSONL **ne fait pas planter** la lecture.
- [x] Un arbre à IDs dupliqués s'affiche sans exploser en multiparent.
- [x] Une durée négative est **affichée**, jamais corrigée ni masquée.
- [x] La durée d'un nœud n'est jamais la somme de durées concurrentes de son sous-arbre.
- [x] Toute projection partielle déclare chemin, total de lignes, lignes au-dessus et en dessous.
- [x] Les traces sont **échappées avant rendu HTML** — rendu React en texte ; le test jsdom d'un
      diagnostic portant une balise script constate le texte et l'absence de nœud script.
- [x] Les cinq indicateurs sont servis et cohérents avec un jeu de JSONL de référence — trois d'entre eux
      restent structurellement à `None`/0 tant qu'`engine` et `campaign` n'émettent rien (§ *Blocages* n°1).
- [x] Le bind est `127.0.0.1` **en dur** — test statique, plus une vérification réelle (niveau 6).
- [x] Un test statique confirme qu'aucune ouverture de fichier en écriture n'existe dans le module.
- [x] Les six scénarios jsdom de v1 passent après rebranchement ; deux tests de preuves/métriques ajoutés.

## Journal

### 07:09 — API complète : index, arbre, agrégats, indicateurs, routes

**Fait.** Les quatre fichiers de `MODULE.md` § 7 sont écrits et verts : `api/index.py` (index mémoire,
segments, suivi `mtime`), `api/render.py` (aplatissement d'arbre, `window`, `status_text`), `api/stats.py`
(quatre agrégats, cinq indicateurs, `validate`), `api/routes.py` (dix routes FastAPI). Le double
`tests/doubles/observatory.py` et son test de contrat existent, ainsi que le test de graphe d'imports.

**Mesuré.** `PYTHONDONTWRITEBYTECODE=1 python -m pytest src/observatory -q -p no:cacheprovider` dans le venv
`pithos` (Python 3.12.9) : **93 tests verts**. Suite complète du dépôt : **600 tests verts**, aucun autre
module touché.

**Mesuré en réel.** `uvicorn` lancé sur un jeu de JSONL écrit à la main, avec queue déchirée :
`/ready` rend `ready:true`, `/missions/m1/tree` rend le nœud avec `torn_tail:events.jsonl:636:15` en anomalie,
`/stats/context` rend `occupancy 0.0671`, `margin_tokens 14772`, `pressure low`, `density 1.222`. Le port
`8823` **refuse la connexion depuis l'adresse LAN de la machine** (curl exit 7) et n'accepte que `127.0.0.1`.
La densité 1,222 est celle d'une **fixture**, pas une mesure de Ling : elle ne dit rien du spike n°4.

**Décidé.** Le catalogue ne retient aucun événement : `scan()` fait une passe et jette. Le détail relit à la
demande, ce qui supprime le cache et rend la fraîcheur gratuite. Pas de thread de surveillance : le suivi
`mtime` est un `refresh()` appelé par la requête, encapsulé — un suivi qui échoue laisse l'index servi avec
`watch_error` visible, ce que `test_readiness_comes_from_the_index_not_from_the_spawn` observe.

**Niveau de preuve atteint** : **6** pour le bind, la lecture disque et les trois routes probées ;
**5** pour le contrat de double ; **4** pour les agrégats et les autres routes (tests métier verts en
process, `TestClient`). Aucun événement d'`engine` ni de `campaign` n'existe : les indicateurs 2, 3 et 5 ne
sont vérifiés que sur des payloads **fabriqués à la forme des émetteurs réels**, pas sur une campagne.

### 07:09 — Écart de lignes constaté, non résorbé

977 L sous `api/` contre une cible de ~550 L, soit **+78 %** ; 1 017 L avec `__init__.py`. Répartition
contre les cibles de `MODULE.md` § 7 :

| Fichier | Cible | Réel | Écart |
|---|---:|---:|---:|
| `api/index.py` | 120 | 171 | +51 |
| `api/render.py` | 100 | 229 | +129 |
| `api/routes.py` | 130 | 249 | +119 |
| `api/stats.py` | 150 | 328 | +178 |
| `__init__.py` | — | 40 | protocole et exports, hors table |

Trois causes mesurables, aucune n'étant du code spéculatif : **le style du dépôt** (ligne vide après
docstring, blocs commentés, littéraux verticaux) coûte une part importante du volume ; **`render.py` porte
`window` et `label`**, que la table ne comptait pas ; **`routes.py` sert dix routes** là où l'interface en
listait huit (`/ready` vient du critère de socle § 8, l'enveloppe `freshness` du piège nommé § 11). Pistes de
réduction pour un successeur, par ordre de rendement : retirer les libellés `question` des indicateurs
(~10 L), fusionner `_artifacts` dans `stats` (~20 L), remplacer les quatre prédicats de `stats.py` par un
accès direct au payload (~30 L, au prix de la lisibilité). **La cible de `MODULE.md` n'a pas été relevée** —
le ratchet reste shrink-only.

### 10:09 — passe transverse : `tests/boundaries/` et `tests/contracts/` sont peuplés

Écrite par l'agent d'intégration, pas par un agent de module. Ce module n'a **pas** été modifié : seuls
ses deux tests transverses ont été déplacés à l'emplacement qu'`AGENTS.md` § 11 leur assigne.

**Découvert au passage, et mesuré** : la suite complète du dépôt **n'était pas collectable**. Chaque
agent ne lançait que `pytest src/<son module>`, vert en isolation ; à l'échelle du dépôt, huit
`test_import_boundaries.py` et sept `test_double_contract.py` entraient en collision de nom de module
pytest, parce que `kernel`, `engine` et `lifecycle` n'avaient pas de `__init__.py`. Les trois ont été
ajoutés, et les quinze fichiers renommés à un nom unique en migrant.

**Mesuré, après la passe** : `pytest -q` à la racine, venv `pithos`, Python 3.12.9 →
**1215 passed, 3 skipped**. Les onze tests de frontière et les neuf corpus de contrat ont été
**prouvés mordants** par injection : une violation d'import réelle dans le code livré de chaque module
rend son test de frontière rouge, et une signature de double divergente rend son contrat rouge.

**Niveau de preuve** : 5 — validé sur double, à l'échelle du dépôt cette fois.

## Blocages

| Quoi | Pourquoi | Ce qui débloquerait | Résolu le |
|---|---|---|---|
| 1. Le vocabulaire de payload d'`engine` et de `campaign` n'existe pas | L'arbre, les nœuds bloqués et les propositions d'arrêt se lisent dans des payloads que personne n'émet encore. L'observatoire lit `payload["node"]` (dump de `kernel.contracts.Node`) et `payload["stop_proposal"]`, par la convention déjà appliquée par `verifier/receipt.py` — un contrat dumpé sous son nom | Qu'`engine` et `campaign` confirment ces deux clés, ou les nomment autrement : dans ce cas, seules `NODE_KEY` (`render.py`) et la clé lue par `indicators` changent | **Résolu pour le banc le 13:09** : état publié dans tree.json, diagnostic d'opération, rapports durables ; qualification de la campagne complète encore à faire. |
| 2. La fenêtre de contexte est une constante de lecture | `bridge` consigne `max_tokens`, `usage` et `prompt_estimate`, mais pas la fenêtre du modèle. `stats.CONTEXT_WINDOW = 16_384` la fixe depuis le nom du modèle et la décision 14 ; une campagne sur un autre modèle rendrait `occupancy` et `pressure` faux sans le dire | Que `bridge` ajoute `context_window` à son payload d'appel — changement hors périmètre, à demander à son agent. `TODO` posé dans `stats.py` | **Résolu le 13:09** : capacité et provenance consignées par bridge, sidecar pour les anciens essais, inconnue sinon ; constante retirée. |
| 3. `npm install` n'a pas été lancé | Le web de v1 (~760 L TSX) ne peut être ni typé, ni buildé, ni testé sans `node_modules`. Installer ces dépendances est un acte que l'humain arbitre, comme le commit | L'accord humain, puis `npm install` dans `src/observatory/web/` | **Résolu le 13:09** : installation autorisée, huit tests et build verts sous Node 26.7.0. |
| 4. Emplacement du test de graphe d'imports et du test de contrat | `AGENTS.md` § 11 les veut dans `tests/boundaries/` et `tests/contracts/`, § 6 interdit d'écrire hors de `src/observatory/`. Même blocage que `kernel`, `journal`, `workspace` et `bridge` | La dérogation de périmètre : déplacer `test_import_boundaries.py` → `tests/boundaries/test_observatory.py` et `test_double_contract.py` → `tests/contracts/test_observatory_double.py` | **Résolu le 10:09** — déplacés par la passe transverse ; suite complète verte. |

## Décisions locales

- **Le catalogue ne garde aucun événement.** `scan()` compte en une passe et jette ; `mission_events()` relit
  à la demande. Un cache aurait ajouté une invalidation à tenir, et la relecture d'une mission de quelques
  centaines d'événements est gratuite. Conséquence assumée : le détail compte **ce qu'il vient de lire**,
  donc il peut dépasser le catalogue d'une mission vivante — `freshness` le dit sur chaque réponse.
- **Aucun thread de surveillance.** Le suivi `mtime` est un `refresh()` appelé par la requête. Il n'y a donc
  aucun watcher à faire tomber : le piège nommé de `MODULE.md` § 11 est supprimé plutôt que géré.
- **L'échappement HTML n'a pas lieu dans l'API.** Les réponses sont du JSON (`application/json`), et
  `status_text` est un transport **texte** pour le CLI et Telegram : y échapper produirait du double
  échappement dans Telegram. Le seul point de rendu HTML est React, qui échappe par défaut. Deux tests
  gardent la frontière : `test_the_api_never_renders_a_document` (aucun `HTMLResponse`, aucun `text/html`)
  et `test_a_payload_carrying_markup_is_served_as_data_not_as_a_document`. **Le port du web doit ajouter
  l'interdiction de `dangerouslySetInnerHTML`** pour fermer l'item.
- **La parenté est fixée par la première entrée d'un identifiant, le statut par la dernière.** Dédup à la
  Langfuse pour la parenté, statut dérivé de la branche à la Prime Agent : les deux règles portent sur des
  champs différents et ne se contredisent pas.
- **`routes.bind()` porte le même nom que `journal.bind()` volontairement** : fixer la source avant de
  servir est le même geste. Le test de graphe d'imports vérifie qu'aucun appel à `journal.bind`,
  `journal.emit` ou `journal.update_json_locked` n'existe dans le module.
- **Les anomalies sont des chaînes préfixées** (`torn_tail:`, `duplicate_id:`, `orphan:`, `unreachable:`,
  `negative_duration:`, `depth_mismatch:`, `invalid_node:`, `unreadable:`, `unusable_ts:`). Le suffixe après
  le dernier `:` est l'identifiant de nœud quand il y en a un — c'est ce qui permet à `flatten_tree` de
  ventiler les anomalies globales sur les lignes concernées.

## Reprises traitées

| Source | Verdict | Fait ? | Note |
|---|---|---|---|
| `villani/trace_summary.py:439-757` — `aggregate_summary_from_events` | Copier | oui | Porté sur notre vocabulaire à trois familles : `stats.daily/tools/context` reconstruisent tout depuis les seuls JSONL, sans base. Le vocabulaire d'événements de Villani (`tool_call_started`, `model_request_completed`) n'existe pas ici. |
| `villani/trace_summary.py:196-427` — anomalies de reconstruction | Adapter | oui | Chaque lecture rend `(données, anomalies)` : `read_events`, `flatten_tree`, `node_entries`. Aucun trou n'est comblé. |
| `villani/trace_summary.py:777-820` — `validate_summary` | Copier | oui | `stats.validate`, écrit sur `ErrorAccumulator` : toutes les violations d'un coup, chacune avec son chemin de champ. |
| `villani/trace_summary.py:11-13` — `AGGREGATION_VERSION` | Copier | oui | `stats.AGGREGATION_VERSION`, porté par chaque agrégat servi et par la version de l'app FastAPI. |
| `villani/trace_summary.py:758-776` — `_build_artifact_manifest` | Copier | oui | `routes._artifacts` : segments, `CONTEXT.md`, `tree.json` et les artefacts nommés par les reçus. Présence et taille, jamais le contenu. |
| `villani/event_recorder.py:35-59` — `build_digest` | Copier | oui | `families` + les 25 derniers événements, fenêtre déclarée. |
| `villani/debug_recorder.py:64-72` — `_safe` | Copier | oui | Trivial ici : processus séparé. Appliqué au suivi `mtime` (`refresh` encapsule `OSError`) et à `_size`. |
| `villani/debug_recorder.py:87-406` — vocabulaire d'enregistrement | Inspirer | non | Liste de référence d'écriture ; l'observatoire n'écrit pas. |
| `villani/debug_recorder.py:414-446` — `write_final_summary` | Copier | non | **Écriture** : appartient au harness, pas à ce module. Consigné comme tel. |
| `pi/…/in-memory-storage-state.ts:62` — index mémoire | Adapter | oui | `build_index` ; pas de DuckDB, pas de collecteur. |
| `pi/…/jsonl/repo.ts:50` — catalogue vs détail | Adapter | oui | `MissionRow` d'un côté, `mission_events` de l'autre. |
| `pi/…/tree-selector.ts:27,121` — aplatir en conservant parenté | Adapter | oui | `flatten_tree` ; le gutter ASCII de Pi n'est pas porté — c'est du TUI, le rendu est côté web. |
| `pi/…/ansi-to-html.ts:63` — échapper avant rendu HTML | Adapter | partiel | L'API ne rend pas d'HTML ; l'item se ferme avec le port du web. Voir § *Décisions locales*. |
| `pi/scripts/stats.ts:86` — statistiques journalières | Adapter | oui | `stats.daily`. |
| `pi/scripts/tool-stats.ts:112` — appels/résultats/erreurs par outil | Adapter | oui | `stats.tools`. |
| `pi/scripts/edit-tool-stats.mjs:157` — inflation d'un patch | Adapter | oui | `splice_inflation` : source émise / changement utile, ce dernier mesuré par préfixe et suffixe communs. |
| `pi/scripts/session-context-stats.mjs:156` — occupation du contexte | Adapter | oui | `stats.context`, avec les quatre paliers de la décision 14 et la densité `mesuré / estimé`. |
| `pi/…/fs-watch.ts:17` — un watcher défaillant ne tombe pas | Adapter | oui | Supprimé plutôt que géré : pas de watcher, un `refresh()` encapsulé par requête. |
| `prime/ca/core/context-tree.ts:76-105` — usage propre vs sous-arbre | Adapter | oui | `own_ms` et `subtree_ms`, distincts et jamais sommés. |
| `prime` — statut dérivé de la branche, jamais stocké | Traduire | oui | Statut = dernière entrée du nœud. |
| `prime` — libellé borné à 80 caractères | Traduire | oui | `render.label`, dérivé du critère et de la cible. |
| `prime/ca/core/event-log.ts:73-111` — parseur injecté | Adapter | non | Notre parseur **est** `journal` : un format, un parseur. L'injection ferait deux lecteurs du même format. |
| `lf/…/treeBuilding.ts:111` — dédup cohérente arbre/détail | Adapter | oui | Première entrée gagnante ; l'identifiant dupliqué produit une anomalie, jamais un second nœud. |
| `lf` LF078 — parcours itératif avec `visited` | Adapter | oui | DFS sur pile ; un cycle rend `unreachable:<id>` au lieu de boucler. |
| `lf` LF079 — durée de span vs enveloppe du sous-arbre | Adapter | oui | `_spans` agrège `max(fin) − min(début)` en remontant. |
| `lf` LF086 — correction silencieuse d'une durée négative | Écarté (contre-exemple) | oui | `own_ms` négatif est servi tel quel avec `negative_duration:<id>`. |
| `lf` LF074/LF075 — périmètre exigé, pagination bornée | Adapter | partiel | `limit`/`offset` bornés et `has_more` partout ; le paramètre `mission` **scope** les agrégats mais n'est pas exigé — les cinq indicateurs sont par nature transversaux. Le coût de lecture est déclaré par `freshness.missions`. |
| `lf` LF076 — projection pure, champs absents visibles | Adapter | oui | `None` partout où rien n'a été observé ; jamais un zéro. |
| `lf` LF081 — budget de rendu en nœuds vs en caractères | Écarté | oui | Écarté par `MODULE.md` § 11 : arbre borné en profondeur et en largeur. |
| `our/observability.py:262-340` — refs de blob | Écarté | oui | Écarté par `MODULE.md` § 11 : payloads déjà bornés. |
| `our/sup/state.py:772-917` — `status_text` | Copier | oui | Rendu `clé: valeur`, aperçu borné à 10 nœuds, `unavailable` pour ce qui n'a pas été observé. |
| `our/od/DEVELOPMENT.md:494-541` — projection over replay | Copier | oui | Rejeu **par démarrage**, jamais par interaction : c'est exactement `build_index`. |
| `oh/…/metrics-store.ts:21` — état métrique vide explicite | Adapter | oui | Aucun `undefined` : `value: null` plus le compte d'observations. |
| `uns/…/lan_access.py:479` — endpoint de statut read-only | Adapter | oui | `/ready` : adresse, état, fraîcheur, erreur — aucun secret. |
| `swe/…/inspector/server.py:188,205` — résultat absent lisible | Adapter | oui | Une mission inconnue est un 404 typé ; un artefact absent est `exists:false, size:null`. |
| `kilo/opencode/src/session/summary.ts:85-99` — champs absents laissés absents | Traduire | oui | Appliqué à tous les agrégats. |
| `kilo` — rejeu d'une campagne sans Ollama | Adapter | oui | Conséquence directe de la lecture disque : `bind(logs_root)` sert n'importe quel jeu de JSONL. |
| `swe/…/compare_runs.py`, `merge_predictions.py`, `run_replay.py` | Adapter | non | **Reporté** de fait : comparer deux campagnes suppose deux campagnes. Aucune n'existe. |
| `F` — registry typé, préprocesseur séparé, sondes parallèles | Adapter | non | Sans objet dans ce module : ni registre d'outils, ni génération, ni sondes multiples. |


### 11:09 — mesure de production et en-tête courant

Passe transverse demandée via TEMPO.md. Aucun code métier ni case de livraison modifié.
Mesure AST/tokenize : **643 lignes de code**, **1017 physiques**, cible globale **550**. Sous-paquets et __init__.py inclus ; tests et doubles exclus.
L’empreinte de l’en-tête couvre les chemins et octets de toute la production.
La nouvelle métrique ne valide aucun item métier et ne relève aucune cible numérique.

**En-tête antérieur conservé** :

```text
**Statut** : en cours — API livrée et verte, `web/` non porté
**Mise à jour** : 07:09
**Lignes** : 1 017 (dont 977 sous `api/`) + 68 de double / ~550 L API · ~700 L web — écart justifié plus bas
```

**Plafond justifié** : 643 code
**Justification** : Les contrats de lecture, l’index des traces, les projections bornées, les agrégats et les routes API totalisent 643 lignes de code. Les 93 lignes au-delà de 550 portent ces contrôles déjà couverts ; le web non livré et ses 700 lignes de cible sont exclus de ce compte.

### 13:09 — projection des essais et métriques sourcées

Le test initial a échoué à la collecte (`build_run_index` absent), puis deux tests de
contexte ont échoué sur les champs de capacité/troncature manquants. Après implémentation :
**101 passed**, 1 avertissement Starlette, corpus observatory + contrat + frontière, Python 3.12.9.
Niveau **5** sur doubles ; lecture des sidecars et agrégats au niveau **4**.

Collection directe explicite, snapshot publié prioritaire sur les intentions, prévisualisation
bornée à 2 Mo et paginée, refus des liens sortants, gates historiques rattachées par empreinte
de source. Aucun JSONL réécrit ni reçu reconstruit. La capacité vient de la trace ou du sidecar,
avec provenance ; sans preuve elle reste inconnue. Comptages séparés par mode et appel réel.

**Plafond justifié** : 899 code
**Justification** : +256 lignes sur le plafond précédent pour lire les trois sources publiées
(événements, arbre, résultat), rattacher les preuves des refus sans reçu, borner les aperçus,
exposer la collection directe et son lanceur local, mesurer troncatures/capacité/modes.
Ce périmètre a été explicitement demandé le 13:09 ; la cible de 550 n'est pas relevée.

### 13:09 — web porté, build et lecture HTTP locale

React/Vite de v1 adapté sans dépendance au graphe Graphify, ni collecteur, ni base.
**7 tests jsdom verts** : polling, réponse périmée, erreur de navigation, readiness indépendante,
pagination des artefacts, pagination du catalogue et échappement du contenu des refus.
Le premier lancement a échoué avant App.tsx (test écrit en premier), puis deux fixtures arbre
ont dû prendre en compte la query de pagination. Build TypeScript/Vite vert, 18 modules.
Node cible **26+** : l'installation initiale depuis web/ utilisait Node 22.17 et émettait deux
EBADENGINE. Commandes exécutées depuis la racine avec Node **26.7.0**, npm **11.19.0** ; lock actualisé.
Blocage npm du 07:09 **résolu le 13:09**, accord utilisateur et dépendances déclarées.

Suite Python après l'API : **1 409 passed, 3 skipped, 7 warnings, 40,27 s**. Skips inchangés
(variantes réelles bridge/campaign/refinery non scénarisables), warnings Starlette/fork conservés.
Les onze mesures STATE passent. Lecture disque du trial réel : 5 gates (avant rouge, candidat vert,
3 variantes vertes), 0 reçu, restored=true, cause tautology ; deux appels, 2 461 tokens rapportés.

API lancée sur 127.0.0.1:8823 ; build web sur 127.0.0.1:5173. Le curl sandboxé échoue (exit 7),
puis la lecture autorisée via le proxy web rend ready=true et le nœud clamp-level bloqué sans anomalie.
**Niveau 6 pour cette lecture HTTP locale**, niveau 4 pour le rendu jsdom.
**Validation visuelle non obtenue** : CUA retourne apps=[] et browsers=[] ; aucun screenshot annoncé.

### 13:09 — distinctions de comptage et contrôle documentaire

Refus de préflight exclus du nombre de requêtes modèle ; intentions de nœud exclues des indicateurs.
Les IDs identiques de deux essais restent indépendants. Les erreurs d'admission sans arbre sont
séparées des nano-étapes réellement démarrées ; leur erreur et les probes refusées restent affichées.
Les rapports de vérification futurs sont conservés dans l'ordre et inspectables dans la vue preuves.
Les huit tests web passent ; mesures d'outils et bilan journalier sont consommés dans la vue Contexte.
**114 passed** pour observatory + contrats/frontière + les 8 tests documentaires. Trois tests ont
rougi avant correction du comptage ; artefact >2 Mo rendu 413, sans total de lignes inventé.

**Plafond justifié** : 902 code
**Justification** : +3 lignes nettes sur 899 pour distinguer préflight/intention/état publié et
rapporter les erreurs d'admission ; traitement des indicateurs simplifié par projection de chaque essai.
Le web reste sous sa cible séparée de 700 lignes physiques de production.

**Niveau de preuve : 2** pour la mesure documentaire ; la suite initiale complète du 11:09 a rendu 1 215 passed et 3 skipped hors sandbox. Le détail des nouvelles validations vit dans tests/STATE.md.

### 13:09 — clôture des preuves de lecture

Suite commune avec l'entrée TUI : **1 444 passed, 3 skipped, 7 warnings en 43,83 s**,
Python 3.12.9/pithos ; huit tests jsdom et build Vite verts sous Node 26.7.0.
Le web porte **373 lignes physiques de production** dans src/, hors tests et configuration.
Les onze STATE passent ; le commentaire de render décrit désormais l'autorité du snapshot publié.

Lecture HTTP réelle via 127.0.0.1:5173 vers 8823 : ready=true, trial-44kcg6ig bloqué sur
tautology, cinq gates, zéro reçu, sept événements, deux appels et 2 461 tokens rapportés.
La cible active retrouve exactement son SHA initial ; selftest-wo3aa7e5 expose le nouveau rapport
de vérification. Les services sont laissés disponibles sur loopback, sans mutation des preuves.
Les trois blocages historiques sont résolus pour le banc ; la campagne complète reste à qualifier.

**Niveau 5** pour les doubles, **4** pour jsdom, **6 limité à HTTP et aux fichiers locaux**.
CUA ne fournit aucun navigateur : la vérification visuelle demeure la prochaine action explicite.
Le statut en cours conserve cette limite ; aucun premier vert réel ni campagne complète revendiqué.
