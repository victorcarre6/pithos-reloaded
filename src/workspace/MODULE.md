# `workspace` — l'autorité filesystem

> **Lis [`AGENTS.md`](../../AGENTS.md) avant de commencer.** Ce fichier est ton contrat complet : tu ne
> devrais pas avoir besoin d'ouvrir `docs/`. Ton point d'entrée exact est la rubrique « Prochaine action » de
> [`STATE.md`](STATE.md), à côté de ce fichier.
>
> **Tu ne commites, ne pousses et ne merges jamais.** Tes commits se *proposent* dans [`git.md`](git.md),
> avec les `ga`/`gcmsg` exacts — voir [`AGENTS.md`](../../AGENTS.md) § 7.

**Cible** : ~200 L au socle · +~150 L de `sandbox` en P7bis · ratchet **shrink-only**
**Dépend de** : `kernel`, `journal`.
**Niveau de dépendance** : 2.
**Stack** : **stdlib pur** — `pathlib`, `ast`, `os.replace`, `py_compile`, `subprocess` (pour `sandbox-exec`).

## 1. Autorité

`workspace` existe parce que **le pire incident de v1 était une écriture** : un appel d'outil mal formé,
écrit comme contenu de fichier, était du Python littéral valide — boucle de six heures sur un fichier vidé.
Ce module est isolé et sur-testé.

> **Le modèle ne renvoie jamais un fichier.** Il renvoie `{function_name, new_source}` ; le harness parse,
> vérifie un `def` unique au bon nom d'arité compatible, et le splice par plage de lignes issue de l'AST.
> **La destruction de v1 devient structurellement impossible** : un blob JSON écrit comme contenu de fichier
> ne passerait pas le parse en `def`.

Le splice par lignes préserve commentaires et formatage du reste du module — donc **pas besoin de LibCST**.

## 2. Interface publique

```python
def splice(target: Path, function_name: str, new_source: str) -> FileFact:
    "Parse, vérifie, splice par plage AST, écrit. Rend le fait typé que verifier consomme."

class Transaction:
    "before = read_bytes() à l'entrée ; restore() réécrit à l'octet près."
    def __enter__(self) -> Transaction: ...
    def restore(self) -> None: ...
    def cas_write(self, content: bytes) -> None:
        "Compare-and-swap : lève StaleContentError si le contenu courant a bougé depuis `before`."

def run_confined(argv: list[str], roots: Roots, deadline: Deadline) -> Completed:
    "sandbox-exec. P7bis — ne l'écris pas avant que la phase soit ouverte."
```

## 3. Interdits

- **N'importe jamais `verifier`, `bridge`, `engine`, `campaign`.**
- **N'écrit jamais hors d'un chemin `authoritative`** — le prédicat vient de `kernel.codeview`, et il est
  **partagé** : v1 avait cette logique éparpillée dans quatre modules avec des définitions divergentes.
- ⚠️ **N'applique jamais un patch approximatif** !
  → Le repli fuzzy de Villani — déplacement ≤ 6 lignes, normalisation des blancs — est bien fait, et il
  contredit frontalement « le modèle renvoie une fonction, pas un diff ». **Un patch approximatif appliqué
  avec succès est un risque que le splice supprime par construction.**
- **N'autorise aucune commande.** Le modèle n'en émet pas. Voir § 9.

## 4. Les six gardes, dans cet ordre

Aucune écriture ne se produit avant que les six soient passées. **Valider tout, puis appliquer.**

```text
1. chemin assaini (déquoté, normalisé, résolu) ET `authoritative`
2. parse en `def` unique, au bon nom
3. arité compatible avec la signature existante
4. py_compile du fichier splicé — message nommant fichier, validateur, exception, action attendue
5. refus d'une écriture sans effet
6. compare-and-swap contre `before` → StaleContentError typée
```

La sixième est **gratuite** : on détient déjà `before` pour la transaction, comparer le contenu courant avant
d'écrire fait trois lignes.

## 5. La transaction est une copie d'octets

La contrainte dure n°3 dit **« son fichier cible »**, au singulier — et `Node.target` est un `Path`, pas une
liste. Donc :

```python
before = path.read_bytes()      # à l'entrée
...
path.write_bytes(before)        # si le nœud n'est pas vert
```

**~10 L au lieu des ~150 L du dépôt Git fantôme** (`git init --git-dir` hors projet, `write-tree`,
`read-tree` + `checkout-index`, capture incrémentale, comparaison de snapshots). Le dépôt fantôme est
**`Reporté`**, pas écarté : il revient le jour où une étape devra toucher plusieurs fichiers.

**Préserve CRLF et BOM** : `_detect_newline_style` fait trois lignes et évite un diff de 400 lignes sur un
fichier Windows.

## 6. Critères de socle que ce module rend verts

- **Une nano-étape échouée restaure son fichier cible à l'identique.**
- **Un changement `.py` qui ne compile pas, ou qui perd toutes ses `def` de module, est refusé avant
  écriture.**
- **Un chemin non-`authoritative` n'est jamais proposé, écrit, projeté au modèle, ni compté comme
  changement** — un seul prédicat partagé décide (décision 12).
- **Une écriture concurrente est détectée au moment d'écrire**, pas seulement réparée après : le CAS échoue
  en `StaleContentError` typé.
- Contribue à : *un nœud dont la cible n'a pas effectivement changé ne peut pas être compté vert* — c'est
  `workspace` qui produit le `FileFact` avec son **bilan chiffré** (`n_replacements`, lignes ajoutées).

## 7. Le double

`tests/doubles/workspace.py` — un filesystem **en mémoire** : dict `{chemin: bytes}`, avec la même
interface. Il doit savoir simuler :

- un splice réussi rendant un `FileFact` cohérent ;
- un `StaleContentError` (contenu modifié entre l'entrée en transaction et l'écriture) ;
- un refus pour chacune des six gardes ;
- une restauration à l'octet près après échec.

> **Si le double doit simuler un état interne pour que `verifier` passe, la frontière est fausse** :
> `verifier` reçoit des `FileFact`, il ne lit pas le workspace. Consigne-le plutôt que de contourner.

## 8. Fini quand

- [ ] Un blob JSON passé en `new_source` est **refusé au parse**, pas écrit — test qui rejoue l'incident v1.
- [ ] Une `new_source` contenant **deux `def`** est refusée ; une contenant **zéro `def`** aussi.
- [ ] Une `new_source` dont l'arité diffère de la signature existante est refusée avec un message nommant
      les deux signatures.
- [ ] Un splice qui casserait la compilation est refusé **avant écriture** — le fichier sur disque est
      inchangé, vérifié par empreinte.
- [ ] Un splice qui ne change rien est refusé (`n_replacements == 0`).
- [ ] Le splice préserve **commentaires, formatage, CRLF et BOM** du reste du module — test par comparaison
      octet à octet hors plage splicée.
- [ ] Une écriture concurrente lève `StaleContentError`, et le fichier n'est pas écrit.
- [ ] `restore()` rend le fichier **identique à l'octet près** — comparaison de hash, pas de contenu texte.
- [ ] Un chemin non-`authoritative` est refusé à l'écriture **et** à la projection.
- [ ] Un chemin sortant du workspace par `..` ou par symlink est refusé — les deux côtés résolus.
- [ ] `tests/boundaries/` confirme les interdits d'import.

## 9. Pièges connus, et ce qui a été écarté

**La distinction qui décide de deux sous-domaines :**

> **Le modèle n'émet aucune commande — donc il n'y a rien à autoriser.**
> **Mais son code *est* exécuté — donc le confinement reste nécessaire.**

| Écarté | Pourquoi |
|---|---|
| **Toute la couche `permission`** (~200 L) | `PermissionEngine`, allowlist par préfixe de tokens, matching conscient des opérateurs, **l'arité des commandes shell — 161 L chez Kilo**, découpage de ligne shell, permissions de sous-agent. **Le modèle n'émet aucune commande.** |
| **`MutationGuardThresholds` et `_analyze_text_rewrite`** (~60 L) | le splice par plage AST **borne le rayon d'action par construction** : une réécriture massive n'est pas un cas à détecter, c'est un cas que le mécanisme ne peut pas produire |
| **La machinerie de patch** | parsing strict de diff, hunks, normalisation de chemins. Le splice a remplacé le patch |

**`sandbox` est gardé** avec sa phase P7bis — `new_source` finit dans un `subprocess`, et c'est une menace
réelle. Le profil `seatbelt` de base est la partie coûteuse à dériver ; **détecte la disponibilité de
`sandbox-exec` avant de t'y fier**, et refuse les descripteurs de fichier inscriptibles.

---

## Sources — reprises retenues

**121 lignes.** Chaque pointeur se lit dans `resources/`. Le détail complet et le contexte de chaque partie sont dans [`resources/IMPORT_REPORT.md`](../../resources/IMPORT_REPORT.md).
**Lis la source avant de porter.** Une reprise collée sans être relue est un défaut.

#### A — Villani Code · `resources/villani-code-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| A4.4 | `state_tooling.py:236-291` | Validation `py_compile` avec message nommant fichier, validateur, exception et action attendue. Chez nous la validation est **avant** écriture ; le format du message est le bon. | **Adapter** |
| A4.4 | `state_tooling.py:44-86` | Extraction du code depuis un payload enveloppé en blocs ```` ``` ````. **Un petit modèle enveloppe systématiquement sa sortie** — `new_source` y sera exposé malgré la sortie structurée. | **Copier** |
| A4.4 | `state_tooling.py:177-207` | `_sanitize_tool_input_file_path` — déquote, normalise, résout avant toute décision de politique. | **Copier** |
| A4.4 | `patch_apply.py:68-106` | **Valider tous les patchs, puis appliquer** (`# apply atomically after validation`, l. 95). | **Copier** |
| A4.4 | `patch_apply.py:330-333` | `_detect_newline_style` — préserve CRLF si le fichier en avait. | **Copier** |
| A4.4 | `state_runtime.py:508-590` | `small_model_tool_guard` — cible `authoritative` obligatoire, `Patch` refusé sur fichier absent, **read-before-edit** avec auto-lecture forcée. | **Copier** |
| A4.4 | `state_runtime.py:479-505` | `_is_strongly_adjacent_path` — définit « proche d'une cible verrouillée » (même dossier, `__init__.py`, même stem, `test_<stem>`). | **Adapter** |
| A4.4 | `runtime_safety.py:42-55` | `ensure_runtime_dependencies_not_shadowed` — **refuse de démarrer si le repo cible masque une dépendance du harness.** Notre campagne construit un paquet Python : le piège nous vise. | **Copier** |
| A4.4 | `runtime_safety.py:58-66` | `temporary_sys_path` — contextmanager restaurant `sys.path` intégralement. Le `verifier` importe du code produit. | **Copier** |
| A4.4 | `command_environment.py:153-260` | `runner_private_roots` / `build_agent_command_environment` — retire de l'environnement tout chemin absolu du harness. | **Adapter** |
| A4.4 | `benchmark/policy.py:29-57` | `normalize_path` / `comparison_key` / `path_is_within` / `path_matches_glob` — une seule implémentation partagée. | **Copier** |


#### B — Pi · `resources/pi-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| B3.4 | `packages/coding-agent/src/core/tools/edit.ts:192` | Préserver BOM et fins de ligne. Pi normalise tout en LF puis restaure un style global : **insuffisant pour notre promesse à l'octet près** sur fichiers mixtes. | **Adapter** |
| B3.4 | `packages/coding-agent/src/core/tools/edit-diff.ts:300` | Valider **toutes** les modifications avant d'en appliquer une : unicité et absence d'overlap. Transposer au remplacement d'un `def` unique, décorateurs compris. | **Adapter** |
| B3.4 | `packages/coding-agent/src/core/tools/edit-diff.ts:357` | **Détecter un patch sans effet.** Comparer les octets avant/après : un no-op n'est pas un progrès. Cause mécanique courte à `engine`, tentative conservée. | **Adapter** |
| B3.4 | `packages/coding-agent/src/core/tools/edit-diff.ts:207` | **Écarter le fuzzy matching du chemin nominal.** Cible = symbole AST exact + snapshot exact ; un mismatch fait réassembler le contexte ou rejette. | **Adapter** |
| B3.4 | `packages/coding-agent/src/core/tools/edit-diff.ts:365` | Diff relisible attaché à chaque tentative, produit par `difflib` avant écriture. **Le diff prouve la modification, pas la correction.** | **Adapter** |
| B3.4 | `packages/coding-agent/src/core/tools/write.ts:69` | **Garder l'exclusivité jusqu'à la fin réelle de l'écriture.** Libérer le verrou à l'annulation permet une écriture tardive après rollback. Tester l'intercalation. | **Adapter** |
| B3.4 | `packages/coding-agent/src/utils/paths.ts:108` | Inclusion de chemin **par composants**, pas par `startswith` (`/campaign2` n'est pas `/campaign`). Résoudre symlinks et parent existant. | **Adapter** |
| B3.4 | `packages/coding-agent/src/utils/paths.ts:36` | Détecter un contexte de fichier périmé. Préférer le digest des octets snapshotés ; si le fichier a changé depuis la génération, **ne pas écraser**. | **Adapter** |
| B3.4 | `packages/agent/src/harness/session/jsonl/storage.ts:94` | Staging puis rename atomique. Temporaire **unique** dans le même filesystem, flush/fsync, `os.replace`, nettoyage sur échec. Le `.tmp` fixe de Pi ne suffit pas. | **Adapter** |
| B3.4 | `packages/agent/test/harness/tools.test.ts:186` | Mutations concurrentes, annulation, conservation. Ajouter nos exigences absentes de Pi : `def` unique, nom/arité, décorateurs, `async def`, compilation, rollback d'un fichier créé. | **Adapter** |
| B3.4 | `packages/coding-agent/src/core/tools/file-mutation-queue.ts:32` | Sérialisation par identité réelle du fichier. Utile seulement si des feuilles deviennent concurrentes ; **le fallback sur fichier absent n'est pas une protection TOCTOU.** | **Adapter** |


#### C — Kilo Code · `resources/kilocode-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| C3.4 | `core/src/file-mutation.ts:144-158` | **`writeIfUnchanged` — compare-and-swap sur le contenu.** Transforme « on a écrasé sans le savoir » en `StaleContentError` typé. | **Traduire** |
| C3.4 | `core/src/file-mutation.ts:79-83` | Verrou par **chemin canonique** et section `uninterruptible` autour de l'écriture. | **Traduire** |
| C3.4 | `core/src/file-mutation.ts:53-66,124-142,198-204` | Résolution de chemin, création de parents, nettoyage sur échec. | **Traduire** |
| C3.4 | `opencode/src/tool/edit.ts:744-764` | Détection d'un fichier modifié depuis la lecture, avant application. | **Traduire** |
| C3.4 | `opencode/src/tool/edit.ts:49-72,117-125,164-166` | Contrats d'édition : unicité du motif, refus si ambigu, comptage des occurrences. | **Traduire** |
| C3.4 | `opencode/src/tool/edit.ts:222-228` | Refus d'une édition sans effet. | **Traduire** |
| C3.4 | `opencode/src/tool/edit.ts:30-46` | Rendu du diff d'une édition pour la trace. | **Traduire** |
| C3.4 | `opencode/src/patch/index.ts:398-425,460-484` | Application de patch avec validation préalable de toutes les hunks. | **Traduire** |
| C3.4 | `opencode/src/patch/index.ts:48-53,176-183,575-684` | Parsing strict, normalisation des chemins, gestion des fins de ligne. | **Traduire** |
| C3.4 | `opencode/src/tool/read.ts:88-101,251-263` | Lecture bornée avec offset et limite, refus des fichiers binaires. | **Traduire** |
| C3.4 | `kilo-sandbox/src/seatbelt-base.ts:1-4` | **Le profil `sandbox-exec` de base** — la partie coûteuse à dériver, fournie. | **Traduire** |
| C3.4 | `kilo-sandbox/src/seatbelt.ts:34-73` | Composition du profil : racines autorisées en lecture, en écriture, réseau. | **Traduire** |
| C3.4 | `kilo-sandbox/src/seatbelt.ts:46` | Détection de disponibilité de `sandbox-exec` avant de s'y fier. | **Traduire** |
| C3.4 | `kilo-sandbox/src/profile.ts:1-33` | Profil déclaratif compilé vers la syntaxe seatbelt. | **Traduire** |
| C3.4 | `kilo-sandbox/src/path.ts:11-33` | Normalisation des chemins pour le profil. | **Traduire** |
| C3.4 | `kilo-sandbox/src/context.ts:16-70` | Contexte d'exécution confinée : racines, variables, cwd. | **Traduire** |
| C3.4 | `kilo-sandbox/src/filesystem.ts:107-230` | **Garde in-process sur chaque opération d'écriture**, en complément du sandbox OS. | **Traduire** |
| C3.4 | `kilo-sandbox/src/filesystem.ts:151-158` | **Refus des descripteurs de fichier inscriptibles.** | **Traduire** |
| C3.4 | `kilo-sandbox/src/backend.ts:32-73` | Abstraction du backend de confinement, avec repli explicite si indisponible. | **Adapter** |
| C3.4 | `opencode/src/kilocode/sandbox/config.ts:39-60` | Configuration du sandbox par déclaration, pas par code. | **Adapter** |
| C3.4 | `opencode/src/skill/discovery.ts:72-152` | Découverte de capacités avec précédence par répertoire et détection de collision. | **Adapter** |


#### D — Ouroboros · `resources/ouroboros-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| D3.5 | `our/tools/edit_ops.py:79-157` | `_resolve_edit_target` — **canonicalisation du chemin en PREMIER**, puis root, puis artefacts protégés, puis runtime protégé. *« A guard that judges a different string than the one that executes is not a guard. »* | **Copier** |
| D3.5 | `our/tools/edit_ops.py:208-239` | `_partial_write_failure` — préfixe distinct des refus de validation : une mutation partielle réelle reste un échec d'**exécution**. | **Copier** |
| D3.5 | `our/tools/edit_ops.py:573-677` | `edit_batch` — chaque édition déclare son **nombre d'occurrences attendu** ; un écart annule le lot **entier avant écriture**. La forme sûre de « replace all ». | **Copier** |
| D3.5 | `our/tools/edit_ops.py:678-698` | `_syntax_check` — `compile()` pour `.py`, `json.loads` pour `.json`, et le `ValueError` nu de `compile()` (octet NUL) rapporté **contre le format réellement testé**. | **Copier** |
| D3.5 | `our/tools/edit_ops.py:699-730` | `_unified_diff` avec **note explicite sur la newline finale** : ne jamais rapporter « aucun changement textuel » pour un fichier dont les octets ont changé. | **Copier** |
| D3.5 | `our/shell_parse.py:1-60` | Parseurs argv **partagés par tous les garde-fous**, pour que la garde inspecte exactement ce qui s'exécute. | **Copier** |
| D3.5 | `our/tools/write_shape.py:1-40` | **Un seul seam** décide si une ligne de commande est *write-shaped*, avant que toute garde d'écriture n'agisse. | **Copier** |
| D3.5 | `our/git_shell_policy.py:19-40` | `GIT_READONLY_SUBCOMMANDS` — classification structurelle des sous-commandes git. Notre broker git en a besoin. | **Copier** |
| D3.5 | `our/argv_budget.py:1-120` | **Budget argv+env en octets encodés** : cap par chaîne et total via `sysconf`. | **Adapter** |
| D3.5 | `our/argv_budget.py:88-95` | Le noyau mesure la chaîne **avec son NUL** : tester `contenu > limite` laissait passer le cas exact-frontière, qui échouait ensuite en `E2BIG`. | **Copier** |
| D3.5 | `our/runtime_mode_policy.py:1-40` | `SAFETY_CRITICAL_PATHS` — liste **nommée** de chemins que le mode courant n'a pas le droit de réécrire, séparée des chemins runtime protégés. | **Copier** |
| D3.5 | `our/protected_artifacts.py:1-30` | Artefacts « boîte noire » : un binaire de référence est **exécutable mais non lisible en octets** — comparer ses octets, c'est les lire. | **Inspirer** |


#### E — Prime Agent · `resources/prime-agent-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| E3.4 | `ca/core/refinement/refinement.ts:345-359` | Temp nommé `<pid>.<uuid>.tmp` **dans le même répertoire**, `renameSync` atomique, **mode du fichier existant préservé** (0600 pour un état de harness). | **Adapter** |
| E3.4 | `rt/repl.py:661-680` | `stage_temp` — temps uniques par `mkstemp` dans le répertoire cible, avec le piège nommé : *« a fixed '.tmp' name could alias the other final path »*. | **Copier** |
| E3.4 | `rt/repl.py:681-690` | **Stager les deux temps avant de remplacer quoi que ce soit** : tout échec jusqu'au premier `replace` laisse la paire précédente intacte. | **Copier** |
| E3.4 | `ca/core/tools/truncate.ts:1-38` | Troncature à **deux limites indépendantes**, la première atteinte gagne, **jamais de ligne partielle**, et la troncature **rend son bilan** (`truncatedBy`, totaux, limites appliquées). | **Adapter** |
| E3.4 | `ca/core/tools/truncate.ts:67,153,249` | `truncateHead` / `truncateTail` / `truncateLine` — **trois fonctions nommées plutôt qu'un `truncate(mode=...)`**. Conforme à notre règle « pas de booléen qui pilote le comportement ». | **Traduire** |
| E3.4 | `rt/bash.py:60-104` | **Buffer de sortie borné tête + queue roulante avec marqueur d'octets jetés.** Ferme le collecteur v1 à 1,3 Go et toute exécution de code produit qui imprime en boucle. | **Copier** |
| E3.4 | `rt/bash.py:711-727` | Code de sortie récupéré par **canal de statut sur fd dédié**, pas par le code de retour du shell. Une commande qui laisse un descendant vivant ne fausse plus le verdict. | **Copier** |
| E3.4 | `rt/bash.py:699-709` | `printf` résolu sur le **PATH système par défaut**, avec six lignes expliquant qu'une fonction shell homonyme casserait le protocole. | **Copier** |
| E3.4 | `rt/bash.py:740-751` | `_signal_group` — `True` quand le signal est délivré **ou** que le groupe est déjà mort ; `False` seulement s'il n'a pas été délivré. | **Copier** |
| E3.4 | `rt/bash.py:731` | `NO_COLOR=1`, `TERM=dumb`, `CLICOLOR=0`, `FORCE_COLOR=0` sur tout sous-processus. **Notre `verifier` parse du pytest : les codes ANSI dans un contre-exemple le cassent.** | **Copier** |
| E3.4 | `ca/core/kernel/bootstrap.ts:439-472` | Verrou-répertoire à côté du venv, pour que deux sessions concurrentes n'installent pas en même temps. | **Adapter** |
| E3.4 | `ca/core/orphan-process-journal.ts:24-50` | Journal append-only `{pid, ownerPid, kernelPid, processStartId, active}` avec `fsync`. *« Process identity is pid + start time. »* | **Adapter** |
| E3.4 | `rt/mcp.py:26-95` | `_StderrTail` — stderr d'un serveur enfant en **tail borné (8 Ko / 40 lignes)**, strip ANSI et caractères de contrôle. | **Copier** |
| E3.4 | `rt/mcp.py:28` | `_SAFE_ENV` — l'environnement d'un serveur stdio est réduit à `HOME`, `PATH`, `TMPDIR`, `TEMP`, `TMP`. Version radicale du `runner_private_roots` de Villani. | **Copier** |
| E3.4 | `rt/mcp.py:249-261` | Rédaction du stderr diagnostique : les valeurs de configuration ≥ 4 caractères sont masquées ; **si une valeur est plus courte, tout le stderr est supprimé**. | **Copier** |


#### F — Unsloth · `resources/unsloth-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| F3.4 | `unsloth_cli/_tool_policy.py:165` | **Politique unique décidant si des outils peuvent être exposés**, selon l'adresse de bind et le mode sécurisé. | **Adapter** |
| F3.4 | `unsloth_cli/_tool_policy.py:19` | Détection d'adresse externe **incluant résolution DNS et IP littérale**, avant ouverture réseau. | **Adapter** |
| F3.4 | `unsloth_cli/_tool_policy.py:108` | **Normaliser les binds wildcard avant** d'évaluer l'exposition. Un `0.0.0.0` non normalisé qui se lit « local » est la faille type. | **Adapter** |
| F3.4 | `studio/backend/lan_access.py:213` | Prédicat **`is_public_address` partagé** par le bind, l'affichage et la politique d'outils. Trois consommateurs, une définition. | **Adapter** |
| F3.4 | `studio/backend/lan_access.py:72` | Énumérer les adresses LAN **sans inclure aveuglément** loopback ni interfaces hôte-only. | **Adapter** |
| F3.4 | `studio/backend/lan_access.py:370` | Sur échec de bind, **fermer tous les sockets partiellement ouverts et conserver la cause**. | **Adapter** |
| F3.4 | `studio/backend/lan_access.py:350` | Synchroniser l'état de confiance réseau avec **l'état réel du listener**, jamais avec le seul flag CLI. | **Adapter** |
| F3.4 | `studio/backend/lan_access.py:423,497` | Arrêt **idempotent** libérant tous les sockets ; décision d'accès **par requête**, centralisée et testable. | **Adapter** |
| F3.4 | `studio/backend/cloudflare_tunnel.py:507` | **Ne jamais considérer le spawn comme un succès** : attendre une readiness observable sous deadline. | **Adapter** |
| F3.4 | `studio/backend/cloudflare_tunnel.py:354,516` | Vérifier une URL par **probe** avant de l'annoncer prête ; **confirmer l'état de sortie** avant de finaliser. | **Adapter** |
| F3.4 | `studio/backend/cloudflare_tunnel.py:930` | Arrêt avec **jeton d'admission/génération** pour qu'une ancienne instance ne tue pas la nouvelle. Directement applicable à deux réveils launchd rapprochés. | **Adapter** |
| F3.4 | `studio/backend/cloudflare_tunnel.py:217,400` | Téléchargement d'un binaire externe **dans un cache contrôlé uniquement**, avec vérification d'existence ; encapsulation en objet à `start`/`wait_for_ready`/`stop`/`is_running`. | **Adapter** |
| F3.4 | `unsloth_cli/_system_dir_guard.py:1` | **Protéger les répertoires système et les chemins de configuration** contre les écritures de l'agent. Seconde ligne derrière le prédicat `authoritative`. | **Adapter** |
| F3.4 | `unsloth_cli/commands/start.py:1507` | **Écriture texte privée avec permissions restrictives** pour secrets et tokens. | **Adapter** |
| F3.4 | `unsloth_cli/commands/start.py:1498,1569` | Écriture JSON privée atomique ; **tester une clé contre le serveur avant de la mémoriser**. | **Adapter** |
| F3.4 | `unsloth_cli/commands/start.py:1191` | **Ne pas tuer un serveur encore utilisé par une session active** : le propriétaire est explicite. | **Adapter** |
| F3.4 | `unsloth/dataprep/synthetic.py:52,148,162` | **Terminaison récursive d'un arbre de processus** avec timeout de nettoyage ; readiness attendue explicitement ; **deadlines monotoniques partagés** entre subprocess, serveur et nettoyage. | **Adapter** |
| F3.4 | `unsloth/dataprep/raw_text.py:56,98,346` | Détecter le format **avant lecture** ; chunking à longueur et chevauchement explicites ; validation de dataset **avant écriture**. | **Adapter** |
| F3.4 | `unsloth/dataprep/raw_text.py:125` | Chunking préservant les **frontières sémantiques**, avec stride mesuré. | **Adapter** |


#### G — OpenHands · `resources/OpenHands-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| G3.4 | `src/services/child-conversation-launch.ts:110` | **Paramètres validés avant toute mutation.** | **Adapter** |
| G3.4 | S | **Claim idempotent d'un tool call parent : une demande ne peut pas être exécutée deux fois.** | **Adapter** |
| G3.4 | A | **Note explicite** quand le lien parent/enfant n'est pas disponible — jamais un silence. | **Adapter** |
| G3.4 | S | Lancement avec **paramètres d'isolation contrôlés** ; polling avec **intervalle et timeout nommés**. | **Adapter** |
| G3.4 | S | Résultat rapporté sous forme **succès/échec guidé** ; **point d'entrée unique** pour l'action. | **Adapter** |
| G3.4 | `src/constants/child-conversation.ts:26` | **Modes d'isolation énumérés** (`worktree`, `shared`) au lieu d'un booléen implicite. Conforme à notre règle de style. | **Adapter** |
| G3.4 | `src/constants/child-conversation.ts:37` | **Refuser la fonctionnalité si le backend est trop ancien.** | **Adapter** |
| G3.4 | `src/services/canvas-ui.ts:53` | Router les actions vers des **opérations nommées**, jamais vers des chemins arbitraires. | **Adapter** |
| G3.4 | `src/stores/use-event-store.ts:17,41,92` | Identifiant et timestamp extraits **avec repli explicite** ; tri **seulement quand l'ordre entrant l'exige** ; **append pur**. | **Adapter** |
| G3.4 | `src/hooks/use-websocket.ts:19` | Backoff de reconnexion borné, **délai initial et maximum nommés**. | **Adapter** |
| G3.4 | `src/api/agent-server-adapter.ts:592,600` | Settings **normalisés avant comparaison ou persistance** ; **un secret vide est traité comme absent**, il n'écrase jamais une valeur existante. | **Adapter** |
| G3.4 | `src/api/agent-server-adapter.ts:1033` | Settings de conversation et settings d'agent construits **en deux couches**. | **Adapter** |
| G3.4 | `src/api/agent-server-compatibility.ts:341` | **Probe locale du backend avant activation d'une mission.** | **Adapter** |


#### H — SWE-agent · `resources/SWE-agent-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| H4.4 | `tools/windowed/lib/windowed_file.py:150-175` *(hors extraction)* | **`get_window_text` avec ligne de statut et compteurs pré/post** : `[File: X (N lines total)]`, `(N more lines above)`, `(N more lines below)`. **Le modèle sait toujours ce qu'il ne voit pas.** Décision 29. | **Adapter** |
| H4.4 | `tools/windowed/lib/windowed_file.py:36-52` *(hors extraction)* | `ReplacementInfo` / `InsertInfo` — **une mutation rend son bilan chiffré** : ligne de départ, lignes cherchées, lignes remplacées, **nombre de remplacements**. | **Adapter** |
| H4.4 | `tools/windowed/lib/windowed_file.py:276` *(hors extraction)* | `undo_edit` — annulation **au niveau du fichier**, distincte du rollback transactionnel de mission. | **Adapter** |
| H4.4 | `tools/windowed/lib/windowed_file.py:228,240,264,270` *(hors extraction)* | `find_all_occurrences`, `replace` avec `reset_first_line`, `goto`, `scroll` — navigation bornée à sémantique nommée. | **Adapter** |
| H4.4 | `sweagent/environment/swe_env.py:24,51` | Contrat d'environnement séparant **deployment, repo, setup commands et timeout** ; wrapper mince — **l'agent ne connaît pas le runtime concret**. | **Adapter** |
| H4.4 | `sweagent/environment/swe_env.py:78,112` | **Copie profonde de configuration avant création d'une instance isolée** ; démarrage qui initialise, reset, puis exécute les commandes de préparation. | **Adapter** |
| H4.4 | `sweagent/environment/swe_env.py:103` | Hooks d'environnement **injectables aux étapes du lifecycle**. | **Adapter** |
| H4.4 | `sweagent/environment/repo.py:31,236` | Commandes de **reset vers un commit de base connu** ; fabrique repo depuis une entrée simplifiée et contrôlée. | **Adapter** |
| H4.4 | `sweagent/environment/repo.py:42,77` | Repo préexistant comme source locale **sans clone implicite** ; chemins **explicitement validés**. | **Adapter** |
| H4.4 | `sweagent/environment/hooks/abstract.py:1` | Protocole de hooks **sans import inverse**. | **Adapter** |
| H4.4 | `sweagent/agent/hooks/abstract.py:10-53` *(hors extraction)* | **Treize hooks nommés du cycle de vie de l'agent** — `on_step_start`, `on_actions_generated`, `on_action_started`, `on_action_executed`, `on_step_done`, `on_model_query`, `on_query_message_added`… plus `CombinedAgentHook` (`:56`) qui compose sans que l'appelant sache combien il y en a. | **Adapter** |
| H4.4 | `sweagent/utils/github.py:17,53` | Exception dédiée aux URL invalides ; **parser l'URL sans laisser la forme brute pénétrer le cœur**. | **Adapter** |


#### I — Langfuse · `resources/langfuse-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| I4.4 | `packages/shared/src/server/services/safeBlobKeySegment.ts:16` | **Découpe UTF-8 respectant les frontières de codepoints.** À n'appliquer qu'aux aperçus, **jamais au contenu probant**. | **Adapter** |
| I4.4 | LF030 | **ID logique séparé du nom de stockage.** Réserve reprise : un hash tronqué à 64 bits ne prouve pas l'injectivité. | **Adapter** |
| I4.4 | `worker/src/features/observation-field-overflow/processObservationFieldOverflow.ts:35` | **Référence publiée seulement après upload réussi** ; en cas d'échec, la valeur reste en place. | **Adapter** |
| I4.4 | `worker/src/features/blobstorage/manifest.ts:22` | **Manifest versionné de complétude** : fichiers, formats, tailles, intervalle **demi-ouvert**. Ajouter empreintes et génération. | **Adapter** |
| I4.4 | `worker/src/features/blobstorage/handleBlobStorageIntegrationProjectJob.ts:1433` | **Le manifest est le commit point** — écrit après tous les fichiers, curseur avancé ensuite. | **Adapter** |
| I4.4 | `worker/src/features/blobstorage/gzipStream.ts:28` | Flux compressé : **attendre la fin côté lisible pour ne pas perdre le trailer**. | **Adapter** |
| I4.4 | `worker/src/services/ClickhouseWriter/index.ts:180` | La division de batch est une bonne référence de backpressure ; **la troncature du dernier enregistrement trop gros est à écarter**. | **Adapter** |


---

## Sources — reprises écartées ou reportées

**20 lignes. N'implémente aucune de ces lignes.** Le pointeur reste pour qu'un retournement de décision retrouve la source. Si tu penses qu'une raison est fausse, **écris-le dans `STATE.md`, n'implémente pas.**

#### A — Villani Code · `resources/villani-code-main/`

| § | Source | Notion | Statut |
|---|---|---|---|
| A4.4 | `state_tooling.py:21-28` | `MutationGuardThresholds` — `120` lignes, ratio `0.35`, plancher `40`. **Des seuils nommés, versionnés, testables.** | **Écarté** |
| A4.4 | `state_tooling.py:89-122` | `_analyze_text_rewrite` — `SequenceMatcher` sur les lignes ⇒ `probable_rewrite`. Détection générique de ce qui a détruit `audio_visualizer.py`. | **Écarté** |
| A4.4 | `state_tooling.py:125-174` | `_analyze_patch_mutation` — même analyse appliquée à un diff, sans l'appliquer. | **Écarté** |
| A4.4 | `checkpoints.py:18-60` | `CheckpointManager` — snapshot **sur disque** avec `metadata.json`, et `rewind()`. Survit à un crash du processus. | **Reporté** |
| A4.4 | `permissions.py:174-209` | `classify_bash_command` — allowlist par **préfixe de tokens**, refus du chaînage, de la redirection et de la substitution. | **Écarté** |
| A4.4 | `permissions.py:212-233` | `bash_matches` — matching **conscient des opérateurs**, avec le commentaire qui nomme la faille : `to avoid prefix exploits like '&& rm -rf /'`. | **Écarté** |
| A4.4 | `permissions.py:51-107` | `PermissionEngine.evaluate_with_reason` — ordre `deny` → `ask` → `allow`, **chaque décision retourne sa raison**. | **Écarté** |


#### C — Kilo Code · `resources/kilocode-main/`

| § | Source | Notion | Statut |
|---|---|---|---|
| C3.4 | `opencode/src/snapshot/index.ts:107,111` | **`git init` dans un `--git-dir` hors projet** — le dépôt fantôme n'apparaît jamais dans le `git status` du produit. | **Reporté** |
| C3.4 | `opencode/src/snapshot/index.ts:406-408` | `write-tree` pour capturer : adressé par contenu, dédupliqué, gratuit à conserver. | **Reporté** |
| C3.4 | `opencode/src/snapshot/index.ts:465-501` | `read-tree` + `checkout-index` pour restaurer, avec **validation de tous les hashes avant de toucher un fichier** et **échec fatal plutôt que restauration partielle**. | **Reporté** |
| C3.4 | `opencode/src/snapshot/index.ts:526-547` | Nettoyage borné des snapshots anciens. | **Reporté** |
| C3.4 | `opencode/src/snapshot/index.ts:46,297-315` | Capture incrémentale sur les seuls chemins déclarés. | **Reporté** |
| C3.4 | `opencode/src/snapshot/index.ts:44,336-355` | Comparaison de deux snapshots sans matérialiser les fichiers. | **Reporté** |
| C3.4 | `opencode/src/snapshot/index.ts:216-217` | Exclusions explicites du snapshot. | **Reporté** |
| C3.4 | `opencode/src/session/revert.ts:78-118` | Revert par snapshot avec vérification préalable et journalisation de ce qui a été restauré. | **Reporté** |
| C3.4 | `opencode/src/permission/index.ts:102-154` | Évaluation de permission avec raison, ordre de précédence, et `ask` par défaut. | **Écarté** |
| C3.4 | `opencode/src/permission/index.ts:314-332,470-476` | Réponses persistées et portée d'une autorisation. | **Écarté** |
| C3.4 | `opencode/src/permission/arity.ts:1-161` | **Arité des commandes shell** : combien d'arguments une commande accepte, pour détecter une injection par argument surnuméraire. | **Écarté** |
| C3.4 | `opencode/src/tool/shell.ts:280-285,387-457` | Découpage d'une ligne shell en commandes, avec opérateurs et substitutions traités explicitement. | **Écarté** |
| C3.4 | `opencode/src/agent/subagent-permissions.ts:14-27` | Permissions d'un sous-agent dérivées de celles du parent, jamais élargies. | **Écarté** |



## Décisions locales — 07:09, socle implémenté

### Frontière réellement publiée

`Workspace(root: Path, *, view=kernel.codeview, trace=journal)` porte une racine
résolue explicite. La façade satisfait `WorkspacePort` : `splice`, `transaction`,
`project`. La fonction de module `splice` reste disponible, avec `root` obligatoire
en keyword-only ; aucune autorité ne se déduit du cwd. Le journal doit être lié
par son propriétaire avant usage ; les tests injectent les doubles officiels.

`TransactionPort` expose `before`, `last_plan`, le contexte, `splice`, `cas_write`,
`restore`. Utiliser **`transaction.splice` dans le contexte qui devra restaurer** :
la transaction sait alors qu'elle a écrit. Une autre transaction obtenue via
`workspace.splice` est une opération indépendante, pas un contexte imbriqué implicite.

```python
ws = Workspace(campaign_root)  # journal déjà lié par l'appelant
with ws.transaction(target) as transaction:
    fact = transaction.splice(function_name, new_source)
    # l'appelant vérifie ; une exception restaure automatiquement
    if verdict_is_red:
        transaction.restore()
```

Une sortie normale du contexte conserve la mutation. **Le module ne décide jamais
si un nœud est vert.** L'appelant doit invoquer `restore()` sur un verdict non vert
qui ne lève pas d'exception. `cas_write(bytes)` est le primitive bas niveau du
harness, pas une entrée exposée au modèle ; le chemin modèle passe par `splice` et
ses gardes AST. Une transaction est mono-usage ; les snapshots restent inspectables
après sa sortie. Pas de création implicite de cible ou de parents.

### Gardes, représentation et preuves

- Une racine résolue et le chemin canonique sont comparés par composants ; le même
  `kernel.codeview.classify_repo_path` décide de l'édition et de la projection.
  Le sanitizer conserve `..` et les préfixes sensibles : le `lstrip("./")` de
  Villani n'est pas porté, car il masquerait un échappement.
- Une seule fonction **de premier niveau**, nom exact ; fonctions imbriquées dans
  son corps permises. Deux définitions de module de même nom, dont une classe,
  sont ambiguës et refusées. Décorateurs, y compris parenthésés multilignes, inclus
  dans la plage ; `async def` reste async.
- Signature compatible conservatrice : mêmes positions, noms utilisables par
  mots-clés, présence des défauts, keyword-only, variadiques, catégorie sync/async.
  Renommage des paramètres position-only/variadiques, annotations et valeurs des
  défauts permis. Une incompatibilité nomme les deux signatures.
- Markdown admis uniquement comme enveloppe complète ; aucune extraction parmi
  de la prose. Numérotation admise si toutes les lignes sont préfixées `N: ` avec
  indices consécutifs (décision 29). Pas de fuzzy matching, de patch ou d'exécution.
- UTF-8, avec ou sans BOM, seulement ; le cookie d'encodage est vérifié **avant et
  après** splice. Les octets hors plage sont recollés directement, sans normaliser
  le module entier. Le premier terminateur de la plage guide l'insertion ; CRLF,
  LF, CR, fichiers mixtes et absence de newline finale sont couverts.
- `compile(bytes, filename, "exec", dont_inherit=True)` utilise le compilateur de
  `py_compile`, sans écrire de `.pyc` et sans exécuter le code objet. Nom de fichier,
  validateur, classe d'exception et action attendue dans le diagnostic.
- `SplicePlan` est un contrat Pydantic kernel : octets candidats, `FileFact`, diff
  relisible et `lines_added` (delta signé). `FileFact` reste celui du kernel :
  chemin canonique, SHA-256 exacts, plage 1-based inclusive, un remplacement.
  Les snapshots typés supplémentaires attendus par verifier restent à publier
  par kernel ; aucun champ local ne se fait passer pour un `Fact` partagé.

### Écriture et conservation

La source candidate est journalisée avant validation ; les octets avant/après
(hexadécimaux, sans perte) sont journalisés avant staging. Un `emit` autre que
`True` produit `attempt_not_written` et empêche l'écriture. Aucune source invalide
n'est corrigée silencieusement ; sa tentative reste dans le journal.

Un temporaire unique dans le même répertoire est écrit, flushé/fsyncé, puis remplacé
atomiquement ; mode du fichier conservé. Le CAS est contrôlé avant staging puis
avant rename. Les copies temporaires sont nettoyées ; les données brutes restent
dans le journal. Une panne de ce journal après mutation n'interdit pas le rollback,
puisque ses deux états ont déjà été archivés.

Un verrou local couvre comparaison et écriture entre appels coopérants ; il ne
prétend pas protéger contre un processus extérieur modifiant le filesystem entre
la dernière comparaison et le rename. La campagne du socle doit rester exclusive.
La sauvegarde persistante pour SIGKILL, le dépôt fantôme, les feuilles concurrentes
et le confinement OS restent reportés. Aucun `sandbox-exec`, subprocess, Git,
réseau, hook de mission ou logique de permission dans ce socle.

### Stack et taille mesurée

Toujours aucune dépendance tierce supplémentaire : stdlib (`ast`, `difflib`, `io`,
`re`, `tokenize`, `hashlib`, `pathlib`, `os`, `stat`, `tempfile`, `threading`,
`datetime`, `typing`), contrats Pydantic déjà publiés par kernel, interface publique
journal. Pytest est déjà déclaré pour les tests.

**388 lignes physiques de production / cible indicative ~200**, notice MIT et
lignes vides comprises : façade 38, chemins 36, Protocols 27, préparation 125,
transaction 162. La cible n'est pas relevée. Cet écart est justifié par les gardes
mesurées du splice binaire (encodage, décorateurs, compilation), l'interface/double
obligatoires et la transaction qui conserve les preuves avant mutation et rend
les pannes explicites. Le prototype de dix lignes n'assurait ni staging, ni CAS
sérialisé, ni confinement de chemin, ni propagation d'un échec de restauration.
