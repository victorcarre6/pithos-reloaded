# `kernel` — le vocabulaire du projet

> **Lis [`AGENTS.md`](../../AGENTS.md) avant de commencer.** Ce fichier est ton contrat complet : tu ne
> devrais pas avoir besoin d'ouvrir `docs/`. Ton point d'entrée exact est la rubrique « Prochaine action » de
> [`STATE.md`](STATE.md), à côté de ce fichier.
>
> **Tu ne commites, ne pousses et ne merges jamais.** Tes commits se *proposent* dans [`git.md`](git.md),
> avec les `ga`/`gcmsg` exacts — voir [`AGENTS.md`](../../AGENTS.md) § 7.

**Cible** : ~380 L · ratchet **shrink-only**
**Dépend de** : rien. `kernel` n'importe aucun module interne.
**Niveau de dépendance** : 0 — tous les autres modules dépendent de lui.
**Stack** : Pydantic v2 · `ast`, `pathlib`, `hashlib` stdlib. **Rien d'autre.**

## 1. Autorité

`kernel` est l'autorité sur **le vocabulaire** : les types que tous les autres modules échangent, la lecture
AST du workspace, et la forme des erreurs. Il ne décide rien, il ne fait aucun effet de bord, il ne lit
aucun fichier hors de `codeview`.

> **Il porte la *forme* du reçu, jamais l'autorité de l'émettre.** Celle-ci appartient à `verifier` seul.
> Le vocabulaire est en bas, la décision au-dessus.

## 2. Interface publique

### `contracts` — cinq modèles au socle

Ceux que la tranche verticale traverse. **Un contrat s'écrit quand son producteur existe** : `Proposal` et
`ToolEntry` arrivent avec `campaign`, `RepoFact` avec `broker`, `HostFact` avec `lifecycle`. Ne les écris pas
d'avance.

```python
class Node(BaseModel):
    id: str
    parent_id: str | None
    depth: int                 # plafond dur : 3
    target: Path               # PAS une liste — voir § 3
    criterion: Criterion | None
    status: NodeStatus         # enum fermée
    blocked_cause: BlockedCause | None

class Criterion(BaseModel):
    relation: Relation         # enum fermée de 9 valeurs
    symbols: list[str]         # noms de symboles existants, vérifiés
    domain: Domain             # enum fermée

class Event(BaseModel):
    ts: str
    v: int                     # version de format, une ligne, migration future possible
    type: EventType
    durable: bool              # preuve vs télémétrie
    payload: dict

class FileFact(BaseModel):
    path: Path
    sha_before: str
    sha_after: str
    spliced_range: tuple[int, int]
    n_replacements: int        # une mutation rend son bilan chiffré

class Receipt(BaseModel):
    node_id: str
    attempt: int
    returncode: int | None     # jamais coercé par `or` — voir § 9
    artifact_path: Path
    facts: list[Fact]
```

### `codeview` — lire et parser, jamais choisir

```python
def symbols(path: Path) -> list[Symbol]: ...        # nom, arité, kwonly, défauts, annotations
def module_defs(path: Path) -> list[str]: ...
def snippet(path: Path, start: int, end: int) -> str: ...   # borné en octets ET en lignes
def is_binary(path: Path) -> bool: ...
def classify_repo_path(path: Path) -> PathClass: ...  # 5 classes dont `authoritative`
def is_path_within(child: Path, parent: Path) -> bool: ...
```

### `errors` — une hiérarchie, pas une taxonomie

```python
class PithosError(Exception):
    cause: Cause               # enum FERMÉE — pas une classe par cas d'échec
    field_path: str | None

class ErrorAccumulator:
    "Collecte toutes les violations d'un coup, chacune avec le chemin exact du champ fautif."
    def add(self, field_path: str, cause: Cause, detail: str) -> None: ...
    def raise_if_any(self) -> None: ...
```

L'accumulateur vit ici parce que **deux modules l'utilisent** : `campaign` pour l'admission d'une proposition
(décision 28) et `bridge` pour la revalidation de schéma. Les **règles** d'admission, elles, vivent dans
`campaign` — pas ici.

## 3. Interdits

- **N'importe aucun module interne.** Aucun. C'est le niveau 0.
- **Aucun I/O hors `codeview`**, qui lit des fichiers pour les parser. Pas d'écriture, pas de subprocess, pas
  de réseau.
- **Pas de `logging`.** La décision 10 l'exclut du projet entier.
- ⚠️ **Pas de regex pour extraire des symboles Python** !
  → C'est l'erreur exacte de v1, qui a coûté l'incident d'arité `smooth_levels(0.0, 0.0, 0.0)` sur une
  signature `(tuple, tuple, float)`. **L'AST donne arité, défauts, kwonly et annotations gratuitement.**
  Les regex restent acceptables pour les langages non-Python.
- **`Node.target` est un `Path`, pas une liste.** La contrainte dure n°3 dit « son fichier cible », au
  singulier : une nano-étape qui voudrait toucher deux fichiers **ne doit pas pouvoir se construire**. C'est
  une garde de type, pas une convention.

## 4. Ce qu'on ne refait pas

**`trace` a quitté ce module.** Il est devenu `journal` (niveau 1). Si tu vois un pointeur du rapport d'import
qui parle d'append JSONL, de `fsync`, de verrou ou de rotation, **ce n'est pas ici**.

**La sélection de fichiers n'est pas ici non plus.** `relevant_files`, `impact_files`, la fermeture d'imports
et le scoring vivent dans `engine/context` : c'est du contexte, pas du vocabulaire. `codeview` lit et parse.

## 5. Contenu, sous-module par sous-module

| Fichier | Contenu | ~L |
|---|---|---:|
| `contracts.py` | les 5 modèles du socle + les enums fermées | 120 |
| `facts.py` | `FileFact`, `Receipt`, et le type union `Fact` | 40 |
| `codeview.py` | AST, symboles, arité, snippet borné, binaire, `classify_repo_path` | 180 |
| `errors.py` | classe de base, enum `Cause`, `ErrorAccumulator` | 40 |

**Au socle, ni index persistant ni reconstruction incrémentale.** Ils arrivent quand relire le dépôt de
campagne coûtera quelque chose — le dépôt démarre vide.

## 6. Critères de socle que ce module rend verts

- **Toute identité d'enregistrement est une clé typée, jamais une chaîne de repli**, et la relation de
  réconciliation est vérifiée **réflexive, symétrique et transitive par test** (décision 22). *« A chain is
  not an equivalence relation. »*
- **Une proposition mal formée reçoit toutes ses violations en une fois**, chacune avec le chemin exact du
  champ fautif (décision 28) — le mécanisme est ici, les règles dans `campaign`.
- Contribue à : *un nœud non vérifiable ne s'exécute jamais* (le type `Criterion` le rend représentable), et
  *un chemin non-`authoritative` n'est jamais proposé, écrit ni compté* (le prédicat unique est ici).

## 7. Le double

`tests/doubles/kernel.py` — **le plus simple du projet** : `kernel` est pur, donc son double est un jeu de
constructeurs qui produisent des objets valides et un `codeview` qui répond depuis un dict `{chemin:
source}` en mémoire, sans toucher le disque.

C'est ce double que **tous** les autres modules utilisent. Soigne-le : une erreur ici se propage partout.

## 8. Fini quand

- [ ] Les 5 modèles valident et rejettent selon leurs contraintes, avec un test par cas de rejet.
- [ ] `Node.target` **refuse** une liste — test explicite.
- [ ] `codeview.symbols` rend l'arité correcte sur une signature à `tuple`, défauts et kwonly ; un test
      rejoue précisément l'incident `smooth_levels(0.0, 0.0, 0.0)`.
- [ ] `classify_repo_path` rend les 5 classes, et `authoritative` est vrai **exactement** pour les chemins
      attendus — table de cas, pas d'échantillon.
- [ ] `snippet` est borné **en octets et en lignes**, vérifié sur un fichier d'une seule ligne de 10 Mo.
- [ ] `is_binary` détecte : extension, BOM UTF-16/32, octet NUL, > 30 % de non-imprimables.
- [ ] `ErrorAccumulator` rend **toutes** les violations d'une structure à trois défauts, chacune avec son
      chemin de champ — jamais seulement la première.
- [ ] La relation d'identité est prouvée réflexive, symétrique et transitive **par test**.
- [ ] `tests/boundaries/` confirme que `kernel` n'importe aucun module interne.
- [ ] Le double existe et satisfait le même `Protocol` que l'implémentation.

## 9. Pièges connus

- **`None or 0` lit un résultat inconnu comme un succès.** Aucune coercition `or` sur un code de retour :
  `returncode: int | None` reste `None` quand il est inconnu, et c'est `verifier` qui décide de ce que ça
  vaut.
- **Un token absent n'est jamais un zéro.** Les compteurs d'usage peuvent rester `None` ; ne les normalise
  pas à 0.
- **Refuse `NaN` et `Infinity`** à la frontière des contrats : une ligne de `parse_constant`, une classe
  entière de littéraux dangereux fermée.
- **Un plancher sur un champ de budget** : un zéro dans un champ de budget est un interrupteur déguisé, pas
  une valeur.

---

## Sources — reprises retenues

**76 lignes.** Chaque pointeur se lit dans `resources/`. Le détail complet et le contexte de chaque partie sont dans [`resources/IMPORT_REPORT.md`](../../resources/IMPORT_REPORT.md).
**Lis la source avant de porter.** Une reprise collée sans être relue est un défaut.

#### A — Villani Code · `resources/villani-code-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| A4.1 | `mission_state.py:12-95` | État sérialisable avec `verified_facts`, `open_hypotheses`, `steps`, `intended_targets`, et `from_dict` défensif — chaque champ recoercé. Modèle direct de notre `Node`. | **Inspirer** |
| A4.1 | `mission_state.py:114-117` | `new_mission_id()` — horodatage UTC triable **avec sous-seconde**, explicitement pour éviter les collisions dans la même seconde. | **Copier** |
| A4.1 | `mission_state.py:162-171` | `load_resume_bundle` — la reprise charge état + messages + résumé en un appel typé. | **Adapter** |
| A4.1 | `indexing.py:69-114` | `RepoIndex.build/save/load/needs_rebuild` — index de fichiers avec symboles et snippet borné, persisté en JSON. | **Adapter** |
| A4.1 | `indexing.py:117-127` | `compute_repo_fingerprint` — SHA-256 de `path:size:mtime` pour invalider un index sans le relire. Réutilisé par l'index mémoire du dashboard. | **Copier** |
| A4.1 | `indexing.py:146-150` | `extract_snippet` — lecture bornée en octets **et** en lignes avant tout parsing. | **Copier** |
| A4.1 | `repo_rules.py:44-51` | `is_ignored_repo_path` — un seul prédicat partagé par le planner, le verifier et le reporting. | **Copier** |
| A4.1 | `repo_rules.py:54-68` | `classify_repo_path` → `vcs_internal` / `editor_artifact` / `runtime_artifact` / `generated` / **`authoritative`**. Pivot de la décision 12. | **Copier** |
| A4.1 | `repo_rules.py:71-91` | `is_authoritative_doc_path` — restreint la doc éditable au `README` racine et à `docs/*`. | **Adapter** |
| A4.1 | `state_execution.py:17-30` | `summarize_changes` → `intentional` vs `incidental` via `classify_repo_path`. | **Copier** |
| A4.1 | `utils.py:22-27` | `is_path_within` par `relative_to` + `ValueError`. Trois lignes, aucun `..` à gérer. | **Copier** |


#### B — Pi · `resources/pi-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| B3.1 | `packages/agent/src/harness/session/types.ts:18` | Identités stables, parent explicite, séquence de stockage. Séparer id, parent_id, numéro de séquence, horodatage. Une branche conversationnelle Pi n'est pas notre arbre de travail. | **Adapter** |
| B3.1 | `packages/agent/src/harness/result.ts:1` | Résultats discriminés à codes fermés : `invalid_schema`, `invalid_symbol`, `timeout`, `interrupted`, `invariant_failed`. **Une exception d'infrastructure ne devient jamais un verdict vert.** | **Adapter** |
| B3.1 | `packages/agent/src/harness/session/commit.ts:90` | Contrôler ids uniques et parent antérieur **avant** publication. Choisir et tester explicitement notre règle de monotonie. | **Adapter** |
| B3.1 | `packages/agent/src/harness/session/jsonl/types.ts:4` | Version explicite du format persistant. Versionner `Event`, `tree`, `registry` dès P0 ; refuser une version inconnue avec diagnostic. | **Adapter** |
| B3.1 | `packages/agent/src/harness/session/jsonl/storage.ts:79` | Une ligne JSONL comme unité logique indivisible au rejeu. Ne rend pas atomiques ensemble `tree.json`, fichiers produit et journal. | **Adapter** |
| B3.1 | `packages/agent/src/harness/session/jsonl/storage.ts:253` | **Publier sur disque avant de modifier la projection mémoire.** Tester un append refusé. | **Adapter** |
| B3.1 | `packages/agent/src/harness/session/jsonl/storage.ts:87` | Distinguer fin tronquée et corruption au milieu. **Ne pas reprendre la réparation destructive de `open` l. 210.** | **Adapter** |
| B3.1 | `packages/coding-agent/src/modes/rpc/jsonl.ts:21` | Framing sur **LF uniquement** et décodage UTF-8 incrémental. Éviter `str.splitlines()`. Borner la taille. | **Adapter** |
| B3.1 | `packages/coding-agent/src/modes/json-event.ts:20` | Deltas linéaires sans duplication du cumulatif. Doubler une réponse ne doit pas quadrupler le volume de traces. | **Adapter** |
| B3.1 | `packages/agent/src/harness/utils/usage.ts:14` | Usage en champs distincts (input/output/reasoning/cache), agrégé une fois. **Un compteur absent reste inconnu, pas zéro.** | **Adapter** |
| B3.1 | `packages/telemetry/src/index.ts:18` | Cycle de vie d'un span indépendant du fournisseur : parent, début, fin, statut, attributs. Mission → nœud → appel/gate. Aucun SDK requis. | **Adapter** |
| B3.1 | `packages/telemetry/src/memory.ts:54` | Snapshots détachés des objets mutables. **Une trace émise ne doit pas changer quand la source mute.** Tester en mutant après émission. | **Adapter** |
| B3.1 | `packages/chord/src/json.ts:4` | Sous-ensemble JSON strict et fini. Refuser NaN/Infinity à la frontière des contrats. | **Adapter** |
| B3.1 | `packages/telemetry/src/noop.ts:3` | Instrumentation facultative — jamais pour désactiver les preuves JSONL obligatoires. | **Adapter** |
| B3.1 | `packages/ai/src/utils/assistant-message-frame.ts:8` | Frames rejouables, message final autoritatif. Référence pour une feuille agentique ; le contrat nominal reste requête / sortie brute / verdict / usage. | **Adapter** |


#### C — Kilo Code · `resources/kilocode-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| C3.1 | `core/src/util/error.ts:3-72` | `NamedError.create` — classe d'erreur portant **un schéma**, forme filaire `{name, data}`, et `isInstance` testant **par nom, pas par prototype**. Une erreur sérialisée en JSONL et relue par le dashboard reste identifiable. | **Traduire** |
| C3.1 | `opencode/src/mcp/index.ts:107-128` | `Status` = union discriminée fermée `connected`/`disabled`/`failed(error)`/`needs_auth`/`needs_client_registration`. **La santé d'un serveur est une énumération, pas un booléen.** Modèle du statut de `ToolEntry`. | **Traduire** |
| C3.1 | `opencode/src/worktree/index.ts:49-88` | Sept erreurs typées pour un module de 630 L, unionées en un type `Error`. Taxonomie d'échec **par opération**, pour que l'appelant branche. | **Inspirer** |
| C3.1 | `kilo-memory/src/schema.ts:187-227` | `parse()` défensif : un coerceur par type avec fallback, et **une version incompatible lève** au lieu d'être coercée silencieusement. Modèle du `from_dict` de `Node`. | **Traduire** |
| C3.1 | `kilo-memory/src/schema.ts:174-185` | `persist()` **omet délibérément les `limits`** : constantes du harness, jamais relues du disque. Séparer dans un même fichier d'état ce que l'opérateur possède de ce que le harness possède. | **Traduire** |
| C3.1 | `kilo-memory/src/schema.ts:206-211` | Planchers à 1000 ms sur `minIntervalMs`/`timeoutMs` : **un zéro dans un champ de budget est un interrupteur silencieux**. Applicable à notre borne murale et à l'intervalle de réveil. | **Traduire** |
| C3.1 | `kilo-memory/src/schema.ts:14` | « Topics are assigned **by rule (never by the LLM)** ». Confirmation externe de notre contrainte dure n°1, écrite par un tiers. | **Inspirer** |
| C3.1 | `opencode/src/tool/read.ts:394-435` | `collect()` — lecture en flux avec **trois plafonds indépendants** : lignes, `MAX_LINE_LENGTH = 2000`, `MAX_BYTES = 50 KB`. Retourne `cut` et `more` **distincts**. | **Traduire** |
| C3.1 | `opencode/src/tool/read.ts:352-364` | Lignes préfixées `N: ` et **marqueur de fin explicite** `(End of file - total N lines)`. Le modèle sait s'il a tout vu. À croiser avec `ling.txt:109`. | **Traduire** |
| C3.1 | `opencode/src/tool/read.ts:146-190` | `isBinaryFile` — extensions, puis BOM UTF-16/32, puis octet NUL, puis **> 30 % de non-imprimables**. Quatre passes, aucune dépendance. | **Traduire** |
| C3.1 | `opencode/src/util/filesystem.ts:210-262` | `findUp`/`up`/`globUp` — remontée vers une racine d'arrêt, avec `rootFirst` pilotant la précédence. Mécanisme des règles par répertoire. | **Traduire** |
| C3.1 | `core/src/util/hash.ts:3-11` | `Hash.fast` (SHA-1, clés de cache) vs `Hash.sha256` (contenu). **Deux intentions nommées** plutôt qu'un hash générique. | **Traduire** |
| C3.1 | `core/src/util/token.ts:3-5` | `CHARS_PER_TOKEN = 4` — grossier, mais **une seule constante partagée** par tout le budget de contexte. À fixer pour Ling. | **Traduire** |
| C3.1 | `core/src/util/wildcard.ts:3-14` | Glob → RegExp en 12 lignes. Subtilité : un motif finissant par `" .*"` devient `"( .*)?"`, donc **`"git diff *"` matche aussi `"git diff"` sans argument**. | **Traduire** |
| C3.1 | `core/src/policy.ts:36-42` | `evaluate(action, resource, fallback)` — `findLast` sur des statements wildcard, **fallback fourni par l'appelant**. Moteur allow/deny complet en 49 lignes. | **Traduire** |
| C3.1 | `opencode/src/session/summary.ts:12-70` | `unquoteGitPath` — décodage octal C **à la frontière d'affichage**. Évitable en amont par le prélude git (`git/index.ts:6-18`). | **Inspirer** |


#### D — Ouroboros · `resources/ouroboros-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| D3.2 | `our/code_intelligence.py:73-115` | `FileFact` / `CodeInventory` — projection structurelle **dérivée seulement** : la source est lue pour être parsée, **jamais mise en cache**. `coverage` = comptage par disposition. | **Copier** |
| D3.2 | `our/code_intelligence.py:485-555` | `_file_fact` — ordre des gardes : échappement de chemin (symlink résolu inclus) → sensible → taille → NUL dans les 4 premiers Ko → parse. **Chaque refus produit une disposition nommée.** L'index ne ment jamais par omission. | **Copier** |
| D3.2 | `our/code_intelligence.py:548-551` | `structural_unavailable:<lang>` — un langage connu sans grammaire disponible est **déclaré**, jamais rabattu sur des regex. | **Copier** |
| D3.2 | `our/code_intelligence.py:583-635` | Reconstruction incrémentale par **SHA-256 de contenu** (pas mtime) : un digest inchangé réutilise son `FileFact`. | **Copier** |
| D3.2 | `our/code_intelligence.py:116-121` | Clé de cache = SHA-256 du chemin racine résolu. Deux workspaces ne partagent jamais un index. | **Copier** |
| D3.2 | `our/code_intelligence.py:737-764` | `impact_files` — fermeture d'imports/références bornée en profondeur, **chaque fichier avec sa raison** (`imports depth N`, `references <sym>`, `target`). | **Copier** |
| D3.2 | `our/code_intelligence.py:766-800` | `relevant_files` — sélection par score déterministe **avec raison textuelle par fichier**. **Zéro appel modèle pour construire le contexte.** | **Copier** |
| D3.2 | `our/code_intelligence.py:261-270` | `_signature` — signature AST d'une fonction/classe. Notre gate d'arité s'y branche directement. | **Copier** |
| D3.2 | `our/code_intelligence.py:556-582` | Un `.env`, une clé, un `.pem` n'entrent **jamais** dans l'inventaire, donc jamais dans le contexte. | **Copier** |
| D3.2 | `our/code_search_rg.py:1-304` | Recherche `ripgrep` optionnelle, **chaque match post-filtré** par les gates protégé/secret. La recherche ne contourne pas la politique de chemins. | **Adapter** |


#### E — Prime Agent · `resources/prime-agent-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| E3.1 | `ca/core/refinement/refinement.ts:34-48` | `HarnessEntry` avec `version` incrémenté et `created_at` conservé à l'update. **Un `ToolEntry` de registre doit porter la même histoire.** | **Adapter** |
| E3.1 | `ca/core/goals.ts:10` | `GoalStatus` — **`budget_limited` est un statut, pas un échec.** Exactement notre décision 8 et la décision 23. | **Traduire** |
| E3.1 | `ca/core/goals.ts:100-123` | Type guard structurel **avant** toute désérialisation. Chez nous c'est Pydantic ; la discipline « ne jamais faire confiance à ce qu'on relit » est la même. | **Inspirer** |
| E3.1 | `ca/core/kernel/bootstrap.ts:686-712` | `hashRuntimeSource` — identité du runtime = **hash de contenu de tous les `.py` + `pyproject.toml`**. Tout changement de code ou de dépendance invalide automatiquement. | **Adapter** |


#### H — SWE-agent · `resources/SWE-agent-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| H4.1 | `sweagent/types.py:15-31` *(hors extraction)* | **`StepOutput` — `thought`, `action`, `output`, `observation` en champs distincts**, jamais concaténés, plus `execution_time`, `exit_status`, `state`, `thinking_blocks`. La séparation est la forme du contrat, pas un traitement. | **Adapter** |
| H4.1 | `sweagent/types.py:33-41` *(hors extraction)* | `to_template_format_dict` — **ce qui sert au template n'est pas ce qui sert à la machine** : `tool_calls` et `state` exclus du rendu, `state` aplati à la racine. | **Adapter** |
| H4.1 | `sweagent/types.py:56-74` *(hors extraction)* | `HistoryItem` avec `message_type` **obligatoire** en littéral fermé, et des `tags` que les processeurs ajoutent pour marquer un traitement spécial. | **Adapter** |
| H4.1 | `sweagent/types.py:82-100` *(hors extraction)* | `AgentInfo` / `AgentRunResult` — résultat de run typé, distinct de l'état interne. | **Adapter** |
| H4.1 | `sweagent/agent/problem_statement.py:26` | **Protocol de problème minimal** permettant plusieurs sources sans coupler l'agent. | **Adapter** |
| H4.1 | `sweagent/agent/problem_statement.py:68,101,294` | Problème borné et sérialisable ; chargé depuis un fichier **avec provenance explicite** ; fabrique unique convertissant une entrée simplifiée. | **Adapter** |
| H4.1 | `sweagent/utils/serialization.py:36` | **Fusion récursive de dictionnaires de configuration**, sans écraser silencieusement les sous-clés. | **Adapter** |
| H4.1 | `sweagent/utils/config.py:30` | **Retirer les chemins absolus avant d'écrire une trace partageable.** | **Adapter** |
| H4.1 | `sweagent/utils/files.py:8` | Loader tolérant à l'absence, **utilisé uniquement aux frontières**. | **Adapter** |
| H4.1 | `sweagent/run/common.py:24` | Troncature **récursive** des chaînes de configuration avant affichage. | **Adapter** |


#### I — Langfuse · `resources/langfuse-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| I4.1 | `packages/shared/src/domain/observations.ts:5` | Observation typée et **causalité explicite** : appel modèle, outil et évaluation séparés ; mission, nœud, tentative, parent et horodatages conservés. | **Adapter** |
| I4.1 | `packages/shared/src/domain/scores.ts:4` | **La source d'un résultat est distincte de sa valeur.** Une source « évaluateur » peut désigner un LLM judge : **elle ne certifie pas un invariant**. | **Adapter** |
| I4.1 | `packages/shared/src/domain/scores.ts:18` | **L'autorité interne n'est pas attribuable par l'API publique** — l'énumération d'admission exclut la valeur réservée. Plus fort qu'un défaut sûr. | **Adapter** |
| I4.1 | `packages/shared/src/domain/score-configs.ts:5` | Configuration de score : noms, types, **bornes numériques et catégories explicites**, unicité des labels. | **Adapter** |
| I4.1 | `packages/shared/src/server/evals/evalScoreIds.ts:6` | **Identité déterministe d'un résultat** (UUID v5 sur un tuple), stable à travers les retries. Décision 30. | **Adapter** |
| I4.1 | `worker/src/features/evaluation/evalScoreEvent.ts:21` | **Identité de transport renouvelée, identité de résultat déterministe.** Republier sans recompter. | **Adapter** |
| I4.1 | `worker/src/features/evaluation/evalScoreEvent.ts:54` | **Métadonnées de provenance de l'hôte écrites après la charge utile**, dans un espace de champs réservé. | **Adapter** |
| I4.1 | `packages/shared/src/domain/observations.ts:82` | **Mesure fournie distincte de mesure calculée** : valeur, origine et disponibilité. Ne pas reprendre les agrégats qui **convertissent une absence en zéro**. | **Adapter** |
| I4.1 | `packages/shared/src/server/otel/OtelIngestionProcessor.ts:133` | **Budget transactionnel** avant reconstruction de métadonnées imbriquées — compter les emplacements, trous d'index compris. | **Adapter** |
| I4.1 | `packages/shared/src/server/otel/OtelIngestionProcessor.ts:107` | **Refus des segments de chemin dangereux** (`__proto__`, `constructor`, `prototype`). En Python : grammaire fermée de chemins. | **Adapter** |

## Décisions locales — 06:09

- Interface livrée : `kernel.contracts` (`Node`, `Criterion`, `Event`, enums), `kernel.facts` (`FileFact`, `Receipt`, `RecordKey`, `same_identity`), `kernel.errors`, `kernel.codeview` et `kernel.protocol.CodeView`. Les imports `enum`, `typing`, `keyword` sont du vocabulaire stdlib nécessaire aux enums, au Protocol et aux noms Python ; aucune nouvelle dépendance externe.
- Les symboles décrits sont les fonctions synchrones/asynchrones de premier niveau. `Symbol.arity` compte les positions déclarées, même optionnelles ; `posonly`, `kwonly`, `defaults`, `annotations`, `vararg`, `kwarg` évitent de confondre arité et compatibilité de domaine. Les annotations/défauts sont des textes AST, jamais évalués. `module_defs` ajoute les classes, sans prétendre déduire leur constructeur.
- Le catalogue initial comprend les neuf relations et les cinq domaines concrets de la décision 2. `lists_of<T>` reste reporté à la définition de stratégies concrètes dans verifier. Le nombre de symboles suit le tableau de la décision 2. Leur existence doit être revalidée sur l'AST avant exécution ; `Criterion` n'effectue aucune I/O.
- `Node` vérifie la cohérence locale parent/profondeur (0 à 3), critère obligatoire pour `running`/`passed`, cause obligatoire exclusivement pour `blocked`. L'arbre vérifie l'existence du parent et l'unicité des ids. Les contrats sont gelés ; une transition doit reconstruire un modèle validé. Le gel n'est pas profond.
- `Event.v=1` est imposé ; types initiaux `status`, `validation`, `tool_activity`. Le payload est validé en mode Python par `TypeAdapter(dict[str, JsonValue], allow_inf_nan=False)` **aussi à l'entrée JSON**. Tests dédiés : la configuration globale seule ne suffisait pas avec Pydantic 2.13.4 ; l'union récursive alternative coercait tuples/sets/Decimal. Aucun de ces cas n'est conservé silencieusement dans la version livrée.
- `spliced_range` est une plage de lignes 1-based inclusive. Un no-op (`n_replacements=0`) et un code retour inconnu (`None`) sont représentables ; kernel ne les transforme jamais en verdict. `Fact` est actuellement `FileFact`, les autres producteurs n'existant pas encore.
- L'identité de résultat est `RecordKey(kind="verification", value=(mission_id, node_id, attempt, relation))`, conforme aux décisions 22/30. Les clés sont gelées et hashables. `same_identity` refuse les données non typées et les clés absentes ; aucun fallback ni nettoyage des octets d'un nom.
- `snippet` ne lit que les 8 000 premiers octets et rend au plus 40 lignes. Les bornes `start/end` sont 1-based inclusives **dans ce préfixe** ; une plage hors préfixe rend une chaîne vide. La taille UTF-8 de sortie reste bornée après décodage. Le parseur AST lit au plus 2 000 001 octets et refuse au-delà de 2 000 000.
- `classify_repo_path` est lexical et n'accepte que des chemins relatifs sans `..`. Les cinq classes suivent la précédence Villani. Environnements et caches sont runtime ; secrets et chemins cachés sans classe sont refusés explicitement, y compris `.env.example`. Cette politique conservatrice a été annoncée à l'utilisateur en attendant sa réponse à l'écart des six retours de la source. Le consommateur doit appeler séparément `is_path_within(child, parent)` pour le confinement après résolution des symlinks.
- `is_binary` examine les extensions de la reprise Kilo et les 4 096 premiers octets. UTF-16/32 est classé binaire pour ce lecteur UTF-8, alors que la source récente sait lire ces encodages. Notice MIT et pointeur réel conservés dans `codeview.py`.
- Le double fournit les cinq constructeurs et `MemoryCodeView({Path: str | bytes})`. Parsing indépendant sur `ast` ; réutilisation du seul prédicat public pur `classify_repo_path` et des constantes du contrat. Le filesystem virtuel ne modélise pas de symlinks. Les tests de symlinks portent sur l'implémentation réelle ; aucune preuve d'intégration avec un module voisin n'est revendiquée.
- Tests propres au kernel conservés sous `src/kernel/` pour respecter le périmètre § 6. Les contrôles préparés `test_double_contract.py` et `test_import_boundaries.py` doivent être déplacés sous `tests/contracts/test_kernel_double.py` et `tests/boundaries/test_kernel.py` après autorisation explicite. Le module reste formellement bloqué jusque-là.
