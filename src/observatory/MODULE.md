# `observatory` — lecture seule, processus séparé

> **Lis [`AGENTS.md`](../../AGENTS.md) avant de commencer.** Ce fichier est ton contrat complet : tu ne
> devrais pas avoir besoin d'ouvrir `docs/`. Ton point d'entrée exact est la rubrique « Prochaine action » de
> [`STATE.md`](STATE.md), à côté de ce fichier.
>
> **Tu ne commites, ne pousses et ne merges jamais.** Tes commits se *proposent* dans [`git.md`](git.md),
> avec les `ga`/`gcmsg` exacts — voir [`AGENTS.md`](../../AGENTS.md) § 7.

**Cible** : ~550 L d'API · ~700 L de web **déjà écrits** · ratchet **shrink-only**
**Dépend de** : `kernel`, `journal`.
**Niveau de dépendance** : 2. **Processus séparé du harness.**
**Stack** : FastAPI · React 19 + Vite. **Pas de DuckDB, pas de SQLite, pas de collecteur permanent.**

## 1. Autorité

`observatory` est en **lecture seule**. Il n'écrit jamais dans l'état du harness, ne touche pas l'arbre, ne
lance pas de mission. Il lit les JSONL **par `journal`** — un format, un parseur — les indexe en mémoire au
démarrage, suit les fichiers par `mtime`, et sert des agrégats.

**Le web est déjà écrit** : ~700 L React 19 + Vite portés de v1, six tests jsdom verts, design fait. Restent
**la vue d'arbre et le rebranchement de la source**.

## 2. Interface publique

```python
# api/index.py
def build_index(logs_root: Path) -> Index:
    "Index mémoire reconstruit depuis le disque au démarrage. Pas de collecteur permanent."

# api/routes.py — catalogue et détail SÉPARÉS
GET /missions                  -> catalogue (léger)
GET /missions/{id}             -> détail
GET /missions/{id}/tree        -> arbre aplati en lignes
GET /missions/{id}/artifacts   -> manifeste (présence, taille)
GET /stats/daily               -> statistiques journalières
GET /stats/tools               -> appels, résultats, erreurs, volume par outil
GET /stats/context             -> occupation du contexte et marge restante par appel
GET /indicators                -> les cinq indicateurs des questions expérimentales
```

## 3. Interdits

- **N'écrit jamais.** Aucun `open(..., "w")` dans ce module, aucune mutation d'état du harness.
- **Ne reparse jamais le JSONL de son côté.** Il lit par `journal`. Deux parseurs du même format divergent,
  c'est une question de temps.
- **Ne binde jamais ailleurs que `127.0.0.1`.** L'adresse est une **constante**, pas un réglage — voir
  `lifecycle` § 5. Aucun chemin de code ne doit pouvoir binder ailleurs.
- **N'importe jamais `engine`, `campaign`, `verifier`, `workspace`, `broker`.**
- **Aucune projection SQLite.** Les JSONL sont la source de vérité (décision 10).

## 4. Pourquoi il n'y a pas de base

v1 avait un `pithos_event_store` de 558 L et un LaunchAgent dont le stdout avait atteint **1,3 Go**. Le
volume attendu par mission se compte en **centaines d'événements**, sans Pi pour produire 12 000
`thinking_delta` — et le streaming est écarté, donc il n'y en aura pas.

**Index mémoire au démarrage, suivi par `mtime`.** C'est tout. Cela supprime le collecteur, la base, et la
classe de bugs qui va avec.

## 5. Les agrégats sont des routes

Les cinq scripts d'analyse de Pi — statistiques journalières, stats par outil, inflation de patch,
**occupation du contexte par appel** — sont implémentés comme routes FastAPI consommées par le web.
**Les cinq indicateurs des questions expérimentales deviennent visibles sans terminal.**

| Question expérimentale | Indicateur à servir |
|---|---|
| Progresse-t-il sans intervention ? | outils vérifiés livrés / cycles consommés |
| Reprend-il après interruption ? | reprises d'arbre sans historique conversationnel |
| Diagnostique-t-il ses limitations ? | nœuds `blocked` avec cause mécanique attribuée |
| Crée-t-il un outil utile, puis le réutilise-t-il ? | outils vérifiés **effectivement appelés** ensuite |
| Converge-t-il et propose-t-il l'arrêt ? | propositions d'arrêt sur épuisement mécanique du backlog |

**Conséquence assumée** : l'analyse expérimentale dépend du dashboard tournant.

## 6. Les règles de rendu d'arbre

Elles viennent de Langfuse, qui a payé chacune :

- **Résistance aux IDs dupliqués** — sinon le graphe devient multiparent et explose.
- **La durée d'un nœud est distincte de l'enveloppe de son sous-arbre.** Ne somme **jamais** des durées
  concurrentes.
- ⚠️ **Ne corrige jamais silencieusement une durée négative** !
  → C'est une anomalie à **conserver et à montrer**, pas un défaut d'affichage à lisser.
- Un état de repli séparé des données, pour qu'un arbre partiel s'affiche quand même.

Et de Villani, la règle absolue : **toute écriture d'observabilité est encapsulée — une panne du recorder ne
casse jamais la mission.** Ici elle est triviale : `observatory` est un autre processus.

## 7. Contenu

| Fichier | Contenu | ~L |
|---|---|---:|
| `api/index.py` | index mémoire, suivi `mtime`, catalogue vs détail | 120 |
| `api/routes.py` | routes de lecture, manifeste d'artefacts, digest par famille | 130 |
| `api/stats.py` | les cinq agrégats + les cinq indicateurs | 150 |
| `api/render.py` | aplatissement d'arbre, `status_text` compact réutilisé par le CLI et Telegram | 100 |
| `web/` | **porté de v1** — reste la vue d'arbre et le rebranchement | ~700 |

## 8. Critères de socle que ce module rend verts

- **Toute projection partielle d'un fichier déclare ce qu'elle omet** : chemin, nombre total de lignes,
  nombre de lignes au-dessus et en dessous de la fenêtre (décision 29).
- Contribue à **aucun service local n'est déclaré prêt sur la base de son spawn** — la readiness vient de
  `lifecycle`, mais c'est `observatory` qui doit l'exposer.

## 9. Le double

`tests/doubles/observatory.py` — rarement utile, `observatory` étant en bout de chaîne. En revanche il
**consomme** le double de `journal`, et il doit être testé contre :

- une **queue déchirée** — le lecteur doit tolérer, pas planter ;
- des **IDs dupliqués** dans l'arbre ;
- une **durée négative** — elle doit être affichée telle quelle, jamais corrigée ;
- un fichier qui grossit **pendant** la lecture.

## 10. Fini quand

- [ ] L'index est reconstruit **au démarrage depuis le disque**, sans collecteur, et suivi par `mtime`.
- [ ] Catalogue et détail sont deux routes distinctes — le catalogue ne charge pas les détails.
- [ ] Une queue déchirée en fin de JSONL **ne fait pas planter** la lecture.
- [ ] Un arbre à IDs dupliqués s'affiche sans exploser en multiparent.
- [ ] Une durée négative est **affichée**, jamais corrigée ni masquée.
- [ ] La durée d'un nœud n'est jamais la somme de durées concurrentes de son sous-arbre.
- [ ] Toute projection partielle déclare chemin, total de lignes, lignes au-dessus et en dessous.
- [ ] Les traces sont **échappées avant rendu HTML** — test avec une charge utile contenant du balisage.
- [ ] Les cinq indicateurs sont servis et cohérents avec un jeu de JSONL de référence.
- [ ] Le bind est `127.0.0.1` **en dur** — test qui vérifie qu'aucune variable d'environnement ne le change.
- [ ] Un test statique confirme qu'aucune ouverture de fichier en écriture n'existe dans le module.
- [ ] Les six tests jsdom portés de v1 passent toujours après rebranchement.

## 11. Pièges connus, et ce qui a été écarté

| Écarté | Pourquoi |
|---|---|
| **Budget de rendu en nœuds distinct du budget en caractères** | notre arbre est borné en profondeur (3) et en largeur (`cap_children`) : il est petit |
| **Les références de blob** | nos payloads sont déjà bornés — 20 000 caractères pour la sortie d'un reçu, tête + queue pour un échec |
| **Toute projection SQLite ou DuckDB** | décision 10 : les JSONL sont la source de vérité |

**Piège nommé** : un watcher défaillant ne doit **pas** faire tomber l'observation. Encapsule le suivi
`mtime` ; s'il meurt, l'index reste servi tel quel, avec une mention visible de sa fraîcheur.

---

## Sources — reprises retenues

**117 lignes.** Chaque pointeur se lit dans `resources/`. Le détail complet et le contexte de chaque partie sont dans [`resources/IMPORT_REPORT.md`](../../resources/IMPORT_REPORT.md).
**Lis la source avant de porter.** Une reprise collée sans être relue est un défaut.

#### A — Villani Code · `resources/villani-code-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| A4.8 | `trace_summary.py:439-757` | `aggregate_summary_from_events` — reconstruit **tout** l'agrégat d'un run depuis les seuls JSONL. ~300 lignes, aucune base. Littéralement la fonction que notre API exécute au démarrage. | **Copier** |
| A4.8 | `trace_summary.py:196-427` | `build_tool_call_records_from_events` — reconstruction **avec la liste des anomalies rencontrées**. Signale ses propres trous au lieu de les combler. | **Adapter** |
| A4.8 | `trace_summary.py:777-820` | `validate_summary` — l'agrégat est **validé contre un contrat** avant d'être servi. | **Copier** |
| A4.8 | `trace_summary.py:11-13` | `AGGREGATION_VERSION` / `TOOL_CALL_SCHEMA_VERSION` — l'agrégat porte la version de la logique qui l'a produit. | **Copier** |
| A4.8 | `trace_summary.py:758-776` | `_build_artifact_manifest` — manifeste des artefacts d'un run, servi tel quel au frontend. | **Copier** |
| A4.8 | `event_recorder.py:35-59` | `build_digest` — comptage par famille + les 25 derniers événements. | **Copier** |
| A4.8 | `debug_recorder.py:64-72` | `_safe` — **toute écriture d'observabilité est encapsulée : une panne du recorder ne casse jamais la mission.** Règle absolue. | **Copier** |
| A4.8 | `debug_recorder.py:87-406` | Vocabulaire d'enregistrement exhaustif, dont **`record_context_compacted`** et `record_mission_state_snapshot`. Liste de référence de ce qu'un runtime doit tracer. | **Inspirer** |
| A4.8 | `debug_recorder.py:414-446` | `write_final_summary` — un run se termine toujours par un résumé écrit. | **Copier** |


#### B — Pi · `resources/pi-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| B3.8 | `packages/agent/src/harness/session/in-memory-storage-state.ts:62` | **Index mémoire reconstruit depuis les enregistrements durables.** Exactement notre choix « pas de DuckDB ». | **Adapter** |
| B3.8 | `packages/agent/src/harness/session/jsonl/repo.ts:50` | Séparer catalogue de missions et chargement détaillé d'une mission. | **Adapter** |
| B3.8 | `packages/agent/src/harness/runtime/reducer.ts:22` | Reducer **pur** de projection pour l'interface. | **Adapter** |
| B3.8 | `packages/coding-agent/src/modes/interactive/components/tree-selector.ts:27` | **Aplatir l'arbre en lignes en conservant parenté et branche active.** Directement la vue d'arbre de P5. | **Adapter** |
| B3.8 | `packages/coding-agent/src/modes/interactive/components/tree-selector.ts:121` | État de repli séparé des données métier. | **Adapter** |
| B3.8 | `packages/coding-agent/src/core/export-html/ansi-to-html.ts:63` | **Échapper les traces avant rendu HTML.** Les traces contiennent de la sortie de commande arbitraire. | **Adapter** |
| B3.8 | `packages/evals/src/vitest-evals/summary.ts:3` | Distinguer résultats scorés, absents, en attente et erreurs. Quatre états, pas deux. | **Adapter** |
| B3.8 | `packages/evals/src/vitest-evals/harness-table.ts:110` | Grouper un essai par entrée et répétition. | **Adapter** |
| B3.8 | `packages/evals/src/vitest-evals/reporter.ts:14` | Index JSONL de runs et références d'artefacts. | **Adapter** |
| B3.8 | `packages/evals/src/vitest-evals/artifacts.ts:87` | **Artefacts associés strictement au run propriétaire.** | **Adapter** |
| B3.8 | `scripts/stats.ts:86` | Statistiques journalières depuis les JSONL. | **Adapter** |
| B3.8 | `scripts/tool-stats.ts:112` | Relier appels, résultats, erreurs et volume par outil. | **Adapter** |
| B3.8 | `scripts/edit-tool-stats.mjs:157` | **Mesurer l'inflation d'un patch par rapport au changement utile.** Métrique directe de la qualité du splice. | **Adapter** |
| B3.8 | `scripts/edit-tool-stats.mjs:243` | Catégoriser mécaniquement les échecs d'édition. | **Adapter** |
| B3.8 | `scripts/session-context-stats.mjs:156` | **Occupation du contexte et marge restante par appel.** Instrumentation de la décision 14 sur 16k. | **Adapter** |
| B3.8 | `packages/agent/src/harness/events.ts:5` | Snapshot et abonnement **sans trou** entre les deux. | **Adapter** |
| B3.8 | `packages/chord/src/services/state.ts:93` | Détecter une rupture de séquence et redemander un snapshot. | **Adapter** |
| B3.8 | `packages/agent/src/harness/utils/adaptive-publisher.ts:18` | Coalescer les rafraîchissements UI sous budget de débit. | **Adapter** |
| B3.8 | `packages/coding-agent/src/utils/fs-watch.ts:17` | **Un watcher défaillant ne doit pas faire tomber l'observatoire.** | **Adapter** |
| B3.8 | `packages/coding-agent/src/core/export-html/index.ts:35` | Export autonome d'une mission avec preuves et métadonnées. | **Adapter** |
| B3.8 | `packages/tui/src/fuzzy.ts:99` · `.../session-selector-search.ts:39` | Recherche locale multi-termes, score stable, expressions entre guillemets. | **Adapter** |
| B3.8 | `packages/evals/src/vitest-evals/summary.ts:212` | Mesures appariées avec couverture explicite. | **Adapter** |
| B3.8 | R | Mesurer le débit sur **l'intervalle effectif de génération**, pas la durée totale du run. | **Adapter** |
| B3.8 | `scripts/cost.ts:52` · `scripts/session-transcripts.ts:37` | Ventilation temporelle ; transcript textuel par blocs bornés. | **Adapter** |
| B3.8 | `scripts/read-tool-stats.mjs:182` | Détecter lectures complètes répétées et coût du contexte. | **Adapter** |


#### C — Kilo Code · `resources/kilocode-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| C3.8 | `opencode/src/session/summary.ts:85-99,170-176` | Résumé de session dérivé des événements, avec champs absents laissés absents. | **Traduire** |
| C3.8 | `opencode/src/lsp/diagnostic.ts:20-28` | Format de rendu des diagnostics, réutilisable pour l'affichage d'un échec d'invariant. | **Traduire** |
| C3.8 | `core/src/util/error.ts:3-72` | Erreurs identifiables par nom après sérialisation. Voir § C3.1. | **Traduire** |
| C3.8 | `opencode/src/bus/index.ts:41-89` | Abonnement sans trou et terminaison explicite. Voir § C3.1. | **Traduire** |
| C3.8 | `opencode/src/storage/storage.ts:53-58` | Magasin arborescent de JSON, lisible sans outil. | **Traduire** |
| C3.8 | `observatory` | Rejeu d'une campagne complète sans Ollama, pour développer le dashboard. | **Adapter** |


#### D — Ouroboros · `resources/ouroboros-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| D3.8 | `our/process_custody.py:233-260,496-560` | Appariement par empreinte **stricte** `(pid, start_time, cmd_sha256)`, jamais par classe de commande. PID mort ou empreinte non concordante ⇒ on n'adopte pas. | **Copier** |
| D3.8 | `our/process_custody.py:12-19` | Scopes `task` / `session` / `daemon` à sémantique de moisson distincte. Notre verrou de campagne et nos subprocess de vérification ne sont pas le même scope. | **Copier** |
| D3.8 | `sup/state.py:177-187` | Procéder sans verrou est un arbitrage de disponibilité assumé (un verrou coincé ne doit pas figer le superviseur), **mais jamais silencieux**. | **Copier** |
| D3.8 | `sup/state.py:33-51` | Sous pytest, tout writer qui résout vers l'arbre de données **vivant** lève. Nos tests écriront sous `~/logs/pithos2/`. | **Copier** |
| D3.8 | `our/agent_startup_checks.py:823-915` | `verify_system_state` — une vérification de démarrage qui émet **un seul événement JSONL typé** portant chaque contrôle et un verdict global. | **Copier** |
| D3.8 | `our/agent_startup_checks.py:916-929` | Réconciliation limitée aux **propriétaires prouvés morts d'une génération antérieure**. Un TTL n'autorise jamais un renvoi payant. | **Copier** |
| D3.8 | `our/agent_startup_checks.py:710-805` | `hot_store_growth_notes` — tripwire déterministe sur la croissance des stores chauds, surfacé au démarrage **et** à chaque tour. | **Copier** |
| D3.8 | `pk/systemd/ouroboros.service:1-24` | **Aucune politique de redémarrage** : *« the launcher owns its crash fuse and treats a panic exit as a complete stop until the owner starts Ouroboros again. »* Directement applicable à nos LaunchAgents. | **Copier** |
| D3.8 | `pk/systemd/README.md:1-40` | Un seul chemin de lancement par instance, verrou d'instance **partagé** par les deux chemins ; l'installation n'active ni ne démarre jamais l'unité. | **Copier** |
| D3.8 | `sk/telegram/lib/telegram_api.py:39-75` | Deux erreurs typées : `TelegramRequestRejected` (réponse négative explicite, `transient` = 429/5xx) et `TelegramTransportError` (pas de réponse). | **Copier** |
| D3.8 | `sk/telegram/lib/telegram_api.py:61-75` | Backoff **monotone partagé** par le poller et le notifier : 5 s → doublement → 60 s, **remis à l'initial par tout tour réussi**. | **Copier** |
| D3.8 | `sk/telegram/lib/telegram_api.py:24-36,82-113` | Découpe de texte en **unités UTF-16**, pas en caractères : la limite Telegram est en UTF-16 et un emoji en compte deux. | **Copier** |
| D3.8 | `sk/telegram/lib/telegram_state.py:37-70` | `_jsonl_tail` renvoyant `(lignes, un_préfixe_a_été_omis)` — un tail borné **déclare** son omission. | **Copier** |
| D3.8 | `od/DEVELOPMENT.md:494-541` | Invariant **Projection over replay** : un lecteur *par interaction* ne rejoue jamais un store qui grandit. Par-boot est autorisé. **Notre choix « index JSONL au démarrage » est conforme** — voir conflit n°7. | **Copier** |
| D3.8 | `our/observability.py:262-340` | `write_blob` / `read_blob_ref` — au-delà d'un seuil le payload devient un **ref content-addressé** ; le résumé porte le ref, jamais la copie. | **Copier** |
| D3.8 | `our/_outcome_receipts.py:529-670` | `receipt_identity_projection` et `verification_receipt_ledger_row` — projection destinée au relecteur portant **le compte omis et un hash durable de l'identité complète** ; une ligne de registre par reçu, prête pour le dashboard. | **Adapter** |
| D3.8 | `our/outcomes.py:1387-1525` | `build_verification_ledger` — registre par tâche construit depuis **les seuls faits d'exécution faisant autorité**, jamais une reformulation. | **Adapter** |
| D3.8 | `sup/state.py:772-917` | `status_text` — rendu texte compact de l'état complet, réutilisé par le CLI, Telegram et le dashboard. **Une seule vue, trois transports.** | **Copier** |


#### E — Prime Agent · `resources/prime-agent-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| E3.8 | `ca/core/context-tree.ts:76-105` | **Usage propre du nœud vs usage total du sous-arbre**, calculé récursivement. Notre vue d'arbre en a besoin. | **Adapter** |
| E3.8 | `observatory` | **L'arbre est reconstruit depuis les répertoires sur disque**, sans passer par le processus vivant. | **Adapter** |
| E3.8 | `observatory` | Le statut d'un nœud est **dérivé de la branche d'entrées, jamais stocké**. Un statut stocké ment dès qu'un enfant change. | **Traduire** |
| E3.8 | `observatory` | Libellé de nœud borné à 80 caractères, dérivé du premier message. Rendu lisible sans champ dédié. | **Traduire** |
| E3.8 | `ca/core/event-log.ts:73-111` | `replaySync(parse)` — **le parseur est injecté par le consommateur**, qui décide ce qu'il rejette et ce qu'il saute. Un même journal sert plusieurs vues. | **Adapter** |
| E3.8 | `ca/core/semantic-edges.ts:383-424` | La lecture renvoie **les événements valides et la longueur valide**, ce qui permet à l'écrivain de reprendre au bon offset. | **Traduire** |
| E3.8 | `sk/agent-observe/SKILL.md` | **Surface d'observation strictement en lecture seule, bornée par la famille** (parent, frères, enfants directs), `limit` 1-50 et `max_chars` 80-2000 imposés. | **Inspirer** |
| E3.8 | `ca/core/refinement/refinement.ts:508-517` | **L'historique d'auto-amélioration est visible dans le prompt lui-même** : `recent refinements: N`, les 5 derniers, `+N older`. | **Traduire** |


#### F — Unsloth · `resources/unsloth-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| F3.6 | `unsloth/registry/registry.py:20,56` | Registry **typé** avec métadonnées ; **enregistrement explicite par famille plutôt que découverte dynamique** depuis le modèle. Analogue direct de notre registre d'outils. | **Adapter** |
| F3.6 | `unsloth/dataprep/raw_text.py:318` | **Nettoyage textuel déterministe avant génération** d'un invariant ou d'un prompt. | **Adapter** |
| F3.6 | `unsloth/dataprep/raw_text.py:307,328` | Préprocesseur **séparé du loader**, sans effet caché ; extraction de sections **par motifs fermés**. | **Adapter** |
| F3.6 | `unsloth/dataprep/synthetic.py:459` | Découper un corpus en **unités traitables avant lancement**. | **Adapter** |
| F3.6 | `unsloth/dataprep/synthetic.py:517` | Génération QA à paramètres bornés et sortie inspectable — **candidat pour produire des fixtures, jamais une preuve**. | **Adapter** |
| F3.6 | `unsloth/models/rl.py:921` | Vérifier qu'une borne tient **avant toute itération coûteuse**. | **Adapter** |
| F3.6 | `unsloth/models/rl.py:1036` | **Inspecter la première ligne sans consommer un flux**, pour valider sa forme. | **Adapter** |
| F3.6 | `studio/backend/mcp_server.py:263` | Agréger plusieurs sondes d'état **en parallèle** puis restituer un snapshot cohérent. | **Adapter** |
| F3.6 | `unsloth_cli/commands/start.py:1145,1152` | Queue récente de logs **bornée en lignes**, et **rédaction systématique des tails avant projection** à l'utilisateur ou au modèle. Troisième source. | **Adapter** |
| F3.6 | `unsloth_cli/_inference.py:69` | **Distinguer erreur différée côté serveur, corps incomplet et erreur HTTP** dans l'affichage. Trois causes, trois messages. | **Adapter** |
| F3.6 | `unsloth_cli/_inference.py:882` | Refus de connexion avec **raison courte et stable, exploitable dans un finding**. | **Adapter** |
| F3.6 | `studio/backend/lan_access.py:479` · `cloudflare_tunnel.py:686` | Endpoint de statut **read-only** : adresse, port, état, erreur, génération — **sans jamais exposer le token de contrôle**. | **Adapter** |
| F3.6 | `studio/backend/startup_banner.py:1` | Bannière de démarrage lisible : endpoints, mode réseau, **avertissement sur l'exposition des outils**. | **Adapter** |


#### G — OpenHands · `resources/OpenHands-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| G3.7 | `src/manifests/automation-insights.ts:81` | **Statuts terminaux énumérés avant agrégation.** | **Adapter** |
| G3.7 | A | **Prédicat de succès distinct du prédicat d'échec** ; durée compacte formatée **sans perdre la valeur nulle**. | **Adapter** |
| G3.7 | `src/api/agent-server-compatibility.ts:302` | Message d'incompatibilité **stable et actionnable**. | **Adapter** |
| G3.7 | `src/api/agent-server-compatibility.ts:214` | **Version serveur et version SDK affichées séparément.** | **Adapter** |
| G3.7 | `src/stores/metrics-store.ts:21` | **État métrique vide explicite**, évitant les `undefined` dans les cartes. | **Adapter** |
| G3.7 | `src/services/telemetry.ts:104,224,416` | **Hard-disable de la télémétrie indépendant du consentement applicatif** ; configuration depuis **un seul service propriétaire** ; état de consentement exposé par une **API stable**. | **Adapter** |
| G3.7 | `src/services/telemetry.ts:209` · `src/services/telemetry-context.ts:33` | Propriétés comparées **avant mutation** pour éviter les événements redondants ; propriétés normalisées **sans données brutes**. | **Adapter** |
| G3.7 | `src/stores/use-workspace-mutation-counter.ts:41` | **Cache-buster explicite après mutation** du workspace. | **Adapter** |
| G3.7 | `src/constants/server-connection-error.ts:1` | Message d'erreur de connexion **constant**. | **Adapter** |


#### H — SWE-agent · `resources/SWE-agent-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| H4.6 | `sweagent/run/batch_instances.py:32,39` | **Source d'instances abstraite** ; instance typée avec **identifiant et problème séparés**. | **Adapter** |
| H4.6 | `sweagent/run/batch_instances.py:48,67,195` | Parser de slice `start:stop` pour un **sous-ensemble reproductible** ; filtrage **avant consommation de ressources**. | **Adapter** |
| H4.6 | `sweagent/run/compare_runs.py:8,69` | Résoudre l'ensemble des runs terminés ; **comparer deux campagnes en distinguant mêmes résultats et divergences**. | **Adapter** |
| H4.6 | `sweagent/run/merge_predictions.py:13` | Fusionner plusieurs sorties **sans réécrire les trajectoires sources**. | **Adapter** |
| H4.6 | `sweagent/run/remove_unfinished.py:13` | Identifier les runs inachevés — **dry-run par défaut**. | **Adapter** |
| H4.6 | `sweagent/run/run_traj_to_demo.py:27,35` | Transformer une **trajectoire validée en démonstration réutilisable**, conversion contrôlée. | **Adapter** |
| H4.6 | `sweagent/run/hooks/swe_bench_evaluate.py:1` · `hooks/apply_patch.py:1` | Évaluation post-run et application de patch **isolées du runner**. | **Adapter** |
| H4.6 | `sweagent/inspector/server.py:15,39,168` | Section problème ajoutée au rendu ; **état de sortie ajouté explicitement** ; trajectoire chargée en **structure JSON portable**. | **Adapter** |
| H4.6 | `sweagent/inspector/server.py:61,147,188,205` | Patches affichés **séparément du texte** ; résumé compact d'actions ; **résultat absent chargé comme état lisible plutôt qu'exception opaque** ; statut **déduit des artefacts présents**. | **Adapter** |
| H4.6 | `sweagent/inspector/static.py:86,155` | Arbre de fichiers relatif pour naviguer dans un diff ; **vue statique partageable sans backend actif**. | **Adapter** |
| H4.6 | `sweagent/run/quick_stats.py:16` | Résumé de campagne **sans charger tous les détails dans le contexte modèle**. | **Adapter** |


#### I — Langfuse · `resources/langfuse-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| I4.8 | `web/src/features/mcp/server/observations/schema.ts:137` | **Projection compacte par défaut** : identité, type, statut, temps, liens ; entrées/sorties/métadonnées **chargées à la demande**. | **Adapter** |
| I4.8 | LF073 | **Pagination bornée et champs explicitement admis**, wildcard exclusif. | **Adapter** |
| I4.8 | LF074 | **Une lecture coûteuse est subordonnée à un périmètre** : nœud, mission, identifiant ou intervalle **exigés avant gros IO**. | **Adapter** |
| I4.8 | LF075 | `limit+1` pour `hasMore` ; **curseur opaque** adapté aux journaux — génération de segment et offset vérifié. | **Adapter** |
| I4.8 | LF076 | **Projection pure indépendante de la collecte** ; les champs absents restent visibles ; une troncature d'aperçu **se déclare**. | **Adapter** |
| I4.8 | `web/src/features/traces/fns/treeBuilding.ts:111` | **Déduplication cohérente entre arbre et détail** — un ID dupliqué crée sinon un graphe multiparent explosif. | **Adapter** |
| I4.8 | LF078 | **Parcours itératif avec ensemble `visited`**, agrégation bottom-up, garde contre les visites multiples. | **Adapter** |
| I4.8 | LF079 | **Durée du span distincte de l'enveloppe temporelle du sous-arbre** — `max(fin) − min(début)` quand des enfants dépassent le parent. **Ne pas sommer les durées.** | **Adapter** |
| I4.8 | LF080 | **Sérialisation unique** réutilisée pour la taille, l'aperçu et le téléchargement ; échec de sérialisation → erreur visible. | **Adapter** |
| I4.8 | LF081 | **Budget de rendu en nœuds distinct du budget en caractères** — une chaîne énorme est une ligne, un JSON imbriqué des milliers. | **Adapter** |
| I4.8 | `packages/shared/src/features/query/server/queryBuilder.ts:140` | **Catalogue fermé d'agrégations** : compteurs, percentiles, histogrammes. Reprendre le contrat de requête validée, pas le query builder. | **Adapter** |
| I4.8 | `web/src/features/score-analytics/lib/statistics-utils.ts:169` | **Accord avec effectif et données absentes explicites** ; retourner « inconnu » sans observations. | **Adapter** |
| I4.8 | LF084 · **I** | Mesure d'accord corrigée du hasard — **ne pas copier sans revue**, le cas dégénéré est délicat. | **Adapter** |
| I4.8 | `worker/src/services/IngestionService/index.ts:1240` | **Ordre déterministe de fusion des événements.** Chez nous : ordre par séquence hôte. | **Adapter** |
| I4.8 | LF086 · **X** | **Correction silencieuse d'une durée négative** — à écarter : une fin antérieure au début est **une anomalie à conserver et à montrer**. | **Adapter** |
| I4.8 | `packages/shared/src/server/ingestion/sampling.ts:6` | Échantillonnage cohérent au niveau trace — **interdit sur les traces brutes**, utile en analyse dérivée seulement. | **Adapter** |
| I4.8 | `packages/shared/src/utils/IORepresentation/parseIO.ts:3` | **Le compactage est une tentative explicite ; son échec rend l'original.** | **Adapter** |
| I4.8 | `packages/shared/src/utils/json.ts:9` | **Réparation textuelle de pseudo-JSON** — à écarter de l'admission : remplacer `True`/`False`/`None` et les apostrophes **peut changer une chaîne valide métier**. | **Adapter** |

