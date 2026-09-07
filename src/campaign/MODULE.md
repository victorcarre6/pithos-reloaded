# `campaign` — la politique

> **Lis [`AGENTS.md`](../../AGENTS.md) avant de commencer.** Ce fichier est ton contrat complet : tu ne
> devrais pas avoir besoin d'ouvrir `docs/`. Ton point d'entrée exact est la rubrique « Prochaine action » de
> [`STATE.md`](STATE.md), à côté de ce fichier.
>
> **Tu ne commites, ne pousses et ne merges jamais.** Tes commits se *proposent* dans [`git.md`](git.md),
> avec les `ga`/`gcmsg` exacts — voir [`AGENTS.md`](../../AGENTS.md) § 7.

**Cible** : ~550 L · ratchet **shrink-only**
**Dépend de** : `kernel`, `journal`, `verifier`, `bridge`, `workspace`, `engine`.
**Niveau de dépendance** : 4.
**Stack** : Pydantic v2 · `json` · `difflib.SequenceMatcher` **stdlib**. Aucune dépendance externe nouvelle.

## 1. Autorité

`campaign` possède **le magasin** — un fichier, un propriétaire — les propositions, la détection de
redondance, l'admission déclarative et la condition d'arrêt.

**La famille `skill` du magasin *est* le registre d'outils.** Il n'y a pas deux objets : c'est le même.

## 2. Interface publique

```python
# store.py — deux familles vivantes au socle
class Family(str, Enum):
    skill = "skill"        # LE registre d'outils
    memory = "memory"      # alimentée dès le socle (décision 31)
    prompt = "prompt"      # consommée par refinery seul — enabled: false
    subagent = "subagent"  # vide tant que le mode agentic est différé

def load() -> Store:
    "Relecture défensive champ par champ. NE LÈVE JAMAIS. Voir § 4."
def put(family: Family, key: str, entry: Entry) -> None: ...
def render_compact(family: Family, budget: int) -> str: ...

# admit.py — les RÈGLES ; le mécanisme (accumulateur) est dans kernel
def admit(proposal: dict) -> Ok[Proposal] | Err[list[Violation]]: ...

# propose.py
def dedup(proposal: Proposal, store: Store) -> Redundancy | None: ...
def rank(proposals: list[Proposal]) -> list[Proposal]:
    "Tuple lexicographique d'axes nommés. AUCUN scalaire pondéré."
def derive(index: RepoIndex) -> list[Proposal]:
    "Filet déterministe. Ne se déclenche qu'après trois rejets consécutifs."

# stop.py
def should_stop(store: Store) -> StopProposal | None: ...
```

## 3. Interdits

- **Aucun appel modèle dans la décision de redondance.** La décision 24 refuse qu'une décision de politique
  soit prise par un modèle, et la redondance *est* une décision de politique. L'option d'Ouroboros —
  light-model à choix fermé, fail-open — respecte la contrainte n°1 à la lettre, et elle est **écartée quand
  même**.
- **Aucun scalaire pondéré pour classer.** Pas de `priority*0.7 + confidence*0.3`, pas de score de
  confiance. Décision 23 : le résultat est un **produit d'axes**, pas un statut.
- **Le magasin ne lève jamais à la relecture.** Voir § 4.
- **N'écris pas les familles `prompt` et `subagent`.** Elles n'ont aucun consommateur au socle.

## 4. Le magasin — la règle qui compte plus que le reste

⚠️ **Un magasin écrit par un modèle doit se relire sans jamais lever** !
→ Une entrée mal formée est ignorée avec sa raison journalisée, jamais propagée en exception.

C'est le cœur du **spike n°6** : `rt/harness.py` est en dataclass + `json` stdlib, avec une relecture
défensive champ par champ ; nos contrats sont en Pydantic, et **Pydantic lève là où l'original dégrade**.
C'est exactement le comportement à **ne pas** reproduire. Une entrée mal formée est ignorée avec sa raison
journalisée, jamais propagée en exception.

**Deux familles vivantes au socle, pas quatre.** `prompt` n'est consommée que par `refinery`, qui est
`enabled: false` ; `subagent` est vide. Or **tout ce qui est lourd dans `rt/harness.py` existe pour éditer
des `prompt`** : deux scopes, rollback par reconstruction inverse, label mobile séparé de la version
immuable, clé de cache typée. **Tout cela est `Reporté` avec P9.** Chaque entrée garde `version` entier,
horodatages et `source` — ~5 L.

**~150 L au lieu d'un portage de 820 L.**

## 5. La redondance se mesure en deux temps

```text
temps 1 — lexical            à la proposition          SequenceMatcher sur titre + description normalisés
temps 2 — empreinte de contrat  dès que les critères existent   {relation, symbols, domain} canonicalisé
```

**Deux propositions formulées différemment qui produisent le même contrat sont le même outil.** L'empreinte
tranche là où le lexical est aveugle, et elle ne coûte aucun appel.

Le prix est nommé : **le doublon du temps 2 se découvre tard**, après décomposition, parfois après une
première nano-étape verte. C'est un rejet tardif, pas un outil livré en double.

**La récurrence est comptée, jamais jetée** : un doublon rejeté trois fois est un signal, pas du bruit. Il
incrémente un compteur qui remonte dans la proposition d'arrêt.

## 6. Le modèle propose, la dérivation est un filet

Le backlog ouvert **est le sujet d'étude** : l'une des cinq questions expérimentales est *« crée-t-il un
outil utile, puis le réutilise-t-il ? »*. Si le harness dérivait toutes les propositions, la question
perdrait son sujet.

Donc : **le modèle propose.** `derive()` ne se déclenche **qu'après trois rejets consécutifs** pour
redondance ou malformation, afin qu'une mission ne soit pas stérile. **Et les deux compteurs sont séparés
dans la trace** — propositions du modèle acceptées contre propositions du filet — donc l'indicateur reste
mesurable, et le filet devient lui-même une mesure : *à quelle fréquence le modèle n'arrive-t-il pas à
proposer ?*

## 7. L'admission déclarative

Le **mécanisme** est dans `kernel` (`ErrorAccumulator`). Les **règles** sont ici :

- validation par regex, alphabet **sans métacaractères shell**, préfixes autorisés, bornes de longueur ;
- **placeholders fermés, aucune expression évaluable.** C'est une opposition frontale entre deux sources,
  tranchée : Pi exécute les commandes contenues dans une valeur de configuration
  (`resolve-config-value.ts:10`, écarté) ; OpenHands interdit toute expression évaluable dans un placeholder
  (`manifest-template.ts:76`, repris). **La nôtre est la seconde.**
- **toutes les violations en une fois**, chacune avec le chemin exact du champ fautif — jamais seulement la
  première. Une proposition à trois défauts coûterait sinon trois sessions à 16 k au lieu d'une.

## 8. Contenu

| Fichier | Contenu | ~L |
|---|---|---:|
| `store.py` | magasin 2 familles, relecture défensive, rendu compact | 150 |
| `registry.py` | `ToolEntry`, `TaskLifecycle` (7 états, **3 formes d'échec**), péremption par empreinte | 120 |
| `admit.py` | les règles d'admission | 100 |
| `propose.py` | dédup 2 temps, classement lexicographique, filet déterministe | 120 |
| `stop.py` | taxonomie fermée, raison énumérant ce qui a été examiné | 40 |
| `mcpconfig.py` | écriture de la couche `managed` de la config MCP | 20 |

## 9. Critères de socle que ce module rend verts

- **Une proposition d'outil redondante est rejetée mécaniquement, sans appel au modèle.**
- **Un outil vérifié devient appelable par les sessions suivantes sans intervention humaine.**
- **Le système propose son arrêt quand il ne trouve plus de proposition non redondante.**
- **La satisfaction d'un outil vérifié est invalidée dès que l'empreinte de ses fichiers change**, sans
  intervention humaine.
- **Une proposition mal formée reçoit toutes ses violations en une fois**, chacune avec le chemin exact du
  champ fautif.
- **La famille `memory` est alimentée dès le socle** — `campaign` y écrit les propositions récurrentes.

## 10. Le double

`tests/doubles/campaign.py` — un magasin **en mémoire** avec la même interface, plus un `admit` pilotable
(table `{proposition → verdict}`). Il doit savoir rendre : une entrée mal formée **ignorée sans lever**, un
doublon lexical, un doublon par empreinte, et une proposition d'arrêt.

## 11. Fini quand

- [ ] Le magasin **ne lève jamais** sur une entrée mal formée, corrompue, tronquée, ou d'une version
      inconnue — test par corruption systématique de chaque champ.
- [ ] Une entrée ignorée est **journalisée avec sa raison**.
- [ ] `dedup` rejette un doublon lexical **et** un doublon par empreinte de contrat, sans aucun appel modèle
      — test qui échoue si un client de modèle est instancié.
- [ ] La récurrence est **comptée** : un doublon rejeté trois fois incrémente son compteur et remonte dans
      la proposition d'arrêt.
- [ ] `rank` est un tuple lexicographique — test qui vérifie que chaque départage est attribuable à un axe
      nommé.
- [ ] `derive` ne se déclenche **qu'après trois rejets consécutifs**, et les deux compteurs sont séparés
      dans la trace.
- [ ] `admit` rend **toutes** les violations d'une proposition à trois défauts, chacune avec son chemin de
      champ.
- [ ] Un placeholder contenant une expression évaluable est **refusé**, test explicite.
- [ ] La satisfaction d'une entrée `skill` est invalidée quand l'empreinte de ses fichiers change.
- [ ] `TaskLifecycle` distingue **trois formes d'échec** — « échec » n'est pas un état.
- [ ] `tests/boundaries/` confirme que `campaign` n'est importé que par `refinery`.

## 12. Pièges connus, et ce qui a été écarté

| Écarté | Pourquoi |
|---|---|
| **Scopes, rollback, label mobile du magasin** (~350 L) | ils servent à éditer des `prompt`, et rien n'édite de `prompt` tant que `refinery` est éteint |
| **`effective_priority` et `_RANK_ORDER`** | un scalaire à constantes magiques et un ordre en dur par titre |
| **`TakeoverConfig`** | `max_waves=3` — nous avons des missions et une borne murale, pas de vagues |
| **`policy_hidden_reason`, `alias_for`, `mutates_worktree`** | aucune politique ne cache d'outil ; aucun renommage avant plusieurs outils ; notre snapshot est inconditionnel et fait 10 L |
| **La dédup sémantique par appel à choix fermé** | décision 24 : une décision de politique n'est pas prise par un modèle |

**Gardées** : `capability_omissions` — la surface d'outils projetée porte la **raison typée** de ce qui
manque (décision 29 appliquée au registre) — et **un module d'outils qui échoue à l'import omet *tous* ses
outils**, mode d'échec réel et silencieux du produit MCP. Plus la couche `managed` de la config MCP, écrite
par le runtime : c'est exactement la décision 7.

---

## Sources — reprises retenues

**144 lignes.** Chaque pointeur se lit dans `resources/`. Le détail complet et le contexte de chaque partie sont dans [`resources/IMPORT_REPORT.md`](../../resources/IMPORT_REPORT.md).
**Lis la source avant de porter.** Une reprise collée sans être relue est un défaut.

#### A — Villani Code · `resources/villani-code-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| A4.6 | `autonomy.py:390-400` | `Opportunity` — `priority`, `confidence`, `evidence`, `blast_radius`, `task_contract`. **`evidence` est obligatoire** : une opportunité sans preuve n'existe pas. | **Copier** |
| A4.6 | `autonomy.py:523-631` | `discover_opportunities` — **découverte du backlog par heuristiques déterministes**. Zéro appel modèle. | **Adapter** |
| A4.6 | `autonomy.py:716-722` | `_is_authoritative_opportunity` — élimination avant sélection, donc avant inference. | **Copier** |
| A4.6 | `autonomous.py:53-60` | `TaskLifecycle` — sept états, dont **trois formes d'échec distinctes**. « Échoué » ne dit pas s'il faut réessayer. | **Copier** |
| A4.6 | `autonomous.py:1014-1027` | `_repo_fingerprint_for_task` — empreinte **restreinte à ce qui concerne la tâche**. | **Copier** |
| A4.6 | `autonomous.py:1029-1042` | `_mark_task_satisfied` / `_is_task_satisfied` — satisfaction invalidée dès que l'empreinte bouge. | **Copier** |
| A4.6 | `autonomous_helpers.py:44-52` | `task_key_for_opportunity` — clé normalisée **avec table d'alias**. Sans alias, « ajouter un parseur » et « créer un outil de parsing » passent toutes deux notre rejet de redondance. | **Copier** |
| A4.6 | `autonomous_helpers.py:9-26` | `build_wave_candidates` — filtre en cascade puis déduplication par clé en gardant la meilleure priorité. | **Copier** |
| A4.6 | `autonomous_helpers.py:61-64` | `retry_limit_for_contract` — le nombre de retries dépend du type de contrat. | **Copier** |
| A4.6 | `autonomous_stop.py:7-12` | `StopDecision` — dont **`planner_churn`** et **`stagnation`**, qui nomment précisément les modes d'échec de v1. | **Copier** |
| A4.6 | `autonomous_stop.py:35-47` | `category_exhaustion_reason` — la raison d'arrêt **énumère ce qui a été examiné**. Un arrêt qui ne dit pas ce qu'il a couvert n'est pas auditable. | **Copier** |
| A4.6 | `autonomous_progress.py:10-36` | Machine à états par catégorie : `discovered` → `attempted`. L'épuisement devient mécanique. | **Copier** |
| A4.6 | `autonomous_progress.py:39-88` | `surface_followups` — une catégorie découverte mais non traitée **génère sa tâche de suivi** avant que l'arrêt soit proposable. | **Adapter** |
| A4.6 | `autonomous_reporting.py:77-145` | `build_takeover_summary` — distingue changements intentionnels, incidents et **préexistants**. Sans cette notion, on attribue au système des changements qu'il n'a pas faits. | **Copier** |
| A4.6 | `mcp.py:27-35` | `load_mcp_config` — couches `managed` → `user` → `project` → `local`. **La couche `managed` est écrite par le runtime** : exactement notre décision 7. | **Copier** |
| A4.6 | `mcp.py:11-24` | `_expand_env` récursif avec `${VAR:-default}`, sans secret en dur. | **Copier** |
| A4.6 | `project_memory.py:99-142` | `ValidationStep` / `ValidationConfig` — les commandes de validation sont **une donnée persistée**, pas une constante du harness. | **Copier** |
| A4.6 | `project_memory.py:313-362` | `scan_repo` — dérive `RepoMap` + `ValidationConfig` + `ProjectRules` d'un repo inconnu, une fois, puis persiste. | **Adapter** |
| A4.6 | `skills.py:16-33` | `discover_skills` — `SKILL.md` à frontmatter YAML, découverte par `rglob`. | **Copier** |


#### B — Pi · `resources/pi-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| B3.6 | `packages/evals/src/vitest-evals/harness-table.ts:66` | **Canonicalisation JSON avant comparaison structurelle.** Brique manquante du critère « schémas structurellement identiques » de la décision 5. | **Adapter** |
| B3.6 | `packages/evals/src/vitest-evals/harness-table.ts:105` | **Empreinte stable du contrat plutôt qu'un identifiant fourni par le modèle.** Pilier de la décision 19. | **Adapter** |
| B3.6 | `packages/coding-agent/src/core/source-info.ts:6` | Provenance explicite de chaque ressource. | **Adapter** |
| B3.6 | `packages/coding-agent/src/core/diagnostics.ts:1` | Collisions nommées, avec gagnant et ressource ignorée. Un écrasement silencieux est un bug. | **Adapter** |
| B3.6 | `packages/ai/scripts/model-data.ts:42` | Vérifier l'égalité **exacte** de deux inventaires. | **Adapter** |
| B3.6 | `packages/ai/scripts/model-data.ts:193` | Manifest de versions et empreintes vérifié avant chargement. | **Adapter** |
| B3.6 | `packages/coding-agent/src/utils/paths.ts:36` | Invalidation d'un outil vérifié quand son fichier change. Convergence exacte avec la décision 5 amendée. | **Adapter** |
| B3.6 | `packages/coding-agent/examples/extensions/dynamic-tools.ts:27` | Enregistrement dynamique après initialisation. | **Adapter** |
| B3.6 | `packages/coding-agent/examples/extensions/reload-runtime.ts:30` | Recharger les capacités **à une frontière sûre**, jamais au milieu d'un effet. | **Adapter** |
| B3.6 | `packages/chord/src/node/bundle-loader.ts:231` | Vérifier l'intégrité avant d'activer une nouvelle génération. | **Adapter** |
| B3.6 | `packages/evals/src/extensions.eval.ts:110` | **Prouver création, chargement ET appel effectif de la capacité produite.** C'est littéralement la question expérimentale 4, avec son patron de test. | **Adapter** |
| B3.6 | `packages/tui/src/fuzzy.ts:12` | **Contre-exemple** : ne pas confondre recherche approximative et rejet de redondance. Un score flou ne décide pas d'un rejet mécanique. | **Adapter** |
| B3.6 | `scripts/diff-model-catalog.mjs:36` | Rapport `added`/`removed`/`changed` entre deux catalogues. | **Adapter** |
| B3.6 | `scripts/publish-release-announcement.test.mjs:12` | **Une publication tardive ne doit pas rétrograder une génération.** | **Adapter** |
| B3.6 | `packages/chord/src/facets/host.ts:423` | Préparer et valider le candidat avant de remplacer l'actif. | **Adapter** |
| B3.6 | `packages/chord/src/facets/host.ts:858` | Détection mécanique des cycles de dépendance. | **Adapter** |
| B3.6 | `scripts/publish-release-announcement.mjs:10` | Annoncer une version seulement après vérification de sa disponibilité. | **Adapter** |
| B3.6 | `packages/coding-agent/test/suite/regressions/6162-extension-active-tools-next-turn.test.t … | Une modification du registre devient visible au tour suivant. | **Adapter** |
| B3.6 | `packages/coding-agent/examples/extensions/structured-output.ts:4` | Arrêter une feuille après son résultat structuré, sans tour final inutile. | **Adapter** |


#### C — Kilo Code · `resources/kilocode-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| C3.6 | `opencode/src/tool/registry.ts:332-374` | Registre d'outils avec résolution par nom, détection de collision et provenance. | **Traduire** |
| C3.6 | `opencode/src/permission/index.ts:505-549` | Portée d'une autorisation liée à une ressource identifiée. | **Adapter** |
| C3.6 | `opencode/src/mcp/index.ts:64-128` | Cycle de vie d'un serveur MCP et **statut en union fermée**. | **Traduire** |
| C3.6 | `kilo-memory/src/recall/topics.ts:21,26-96` | **Moteur lexical sans dépendance** : recouvrement de termes tolérant aux formes fléchies. Socle du rejet de proposition redondante, meilleur que `difflib` seul. | **Traduire** |
| C3.6 | `kilo-memory/src/recall/recall.ts:168-192` | Scoring de pertinence explicable, chaque contribution nommée. | **Adapter** |
| C3.6 | `http-recorder/src/matching.ts:11-36` | Canonicalisation avant comparaison. Convergent avec `pi/harness-table.ts:66`. | **Traduire** |
| C3.6 | `opencode/src/skill/index.ts:71-77,110-147,186-190` | Chargement de capacités, validation du frontmatter, activation. | **Adapter** |
| C3.6 | `opencode/src/config/parse.ts:8-72` | Parsing de configuration avec erreurs portant scope et chemin. | **Traduire** |
| C3.6 | `opencode/src/config/variable.ts:43-118` | Substitution de variables **bornée**, sans exécution de commande. Contre-exemple utile face à `pi/resolve-config-value.ts:10`. | **Traduire** |
| C3.6 | `opencode/src/config/managed.ts:20-68` | **Couche de configuration écrite par le runtime**, distincte de celle de l'opérateur. Convergent avec `pi/mcp.ts:27` et notre décision 7. | **Traduire** |


#### D — Ouroboros · `resources/ouroboros-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| D3.7 | `our/improvement_backlog.py:285-374` | **La récurrence n'est jamais jetée** : un doublon incrémente `count`/`last_seen`, **rouvre** un item clos, et élève le rang. | **Copier** |
| D3.7 | `our/improvement_backlog.py:199-220` | Le vivier de candidats est **déterministe, classé et plafonné (20) avant tout appel modèle**. Le modèle ne voit jamais le backlog brut. | **Copier** |
| D3.7 | `our/improvement_backlog.py:221-284` | Deux phases : snapshot sous verrou **partagé**, verrou relâché, appel LLM **hors verrou**, puis passe exacte sous verrou exclusif. | **Copier** |
| D3.7 | `our/improvement_backlog.py:423-455` | `close_backlog_items` — fermeture **sur commit, par le code**, jamais par le modèle. | **Copier** |
| D3.7 | `our/improvement_backlog.py:502-560` | Toilettage **déclenché par la taille**, plafonné, non conditionné à une erreur. Un backlog qui grossit se nettoie mécaniquement. | **Adapter** |
| D3.7 | `our/semantic_dedup.py:1-140` | Dédup sémantique **après** miss exact, sur candidats structurels seulement, modèle renvoyant **un id d'une liste fermée** validé exactement, **fail-open**. Voir conflit n°3. | **Adapter** |
| D3.7 | `our/semantic_dedup.py:52-62` | Le bornage pour comparaison porte un **marqueur visible** et ne touche jamais l'artefact durable — seulement la vue que le juge lit. | **Copier** |
| D3.7 | `our/evolution_fingerprint.py:1-42` | Module **feuille sans dépendances** dont la seule raison d'être est que compteur et gate lisent la même empreinte. **Notre clé de redondance a trois lecteurs.** | **Copier** |
| D3.7 | `our/tools/registry.py:1862-2005` | `capability_omissions()` — la surface d'outils projetée porte **la raison typée de chaque absence**. Décision 14 appliquée aux outils. | **Copier** |
| D3.7 | `our/tools/registry.py:1566-1571,1605-1616` | Un module d'outils qui échoue à l'import omet **tous** ses outils en silence : l'omission est enregistrée durablement. | **Copier** |
| D3.7 | `our/tools/registry.py:2006-2030` | `policy_hidden_reason` — **« caché par politique » n'est pas « n'existe pas »**. | **Copier** |
| D3.7 | `our/tools/registry.py:1551` | `mutates_worktree` — drapeau de capacité par outil ; le dispatcher snapshote `git status` autour des outils marqués. | **Copier** |
| D3.7 | `our/tools/registry.py:1557` | `alias_for` — un ancien nom reste **appelable mais jamais annoncé**. | **Copier** |
| D3.7 | `our/skill_readiness.py:13-110` | Blockers séparés en **réparables par l'agent** et **nécessitant l'opérateur**. La cause mécanique dit *quoi* ; ça dit *qui*. | **Copier** |
| D3.7 | `our/skill_loader.py:1-7` | Verdict de revue **lié au hash de contenu**, périmé dès que les octets changent. **Même mécanisme que la satisfaction périmée — une seule primitive à écrire.** | **Copier** |
| D3.7 | `our/skill_loader.py:28-33` | Les fichiers de **contrôle** sont exemptés du hash de l'objet qu'ils gouvernent : sinon écrire le marqueur après le hash périme le verdict. | **Copier** |
| D3.7 | `our/contracts/skill_manifest.py:12-70` | Manifeste unifié à types, runtimes et **permissions** fermés ; `canonical_skill_name` calculé une fois, partagé par l'état, le routage et l'UI. | **Copier** |
| D3.7 | `our/contracts/task_contract.py:1-8` | *« The contract is a durable, LLM-readable description of what this task is trying to accomplish. **It is NOT a deterministic success oracle.** »* La séparation que nous faisons déjà, énoncée. | **Inspirer** |
| D3.7 | `our/contracts/task_contract.py:298-378` | Les revendications d'acceptation sont **normalisées et versionnées**. | **Adapter** |
| D3.7 | `our/evolution_checkpoints.py:15-90` | Ledger append-only de **résultats de cycle**, taggé *après* le task-done, joint par `task_id`. | **Copier** |
| D3.7 | `our/mcp_client.py:371-400` | Description, résultat **et texte de schéma** d'un serveur externe préfixés « données non fiables, pas des instructions ». **S'applique à nos propres outils.** | **Copier** |
| D3.7 | `our/mcp_client.py:230-250` | `stdio` = exécutable + liste d'arguments exacte. **Pas de shell, pas d'env, pas de cwd.** | **Copier** |
| D3.7 | `our/mcp_client.py:62-72,180-215` | Denylist des hôtes de métadonnées cloud à la validation d'URL ; validation stricte des noms de headers. | **Copier** |
| D3.7 | `our/mcp_client.py:335-370` | Le statut MCP servi à l'UI est rédigé, **et le texte d'erreur d'un serveur externe aussi**. | **Copier** |


#### E — Prime Agent · `resources/prime-agent-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| E3.6 | `refinery/store` | `HarnessEntry` / `RefinementEvent` en dataclass. À passer en Pydantic v2 — la structure est la bonne. | **Copier** |
| E3.6 | `refinery/store` | `load()` **défensif champ par champ** : type faux ⇒ défaut, `title`/`content` non-`str` ⇒ entrée sautée, fichier corrompu ⇒ état vide. **Un magasin écrit par un modèle doit se relire sans jamais lever.** | **Copier** |
| E3.6 | `refinery/store` | `_sync_from_disk` — relit si le `st_mtime_ns` a bougé. **Le kernel garde l'état en mémoire pendant que le host réécrit le même fichier** ; chez nous, dashboard, broker Git et mission concourent. | **Copier** |
| E3.6 | `refinery/store` | Une entrée `skill` **doit** porter un import et un callable. **Une capacité non appelable n'entre pas au registre.** | **Copier** |
| E3.6 | `refinery/store` | `_strip_scope_prefix` — accepte verbatim les ids affichés `local:`/`global:`. **Le modèle recopie ce qu'il a lu ; le harness le tolère au lieu de le refuser.** | **Copier** |
| E3.6 | `refinery/store` | `overview()` — rendu texte compact borné par famille, `args=`/`ref=` tronqués. C'est ce qui entre dans le prompt. | **Copier** |
| E3.6 | `refinery/propose` | `plan_refinement` — plan **déterministe en trois étapes, zéro appel modèle** : diagnostiquer / modifier la plus petite entrée utile / rejouer et enregistrer. | **Copier** |
| E3.6 | `refinery/store` | Mode `in_memory` comme **repli sûr quand la résolution de chemin échoue** : construire le repli ne peut pas relever l'erreur d'origine. | **Copier** |
| E3.6 | `ca/core/goals.ts:125-181` | **Le modèle voit son budget restant**, il ne le devine pas. Un objectif persistant se réinjecte par un message de contexte, pas par mutation du prompt. | **Traduire** |
| E3.6 | `ca/core/goals.ts:75-94` | Objectif borné à 4 000 caractères, budget entier positif. **Validation à l'entrée, pas à l'usage.** | **Traduire** |
| E3.6 | `rt/mcp.py:397-416,483-491` | **`reload(server)` — un outil vérifié devient appelable dans la mission en cours**, sans redémarrage. Décision 7 amendée. | **Copier** |
| E3.6 | `rt/mcp.py:261-294` | Découverte au runtime filtrée par `enabledTools`/`disabledTools` ; verrou d'appel par serveur, timeout, refus explicite si l'outil est inconnu ou désactivé. | **Copier** |
| E3.6 | `rt/mcp_base.py:307-333` | `_parse_result` — **point unique de désérialisation** d'un résultat MCP. Notre invariant `schema_conform` en a besoin. | **Copier** |
| E3.6 | `ca/core/kernel/bootstrap.ts:738-813` | Installation **par hash de `pyproject.toml`**, résolution des dépendances inter-skills, **ordre topologique**. | **Adapter** |
| E3.6 | `ca/core/kernel/bootstrap.ts:554-560,816-821` | Fichier de version dans le venv portant l'identité du runtime **et** la liste des skills installés. | **Adapter** |
| E3.6 | `ca/core/skills.ts:122-161` | **Nom d'outil = nom du répertoire parent**, `[a-z0-9-]`, ≤ 64 car. ; **description vide ⇒ outil non chargé**. | **Traduire** |
| E3.6 | `ca/core/skills.ts:202-255` | Détection à quatre conditions (`SKILL.md`, `pyproject.toml` racine, nom d'import valide, `src/<import>/__init__.py`). Une seule forme acceptée. | **Traduire** |
| E3.6 | `ca/core/skills.ts:443-475` | **Seules les métadonnées entrent au prompt de démarrage** ; le contrat complet est chargé à la demande. Divulgation progressive. | **Traduire** |
| E3.6 | `sk/skill-creator/references/python-skills.md` | **Le contrat complet d'un skill Python** : layout `src/`, `pyproject.toml` hatch, convention `run()`. Directement applicable au produit. | **Inspirer** |
| E3.6 | `rt/skill.py:14-37` | Pont skill Python → commande shell en 37 lignes, avec message d'erreur nommant la contrainte. | **Copier** |


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
| G3.5 | `src/manifests/manifest-registry.ts:19` | **Registry construit à partir d'entrées validées, sans découverte implicite.** Troisième source à le dire. | **Adapter** |
| G3.5 | `src/manifests/manifest-template.ts:21,65,76` | Lecture de valeur imbriquée **par chemin fermé** ; interpolation **conservant le type** quand le placeholder occupe tout le champ ; **interpolation textuelle sans évaluation d'expression**. | **Adapter** |
| G3.5 | `src/manifests/manifest-bundle.ts:29` | Fichiers d'un bundle résolus **par identifiant contrôlé**. | **Adapter** |
| G3.5 | `src/manifests/manifest-bundle.ts:68` | Empaquetage **après calcul des chemins exécutables autorisés**. | **Adapter** |
| G3.5 | `src/manifests/automation-setup.ts:44,86` | Endpoints construits **depuis le manifest**, jamais par concaténation dispersée ; existence **vérifiée avant création**. | **Adapter** |
| G3.5 | `src/manifests/automation-setup.ts:353` | **Corps de preflight séparé de la création effective.** | **Adapter** |
| G3.5 | `src/manifests/automation-setup.ts:403` | **Carte d'erreurs par champ** pour corriger une proposition **sans rejouer tout le cycle**. | **Adapter** |
| G3.5 | `src/manifests/automation-insights.ts:144` | Santé dérivée de **prédicats de statut fermés**. | **Adapter** |
| G3.5 | `src/manifests/automation-insights.ts:236,337` | Filtres et tris comme **fonctions pures** ; tuiles calculées depuis des résumés déjà chargés. | **Adapter** |


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
| I4.6 | `web/src/features/mcp/core/define-tool.ts:112` | **Définition d'outil et validation runtime au même endroit** ; Pydantic reste la source unique, l'accord schéma/handler est testé. | **Adapter** |
| I4.6 | LF046 | Profil de schéma MCP **explicitement restreint** — rejette unions et intersections, exige un objet. Choix de serveur, pas interdiction du protocole. | **Adapter** |
| I4.6 | `web/src/features/mcp/server/registry.ts:82` | **Registre explicite, collisions détectées avant publication**, y compris à l'intérieur d'un même lot. | **Adapter** |
| I4.6 | LF048 | **La gate de disponibilité s'applique à l'appel direct**, pas seulement à la découverte. Masquer n'est pas interdire. | **Adapter** |
| I4.6 | LF049 | Permission de lecture ou allowlist — **ne pas faire confiance à un `readOnlyHint` fourni par du code généré**. | **Adapter** |
| I4.6 | `web/src/features/mcp/core/run-mcp-tool.ts:13` | Instrumentation par outil et **classe de faute** : requête invalide distincte de panne serveur. | **Adapter** |
| I4.6 | `packages/shared/src/server/repositories/dataset-items.ts:285` | **Valider l'état fusionné après un update partiel** ; distinguer champ absent et `null` explicite. | **Adapter** |
| I4.6 | LF052 | **Lecture à version temporelle figée** — comparer deux configurations sur le même corpus. | **Adapter** |
| I4.6 | `worker/src/features/experiments/experimentServiceClickhouse.ts:73` | Identité d'item et tentative **reliées au run**, items existants retrouvés au redémarrage. | **Adapter** |
| I4.6 | `worker/src/features/experiments/scheduleExperimentEvals.ts:37` | **Planification best-effort** : l'erreur est loggée sans invalider l'appelant. À écarter pour une gate de livraison. | **Adapter** |
| I4.6 | `web/src/features/prompts/server/actions/createPrompt.ts:93` | **Version créée avec ses dépendances, publiées ensemble.** | **Adapter** |
| I4.6 | LF056 | **Label mobile séparé d'une version immuable** — notre paire `shadow`/`active`, où seul le déplacement du label passe la gate. | **Adapter** |
| I4.6 | `packages/shared/src/server/services/PromptService/index.ts:242` | Graphe de dépendances **borné en cycles et profondeur** ; tracer **les versions réellement résolues**, pas le nom de la racine. | **Adapter** |
| I4.6 | LF058 | Génération de cache invalidant un ensemble **sans supprimer toutes les clés** ; résolution des créations concurrentes par « premier gagnant ». | **Adapter** |
| I4.6 | LF059 | **Clé de cache distinguant label et version** — sinon la version `2` et le label `"2"` collisionnent. Décision 22 appliquée au cache. | **Adapter** |
| I4.6 | LF060 | **Un échec secondaire après commit ne doit pas faire croire à un échec de la création durable** — ni provoquer un doublon. | **Adapter** |
| I4.6 | `worker/src/features/evaluation/deterministicSampling.ts:6` | **Cohorte déterministe par hash** : SHA-256, 53 premiers bits, seuil demi-ouvert. Une cible garde sa cohorte. | **Adapter** |
| I4.6 | `web/src/features/score-analytics/server/buildScoreComparisonQuery.ts:50` | Comparer candidat et base **sur les mêmes missions, corpus et versions**, en affichant appariés, manquants et dénominateur. | **Adapter** |
| I4.6 | LF093-098 | Vecteur de référence de hash, **cohortes emboîtées quand le taux augmente**, export multichunk **décompressé à l'octet près**, champ nommé `anyOf` restant légal comme donnée, résistance aux IDs dupliqués, **enfant asynchrone terminant après son parent**. | **Adapter** |


---

## Sources — reprises écartées ou reportées

**3 lignes. N'implémente aucune de ces lignes.** Le pointeur reste pour qu'un retournement de décision retrouve la source. Si tu penses qu'une raison est fausse, **écris-le dans `STATE.md`, n'implémente pas.**

#### A — Villani Code · `resources/villani-code-main/`

| § | Source | Notion | Statut |
|---|---|---|---|
| A4.6 | `autonomy.py:423-432` | `_RANK_ORDER` — ordre de priorité **écrit en dur, par titre**. Assumé, lisible, débogable. | **Écarté** |
| A4.6 | `autonomy.py:403-411` | `TakeoverConfig` — `max_waves=3`, `max_total_task_attempts=6`, `min_confidence=0.60`, `stagnation_cycle_limit=2`. | **Écarté** |
| A4.6 | `autonomous_helpers.py:29-41` | `effective_priority` — `priority*0.7 + confidence*0.3`. Formule visible, ajustable. | **Écarté** |

