# `engine` — l'arbre, le contexte, le budget

> **Lis [`AGENTS.md`](../../AGENTS.md) avant de commencer.** Ce fichier est ton contrat complet : tu ne
> devrais pas avoir besoin d'ouvrir `docs/`. Ton point d'entrée exact est la rubrique « Prochaine action » de
> [`STATE.md`](STATE.md), à côté de ce fichier.
>
> **Tu ne commites, ne pousses et ne merges jamais.** Tes commits se *proposent* dans [`git.md`](git.md),
> avec les `ga`/`gcmsg` exacts — voir [`AGENTS.md`](../../AGENTS.md) § 7.

**Cible** : ~1 050 L · **le plus gros module du projet** · ratchet **shrink-only**
**Dépend de** : `kernel`, `journal`, `verifier`, `bridge`, `workspace`.
**Niveau de dépendance** : 3.
**Stack** : Prefect 3 **en enveloppe stricte** · `time.monotonic()` · Pydantic v2.

## 1. Autorité

`engine` possède **l'arbre de travail, le contexte de chaque nœud, et le budget mural**. C'est lui qui
décide de scinder, d'exécuter ou de bloquer.

**La question qu'il pose est unique :** *ce nœud porte-t-il un critère exécutable ?* Si oui il exécute ; si
non il scinde (plafond de profondeur **3**, plafond de largeur **`cap_children`**) ou il bloque avec une
cause mécanique.

## 2. Interface publique

```python
# walk.py — marcheur PUR, testable au pytest nu, sans Prefect
def walk(tree: Tree, budget: Budget, deps: Deps) -> None: ...

# flow.py — l'adaptateur Prefect, mince
@flow(name="mission", timeout_seconds=BUDGET_HARD)
def mission(config: MissionConfig) -> None:
    tree = load_or_create(config)
    try:
        walk(tree, Budget(BUDGET_SOFT), deps)
    finally:
        finalize_green_nodes(tree)

# context.py
def assemble(node: Node, budget: int) -> ContextPacket:
    "Inventaire typé : raison d'inclusion OU d'exclusion par élément, pression, évictions."
def dump(mission_id: str, packet: ContextPacket, verdict: Verdict) -> None:
    "Ajoute une section à CONTEXT.md. Écrit par le harness, jamais par le modèle."

# classify.py — porté de Villani, déterministe, ZÉRO appel modèle
def analyze_instruction(text: str, index: RepoIndex) -> Analysis: ...
```

## 3. Interdits

- **Prefect ne possède rien d'autre que le cycle de vie des tâches.** Table d'autorité :

| Autorité | Détenue par | Pourquoi |
|---|---|---|
| État du domaine | `tree.json` | lisible, servi au dashboard, reprenable hors Prefect |
| Preuve | JSONL + `live.log` | évidence primaire, indépendante de tout framework |
| Sémantique de retry | `engine` | re-demander vs bloquer vs sauter un frère : c'est métier |
| Budget mural | `engine`, `time.monotonic()` | il faut **finaliser ce qui est vert**, pas se faire tuer |
| Frontière transactionnelle | `workspace` | snapshot fichiers, pas état de tâche |

- **Le budget ne passe pas par `timeout_seconds`.** La décision 8 exige qu'à expiration la mission finalise
  ses nœuds verts et sorte proprement ; une annulation ne le garantit pas. Vérification `monotonic()` dans la
  boucle, `timeout_seconds` réglé nettement au-dessus **en kill de dernier recours**.
- **`walk.py` reste testable au pytest nu.** Sans cette séparation, chaque test d'engine traînerait un
  harnais Prefect — or c'est le module qu'on itère le plus.
- **Ne résume jamais.** Voir § 5.

## 4. Le classifieur déterministe

`analyze_instruction` et ses cinq enums fermées — `PlanRiskLevel`, `ActionClass` (13 valeurs),
`EstimatedScope`, `ChangeImpact`, `TaskMode` — dérivent du repo les cibles candidates, la classe d'action, la
portée et l'impact, **avec zéro appel modèle**.

> **Sa place ici n'est pas d'évaluer un risque, mais de dériver les enfants d'un nœud sans appeler le
> modèle.** Une décomposition déterministe est strictement plus alignée sur la contrainte dure n°1 que de
> demander au modèle de scinder.

**Condition pour que ce ne soit pas du code mort** : les enums doivent être **lues**, pas seulement
déclarées. Elles apparaissent aussi dans la trace, pour qu'une campagne s'analyse a posteriori. Si tu portes
le classifieur sans le brancher sur la décomposition, consigne-le comme un blocage.

## 5. Le contexte — évincer, jamais résumer

**Chaque nœud reçoit une session neuve.** Il n'y a aucune conversation à compacter. Et il y a une raison plus
forte que l'inapplicabilité :

⚠️ **Un résumé est du texte produit par le modèle qui entre dans le prompt suivant** !
→ C'est exactement la dérive qui a produit les 12 419 `thinking_delta` de v1.

**Dans la session** : sous pression on **évince**, avec la raison enregistrée. Si le contenu irréductible
dépasse le budget, le nœud est **`blocked` avec cause mécanique**. Un nœud bloqué est un signal exploitable ;
un résumé approximatif est une dette invisible.

**À la fin de la session** : un artefact de passation.

```text
~/logs/pithos2/missions/<mission_id>/CONTEXT.md
```

Un fichier par mission, **une section ajoutée à chaque fin de session** — nœud, critère, inclusions et
exclusions avec leur raison, palier de pression, évictions, verdict, et **l'empreinte des fichiers décrits au
moment de l'écriture**. Écrit par le harness : l'inventaire typé existe déjà, le rendre en markdown est
déterministe, ~30 L.

**L'empreinte n'est pas décorative.** Le mode d'échec n°2 mesuré de v1 était un brief décrivant une fonction
**déjà mergée**. **Un fichier de suivi réinjecté a exactement cette forme.** Il est donc traité comme
n'importe quel élément de contexte — sélectionné sous budget, avec une raison d'inclusion, soumis à
`detect_stale_context` — et une section dont l'empreinte a bougé est **exclue avec sa raison**, jamais
injectée en silence.

## 6. Le budget

Au socle : **un deadline monotone unique**, propagé à toutes les sous-opérations, et une **réserve de
finalisation en constante** au-delà de laquelle on n'ouvre plus de nœud mais on finalise les verts. ~30 L.

Le **seam transport/logique** est conservé : un timeout HTTP n'est pas un jalon logique.

**EWMA, latch d'ancre et `CostCeiling` sont `Reporté`** — ils se calibrent sur des durées observées, et il
n'y en a aucune. Ils arrivent après les dix premières missions, quand `PROJECT.md` fixera la valeur de la
borne.

## 7. Contenu

| Fichier | Contenu | ~L |
|---|---|---:|
| `walk.py` | marcheur pur : prédicat de vérifiabilité, scission, blocage, retry | 250 |
| `classify.py` | `analyze_instruction` + les cinq enums fermées, porté de Villani | 200 |
| `context.py` | inventaire typé, paliers de pression, éviction, `detect_stale_context` | 250 |
| `select.py` | `relevant_files`, `impact_files`, fermeture d'imports, **chaque fichier avec sa raison** | 200 |
| `budget.py` | deadline monotone, réserve de finalisation, seam transport/logique | 60 |
| `flow.py` | l'adaptateur Prefect, mince | 40 |
| `dump.py` | `CONTEXT.md`, une section par session | 40 |

## 8. Critères de socle que ce module rend verts

- **Un nœud sans critère exécutable est toujours scindé ou bloqué, jamais exécuté.**
- **Une mission qui atteint sa borne murale finalise ses nœuds verts et reste reprenable.**
- **Le contexte de chaque nœud est un inventaire typé** : raison d'inclusion ou d'exclusion par élément,
  pression mesurée, évictions comptées, dérive détectée.
- **Une reprise distingue non commencé / effet inconnu / résultat enregistré** et n'exécute jamais un effet
  externe deux fois sans interrogation préalable.
- **La famille `memory` est alimentée dès le socle** — `engine` écrit les nœuds `blocked` avec leur cause.
- **`engine` écrit à chaque fin de mission le triplet de baseline** : nœuds verts / nœuds tentés, temps
  mural consommé, cause de sortie. ~5 L, sans lesquels la gate d'effet de `refinery` n'aura rien à comparer.

## 9. Le double

`tests/doubles/engine.py` — utile surtout à `campaign` et `observatory`. Il expose un arbre figé et un
marcheur qui rejoue une séquence de verdicts fournie au constructeur.

**Mais l'essentiel du travail de test d'`engine` est l'inverse** : `walk` se teste contre les doubles de
`verifier`, `bridge`, `workspace` et `journal`. **Aucun test de `walk` ne doit lancer un subprocess ni
appeler Ollama.**

## 10. Fini quand

- [ ] Un nœud sans critère exécutable n'est **jamais** exécuté — test exhaustif sur les états.
- [ ] Le plafond de profondeur **3** et le plafond de largeur `cap_children` sont tous deux appliqués.
- [ ] À l'expiration de la borne souple, la mission **finalise ses nœuds verts** et l'arbre reste
      reprenable — test par deadline artificiellement court.
- [ ] `walk` passe entièrement **sans Prefect installé** — test au pytest nu.
- [ ] Le contexte rend un inventaire typé où **chaque élément** porte une raison d'inclusion **ou**
      d'exclusion — aucun élément sans raison.
- [ ] Sous pression, l'éviction est FIFO et **chaque éviction est enregistrée** avec sa raison.
- [ ] Un contenu irréductible dépassant le budget produit un `blocked` avec cause, **jamais un résumé**.
- [ ] `detect_stale_context` détecte une section de `CONTEXT.md` dont l'empreinte a bougé et l'**exclut avec
      sa raison** — test qui rejoue l'incident du brief périmé de v1.
- [ ] Le triplet de baseline est écrit à chaque fin de mission.
- [ ] Un parent enregistre `child_result_disposition` **par enfant**.
- [ ] `tests/boundaries/` confirme que `engine` n'est importé par aucun module de niveau ≤ 2.

## 11. Pièges connus, et ce qui a été écarté

| Écarté | Pourquoi |
|---|---|
| **`ExecutionBudget` et `VILLANI_TASK_BUDGET`** | des bornes **de tours** — 20 tours, 40 tool calls, 8 outils, `max_no_edit_turns` — alors que le mode `direct` fait **un appel par nœud** |
| **Toute la compaction** (~150 L) | session neuve par nœud : aucune conversation à compacter, et un résumé serait du texte du modèle entrant dans le prompt suivant |
| **Le ledger d'arbre parallèle** (~120 L) | `tree.json` est l'état du domaine (décision 11). Curseurs, pagination à hash de snapshot, `halt_fanout` supposent un système multi-agent délégant |

**Gardés** : `InterruptController` (premier signal interrompt, second quitte — 18 L, et c'est par là que
`/pause` et `/stop` de Telegram atteignent le marcheur), `RepairContext` comme payload borné en champs typés
pour le retry (sans la boucle de réparation qui l'entoure), `child_result_disposition` et `cap_children`.

---

## Sources — reprises retenues

**133 lignes.** Chaque pointeur se lit dans `resources/`. Le détail complet et le contexte de chaque partie sont dans [`resources/IMPORT_REPORT.md`](../../resources/IMPORT_REPORT.md).
**Lis la source avant de porter.** Une reprise collée sans être relue est un défaut.

#### A — Villani Code · `resources/villani-code-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| A4.5 | `planning.py:215-316` | `analyze_instruction` — **classification entièrement déterministe** : cibles candidates, classes d'action, portée, impact, confiance, `rationale`. Zéro appel modèle. Preuve qu'une grande part de ce qu'on croit devoir demander au modèle se dérive du repo. | **Copier** |
| A4.5 | `planning.py:11-57` | Cinq enums fermées : `PlanRiskLevel`, `ActionClass` (13 valeurs), `EstimatedScope`, `ChangeImpact`, `TaskMode`. | **Copier** |
| A4.5 | `planning.py:319-332` | `classify_plan_risk` — risque dérivé des classes d'action et de la portée, jamais demandé au modèle. | **Copier** |
| A4.5 | `planning.py:388-400` + `validation_loop.py:219-247` | `classify_task_mode`, puis **le mode détermine quelles gates tournent**. | **Adapter** |
| A4.5 | `planning.py:99-142` | `ExecutionPlan.to_human_text` — rendu texte compact réinjectable. Un plan qui ne se rend pas en texte ne sert pas au modèle suivant. | **Inspirer** |
| A4.5 | `context_governance.py:11-31` | `ContextInclusionReason` / `ContextExclusionReason` / `ContextPressureLevel` — **chaque élément porte la raison de sa présence ou de son absence.** | **Copier** |
| A4.5 | `context_governance.py:34-71` | `ContextItem` (avec `pressure_share`) / `ContextBudgetEstimate` / `ContextInventory`. | **Copier** |
| A4.5 | `context_governance.py:252-266` | `_recompute_budget` — quatre paliers de pression (`low` < 0,45 < `moderate` < 0,75 < `high` < 1,0 < `overflow_risk`). Vital avec Ling plafonné à 16k. | **Copier** |
| A4.5 | `context_governance.py:200-208` | `prune_for_budget` — éviction FIFO sous pression, chaque éviction enregistrée avec sa raison et comptée. | **Copier** |
| A4.5 | `context_governance.py:210-220` | `detect_stale_context` — signaux nommés, dont **réparations répétées avec contexte gonflé**. Le capteur qui aurait attrapé les 12 419 `thinking_delta`. | **Copier** |
| A4.5 | `context_governance.py:83-122` | `ContextCompactor` — un compacteur par type de source, chacun avec ses tokens de signal. | **Copier** |
| A4.5 | `context_projection.py:9-20` | `_filter_model_facing_paths` — les chemins d'artefacts runtime ne sont **jamais** montrés au modèle. | **Copier** |
| A4.5 | `context_projection.py:23-70` | Paquet **structuré** puis rendu texte séparé. Le paquet est traçable, le rendu jetable. | **Copier** |
| A4.5 | `execution.py:15-34` | `ExecutionResult` transporte `intended_targets` **et** `before_contents` — le vérificateur reçoit l'intention et l'état antérieur. | **Copier** |
| A4.5 | `repair.py:61-106` | `execute_repair_loop` — réparation ciblée sur **la seule étape en échec**, puis élargissement. Historique de tentatives réinjecté. | **Copier** |
| A4.5 | `repair.py:11-19` | `RepairContext` — payload en champs bornés, sérialisé en JSON. Le prompt de repair est une structure, pas de la prose. | **Copier** |
| A4.5 | `interrupts.py:7-18` | `InterruptController` — premier signal interrompt, second quitte. Dix-huit lignes. | **Copier** |
| A4.5 | `subagent_runtime.py:19-27` | `build_role_launch_request` — quatre rôles avec **allowlist d'outils, droit d'écriture et exigence de preuve** explicites. `fresh_verifier` n'hérite pas de l'état : il vérifie sans être contaminé. | **Copier** |
| A4.5 | `subagent_runtime.py:30-40` | `render_subagent_brief` — huit lignes fixes, dont `Known facts` et **`Ruled out`**. Transmettre ce qui a été écarté évite de le réexplorer. | **Copier** |
| A4.5 | `subagents.py:22-27` | Sous-agents définis par leurs **interdits** plutôt que par leurs permissions. | **Inspirer** |
| A4.5 | `summarizer.py:9-55` | Résumés de phase déterministes, jamais générés. | **Copier** |


#### B — Pi · `resources/pi-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| B3.5 | `packages/agent/src/harness/runtime/drive.ts:29` | Dispatch explicite par état durable. Reprendre la lisibilité des transitions, éviter le runtime complet de lanes/compaction/inbox. | **Adapter** |
| B3.5 | `packages/agent/src/harness/runtime/drive/generation.ts:132` | **Persister l'intention avant l'effet externe.** Pilier de la décision 16. | **Adapter** |
| B3.5 | `packages/agent/src/harness/runtime/restore.ts:131` | Restaurer et vérifier la cohérence avant tout effet. Un état contradictoire est **bloqué avec cause**, pas corrigé en relançant le modèle. | **Adapter** |
| B3.5 | `packages/agent/src/harness/runtime/drive/recovery.ts:44` | Reprise d'un appel orphelin depuis les preuves. Une sortie partielle n'est pas appliquée. **Usage inconnu plutôt que le zéro synthétique de Pi.** | **Adapter** |
| B3.5 | `packages/agent/src/harness/execution/effect-gate.ts:31` | Fermer l'admission de nouveaux effets **avant** de propager l'annulation. | **Adapter** |
| B3.5 | `packages/agent/src/harness/runtime/drive/reconcile.ts:132` | Chemin de réconciliation distinct du chemin nominal. | **Adapter** |
| B3.5 | `packages/agent/src/harness/runtime/drive/terminal.ts:26` | Finalisation terminale commune, résultat immuable. | **Adapter** |
| B3.5 | `packages/ai/src/utils/retry.ts:224` | **Classification des erreurs indépendante de la politique de retry.** Ce qui est retryable est une propriété de l'erreur, pas du contexte d'appel. | **Adapter** |
| B3.5 | `packages/ai/src/utils/retry.ts:163` | Retries bornés, observables et annulables. | **Adapter** |
| B3.5 | `packages/agent/src/agent-loop.ts:177` | Réassembler le contexte **depuis l'état courant**, jamais depuis un brief figé. Convergence exacte avec la décision 14. | **Adapter** |
| B3.5 | `packages/agent/src/harness/compaction/utils.ts:91` | Feedback compact avec sortie brute accessible par référence. | **Adapter** |
| B3.5 | `packages/coding-agent/src/core/resource-loader.ts:119` | Provenance et priorité **déterministes** des fichiers d'instructions. | **Adapter** |
| B3.5 | `packages/agent/src/harness/runtime/drive/retry.ts:6` | Reprise d'un délai de retry déjà programmé après redémarrage. | **Adapter** |
| B3.5 | `packages/agent/src/harness/compaction/utils.ts:54` | Distinguer fichiers lus et fichiers modifiés dans le contexte. | **Adapter** |
| B3.5 | `packages/agent/src/agent-loop.ts:487` | Préflight des appels avant exécution, ordre stable des résultats. | **Adapter** |
| B3.5 | `packages/agent/src/agent-loop.ts:379` | **Un tool call tronqué ne doit jamais être exécuté.** | **Adapter** |
| B3.5 | `packages/agent/src/agent.ts:125` | Steering et follow-up comme files distinctes. | **Adapter** |
| B3.5 | `packages/agent/src/harness/compaction/compaction.ts:311` | Compaction préservant les frontières conversationnelles. | **Adapter** |
| B3.5 | `packages/agent/src/harness/hooks.ts:15` | Contrats de hooks et traitement différencié des erreurs. | **Adapter** |


#### C — Kilo Code · `resources/kilocode-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| C3.5 | `opencode/src/session/compaction.ts:269-324` | Compaction avec **frontières de tour préservées** et résumé inséré, jamais une troncature au milieu. | **Traduire** |
| C3.5 | `opencode/src/session/compaction.ts:207-264,123-146` | `select()` + `splitTurn()` — **la queue conservée est choisie par unités atomiques**, pas par nombre de messages. | **Traduire** |
| C3.5 | `opencode/src/session/compaction.ts:43,97-102,304-305` | Seuils de déclenchement nommés et budget réservé au résumé. | **Traduire** |
| C3.5 | `opencode/src/session/compaction.ts:78-94,348-390,490-500` | Marquage des messages compactés, idempotence de la compaction, garde contre la double compaction. | **Traduire** |
| C3.5 | `kilo-memory/src/recall/recall.ts:141-238` | Rappel de mémoire par pertinence avec budget, et **traçabilité de ce qui a été rappelé et pourquoi**. | **Adapter** |
| C3.5 | `core/src/instruction-context.ts:30-72` | Assemblage des instructions par provenance et précédence déterministes. | **Traduire** |
| C3.5 | `opencode/src/session/run-state.ts:56-73,139-168` | État de run explicite avec transitions nommées et persistance. | **Traduire** |
| C3.5 | `opencode/src/agent/agent.ts:168-329` | Définition d'agent : outils autorisés, modèle, prompt, budget — **par déclaration, pas par code**. | **Adapter** |
| C3.5 | `opencode/src/agent/agent.ts:445-459,515-521` | Résolution de l'agent effectif et héritage de configuration. | **Adapter** |
| C3.5 | `opencode/src/tool/task.ts:36-95` | Délégation à une sous-tâche avec budget propre et résultat structuré. | **Adapter** |
| C3.5 | `opencode/src/question/index.ts:28-32,90-124` | Question à l'opérateur comme **objet persistant avec cycle de vie**, pas comme un prompt bloquant. Modèle pour la proposition d'arrêt. | **Traduire** |


#### D — Ouroboros · `resources/ouroboros-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| D3.6 | `our/task_tree_ledger.py:34-48,170-302` | **Ledger d'arbre append-only par racine**, kinds fermés, `needs_parent_attention` **dérivé du kind et non déclaré**. Un append non écrit renvoie un échec typé. | **Copier** |
| D3.6 | `our/task_tree_ledger.py:618-655` | Curseur `(ts, ids vus)` : le parent avance un curseur au lieu de relire l'historique. Les timestamps égaux sont admis une fois. | **Copier** |
| D3.6 | `our/task_tree_ledger.py:108-168,393-433` | `child_result_disposition` — le parent enregistre par enfant `integrated` / `irrelevant` / `deferred`, **lié au SHA-256 du résultat**. Un résultat qui change périme la disposition. | **Copier** |
| D3.6 | `our/task_tree_ledger.py:580-617` | Pagination portant un **hash de snapshot**, et déclaration explicite quand le ledger a bougé pendant la capture. | **Copier** |
| D3.6 | `our/task_tree_ledger.py:384-391` | Identité de contenu stable d'une ligne (JSON canonique trié + SHA-256), partagée par tous les curseurs. | **Copier** |
| D3.6 | `our/task_tree_ledger.py:49,656-705` | `delegation_constraint` à directives fermées (`halt_fanout`, `cap_children`, `require_lane`, `block_surface`). | **Adapter** |
| D3.6 | `our/task_tree_ledger.py:59-61` | Bornes explicites : 4 000 caractères par entrée, **2 Mo par ledger**. Un ledger plein refuse **avec le message qui dit quoi faire**. | **Copier** |
| D3.6 | `our/task_pacing.py:199-224` | **Deux réserves distinctes** : fenêtre d'émission et réserve en pourcentage. Les confondre a amputé 54 min d'une tâche de 6 h. | **Copier** |
| D3.6 | `our/task_pacing.py:87-110` | `has_deadline=False` **désactive l'axe temps entièrement** plutôt que de simuler un infini. `spendable_sec` = le temps au-dessus de la réserve. | **Copier** |
| D3.6 | `our/task_pacing.py:260-279` | Une gate coûteuse ne démarre que si elle **tient au-dessus de la réserve**, avec une raison typée. | **Copier** |
| D3.6 | `our/task_pacing.py:398-422` | Quand le chiffre faisant autorité est indisponible, la substitution est **divulguée**, jamais silencieuse. | **Copier** |
| D3.6 | `our/deadline_utils.py:1-328` | Seam **transport contre logique** : le timeout d'un outil réseau et le jalon logique de la boucle ne sont pas la même horloge. | **Copier** |
| D3.6 | `our/context_layout.py:69-136` | `generate_doc_nav_map` — carte de navigation H2–H4 à sous-arbres complets : représentation **sans perte** d'un document trop gros, jamais un `[:N]`. | **Adapter** |
| D3.6 | `our/context_budget.py:171-254` | Table de seuils **par store** — un nouveau store append-only doit s'y enrôler dans le même commit. | **Copier** |
| D3.6 | `od/DEVELOPMENT.md:914-985` | **Aucune troncature silencieuse** : marqueur visible, plancher anti-gaspillage, borner une liste = borner une chaîne. La troncature protège le contexte du modèle, **jamais la lecture de l'humain**. | **Inspirer** |
| D3.6 | `od/DEVELOPMENT.md:970-985` | **Pas de gate « seulement si touché »** pour les artefacts de gouvernance : ils entrent inconditionnellement dans les flux de raisonnement. | **Inspirer** |
| D3.6 | `our/outcomes.py:503-568` | `reviewable_effect_projection` — modèle d'**exclusion** (seul le scratch est exempt), pas d'énumération des roots livrables : la gate reste complète quand les roots évoluent. | **Copier** |
| D3.6 | `sup/terminal_delivery.py:255-270,336-395` | Retour **typé** : `True` = durablement suivi, `False` = trou de durabilité réel. La lecture d'application **déclare ses propres lignes illisibles** au lieu de les compter comme absentes. | **Copier** |


#### E — Prime Agent · `resources/prime-agent-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| E3.5 | `ag/agent-loop.ts:304-450` | **Points d'extension nommés dans la boucle** (`shouldStopAfterTurn`, `getSteeringMessages`, `getFollowUpMessages`, `getContinuationMessages`) : une boucle, plusieurs politiques. | **Adapter** |
| E3.5 | `ag/agent-loop.ts:404-410` | *« Steering drained by this poll owns the turn boundary; stop only when it was empty. »* **Une interruption arrivée au moment de l'arrêt gagne contre l'arrêt.** Précédence explicite. | **Traduire** |
| E3.5 | `ca/core/autonomous.ts:45-46` | Prompt de continuation pour un contexte sans humain : *« If you believe you are blocked, prove it with host-observable evidence. »* | **Inspirer** |
| E3.5 | `ca/core/autonomous.ts:48-61` | `DEFAULT_AUTONOMOUS_LIMITS` — 3 continuations / 12 tours / 80 000 tokens / 30 min ; gates 3 retries / 5 min. Point de départ chiffré. | **Inspirer** |
| E3.5 | `ca/core/autonomous.ts:227-252` | **Les gates sont interrogées avant les limites.** Une gate verte arrête proprement même s'il reste du budget ; une gate rouge sur budget épuisé est nommée comme telle. | **Traduire** |
| E3.5 | `ca/core/autonomous.ts:135-155` | Activer l'autonomie **remet à zéro tous les compteurs et efface le dernier échec de gate**. Un redémarrage ne traîne pas l'état de la session précédente. | **Traduire** |
| E3.5 | `ca/core/compaction/compaction.ts:375-425` | `findCutPoint` — marche arrière en accumulant les tokens, coupe au **premier point valide** au-delà du seuil, jamais sur un résultat d'outil. | **Adapter** |
| E3.5 | `context` | Une coupe **au milieu d'un tour** est nommée comme telle et déclenche un résumé de préfixe. | **Traduire** |
| E3.5 | `context` | **Usage réel du dernier message assistant + estimation des messages postérieurs seulement.** On n'estime que ce qu'on ne peut pas mesurer. | **Traduire** |
| E3.5 | `context` | L'output compte dans le contexte du tour suivant. Erreur classique, corrigée nommément. | **Traduire** |
| E3.5 | `context` | Format de résumé **imposé section par section** : `Goal` / `Constraints & Preferences` / `Progress`. | **Adapter** |
| E3.5 | `context` | **Mettre à jour** un résumé existant plutôt que le régénérer. | **Adapter** |
| E3.5 | `context` | Quand un état hors-contexte survit à la compaction, le résumé doit **le dire au modèle**, sinon il redéfinit ce qu'il a déjà. | **Traduire** |
| E3.5 | `ca/core/compaction/utils.ts:24-71` | La liste des fichiers lus et modifiés est **extraite déterministement** et réinjectée. Zéro appel modèle. | **Adapter** |
| E3.5 | `rt/repl.py:607-660` | `_snapshot_state` — sérialisation **par variable, indépendamment** : un objet non sérialisable est sauté **et rapporté**, au lieu d'abandonner tout le snapshot. | **Copier** |
| E3.5 | `ca/core/kernel/state-snapshot.ts:19-37` | `SnapshotResult` / `RestoreResult` — `saved`, `skipped[{name, reason}]`, `pruned`, `bytes`. **La restauration rapporte ce qu'elle n'a pas pu revivre.** | **Adapter** |
| E3.5 | `ca/core/side-question.ts:25,42-70` | Poser une question **sans polluer la conversation courante** : contexte recloné, outils interdits par le prompt **et** par le code. | **Inspirer** |


#### F — Unsloth · `resources/unsloth-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| F3.5 | `unsloth/dataprep/synthetic.py:172` | **Un seul deadline de mission propagé à toutes les sous-opérations**, plutôt que des timeouts indépendants qui s'additionnent. | **Adapter** |
| F3.5 | `unsloth/dataprep/synthetic.py:177` | Encapsuler l'état d'un service dans un kit avec **`cleanup` garanti par contexte**. | **Adapter** |
| F3.5 | `unsloth_cli/_inference.py:310` | **Collecter un stream sans perdre le texte déjà reçu** quand la connexion se ferme prématurément. | **Adapter** |
| F3.5 | `unsloth_cli/_inference.py:351` | Backend abstrait minimal (`stream`, `close`) pour brancher Ollama ou un serveur local. | **Adapter** |
| F3.5 | `unsloth_cli/_inference.py:426,508` | **Séparer choix du backend et chargement effectif** ; chaque étape observable ; token optionnel séparé de la configuration. | **Adapter** |
| F3.5 | `unsloth/models/loader_utils.py:102,443` | Device map déterministe ; **nom canonique résolu séparément du chargement**, pour journaliser la cible. | **Adapter** |
| F3.5 | `unsloth/utils/packing.py:719` | **Masquer les labels aux frontières de séquences** pour empêcher une validation de traverser deux exemples. Analogue direct : un invariant ne doit pas déborder sur le nœud voisin. | **Adapter** |
| F3.5 | `unsloth/utils/packing.py:165,572` | Activer une optimisation **seulement si le verifier l'autorise** ; conserver les métadonnées reliant une sortie à son entrée. | **Adapter** |
| F3.5 | `unsloth_cli/commands/start.py:900` | **Affichage de progression borné et séparé du journal durable.** Ne pas confondre UI et preuve. | **Adapter** |
| F3.5 | `unsloth_cli/commands/start.py:1157` | Shutdown d'un serveur subprocess **centralisé et idempotent**. | **Adapter** |
| F3.5 | `unsloth_cli/commands/start.py:1088,1755,1880` | Chargement asynchrone avec fermeture contrôlée si la mission expire ; **comparer les settings avant réutilisation**, sinon forcer un rechargement. | **Adapter** |


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
| H4.5 | `sweagent/agent/agents.py:224,242` | Classe abstraite avec **lifecycle commun et état explicite** ; **fabrique déterminée par configuration, sans introspection du modèle**. | **Adapter** |
| H4.5 | `sweagent/agent/agents.py:257` | Retry **séparé du comportement nominal**. | **Adapter** |
| H4.5 | `sweagent/run/run_single.py:55,125` | Contrat d'une **action unique** — mappe directement sur une nano-étape ; runner séparant config, environnement, agent et sauvegarde. | **Adapter** |
| H4.5 | `sweagent/run/run_single.py:210` | **Point d'entrée CLI qui ne contient pas la logique métier.** | **Adapter** |
| H4.5 | `sweagent/run/run_batch.py:75` | Configuration batch Pydantic à options **déclaratives**. | **Adapter** |
| H4.5 | `sweagent/run/run_batch.py:137,427` | Boucle **interrompable avec exception de break dédiée** ; exécution depuis une configuration **déjà validée**. | **Adapter** |
| H4.5 | `sweagent/run/run_replay.py:46,66` | **Configuration de replay indépendante du runner original** ; **rejouer une trajectoire sans rappeler le modèle** pour les étapes enregistrées. Directement notre besoin de rejeu de campagne. | **Adapter** |
| H4.5 | `sweagent/run/run_shell.py:40` | Runner shell minimal pour **diagnostiquer l'environnement hors agent**. | **Adapter** |
| H4.5 | `sweagent/run/common.py:370` | Sauvegarde des prédictions **append-safe**, par instance et trajectoire. | **Adapter** |
| H4.5 | `sweagent/run/_progress.py:25,33` | Libellés de progression tronqués **sans ralentir l'exécution** ; gestionnaire **séparé des traces de preuve**. | **Adapter** |
| H4.5 | `sweagent/utils/patch_formatter.py:28-49` *(hors extraction)* | **`_merge_intervals` — fusion des plages chevauchantes avant projection.** Sans elle, deux hunks voisins projettent trois fois le même bloc. | **Adapter** |
| H4.5 | `sweagent/utils/patch_formatter.py:98,147` *(hors extraction)* | `_get_hunk_lines(context_length)` et `get_files_str(context_length, linenos)` — **projection bornée autour d'un diff, paramètres explicites**. | **Adapter** |


#### I — Langfuse · `resources/langfuse-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| I4.5 | `packages/shared/src/in-app-agent/server/runLifecycle.ts:37` | **Claim conditionnel — une seule transition réussit.** Réserve : un CAS de statut n'est pas à lui seul un jeton de propriété. | **Adapter** |
| I4.5 | LF036 | **Heartbeat à perte de propriété explicite** (retour *fenced*, pas un booléen) ; arrêt des écritures et propagation de l'annulation. | **Adapter** |
| I4.5 | LF037 | **Transition terminale conditionnelle**, métrique comptée **une fois et seulement si la transition est acceptée**. | **Adapter** |
| I4.5 | LF038 | **Classification pure des runs périmés** à quatre causes ; **la durée maximale l'emporte sur le heartbeat**. | **Adapter** |
| I4.5 | LF039 | **Réconciliation protégée contre un heartbeat renouvelé.** Une lecture de run périmé ne donne pas le droit de tuer une nouvelle incarnation. | **Adapter** |
| I4.5 | LF040 | **Événements et état terminal dans la même unité de publication.** Reprendre la cohérence, pas le SQL. | **Adapter** |
| I4.5 | LF041 | **Flush limité au préfixe capturé avant l'attente** — les événements ajoutés pendant la persistance sont conservés. | **Adapter** |
| I4.5 | LF042 | Coalescence des deltas **contigus du même message** — pour projection, jamais pour le brut. | **Adapter** |
| I4.5 | `worker/src/features/evaluation/retryObservationNotFound.ts:30` | Retry avec **compteur et âge global conservés** ; chez nous l'âge s'inscrit dans la deadline de mission. | **Adapter** |
| I4.5 | `worker/src/features/evaluation/evalExecutionMetrics.ts:14` | **Résultat d'infrastructure orthogonal à la qualité évaluée.** Confirme la décision 23. | **Adapter** |
| I4.5 | LF090-092 | Scénarios de régression : **heartbeat renouvelé entre lecture et réconciliation**, aucun résultat publié si l'admission échoue, **course entre claim et annulation**. | **Adapter** |


---

## Sources — reprises écartées ou reportées

**7 lignes. N'implémente aucune de ces lignes.** Le pointeur reste pour qu'un retournement de décision retrouve la source. Si tu penses qu'une raison est fausse, **écris-le dans `STATE.md`, n'implémente pas.**

#### A — Villani Code · `resources/villani-code-main/`

| § | Source | Notion | Statut |
|---|---|---|---|
| A4.5 | `execution.py:6-13` | `ExecutionBudget` — cinq bornes dont `max_no_edit_turns` et `max_reconsecutive_recon_turns`. **Borner l'exploration stérile, pas seulement la durée.** | **Écarté** |
| A4.5 | `execution.py:37-43` | `VILLANI_TASK_BUDGET` — valeurs éprouvées : 20 tours, 40 tool calls, **180 s**, 8 tours sans édition, 6 de reconnaissance. Point de départ chiffré pour notre borne murale. | **Écarté** |


#### D — Ouroboros · `resources/ouroboros-main/`

| § | Source | Notion | Statut |
|---|---|---|---|
| D3.6 | `our/task_pacing.py:148-198` | Réserve calibrée par **EWMA des durées observées** (`max(plancher, 1,5 × EWMA)`, `alpha=0.5`), depuis les événements de timing déjà écrits. | **Reporté** |
| D3.6 | `our/task_pacing.py:233-245` | **Latch de l'ancre de départ** : sans lui, chaque snapshot ré-ancre le total sur « maintenant » et la réserve se dégrade vers son plancher. | **Reporté** |
| D3.6 | `our/task_pacing.py:377-380,423-524` | `CostCeiling` — quatre états typés. **`None` n'est pas surchargé** pour signifier à la fois « illimité » et « épuisé ». | **Reporté** |
| D3.6 | `our/context_compaction.py:280-344,681-738` | Unités atomiques `tool_use`/`tool_result` inséparables (confirme Villani), sélection sous budget, **checkpoint de réclamation**. | **Écarté** |
| D3.6 | `our/context_compaction.py:410-417` | `_SUMMARY_CONTRACT_DIGEST` — **le contrat du résumeur est haché** : un résumé produit sous un ancien contrat est reconnaissable. | **Écarté** |

