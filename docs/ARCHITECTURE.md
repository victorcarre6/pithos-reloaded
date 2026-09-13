# Architecture — modules, stack et reprises

Document de référence de la découpe en modules, des choix de librairies et du **code repris de Villani
Code**. Les décisions conceptuelles qui les motivent sont dans [`EXPLANATIONS.md`](EXPLANATIONS.md).

## Interfaces observables — 13:09

Cette table distingue les points d'entrée **livrés** des objectifs encore **prévus**.
`pytest tests/test_doc_check.py` lit cette table et contrôle les noms, l'ordre des paramètres,
leur passage positionnel/nommé et leur caractère obligatoire. `...` indique un paramètre
optionnel ; ni sa valeur par défaut ni les annotations ne sont validées par ce contrôle.
Les contrats Pydantic et les corpus de doubles restent l'autorité pour les types et comportements.
Ce n'est pas un inventaire exhaustif de tous les symboles ; chaque module y a un point d'entrée réel.

| État | Module importable | Signature |
|---|---|---|
| livré | `kernel.codeview` | `symbols(path)` |
| livré | `journal` | `read(path)` |
| livré | `journal` | `torn_tail(path)` |
| livré | `verifier` | `preflight(criterion, source)` |
| livré | `verifier` | `run(criterion, facts, *, artifact_root, timeout)` |
| livré | `bridge` | `candidate_model(function_name)` |
| livré | `bridge` | `call(schema, system, user, deadline)` |
| livré | `bridge` | `probe()` |
| livré | `workspace` | `splice(target, function_name, new_source, *, root, view=..., trace=...)` |
| livré | `engine.attempt` | `run_attempt(tree, node_id, budget, deps, *, tree_path, artifact_root, system, instruction, attempt)` |
| livré | `engine.context` | `assemble(node, budget, *, items, fingerprints)` |
| livré | `campaign` | `admit(proposal)` |
| livré | `campaign` | `project(entries, current, failed_modules)` |
| livré | `lifecycle.custody` | `wait_ready(probe, deadline)` |
| livré | `broker` | `record_intent(ledger, identity, intent, *, trace=...)` |
| livré | `observatory` | `build_index(logs_root)` |
| livré | `observatory` | `build_run_index(runs_root)` |
| livré | `observatory` | `flatten_tree(events, *, snapshot=...)` |
| livré | `observatory.api.routes` | `bind_runs(runs_root)` |
| livré | `refinery` | `gate(edit, before, after)` |
| prévu | `engine.walk` | `walk(tree, budget, deps)` |
| prévu | `engine.context` | `dump(mission_id, packet, verdict)` |

## Principe de découpe

**Un module est défini par ce dont il est l'autorité.** Les dépendances sont strictement descendantes, sans
cycle. **Trois règles** portent tout le reste, et chacune est un test de graphe d'imports — pas une
discipline de relecture :

> `verifier` n'importe jamais le modèle, et n'a d'I/O que sur ce qu'il a lui-même produit.
> `bridge` n'importe jamais la boucle.
> `broker` est le seul module par lequel une donnée quitte la machine.

Les deux premières sont l'inversion de v1, où l'oracle appelait le modèle, qui appelait le contrôleur, qui
rappelait l'oracle. Ici, la couche qui décide de la vérité est **en dessous** de celle qui parle au modèle.
La troisième rend la **contrainte dure n°5** — souveraineté — mécaniquement vérifiable.

## Carte

| # | Module | Autorité sur | Dépend de | Cible |
|---|---|---|---|---:|
| 1 | `kernel` | vocabulaire, AST, contrats, **faits et forme du reçu** | — | ~380 L |
| 2 | `journal` | **la durabilité** : JSONL append-only, `live.log`, lecture | 1 | ~400 L |
| 3 | `verifier` | **la vérité**, et l'autorité d'émettre le reçu | 1-2 | ~950 L |
| 4 | `bridge` | **la frontière modèle** | 1-2 | ~250 L |
| 5 | `workspace` | **le filesystem** | 1-2 | ~200 L |
| 6 | `engine` | l'arbre, le contexte, le budget | 1-5 | ~1 050 L |
| 7 | `campaign` | **le magasin**, propositions, redondance, arrêt | 1-6 | ~550 L |
| 8 | `lifecycle` | verrou, launchd, custody de processus, garde disque | 1-2 | ~250 L |
| 9 | `broker` | **la seule sortie de données** : Git + Telegram | 1-2 | ~550 L |
| 10 | `observatory` | lecture seule, processus séparé, agrégats | 1-2 | ~550 L + 700 L web |
| 11 | `refinery` | politique d'auto-amélioration : `propose` + `gate` | 1-7 | ~100 L |

**Niveaux de dépendance**, testés comme graphe d'imports :

```text
niveau 0   kernel                                          aucun import interne
niveau 1   journal                                         kernel
niveau 2   verifier · bridge · workspace                   kernel, journal
           lifecycle · broker · observatory
niveau 3   engine                                          niveaux 0-2
niveau 4   campaign                                        niveaux 0-3
niveau 5   refinery                                        niveaux 0-4
```

`journal` possède **le format**, donc les deux sens : `observatory` lit par lui plutôt que de reparser le
JSONL de son côté. Un format, un parseur.

**~5 230 lignes de harness Python visées**, contre 8 000 en v1, avec un `verifier` nettement plus capable.
Ordres de grandeur, pas des mesures.

> **Deux révisions du chiffre, le même jour.** La cible du cadrage était de ~3 000 L ; elle a été relevée à
> ~5 900 après comptage des portages — les seize fichiers Python marqués « entier » totalisent à eux seuls
> **4 885 lignes**. Puis la **passe de simplification module par module** l'a ramenée à ~5 230, en écartant
> environ **380 reprises sur 1 180** — presque toutes défendant contre un **agent libre** que la contrainte
> dure n°1 et la décision 6 avaient déjà supprimé.
>
> Un plafond relevé ne mord plus par lui-même : la discipline de taille repose sur le **ratchet shrink-only
> par module** de la décision 25, inscrit dans chaque `MODULE.md`.

**`engine` est devenu le plus gros module**, devant `verifier` : le classifieur déterministe de Villani et la
sélection de fichiers y ont atterri, pendant que `verifier` perdait 600 L de gardes.

**Modules à la racine de `src/`**, sans package intermédiaire : `src/kernel/`, `src/verifier/`, … v1
publiait douze packages installables pour une seule chose déployée. `observatory` garde ses dépendances
propres — autre processus, autre cycle de vie — mais vit au même endroit que les autres.

## Développement par module

Onze modules, ~5 230 lignes, un seul développeur. Le seul ordre qui ne repousse pas les erreurs de découpe à
l'intégration est celui où **chaque module se développe contre un double, jamais contre son voisin**
(décision 32).

### Ce que chaque module publie

| Livrable | Où | Rôle |
|---|---|---|
| **interface** | `src/<module>/__init__.py` | `typing.Protocol` pour le comportement, modèles Pydantic pour les données |
| **double conforme** | `tests/doubles/<module>.py` | ce contre quoi les autres modules se testent |
| **`MODULE.md`** | `src/<module>/MODULE.md` | la spécification complète, colocalisée avec le code |

Un test de conformité vérifie que le double et l'implémentation satisfont le même protocole — sans quoi le
double dérive et les tests deviennent décoratifs.

**Le double est un test de l'architecture, pas seulement du code.** Si le double de `workspace` doit
simuler un état interne pour que `verifier` passe, c'est que `verifier` lit le monde au lieu de recevoir des
faits, et la règle de la décision 13 est violée **avant** la première ligne d'implémentation.

### Les huit rubriques d'un `MODULE.md`

Structure identique pour les dix, pour qu'une session sur un module n'ait rien d'autre à ouvrir.

| Rubrique | Contenu |
|---|---|
| **Autorité** | ce dont ce module est seul propriétaire, en une phrase |
| **Interface** | les `Protocol` et modèles Pydantic exportés |
| **Interdits** | ce qu'il ne doit jamais importer, et pourquoi |
| **Cible** | `<N>` lignes — ratchet shrink-only (décision 25) |
| **Reprises** | `\| Cible \| Source \| Notion \| Verdict \|`, filtré depuis `IMPORT_REPORT.md` |
| **Critères** | ceux des 27 critères de socle que ce module rend verts |
| **Double** | ce que `tests/doubles/<module>.py` doit simuler |
| **Fini quand** | la liste exacte des tests qui doivent passer |

**Le registre propose, le `MODULE.md` engage** : une reprise n'est promue à `Copier` ou `Traduire` que dans
le `MODULE.md` du module qui la porte, avec son pointeur exact.

### Ordre de construction

**Tranche verticale d'abord.** `kernel` minimal → `journal` (append + `fsync` + relecture) → `verifier`
(une relation, une gate) → `workspace` (splice + copie d'octets) → `engine` (`walk` sans Prefect) →
`bridge`, jusqu'au jalon **« premier vert »** :
une nano-étape, un invariant, un mutation-check, un reçu, un fichier réellement modifié — de bout en bout.

Puis chaque module s'élargit à sa cible dans l'ordre P0→P9 de la roadmap. La tranche prouve l'emboîtement
des dix frontières pendant qu'une erreur de découpe coûte encore peu.

### Arborescence

```text
~/code/pithos_reloaded/
├── docs/          PROJECT · EXPLANATIONS (décisions + journal) · ARCHITECTURE · ROADMAP
├── src/
│   ├── kernel/      MODULE.md  contracts · facts · codeview · errors
│   ├── journal/     MODULE.md  write · read · redact
│   ├── verifier/    MODULE.md  relations · domains · mutation · gates · receipt
│   ├── bridge/      MODULE.md  client · schema · revalidate · probe · prompt/
│   ├── workspace/   MODULE.md  splice · guard · sandbox
│   ├── engine/      MODULE.md  walk · flow · context · budget · classify
│   ├── campaign/    MODULE.md  store · registry · propose · admit · stop · mcpconfig
│   ├── lifecycle/   MODULE.md  lock · launchd · custody · disk
│   ├── broker/      MODULE.md  git · telegram
│   ├── observatory/ MODULE.md  api/ (FastAPI) · web/ (React 19 + Vite)
│   └── refinery/    MODULE.md  propose · gate
├── tests/
│   ├── doubles/     un double conforme par module
│   ├── contracts/   conformité double ↔ implémentation
│   └── boundaries/  graphe d'imports — les trois règles structurantes
├── journals/        snapshots des mutations de registre
└── resources/       MANIFEST.md · IMPORT_REPORT.md — les neuf dépôts sont hors dépôt Git
```

Le **produit** — le serveur MCP construit par le système — vit dans un dépôt Git séparé (décision 4).

---

## Sources de reprise

Deux dépôts sont montés en lecture sous `resources/` :

- **`villani-code-main/`** — runtime d'agent codant local-first, 21 512 L. Défend la même thèse que nous et
  la chiffre : Terminal-Bench 2.0 à **44,0 % avec Qwen3.6 27B** contre 40,1 % pour Claude Code + Sonnet 4.5,
  et **63,3 % contre 43,3 % à modèle identique** (Qwen3.5 9B, 6 tâches gagnées, 0 perdue). C'est la source
  principale de garde-fous. Projet personnel, copie libre.
- **`pi-main/`** — runtime Pi, 1 673 fichiers / 397 645 lignes, **MIT**. Le runtime qui portait Pithos v1 ;
  la décision 6 l'a retiré du chemin nominal, mais il reste la meilleure source sur les **contrats de
  durabilité et de reprise** d'un runtime réellement exploité : ordre d'écriture, réconciliation après crash,
  frontière de la contrainte de décodage, annulation qui ne tue pas l'effet. **185 reprises**, cataloguées
  dans [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § Partie B.

- **`kilocode-main/`** — monorepo Effect-TS d'environ 1 M lignes, fork d'OpenCode, **MIT**. Corpus de
  garde-fous industriels : transactionnalité filesystem (snapshot Git fantôme, compare-and-swap, verrou à
  heartbeat), confinement `sandbox-exec` sans conteneur, normalisation de JSON Schema pour le décodage
  contraint. Et surtout un **prompt système et des paramètres d'échantillonnage spécifiques à la famille
  `ling`** — notre modèle exact. **173 reprises**, catalogue en [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § Partie C.

- **`ouroboros-main/`** — agent auto-modifiant à identité persistante, **222 035 lignes de Python**, MIT,
  papier arXiv associé. Terminal-Bench 2.1 à **86,74 %**. Seul dépôt écrit dans notre langage, et **seul des
  quatre à avoir construit la machinerie complète de la preuve d'effet** : reçu attesté par l'hôte, relation
  de réconciliation prouvée transitive, trois capteurs de faux-vert. **~200 reprises**, catalogue en
  [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § Partie D.

- **`prime-agent-main/`** — *« A Self-Improving RLM Harness »* de Prime Intellect, TypeScript avec un cœur
  Python de 4 581 lignes, MIT, papier arXiv. **Seul dépôt des cinq à implémenter l'auto-amélioration au fil du
  cycle de vie de bout en bout** — mais en boucle ouverte, sans jamais vérifier qu'elle améliore quoi que ce
  soit. **~110 reprises**, catalogue en [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § Partie E.

- **`unsloth-main/`** — bibliothèque de fine-tuning, ~2,1 M lignes, **licence mixte dont AGPL pour `studio/`**.
  Seul non-runtime du lot : sa valeur est dans `unsloth_cli/` et `studio/backend/`, qui traitent frontalement
  la **politique d'exposition réseau**, le cycle de vie d'un service local et la garde des répertoires
  système. **~110 reprises**, catalogue en [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § Partie F. **Aucune copie littérale
  depuis `studio/`** — les notions sont reprises, le code est réécrit.

- **`OpenHands-main/`** — frontend Agent Canvas d'OpenHands, ~373 K lignes TypeScript. Seul des sept à
  formaliser un **contrat d'admission de données déclaratives** de bout en bout : validation par regex,
  alphabet sans métacaractères shell, placeholders fermés sans expression évaluable, et **accumulateur
  d'erreurs par chemin de champ**. **~110 reprises**, catalogue en [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § Partie G.
  Aucune copie de code : les reprises sont conceptuelles.

- **`SWE-agent-main/`** — agent codant compact, **14 891 lignes de Python**, MIT. Le plus petit et le plus
  lisible des huit. Apporte un **catalogue de douze parsers fermés** pour lire la sortie d'un modèle sans tool
  calling natif, des history processors composables, la **rejouabilité d'une trajectoire sans rappeler le
  modèle**, et — dans la zone qu'une extraction automatique avait omise — **la projection de fichier qui
  déclare ce qu'elle cache**. **~95 reprises**, catalogue en [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § Partie H.

- **`langfuse-main/`** — plateforme d'observabilité LLM, **1,2 M lignes**, MIT hors `ee/`. Apporte la chaîne
  **observation → évaluation identifiée → résultat versionné → lecture reproductible** : identité de résultat
  déterministe distincte de l'identité de transport, cycle de vie de run avec fencing, lecture bornée de
  grosses traces, et versionnement à label mobile pour `refinery`. **105 reprises**, catalogue en
  [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § Partie I. Extraction **vérifiée : 15 ancres sur 15 exactes**.

Les neuf sources sont complémentaires : Villani dit **quoi mesurer**, Pi **comment ne pas perdre la mesure**,
Kilo **comment ne pas corrompre ce qu'on mesure** et seul des neuf **ce que Ling rate en pratique**, Ouroboros
**comment prouver qu'on a mesuré**, Prime Agent **comment le harness s'améliore lui-même**, Unsloth **à
quelles conditions ce qu'on a construit a le droit d'être joignable**, OpenHands **comment admettre une
donnée déclarative sans jamais l'évaluer**, SWE-agent **comment une projection déclare ce qu'elle cache**,
Langfuse **comment republier un résultat sans le compter deux fois**.

**Convention des tableaux de reprise :** chaque ligne se lit `cible -> <dépôt>/<fichier>:<ligne> -> notion`.
**Quatre verdicts**, depuis le 06:09 — le précédent vocabulaire ignorait que cinq sources sur neuf sont en
TypeScript, où « copier » ne veut rien dire :

| Verdict | Ce que ça veut dire | Obligation dans le fichier dérivé |
|---|---|---|
| **Copier** | Python, porté quasi tel quel | notice de licence de la source conservée |
| **Traduire** | TypeScript → Python, ligne à ligne, structure préservée | en-tête `PORTED_FROM: <dépôt>/<fichier>:<lignes>` |
| **Adapter** | l'idée est juste, l'implémentation suppose leur objet de session | relecture obligatoire, aucune copie |
| **Inspirer** | la structure de données vaut mieux que le code | aucune |

Distribution : **250 Copier · 126 Traduire · 101 Adapter · 40 Inspirer** sur les quatre parties qui portent
une colonne `Verdict`. Les cinq autres ont un défaut déclaré au niveau de la partie — voir
[`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § *Les quatre verdicts*.

> Les tableaux *Reprises de Villani* de ce document regroupent les reprises **par module**, pour le travail
> d'implémentation. [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) porte le même catalogue organisé **par nature du
> changement**, avec ce que chaque reprise a modifié dans la documentation. Les lignes sont identiques,
> l'axe diffère ; **toute correction se fait dans `IMPORT_REPORT.md` en premier.**

---

## 1. `kernel` — le vocabulaire

`contracts` (modèles typés) · `facts` (ce que les modules à effets remontent à `verifier`) · `codeview`
(lecture AST du workspace) · `errors` (une classe de base, un enum de cause fermé, un accumulateur à chemin
de champ).

**Cinq modèles au socle**, ceux que la tranche verticale traverse : `Node`, `Criterion`, `Event`,
`FileFact`, `Receipt`. `Proposal` et `ToolEntry` arrivent avec `campaign`, `RepoFact` avec `broker`,
`HostFact` avec `lifecycle` — **un contrat s'écrit quand son producteur existe.**

**`Node.target` est un `Path`, pas une liste.** La contrainte dure n°3 — « son fichier cible », au singulier —
cesse d'être une convention : une nano-étape qui voudrait toucher deux fichiers ne peut pas se construire.

**`kernel` porte la *forme* du reçu, jamais l'autorité de l'émettre** — celle-ci appartient à `verifier`
seul (décision 13 amendée). Le vocabulaire est en bas, la décision au-dessus.

**Une seule hiérarchie d'erreur** : une classe de base plus un **enum de cause fermé**, pas une classe par
cas d'échec comme chez Kilo. L'enum se compose directement avec l'accumulateur à chemin de champ de la
décision 28 — le mécanisme vit ici, les **règles** d'admission vivent dans `campaign`.

**Pydantic v2.** Le choix pivot : *une* définition sert de type Python, de schéma de contrainte envoyé au
modèle, et de validation au retour. v1 maintenait des dataclasses **et** des JSON Schema séparés.

**`ast` stdlib.** v1 vérifiait les symboles par regex `def <nom>(` et s'est fait avoir sur l'arité —
`smooth_levels(0.0, 0.0, 0.0)` sur une signature `(tuple, tuple, float)`. L'AST donne arité, défauts,
kwonly et annotations gratuitement.

**`codeview` lit et parse, il ne choisit pas.** AST, symboles, arité, `def` de niveau module, snippet borné,
détection de binaire, `classify_repo_path`. La **sélection** — `relevant_files`, `impact_files`, fermeture
d'imports, scoring — vit dans `engine/context` : c'est du contexte, pas du vocabulaire. Et au socle, ni index
persistant ni reconstruction incrémentale : ils arrivent quand relire le dépôt de campagne coûtera quelque
chose. **~180 L au lieu de ~350.**

> **`trace` a quitté ce module** le 06:09 pour devenir `journal`. Il portait ~55 reprises — rotation,
> quarantaine, séquence dense, validation incrémentale de reprise — soit plus que la cible de `kernel` tout
> entier. Ce n'était pas du vocabulaire mais un moteur de stockage durable.

### Reprises de Villani

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `contracts` | `mission_state.py:12-95` | État sérialisable avec `verified_facts`, `open_hypotheses`, `steps`, `intended_targets`, `validation_failures`, et `from_dict` défensif — chaque champ recoercé. Modèle direct de notre `Node`. | Inspirer |
| `contracts` | `mission_state.py:114-117` | `new_mission_id()` — horodatage UTC triable **avec sous-seconde** explicitement pour éviter les collisions dans la même seconde. | Copier |
| `contracts` | `mission_state.py:162-171` | `load_resume_bundle` — la reprise charge état + messages + résumé en un appel typé. | Adapter |
| `codeview` | `indexing.py:69-114` | `RepoIndex.build/save/load/needs_rebuild` — index de fichiers avec symboles et snippet borné, persisté en JSON. | Adapter |
| `codeview` | `indexing.py:117-127` | `compute_repo_fingerprint` — SHA-256 de `path:size:mtime` pour invalider un index sans le relire. Réutilisé par l'index mémoire du dashboard. | Copier |
| `codeview` | `indexing.py:146-150` | `extract_snippet` — lecture bornée en octets **et** en lignes avant tout parsing. | Copier |
| `codeview` | `repo_rules.py:44-51` | `is_ignored_repo_path` — un seul prédicat partagé par le planner, le verifier et le reporting. v1 avait cette logique dupliquée dans quatre modules. | Copier |
| `codeview` | `repo_rules.py:54-68` | `classify_repo_path` → `vcs_internal` / `editor_artifact` / `runtime_artifact` / `generated` / **`authoritative`**. Voir décision 12. | Copier |
| `codeview` | `repo_rules.py:71-91` | `is_authoritative_doc_path` — restreint la doc éditable au `README` racine et à `docs/*`. | Adapter |
| `trace` | `runtime_events.py:28-34` | `RuntimeEvent` porte un flag **`durable`** : un événement de statut éphémère ne pollue pas la preuve. Voir décision 10 amendée. | Copier |
| `trace` | `runtime_events.py:8-25` | `RuntimeEventChannel` / `RuntimeEventType` — deux enums fermées : le canal (qui écoute) et le type (quoi). | Copier |
| `trace` | `runtime_events.py:37-127` | `from_runner_event` — table de correspondance unique entre événements bruts et typés, avec repli explicite. | Inspirer |
| `trace` | `event_recorder.py:20-33` | Une ligne JSONL = `ts` + `type` + `phase` + `durable` + `summary` + **payload complet**. Le brut est conservé à côté du résumé, jamais à sa place. | Copier |
| `trace` | `trace_summary.py:16-51` | `EventLogger._discover_next_event_id` — les identifiants d'événement reprennent après redémarrage en relisant le fichier. Indispensable pour une mission reprise. | Copier |
| `trace` | `trace_summary.py:104-133` | `normalize_token_usage` — les compteurs peuvent rester `None`. Un token absent n'est jamais un zéro. | Copier |
| `kernel` | `state_execution.py:17-30` | `summarize_changes` → `intentional` vs `incidental` via `classify_repo_path`. Un `.pyc` touché n'est pas un changement. | Copier |
| `kernel` | `utils.py:22-27` | `is_path_within` par `relative_to` + `ValueError`. Trois lignes, aucun `..` à gérer. | Copier |

---

## 2. `journal` — la durabilité

`write` (append JSONL + `live.log`) · `read` (itération, lecture bornée, détection de queue déchirée) ·
`redact` (une fonction).

**Zéro dépendance externe** — `os`, `json`, `fcntl`, `hashlib`, `base64`, `pathlib`. C'est le seul module du
projet dans ce cas, et c'est une propriété à préserver.

**Une écriture, deux sorties.** `emit(event)` écrit la ligne JSONL complète **puis** sa projection d'une
ligne dans `live.log`. Un seul chemin d'écriture, donc **impossible qu'un événement soit dans l'un et pas
dans l'autre** ; et `live.log` devient explicitement dérivable, donc jetable et reconstructible. La
décision 29 s'applique : la projection déclare qu'elle omet le payload.

**Un verrou global unique**, ~15 L, plutôt qu'un verrou sidecar par fichier nommé par SHA-256 (~40 L).
Cohérent avec « une mission à la fois, sous `RunLock` ». Le coût est nommé : il sérialise des écritures qui
n'entrent jamais en conflit.

> **Un verrou d'écrivain ne protège pas le lecteur** — `observatory` n'en prend aucun. Ce qui protège d'une
> ligne déchirée reste **une seule syscall `write()` par ligne** plus **un lecteur qui tolère une queue
> déchirée**. Les deux exigences sont indépendantes ; le verrou n'en dispense pas.

**Champ `v` par ligne, plus une signature de génération de fichier** — hash de la première ligne et taille,
pour que lecteur et écrivain sachent qu'ils parlent du même fichier. Le tableau `MIGRATIONS` de Kilo est
écarté (~80 L) : le JSONL étant append-only et jamais réécrit, une migration est **un lecteur qui tolère
deux versions**, pas un script qui transforme le passé — ce que la contrainte dure n°6 interdit.

**Toute écriture est encapsulée et ne lève jamais** (règle absolue de Villani). Ce qui garde la décision 13
n'est pas une exception à l'écriture mais **l'absence du reçu constatée après coup** : un reçu non écrit
retire l'attestation, et le nœud passe `blocked` avec la cause `receipt_not_written`.

**Une seule fonction de rédaction** : `redact(structure) -> (valeur, chemins_rédigés)`, alimentée par une
liste de motifs nommée, ~25 L. Les quatre couches de reconnaissance de clé d'Ouroboros y sont réduites, et
son `SecretRedactingLogFilter` est **retiré du catalogue** — la décision 10 exclut `logging`, il n'y a rien
à filtrer.

**Reportés jusqu'à ce qu'un volume les justifie** : rotation avec lecteurs conscients de l'archive,
quarantaine base64, séquence dense à machine à états, `LedgerResumeState`, rétention de blobs. **~150 L au
socle sur une cible de ~400 L.**

---

## 3. `verifier` — l'autorité de validation

`relations` (les 9 relations fermées → rend un script exécutable) · `domains` (générateurs) · `mutation`
(opérateurs AST + kill-check) · `gates` (séquence d'acceptation, verdict typé) · `receipt` (le reçu d'effet).

> **La règle qui définit ce module** : `verifier` n'a d'I/O que sur ce qu'il a lui-même produit — le script
> d'invariant qu'il vient d'écrire, le process qu'il vient de lancer. **L'état du monde lui arrive toujours
> comme fait typé** : contenu avant/après par `workspace`, `git diff` par `broker`, attestation d'hôte par
> `lifecycle`.

Il ne lit donc jamais un fichier du workspace et n'appelle jamais git. Le module le plus critique du projet
**se teste intégralement avec des faits en dur** — ce qui en fait aussi le plus facile à développer isolément
(décision 32).

**Hypothesis** pour les générateurs. Raison qui tranche : le **shrinking**. Quand un invariant casse,
Hypothesis rend le contre-exemple *minimal*, qui part directement dans le feedback au modèle. v1 renvoyait
« 6 lignes significatives » de sortie pytest brute à un 8B. Notre enum `domain` mappe sur un dict fermé de
stratégies ; **le modèle ne touche jamais Hypothesis**.

**Mutation : `ast.NodeTransformer` maison, ~5 opérateurs.** Pas `mutmut`, pas `cosmic-ray` : ils font du
scoring de suite complète sur un projet, lentement, avec des opinions sur le test runner.

**Exécution : fichier rendu + `subprocess`.** Isolation totale, timeout trivial, et le script rendu est un
**artefact relisible après coup**. Pas de pytest, pas de `exec` en process. Pas de moteur de template : le
squelette est fixe, une f-string suffit.

> **Le cœur de ce module n'existe pas chez Villani.** Aucun invariant métamorphique, aucun mutation-check,
> aucune sortie contrainte par schéma. Sa validation est « exécuter les commandes du repo et lire le code de
> retour ». `relations`, `domains` et `mutation` sont l'apport propre du projet. Ce qui suit est tout ce qui
> *entoure* le cœur : quoi valider, comment exécuter, comment rendre l'échec lisible à un 8B.

### Reprises de Villani

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `gates` | `validation_loop.py:110-124` | `infer_validation_scope` — dérive `docs_only`, `formatting_only`, `dependency_changed` des seuls chemins modifiés. Aucun appel modèle. | Copier |
| `gates` | `validation_loop.py:127-154` | `infer_validation_targets` — mappe une source vers ses tests probables avec un **score de confiance** (0.95 direct, 0.65 inféré). | Adapter |
| `gates` | `validation_loop.py:157-164` | `infer_targeted_command` — restreint `pytest` aux cibles inférées au lieu de lancer la suite entière. Applicable à notre gate de régression accumulée. | Copier |
| `gates` | `validation_loop.py:167-169` | `_step_order` — étapes ordonnées par **coût croissant** (format → lint → typecheck → test → build). Le moins cher échoue en premier. | Copier |
| `gates` | `validation_loop.py:190-279` | `plan_validation` — sélection d'étapes avec une **raison textuelle par étape retenue**. La trace dit pourquoi telle commande a tourné. | Adapter |
| `gates` | `validation_loop.py:274-278` | `ValidationEscalationPolicy` — *targeted first, then broaden*. Une gate ciblée verte déclenche la large ; un changement de dépendance force directement la large. | Copier |
| `gates` | `validation_loop.py:282-299` | `summarize_validation_failure` → `failure_class`, `headline`, `relevant_paths`, `relevant_error_lines`, `concise_summary`, `recommended_repair_scope`. **C'est le feedback rendu au modèle**, pas du stdout brut. | Copier |
| `gates` | `validation_loop.py:302-329` | `run_validation` — sortie au **premier échec**, callback avant/après chaque étape, durée en `monotonic`. | Copier |
| `gates` | `planning.py:403-411` | `compact_failure_output` — tête + `...` + queue, borné en lignes et caractères. Deux paramètres, aucune heuristique. | Copier |
| `gates` | `benchmark/verifier.py:15-29` | `_normalize_verification_command` — réécrit `pytest ...` en `[sys.executable, "-m", "pytest", ...]`. **v1 a payé exactement ce bug** (alias `python` remplacé à la main pour ne pas dépendre d'un shim `pyenv`). | Copier |
| `gates` | `benchmark/verifier.py:32-36` | `_is_launch_failure` — exit 127/9009 + « not found » ⇒ **la commande n'existe pas**, ce n'est pas un test rouge. Sans cette distinction, un environnement cassé se lit comme un contrat non satisfait. | Copier |
| `gates` | `benchmark/verifier.py:39-137` | `run_commands` — chaque exécution archive `stdout`, `stderr` et un `meta.json` (commande, commande normalisée, exit, durée, passed). Notre script d'invariant rendu produit le même triplet. | Copier |
| `verifier` | `autonomy.py:62-246` | `VerificationEngine` — vérificateur **adversarial** post-changement, indépendant des tests : la cible existe-t-elle encore, a-t-elle réellement changé, le diff est-il anormalement large. | Adapter |
| `verifier` | `autonomy.py:99-126` | `before_contents` vs contenu courant croisé avec `git diff --name-only` ⇒ finding **« no effective change »**. Voir décision 13. | Copier |
| `verifier` | `autonomy.py:169-188` | Finding `SUSPICIOUS_BREADTH` si `git diff --stat` dépasse 8 fichiers. Notre règle « un nœud, un fichier » est plus stricte ; le principe est identique. | Adapter |
| `verifier` | `autonomy.py:203-210` | Empreinte des findings ⇒ `repeated_verification_state`. **Détecte la boucle stérile par la répétition à l'identique du diagnostic** — le signal qui manquait aux six heures de boucle de v1. | Copier |
| `verifier` | `autonomy.py:212-225` | Score de confiance par pénalité de sévérité, borné `[0.05, 0.95]`. Jamais 0 ni 1. | Inspirer |
| `verifier` | `autonomy.py:261-302` | `_reconcile_findings` — **un finding contredit par une preuve directe est retiré, et le retrait est journalisé.** Le vérificateur peut se tromper ; la preuve filesystem gagne. | Copier |
| `verifier` | `autonomy.py:17-27` | `FindingCategory` — taxonomie fermée : régression, édition incomplète, référence cassée, doc périmée, effet de bord caché, hypothèse invalidée, trou de test, largeur suspecte. | Copier |
| `verifier` | `autonomy.py:311-324` | `FailureCategory` — 13 causes fermées, dont `REPEATED_NO_PROGRESS` et `EXCESSIVE_BLAST_RADIUS`. Répond à l'indicateur « nœuds `blocked` avec cause mécanique attribuée ». | Copier |
| `verifier` | `autonomy.py:337-387` | `FailureClassifier` — classe par mots-clés **et compte les occurrences** : trois échecs de même catégorie deviennent `REPEATED_NO_PROGRESS` avec changement de stratégie imposé. | Copier |
| `verifier` | `autonomous_helpers.py:88-120` | `meets_contract` / `has_real_validation_artifact` — un artefact doit contenir littéralement `(exit=0)` avec une commande non vide. Voir décision 13. | Copier |

### Écarté par la passe du 06:09 — ~600 L

| Écarté | Pourquoi |
|---|---|
| **Les trois capteurs de faux-vert** (~250 L) | ils supposent un modèle qui compose ses commandes et écrit ses assertions ; le script d'invariant est **rendu par le harness** |
| **Le catalogue de douze parsers** (~200 L) | il existe pour des backends sans sortie structurée ; une sortie non conforme est **rejetée, jamais récupérée** |
| **La planification de gate par coût** (~150 L) | `format → lint → typecheck → test` alors que la stack n'a **ni linter ni typechecker** : une seule marche à ordonner |
| **L'admission déclarative** (17 reprises) | valider une proposition n'est pas vérifier un invariant : mécanisme dans `kernel`, règles dans `campaign` |

**Gardées malgré la coupe**, parce qu'elles ne dépendent d'aucun modèle de menace : aucune coercition `or`
sur un code de retour, `cmp` où `>1` signifie panne d'outillage, `compact_failure_output` (tête + queue),
`summarize_validation_failure`, `_is_launch_failure` (**exit 127 = la commande n'existe pas, pas un test
rouge**), normalisation en `[sys.executable, "-m", …]`.

**~800 L au socle, ~950 L avec la gate hermétique** (conditionnée au spike n°5).

---

## 4. `bridge` — la frontière modèle

150 lignes qui méritent leur nom : **le point d'application de la contrainte dure n°1**. On peut pointer un
module et dire « tout ce que le modèle peut émettre est défini ici ».

**Client OpenAI-compatible sur la route `/v1` d'Ollama.** La contrainte de schéma passe par
`response_format={"type": "json_schema", ...}` alimenté par `Model.model_json_schema()` **après
normalisation** — Pydantic v2 émet des `$defs`/`$ref` que les backends de décodage contraint gèrent mal
(décision 17 amendée).

**Échantillonnage fixé** : `temperature 0.3`, `top_p 0.95`, `top_k 20` — valeurs mesurées par Kilo Code sur
la famille `ling`, versionnées comme donnée du projet (décision 20). Le prompt système dérive de
`prompt/ling.txt` et de ses sept modes d'échec documentés.

**Et surtout : la contrainte de décodage n'est jamais tenue pour acquise.** `response_format` est une
intention que la route peut ignorer et que le retry peut retirer. Toute sortie est **revalidée localement
contre le schéma exact envoyé** avant d'autoriser quoi que ce soit, avec cinq codes d'erreur fermés et un
reçu liant requête, catalogue, schéma et arguments par SHA-256 (décision 17 amendée). Bénéfice
secondaire : le mode `agentic` différé (LangGraph) parlera à la même route avec la même configuration.

Ni LangChain, ni `instructor`, ni `outlines` dans le chemin nominal : la contrainte de décodage est déjà
appliquée côté serveur. La politique de retry est métier et vit dans `engine`.

> **Villani fournit ce client, écrit et testé.** Il ne lui manque que `response_format` — et le point exact
> où l'insérer est `openai_client.py:75-86`. **C'est là que porte le spike n°2.**

### Reprises de Villani

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `bridge` | `openai_client.py:212-234` | `OpenAIClient` — 23 lignes, `httpx`, timeout par défaut **300 s** (un local lent n'est pas une panne), streaming et non-streaming séparés. | Copier |
| `bridge` | `openai_client.py:9-13` | `normalize_openai_base_url` — ajoute `/v1` de façon idempotente. Détail trivial, source d'erreur récurrente. | Copier |
| `bridge` | `openai_client.py:75-86` | `build_openai_payload` — **le point d'insertion de `response_format`**, alimenté par `Criterion.model_json_schema()`. | Adapter |
| `bridge` | `openai_client.py:174-209` | `convert_openai_response_to_anthropic` — normalisation vers un format interne unique, `usage` et `stop_reason` compris. | Adapter |
| `bridge` | `openai_client.py:89-98` | Mapping `finish_reason` avec `length` distingué de `stop`. **Une génération tronquée n'est pas une génération terminée** — sur un modèle 16k, c'est un cas nominal à détecter. | Copier |
| `bridge` | `openai_client.py:101-171` | `openai_stream_to_anthropic_events` — parsing SSE tolérant : ligne vide ignorée, JSON invalide sauté, `[DONE]` géré, `usage` capturé en fin. | Adapter |
| `bridge` | `context_budget.py:82-93` | `_group_atomic_units` — un `tool_use` et son `tool_result` sont **inséparables** au compactage. Casser la paire invalide la conversation côté API. | Copier |
| `bridge` | `context_budget.py:204-205` | `_preserve_exact` — un contenu portant `@@`, `--- `, `+++ ` ou `diff --git` n'est **jamais** compacté. Un diff résumé est un diff faux. | Copier |
| `bridge` | `context_budget.py:208-222` | `_summarize_tool_result` — compactage par extraction de signal (commande, exit, chemins, erreurs), jamais par troncature aveugle. | Copier |
| `bridge` | `state_runtime.py:396-437` | `validate_anthropic_tool_sequence` — validation de la séquence **avant** l'appel réseau. Un message mal formé échoue localement, gratuitement. | Inspirer |

### Écarté par la passe du 06:09 — ~50 L, et tout le streaming

**Pas de streaming.** Un `POST` bloquant, timeout 300 s, une réponse JSON complète. Pi énonce la règle qui
rend le flux inutile ici — *« ne jamais exécuter un JSON partiel ou réparé »* — et **l'incident de contexte
le plus grave de v1 était un incident de streaming**. La séparation thinking/contenu reste obligatoire, mais
sur la réponse complète : trois lignes au lieu d'un parseur d'événements.

**Aucune abstraction de fournisseur.** Écartés : transformations par fournisseur, sélection de prompt par
famille, et `convert_openai_response_to_anthropic` — **du legacy v1, aucun chemin Anthropic n'existe**.
Écartés aussi tous les mécanismes de credential : **Ollama local n'a aucune authentification.**

**La sonde tombe de ~200 à ~40 L** : lire `n_ctx_train`, envoyer un `Criterion` réel, refuser de démarrer
sinon. La fenêtre porte sa provenance en enum à trois valeurs, `unprobeable` étant fail-closed.

**Le prompt système est un fichier de données**, `src/bridge/prompt/ling.md`, hors du décompte de lignes —
et **démarré court, pas 129 lignes** : aucun des sept modes d'échec documentés par Kilo n'a été mesuré sur
*nos* prompts. Chaque ajout ultérieur cite la mission où le mode d'échec a été observé.

---

## 5. `workspace` — l'autorité filesystem

Le module qui existe parce que le pire incident de v1 était une écriture. Isolé, sur-testé.
**Stdlib pur** : `pathlib`, `ast.parse`, `os.replace`.

**Le modèle ne renvoie jamais un fichier.** Il renvoie `{function_name, new_source}` ; le harness parse,
vérifie un `def` unique au bon nom d'arité compatible, et le splice par plage de lignes issue de l'AST.
La destruction de v1 devient **structurellement impossible** : un blob JSON écrit comme contenu de fichier
ne passerait pas le parse en `def`. Le splice par lignes préserve commentaires et formatage du reste du
module — donc pas besoin de LibCST.

> C'est le module où Villani est le plus dense en garde-fous : c'est son domaine.

### Reprises de Villani

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `workspace` | `state_tooling.py:21-28` | `MutationGuardThresholds` — `max_touched_lines=120`, `max_touched_ratio=0.35`, `min_lines_for_ratio_guard=40`. **Des seuils nommés, versionnés, testables** plutôt qu'un booléen « ça a l'air gros ». | Copier |
| `workspace` | `state_tooling.py:89-122` | `_analyze_text_rewrite` — `difflib.SequenceMatcher` sur les lignes ⇒ `probable_rewrite`. **Détection générique de ce qui a détruit `audio_visualizer.py` en v1.** Seconde ligne derrière le splice AST. | Copier |
| `workspace` | `state_tooling.py:125-174` | `_analyze_patch_mutation` — même analyse appliquée à un diff, sans l'appliquer. | Adapter |
| `workspace` | `state_tooling.py:236-291` | Validation `py_compile` avec message d'erreur nommant fichier, validateur, type d'exception et action attendue (« repair only this file with a minimal follow-up patch »). Chez nous la validation est **avant** écriture ; le format du message est le bon. | Adapter |
| `workspace` | `state_tooling.py:44-86` | Extraction du code depuis un payload modèle : blocs ```` ``` ````, détection de diff unifié, repli sur brut. **Un petit modèle enveloppe systématiquement sa sortie** — le champ `new_source` y sera exposé malgré la sortie structurée. | Copier |
| `workspace` | `state_tooling.py:177-207` | `_sanitize_tool_input_file_path` — déquote, normalise, résout un chemin avant toute décision de politique. | Copier |
| `workspace` | `patch_apply.py:68-106` | **Valider tous les patchs, puis appliquer** (`# apply atomically after validation`, l. 95). Aucun fichier touché tant qu'un patch peut encore échouer. Transactionnalité au niveau du lot. | Copier |
| `workspace` | `patch_apply.py:330-333` | `_detect_newline_style` — préserve CRLF si le fichier en avait. | Copier |
| `workspace` | `state_runtime.py:508-590` | `small_model_tool_guard` — trois politiques cumulées : cible **authoritative** obligatoire, `Patch` refusé sur fichier absent avec message explicite, et **read-before-edit** avec auto-lecture forcée. | Copier |
| `workspace` | `state_runtime.py:479-505` | `_is_strongly_adjacent_path` — définit « proche d'une cible verrouillée » (même dossier, `__init__.py`, même stem, `test_<stem>`). | Adapter |
| `workspace` | `checkpoints.py:18-60` | `CheckpointManager` — snapshot de fichiers **sur disque** avec `metadata.json`, et `rewind()`. Notre snapshot/restore en mémoire ne survit pas à un crash du processus ; celui-ci si. | Adapter |
| `workspace` | `permissions.py:174-209` | `classify_bash_command` — allowlist par **préfixe de tokens**, refus du chaînage, de la redirection et de la substitution, `ASK` explicite pour installation et fetch réseau. | Copier |
| `workspace` | `permissions.py:212-233` | `bash_matches` — matching **conscient des opérateurs**, avec le commentaire qui nomme la faille évitée : `to avoid prefix exploits like '&& rm -rf /'`. | Copier |
| `workspace` | `permissions.py:51-107` | `PermissionEngine.evaluate_with_reason` — ordre `deny` → `ask` → `allow`, et **chaque décision retourne sa raison**. Une décision sans raison n'est pas traçable. | Copier |
| `workspace` | `runtime_safety.py:42-55` | `ensure_runtime_dependencies_not_shadowed` — **refuse de démarrer si le repo cible masque une dépendance du harness.** Notre campagne construit un paquet Python : le piège nous vise directement. | Copier |
| `workspace` | `runtime_safety.py:58-66` | `temporary_sys_path` — contextmanager restaurant `sys.path` intégralement. Le `verifier` importe du code produit ; il en aura besoin. | Copier |
| `workspace` | `command_environment.py:153-260` | `runner_private_roots` / `build_agent_command_environment` — **retire de l'environnement tout chemin absolu appartenant au harness**, pour que le modèle ne puisse ni découvrir ni atteindre son propre runtime. | Adapter |
| `workspace` | `benchmark/policy.py:29-57` | `normalize_path` / `comparison_key` / `path_is_within` / `path_matches_glob` — comparaison insensible à la casse et aux `./`, `//`, `/` finaux. Une seule implémentation partagée. | Copier |

### Écarté par la passe du 06:09 — ~350 L

> **Le modèle n'émet aucune commande — donc il n'y a rien à autoriser.**
> **Mais son code *est* exécuté — donc le confinement reste nécessaire.**

**`permission` est écarté** (~200 L) : `PermissionEngine`, `classify_bash_command`, matching conscient des
opérateurs, **l'arité des commandes shell — 161 L chez Kilo**, découpage de ligne shell, permissions de
sous-agent. **`sandbox` est gardé** avec sa phase P7bis.

**La transaction est une copie d'octets** (~10 L au lieu de ~150) : `before = read_bytes()` avant,
`write_bytes(before)` si non vert. Le dépôt Git fantôme revient quand une étape devra toucher plusieurs
fichiers. **Le compare-and-swap devient gratuit** — on détient déjà `before`.

**Six gardes, dans cet ordre** : chemin assaini **et** `authoritative` → parse en `def` unique au bon nom →
arité compatible → `py_compile` du fichier splicé → refus d'une écriture sans effet → CAS contre `before`.

**`MutationGuardThresholds` et `_analyze_text_rewrite` sont écartés** : le splice par plage AST borne le
rayon d'action par construction. Une réécriture massive n'est pas un cas à détecter, c'est un cas que le
mécanisme ne peut pas produire.

---

## 6. `engine` — l'arbre

`walk` (marcheur pur) · `flow` (adaptateur Prefect) · `context` (assemblage borné).

**Prefect 3, en enveloppe stricte.** Il possède le cycle de vie des tâches, les retries d'infrastructure
(Ollama injoignable), l'annulation en filet de sécurité et une UI pour déboguer *le harness*.

Il ne possède rien d'autre :

| Autorité | Détenue par | Pourquoi |
|---|---|---|
| État du domaine | `tree.json` | lisible, servi au dashboard, reprenable hors Prefect |
| Preuve | JSONL + `live.log` | évidence primaire, indépendante de tout framework |
| Sémantique de retry | `engine` | re-demander vs bloquer vs sauter un frère : c'est métier |
| Budget mural | `engine`, `time.monotonic()` | il faut **finaliser ce qui est vert**, pas se faire tuer |
| Frontière transactionnelle | `workspace` | snapshot fichiers, pas état de tâche |

**Le budget ne passe pas par `timeout_seconds`.** La décision 8 exige qu'à expiration la mission finalise ses
nœuds verts et sorte proprement ; une annulation ne le garantit pas. Vérification `monotonic()` dans la
boucle, `timeout_seconds` réglé nettement au-dessus en kill de dernier recours.

```python
# engine/walk.py — pur, testable sans Prefect
def walk(tree, budget, deps): ...

# engine/flow.py — l'adaptateur, mince
@flow(name="mission", timeout_seconds=BUDGET_HARD)
def mission(config):
    tree = load_or_create(config)
    try:
        walk(tree, Budget(BUDGET_SOFT), deps)
    finally:
        finalize_green_nodes(tree)
```

`walk.py` reste testable au pytest nu. Sans cette séparation, chaque test d'engine traînerait un harnais
Prefect — or l'engine est le module qu'on itère le plus.

Le contexte reprend la construction par priorité sous budget de v1, avec la correction née de l'incident des
12 419 `thinking_delta` : la tâche courante est **injectée depuis l'état du nœud**, jamais lue depuis un brief
figé sur disque.

### Reprises de Villani

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `walk` | `planning.py:215-316` | `analyze_instruction` — **classification entièrement déterministe** : cibles candidates, classes d'action, portée, impact, confiance, `rationale` textuelle. Zéro appel modèle. Preuve qu'une grande part de ce qu'on croit devoir demander au modèle se dérive du repo. | Copier |
| `walk` | `planning.py:11-57` | Cinq enums fermées : `PlanRiskLevel`, `ActionClass` (13 valeurs), `EstimatedScope`, `ChangeImpact`, `TaskMode`. Le vocabulaire de décision est fini et inspectable. | Copier |
| `walk` | `planning.py:319-332` | `classify_plan_risk` — risque dérivé des classes d'action et de la portée, jamais demandé au modèle. | Copier |
| `walk` | `planning.py:388-400` + `validation_loop.py:219-247` | `classify_task_mode` puis **le mode détermine quelles gates tournent**. Une tâche docs ne lance pas la suite de tests. | Adapter |
| `walk` | `planning.py:99-142` | `ExecutionPlan.to_human_text` — rendu texte compact du plan, réinjectable. Un plan qui ne se rend pas en texte ne sert pas au modèle suivant. | Inspirer |
| `context` | `context_governance.py:11-31` | `ContextInclusionReason` / `ContextExclusionReason` / `ContextPressureLevel` — **chaque élément porte la raison de sa présence ou de son absence.** Voir décision 14. | Copier |
| `context` | `context_governance.py:34-71` | `ContextItem` (avec `pressure_share`) / `ContextBudgetEstimate` / `ContextInventory`. Le contexte devient un objet inspectable, pas une chaîne. | Copier |
| `context` | `context_governance.py:252-266` | `_recompute_budget` — pression = total / limite, quatre paliers (`low` < 0.45 < `moderate` < 0.75 < `high` < 1.0 < `overflow_risk`). Avec Ling plafonné à 16k, ce cadran est vital. | Copier |
| `context` | `context_governance.py:200-208` | `prune_for_budget` — éviction FIFO sous pression, chaque éviction enregistrée avec sa raison et comptée (`pruning_events`). | Copier |
| `context` | `context_governance.py:210-220` | `detect_stale_context` — signaux de dérive : mode docs avec fichiers de code, **réparations répétées avec contexte gonflé**, contexte multi-sources. Voir décision 14. | Copier |
| `context` | `context_governance.py:83-122` | `ContextCompactor` — un compacteur par type de source, chacun avec ses tokens de signal (`validation_log`, `shell_output`, `repo_summary`, `repair_history`). | Copier |
| `context` | `context_projection.py:9-20` | `_filter_model_facing_paths` — **les chemins d'artefacts runtime ne sont jamais montrés au modèle.** Un modèle qui voit `.villani_code/` finit par y écrire. | Copier |
| `context` | `context_projection.py:23-70` | `build_model_context_packet` / `render_model_context_packet` — paquet **structuré** puis rendu texte séparé. Le paquet est traçable, le rendu jetable. | Copier |
| `walk` | `execution.py:6-13` | `ExecutionBudget` — cinq bornes dont deux originales : `max_no_edit_turns` et `max_reconsecutive_recon_turns`. **Borner l'exploration stérile, pas seulement la durée.** | Copier |
| `walk` | `execution.py:37-43` | `VILLANI_TASK_BUDGET` — valeurs éprouvées en benchmark : 20 tours, 40 tool calls, **180 s**, 8 tours sans édition, 6 tours de reconnaissance. Point de départ chiffré pour notre borne murale. | Inspirer |
| `walk` | `execution.py:15-34` | `ExecutionResult` transporte `intended_targets` **et** `before_contents` — le vérificateur reçoit l'intention et l'état antérieur, pas seulement le résultat. | Copier |
| `walk` | `repair.py:61-106` | `execute_repair_loop` — réparation ciblée sur **la seule étape en échec** (`steps_override`), puis élargissement si la politique l'exige. Chaque tentative conserve son résumé, réinjecté à la suivante. | Copier |
| `walk` | `repair.py:11-19` | `RepairContext` — payload de réparation en champs bornés (`[:200]`, `[:500]`, `[:10]`), sérialisé en JSON. Le prompt de repair est une structure, pas de la prose. | Copier |
| `walk` | `interrupts.py:7-18` | `InterruptController` — premier Ctrl-C interrompt, second quitte. Dix-huit lignes. | Copier |
| `engine` | `subagent_runtime.py:19-27` | `build_role_launch_request` — quatre rôles (`fork_investigator`, `fresh_verifier`, `bounded_patcher`, `planner`), chacun avec **allowlist d'outils, droit d'écriture et exigence de preuve** explicites. `fresh_verifier` n'hérite pas de l'état de mission : il vérifie sans être contaminé. | Copier |
| `engine` | `subagent_runtime.py:30-40` | `render_subagent_brief` — brief en huit lignes fixes, dont `Known facts` et **`Ruled out`**. Transmettre ce qui a été écarté évite de le réexplorer. | Copier |
| `engine` | `subagents.py:22-27` | Sous-agents définis par leurs **interdits** (`denied_tools`) plutôt que par leurs permissions. | Inspirer |
| `engine` | `summarizer.py:9-55` | `summarize_tool_batch` / `summarize_validation` / `summarize_patch` — résumés déterministes d'une phase, jamais générés. | Copier |

### Ce que la passe du 06:09 a changé — le module devient le plus gros

**Le classifieur déterministe de Villani est porté** (~200 L) : `analyze_instruction` et ses cinq enums
fermées dérivent du repo cibles candidates, classe d'action, portée et impact — **zéro appel modèle**. Sa
place ici n'est pas d'évaluer un risque mais de **dériver les enfants d'un nœud sans appeler le modèle** :
une décomposition déterministe est plus alignée sur la contrainte n°1 que de demander au modèle de scindre.

**La sélection de fichiers rejoint `engine/context`** (~200 L) : `relevant_files`, `impact_files`, fermeture
d'imports bornée en profondeur, **chaque fichier avec sa raison**. Lire et parser reste à `kernel/codeview`.

**Écartés** : `ExecutionBudget` et `VILLANI_TASK_BUDGET` — des bornes **de tours** (20 tours, 40 tool calls,
8 outils) alors que le mode `direct` fait un appel par nœud ; la **compaction** entière (~150 L) ; la
machinerie de budget avancée (EWMA, latch d'ancre, `CostCeiling`), reportée après dix missions.

**Le contexte : évincer, jamais résumer.** Sous pression on évince avec raison enregistrée ; si le contenu
irréductible dépasse le budget, le nœud est `blocked` avec cause. **Et à chaque fin de session, un artefact
de passation** — `~/logs/pithos2/missions/<id>/CONTEXT.md`, écrit par le harness, avec **l'empreinte des
fichiers décrits** : réinjecté plus tard, il est soumis à `detect_stale_context` comme tout élément de
contexte. Un fichier de suivi périmé a exactement la forme du brief qui a produit 12 419 `thinking_delta`.

**Deux notions du ledger d'Ouroboros**, sans le ledger : `child_result_disposition` — un parent enregistre
par enfant ce qu'il a fait de son résultat — et **`cap_children`, la borne de largeur qui manquait** : le
plafond dur de 3 porte sur la profondeur.

---

## 7. `campaign` — la politique

`store` (le magasin à quatre familles) · `registry` · `propose` · `stop` · `mcpconfig`.
**JSON + Pydantic**, similarité lexicale par `difflib.SequenceMatcher` **stdlib**. La comparaison de schémas
est une égalité de dicts normalisés.

**`campaign` possède le magasin** — `prompt`, `memory`, `skill`, `subagent` — et la famille `skill` **est**
le registre d'outils : un seul fichier, un seul propriétaire (décision 26 amendée). C'est ici qu'atterrit le
portage de `prime/rt/harness.py` (820 L) : modèle de données, relecture défensive champ par champ,
resynchronisation par `mtime`, deux scopes, rendu compact pour le prompt. La famille `subagent` reste vide
au socle ; la famille `memory`, elle, **est alimentée dès le socle** (décision 31).

**La redondance se décide en deux temps**, sans jamais appeler le modèle : lexical sur la proposition, puis
**empreinte de contrat canonicalisée** dès que les critères existent (décisions 5 et 19 amendées). Deux
propositions formulées différemment qui produisent le même contrat sont le même outil.

> Villani a un mode autonome complet (`--villani-mode`) où **tout le backlog est déterministe** : le modèle
> exécute les tâches, il ne les invente pas. Notre backlog ouvert délègue davantage. Ce catalogue est donc
> autant un socle qu'un contre-modèle utile — une part de nos propositions d'outils peut se dériver du
> registre par heuristique plutôt que d'être demandée au modèle.

### Reprises de Villani

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `registry` | `autonomy.py:390-400` | `Opportunity` — `priority`, `confidence`, `affected_files`, `evidence`, `blast_radius`, `proposed_next_action`, `task_contract`. **`evidence` est obligatoire** : une opportunité sans preuve n'existe pas. | Copier |
| `registry` | `autonomy.py:523-631` | `discover_opportunities` — **découverte du backlog par heuristiques déterministes** : pas de tests ⇒ « bootstrap », artefacts trackés ⇒ « audit », TODO/FIXME ⇒ « triage ». Zéro appel modèle. | Adapter |
| `registry` | `autonomy.py:423-432` | `_RANK_ORDER` — ordre de priorité **écrit en dur, par titre**. Assumé, lisible, débogable. | Inspirer |
| `registry` | `autonomy.py:716-722` | `_is_authoritative_opportunity` — une opportunité touchant un chemin non-authoritative est éliminée avant sélection. | Copier |
| `registry` | `autonomy.py:403-411` | `TakeoverConfig` — `max_waves=3`, `max_total_task_attempts=6`, `min_confidence=0.60`, `stagnation_cycle_limit=2`. Toutes les bornes d'autonomie en un objet. | Copier |
| `registry` | `autonomous.py:53-60` | `TaskLifecycle` — `pending` / `running` / `passed` / `failed` / `blocked` / `retryable` / `exhausted`. **Sept états, dont trois formes d'échec distinctes.** Notre `Node.statut` doit être aussi fin : « échoué » ne dit pas s'il faut réessayer. | Copier |
| `registry` | `autonomous.py:1014-1027` | `_repo_fingerprint_for_task` — empreinte du repo **restreinte à ce qui concerne la tâche**. | Copier |
| `registry` | `autonomous.py:1029-1042` | `_mark_task_satisfied` / `_is_task_satisfied` — satisfaction invalidée dès que l'empreinte bouge. Voir décision 5 amendée. | Copier |
| `proposals` | `autonomous_helpers.py:44-52` | `task_key_for_opportunity` — clé normalisée **avec table d'alias** pour que deux formulations de la même tâche collisionnent. Sans alias, « ajouter un parseur » et « créer un outil de parsing » passent toutes deux notre rejet de redondance. | Copier |
| `proposals` | `autonomous_helpers.py:9-26` | `build_wave_candidates` — filtre en cascade : satisfaite, périmée, lignée terminale, confiance insuffisante ; puis déduplication par clé en gardant la meilleure priorité. | Copier |
| `proposals` | `autonomous_helpers.py:29-41` | `effective_priority` — `priority*0.7 + confidence*0.3` avec bonus explicites. Formule visible, ajustable. | Inspirer |
| `proposals` | `autonomous_helpers.py:61-64` | `retry_limit_for_contract` — le nombre de retries **dépend du type de contrat** (2 pour une validation, 1 sinon). | Copier |
| `stop` | `autonomous_stop.py:7-12` | `StopDecision` — `budget_exhausted`, `no_opportunities`, `below_threshold`, **`planner_churn`**, **`stagnation`**. Les deux dernières nomment précisément les modes d'échec de v1. | Copier |
| `stop` | `autonomous_stop.py:35-47` | `category_exhaustion_reason` — la raison d'arrêt **énumère ce qui a été examiné par catégorie**. Un arrêt qui ne dit pas ce qu'il a couvert n'est pas auditable. | Copier |
| `stop` | `autonomous_progress.py:10-36` | `mark_category_discovery` / `update_category_attempt_state` — machine à états par catégorie : `discovered` → `attempted`. L'épuisement du backlog devient mécanique. | Copier |
| `stop` | `autonomous_progress.py:39-88` | `surface_followups` — une catégorie découverte mais non traitée **génère automatiquement sa tâche de suivi** avant que l'arrêt puisse être proposé. | Adapter |
| `campaign` | `autonomous_reporting.py:77-145` | `build_takeover_summary` — rapport final : par tâche, statut, contrat, tentatives, artefacts, changements intentionnels vs incidents, et **`preexisting_changes`** (ce qui était déjà sale avant). Sans cette notion, on attribue au système des changements qu'il n'a pas faits. | Copier |
| `campaign` | `mcp.py:27-35` | `load_mcp_config` — fusion en couches `managed` → `user` → `project` → `local`. **La couche `managed` est écrite par le runtime** : exactement notre décision 7. | Copier |
| `campaign` | `mcp.py:11-24` | `_expand_env` récursif avec syntaxe `${VAR:-default}`, sans secret en dur. | Copier |
| `campaign` | `project_memory.py:99-142` | `ValidationStep` / `ValidationConfig` — les commandes de validation sont **une donnée persistée**, pas une constante du harness. Notre suite de régression accumulée est le même objet. | Copier |
| `campaign` | `project_memory.py:313-362` | `scan_repo` — dérive `RepoMap` + `ValidationConfig` + `ProjectRules` d'un repo inconnu, une fois, puis persiste. | Adapter |
| `campaign` | `skills.py:16-33` | `discover_skills` — `SKILL.md` avec frontmatter YAML, découverte par `rglob`. Format identique à v1 et à Claude Code. | Copier |

### Ce que la passe du 06:09 a changé

**Deux familles vivantes au socle, pas quatre.** `skill` — qui *est* le registre — et `memory`
(décision 31). Tout ce qui est lourd dans `rt/harness.py` existe pour éditer des `prompt`, et rien n'édite de
`prompt` tant que `refinery` est éteint. **~150 L au lieu d'un portage de 820 L.** Gardée intégralement : **la
relecture défensive champ par champ qui ne lève jamais** — cœur du spike n°6.

**Le modèle propose, la dérivation est un filet.** Le backlog ouvert reste le sujet d'étude ;
`discover_opportunities` ne se déclenche qu'**après trois rejets consécutifs**, pour qu'une mission ne soit
pas stérile. **Les deux compteurs sont séparés dans la trace** — le filet devient lui-même une mesure.

**Le classement est un tuple lexicographique d'axes nommés**, par exemple
`(a_une_preuve, est_authoritative, récurrence, -profondeur)`. Écartés :
`effective_priority = priority*0.7 + confidence*0.3` et `_RANK_ORDER` en dur par titre.

**Trois notions de registre gardées** : `capability_omissions` (la surface projetée porte la raison typée de
ce qui manque), **un module d'outils qui échoue à l'import omet *tous* ses outils**, et `TaskLifecycle` à
sept états dont **trois formes d'échec distinctes**. Écartés : `policy_hidden_reason`, `alias_for`,
`mutates_worktree`, `TakeoverConfig` et ses vagues.

---

## 8. `lifecycle` — la machine, pas le réseau

`lock` · `launchd` · `custody` (processus orphelins) · `disk` (garde d'espace).

Porté de v1, quasi tel quel.

- **Verrou : le `RunLock` de v1** (verrou-répertoire atomique + PID vivant, 78 lignes). Il a correctement
  traité un PID mort en incident réel. Durci par la paire `pid` + **heure de démarrage** de Prime Agent,
  contre le PID recyclé, et par le **verrou à trois états** dont `indisponible`, qui bloque (décision 27).
- **launchd** : génération de plist + `launchctl`, porté. Réclamation de tick avant délivrance et ticks
  manqués coalescés, contre le réveil qui rejoue ou s'empile après une suspension machine.
- **Custody de processus** : journal des orphelins rejoué au démarrage, apparié par `pid` + identité de
  démarrage. Les leases périmées sont relâchées au démarrage, pas à la première collision.
- **Garde disque** : l'espace est vérifié **avant** écriture d'un snapshot, d'une trace ou d'un artefact.
  L'insuffisance est un `blocked` mécanique avec cause, jamais une exception d'écriture.

C'est aussi `lifecycle` qui produit le `HostFact` — attestation d'hôte, horloge monotone, ancre de
démarrage — que `verifier` consomme pour son reçu.

### Reprises de Villani

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `lifecycle` | `hooks.py:19-59` | `HookRunner` — hooks `shell` ou `http` renvoyant `{allow, reason, input}`, avec possibilité de **réécrire l'entrée** avant exécution. Point d'extension propre sans toucher au cœur. | Inspirer |
| `lifecycle` | `shells.py:15-41` | `normalize_command_for_shell` — commande **normalisée avant exécution et journalisée sous sa forme normalisée**. Sur macOS seul, la portabilité est marginale ; la notion reste. | Inspirer |
| `lifecycle` | `command_environment.py:32-48` | `CommandEnvironmentDiagnostics` — l'environnement passé à une commande est **diagnostiqué et journalisé** (variables retirées, variables signalées). | Adapter |

### Ce que la passe du 06:09 a changé — ~150 L évitées

**Le verrou : ~40 L, aucun thread.** Verrou-répertoire atomique de v1, paire `(pid, heure de démarrage)`
contre le PID recyclé, péremption par durée maximale, et l'état `indisponible` qui **bloque** au lieu de
procéder. Le heartbeat ne détecte qu'un processus vivant mais bloqué — cas déjà couvert par la borne murale
et le kill de dernier recours de Prefect.

**La politique d'exposition réseau est sans objet** : `observatory` binde `127.0.0.1` **en dur**, et aucun
chemin de code ne peut binder ailleurs. Écartés : `is_public_address`, résolution DNS, détection d'IP
littérale, normalisation des binds wildcard, validation `Host`/`Origin`. **L'interdiction est dans le type,
pas dans la configuration.**

**Gardé** : readiness observable sous deadline, arrêt idempotent, état de sortie confirmé, fermeture des
sockets partiellement ouverts sur échec de bind — et la garde disque, qui transforme une insuffisance en
`blocked` mécanique plutôt qu'en exception d'écriture.

---

## 9. `broker` — la seule sortie de données

`git` (dépôt de campagne + CLI `gh`) · `telegram` (bidirectionnel).

**Un seul module regroupe les deux effets sortants**, et c'est tout l'intérêt du regroupement : la
contrainte dure n°5 — *aucune donnée ne quitte la machine, hors Git et Telegram déjà brokerisés* — devient
un **test de graphe d'imports** au lieu d'une discipline de relecture. Le terme vient de `PROJECT.md`, qui
parlait déjà de composants « brokerisés ».

- **Git : `subprocess` + CLI `gh`.** Pas de GitPython : le broker de v1 fait 225 lignes, a produit dix PR
  réelles, et sa valeur est justement de *restreindre* les opérations qu'on veut fermer. C'est lui qui
  produit le `RepoFact` — fichiers touchés, lignes ajoutées et retirées — que `verifier` consomme.
- **Telegram bidirectionnel**, porté intégralement : offsets persistants, idempotence des requêtes,
  allowlist utilisateur, commandes `/status`, `/latest`, `/pause`, `/stop`, `/answer`. Justifié par le régime
  nominal — un réveil toutes les trois heures pendant que tu n'es pas devant la machine. `/answer` alimente
  le contexte du réveil suivant et sert de canal de réponse à la proposition d'arrêt.

**Une identité logique par effet, renouvelée jamais** (décision 30) : un message Telegram ou un push Git
rejoué après échec de transport porte la même identité de résultat et une identité de transport neuve. Il ne
compte pas deux fois.

### Ce que la passe du 06:09 a confirmé

**Le broker v1 est porté complet**, et Telegram reste bidirectionnel dès le socle — du réemploi assumé
plutôt qu'une réécriture. ~450 L de code éprouvé.

**Deux conséquences à tenir.** La boucle de polling Telegram est un **processus à cycle de vie propre**,
donc géré par `lifecycle` comme tout autre processus, avec sa custody et son arrêt confirmé. Et `/pause` et
`/stop` doivent atteindre le marcheur : c'est l'`InterruptController` de `engine` — premier signal
interrompt, second quitte.

**La surface de sortie reste double** — Git distant **et** Telegram. La règle d'import « `broker` est le seul
module par lequel une donnée quitte la machine » cesse d'être une formalité : c'est le seul test qui garde la
contrainte dure n°5.

---

## 10. `observatory` — processus séparé

**FastAPI porté de v1**, ~300 lignes, lisant les JSONL **indexés en mémoire au démarrage** et suivis par
mtime. Pas de DuckDB, pas de projection SQLite, pas de collecteur permanent : cela supprime tout
`pithos_event_store` (558 L) et le LaunchAgent dont le stdout avait atteint 1,3 Go en v1. Le volume attendu
par mission se compte en centaines d'événements, sans Pi pour produire 12 000 `thinking_delta`.

**React 19 + Vite porté de v1** : ~700 lignes déjà écrites, six tests jsdom verts, design Argos/Aede fait.
Reste à ajouter la vue d'arbre et rebrancher la source.

> **Villani a déjà écrit l'agrégateur JSONL que ce choix impose.** `aggregate_summary_from_events` reconstruit
> tout l'agrégat d'un run à partir des seuls événements, sans base.

### Reprises de Villani

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `observatory` | `trace_summary.py:439-757` | `aggregate_summary_from_events` — reconstruit **tout** l'agrégat d'un run depuis les seuls JSONL : métriques, tool calls, commandes, durées, statut. ~300 lignes, aucune base. Littéralement la fonction que notre API exécute au démarrage. | Copier |
| `observatory` | `trace_summary.py:196-427` | `build_tool_call_records_from_events` — reconstruction des appels d'outils depuis les événements bruts, **avec la liste des anomalies rencontrées**. La reconstruction signale ses propres trous au lieu de les combler silencieusement. | Adapter |
| `observatory` | `trace_summary.py:777-820` | `validate_summary` — l'agrégat produit est **validé contre un contrat** avant d'être servi. Une projection non validée est une projection fausse. | Copier |
| `observatory` | `trace_summary.py:11-13` | `AGGREGATION_VERSION` / `TOOL_CALL_SCHEMA_VERSION` — l'agrégat porte la version de la logique qui l'a produit. Distingue un vieux résumé d'un neuf sans rejouer. | Copier |
| `observatory` | `trace_summary.py:758-776` | `_build_artifact_manifest` — manifeste des artefacts d'un run (présence, taille), servi tel quel au frontend. Notre panneau d'artefacts en a besoin. | Copier |
| `observatory` | `event_recorder.py:35-59` | `build_digest` — comptage par famille (`tool_activity`, `validations`, `planning`, `failures`) + les 25 derniers événements. Digest peu coûteux, suffisant pour une liste. | Copier |
| `observatory` | `debug_recorder.py:64-72` | `DebugRecorder._safe` — **toute écriture d'observabilité est encapsulée : une panne du recorder ne casse jamais la mission.** Règle absolue. | Copier |
| `observatory` | `debug_recorder.py:87-406` | Vocabulaire d'enregistrement exhaustif : `record_turn_start/finish`, `record_model_request/response/failed`, `record_tool_call/result`, `record_command_start/environment/finish`, `record_file_read/write`, `record_patch_applied`, `record_validation_start/finish`, **`record_context_compacted`**, `record_mission_state_snapshot`. Liste de référence de ce qu'un runtime doit tracer. | Inspirer |
| `observatory` | `debug_recorder.py:414-446` | `write_final_summary` — un run se termine toujours par un résumé écrit, statut et raison de terminaison compris. | Copier |

### Ce que la passe du 06:09 a changé

**Les agrégats d'analyse sont des routes de l'API.** Les cinq scripts de Pi — statistiques journalières,
stats par outil, inflation de patch, **occupation du contexte par appel** — deviennent des routes FastAPI
consommées par le web. ~150 L de plus, et **les cinq indicateurs des questions expérimentales deviennent
visibles sans terminal**. Conséquence : l'analyse expérimentale dépend du dashboard tournant.

**`observatory` lit par `journal`**, il ne reparse pas le JSONL de son côté : un format, un parseur. Il
construit son index mémoire et ses agrégats par-dessus.

**Écartés** : budget de rendu en nœuds distinct du budget en caractères, et les références de blob — nos
payloads sont déjà bornés (20 000 caractères pour la sortie d'un reçu, tête + queue pour un échec). Gardées
sans discussion : la résistance aux IDs dupliqués, la **durée de nœud distincte de l'enveloppe du
sous-arbre**, et **ne jamais corriger silencieusement une durée négative** — c'est une anomalie à montrer.

---

## 11. `refinery` — la politique d'auto-amélioration

`propose` (plan de raffinement déterministe) · `gate` (acceptation sur effet mesuré). **Pas de `store` :
le magasin appartient à `campaign`** (décision 26 amendée) — un fichier, un propriétaire.

**Ce qu'on ajoute et qui n'existe dans aucune des neuf sources** : la gate d'effet. Un edit reste en
`shadow` tant qu'il n'a pas démontré un effet mesurable sur le taux de nœuds verts. Prime Agent implémente
l'auto-amélioration complète mais **ne vérifie jamais qu'elle améliore quoi que ce soit** ; c'est
exactement là que notre autorité de validation ferme la boucle.

Le contenu est **versionné et jamais modifié** : on crée une nouvelle version, et **seul le déplacement du
label `active` est l'acte que la gate contrôle** (décision 26 amendée par Langfuse).

**`enabled: false` au socle.** Activation après mesure sur les dix premières missions. Le raffinement tourne
**en fin de mission**, après finalisation, avant le rapport.

> **La mémoire ne l'attend pas.** Écrire dans la famille `memory` et s'en servir pour réécrire le harness
> sont deux actes séparés : le premier est au socle (décision 31), le second attend cette gate.

Voir décisions 26 et 31.

### Ce que la passe du 06:09 a changé

**Zéro ligne au socle, mais la baseline est mesurée dès la mission 1.** `engine` écrit à chaque fin de
mission le triplet qui la constitue : **nœuds verts / nœuds tentés, temps mural consommé, cause de sortie**.
~5 L dans une trace qui existe déjà. Sans eux, activer la gate d'effet au bout de dix missions reviendrait à
comparer un chiffre à rien — or **vérifier que le raffinement améliore quelque chose est la seule chose que
`refinery` apporte de neuf par rapport à Prime Agent.**

**Deux fonctions, et il reste un module.** `plan_refinement` et la gate d'effet, ~100 L. Sont partis avec le
magasin, parce que ce sont des opérations *du magasin* : rollback par reconstruction inverse, application par
cas fermés, injection bornée par famille, label mobile. **Rester séparé a une valeur précise** : son
`MODULE.md` porte par écrit pourquoi il est éteint et ce qui conditionne son allumage.

## Le produit — dépôt séparé

**FastMCP, schémas Pydantic explicites.** Le schéma de chaque outil vient d'un modèle Pydantic déclaré,
pas dérivé des annotations : le harness peut lire le contrat d'un outil **sans importer FastMCP**, ce dont
l'invariant `schema_conform` a besoin pour être vérifiable de l'extérieur.

Structure imposée par la décision 4 :

```text
core/<outil>.py    fonction pure, sans I/O     → porte les invariants
tools/<outil>.py   coquille MCP : schéma, I/O  → porte schema_conform
```

**Le harness ne dépend jamais de FastMCP.** Seul le produit.

---

## Ce qu'il ne faut pas reprendre de Villani

| Source | Raison |
|---|---|
| `state.py` (2 073 L), `state_runtime.py` (1 427 L), `autonomous.py` (1 307 L) | Trois monolithes construits autour d'un objet `Runner` que tout traverse — `state_runtime.py` prend `runner: Any` en premier argument dans une trentaine de fonctions. C'est le paradigme boucle-d'agent que la décision 6 supprime. **Piocher les notions, jamais l'ossature.** |
| `indexing.py:57-66` | `SYMBOL_PATTERNS` — extraction de symboles Python **par regex**. Erreur exacte de v1, qui a coûté l'incident d'arité `smooth_levels(0.0, 0.0, 0.0)`. Notre `codeview` utilise l'AST. Les regex restent acceptables pour les langages non-Python de l'index. |
| `patch_apply.py:231-323` | Repli **fuzzy** d'application de patch (déplacement ≤ 6 lignes, normalisation des blancs). Bien fait — candidat unique exigé, sinon rejet — mais contredit frontalement « le modèle renvoie une fonction, pas un diff ». Un patch approximatif appliqué avec succès est un risque que le splice AST supprime par construction. |
| `tui/` (13 fichiers) | Textual. Nous avons retenu React/Vite porté de v1. |
| `benchmark/` (4 264 L) | Harnais multi-agents (adaptateurs Claude Code, aider, opencode). Hors périmètre — sauf `verifier.py` et `policy.py`, repris ci-dessus. |
| `anthropic_client.py` | Autre fournisseur, hors périmètre souveraineté. |
| `interactive.py`, `live_display.py`, `optional_tui.py`, `status_controller.py` | UX de session interactive. Notre campagne tourne sous LaunchAgent, sans humain devant. |
| `task_memory.py` (485 L) | Mémoire de tâche exposée **comme des tools au modèle** (`memory_tool_specs`, `execute_tool`). En mode `direct`, le modèle n'a pas de tools : la mémoire est un objet du harness injecté dans le contexte. L'idée d'une mémoire en JSONL reste bonne, la surface d'outil est à jeter. |

---

## Stack récapitulative

| Couche | Retenu | Écarté |
|---|---|---|
| Contrats | Pydantic v2 | dataclasses + jsonschema (v1) |
| AST | `ast` stdlib | regex (v1 et Villani), LibCST |
| Traces | stdlib + flock/fsync | `logging`, DuckDB, SQLite |
| Génération d'entrées | Hypothesis | générateurs maison |
| Exécution d'invariant | script rendu + subprocess | pytest programmatique, `exec` |
| Mutation | `ast.NodeTransformer` maison | mutmut, cosmic-ray |
| Client LLM | OpenAI-compatible sur `/v1`, **porté de Villani** | package `ollama`, httpx brut |
| Appel modèle | `POST` bloquant, réponse complète | **streaming SSE**, deltas, parseur d'événements |
| Confinement | `sandbox-exec` (P7bis) | conteneur, et **toute couche de permission de commande** |
| Moteur | Prefect 3, en enveloppe | Python nu, Temporal, Celery |
| CLI | Typer | argparse (v1), Click |
| API | FastAPI | Starlette, Litestar, statique |
| Frontend | React 19 + Vite | HTMX, Svelte, Textual |
| MCP produit | FastMCP + Pydantic | SDK bas niveau |
| Mode agentic (différé) | LangGraph + langchain-mcp-adapters | pydantic-ai, Pi |
| Env & build | **pyenv `pithos`, Python 3.12.9** + pip + hatchling | uv, Poetry, Conda |
| Tests | pytest | unittest |
| Frontières de module | `typing.Protocol` + doubles maison | `unittest.mock`, dependency injection framework |

**Complexité empruntée contre complexité possédée.** Le code propre passe de ~8 000 à ~5 230 lignes visées,
dont une part majoritaire est **portée et non écrite**. La surface de dépendances augmente nettement (Prefect, Hypothesis, FastAPI, client OpenAI, Typer, puis
LangGraph). Arbitrage assumé : la complexité empruntée est documentée, versionnée et maintenue ailleurs ;
celle de v1 était intégralement à notre charge. Le portage de Villani réduit encore la part **à écrire**,
sans réduire la part **à comprendre** — chaque reprise doit être relue, pas collée.

Sans lock de dépendances (choix `pip`), figer `pip freeze > requirements.lock` après chaque changement
d'environnement reste le minimum pour rendre une campagne rejouable.

---

## Spikes avant de graver

**Sept vérifications courtes** conditionnent l'architecture, et elles précèdent P0. Les deux premières
datent du cadrage et sont détaillées ci-dessous ; les cinq autres sont nées de l'absorption des sources —
revalidation locale du schéma (n°2 reformulé), fenêtre réelle et densité de tokens (n°4), coût de la gate
hermétique (n°5), portage du magasin en Pydantic v2 (n°6), empreinte d'arbre de travail (n°7). La liste
complète, avec son point d'accueil de code pour chacune, est dans [`ROADMAP.md`](ROADMAP.md) § S.

1. **Prefect 3 sous launchd, en mode éphémère.** Latence de démarrage par réveil, persistance dans
   `~/.prefect/prefect.db`, et visibilité des runs passés dans une UI lancée après coup. Si la latence par
   réveil est significative, la question du moteur se rouvre.
2. **Contrainte de schéma sur la route `/v1` d'Ollama.** Vérifier que `response_format` json_schema est
   appliqué aussi strictement que le `format=` natif, sur un schéma `Criterion` réel avec Ling. **Toute la
   contrainte dure n°1 en dépend** : si la route `/v1` n'applique pas la grammaire, on repasse au client
   natif pour le bridge et LangGraph gardera sa propre route. Le code d'accueil existe déjà —
   `openai_client.py:75-86`.
