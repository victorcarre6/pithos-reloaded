# Rapport d'import — héritage des neuf dépôts de référence

Registre complet de ce que Pithos Reloaded prend aux neuf dépôts montés dans ce répertoire, et de ce que ces
reprises ont changé dans la documentation du projet.

**Ce document vit avec les sources qu'il décrit**, pas avec la documentation du harness : tout pointeur
`fichier:ligne` de ce registre se vérifie sans quitter `resources/`. Anciennement `docs/SUCCUBUS.md`,
déplacé le 06:09.

| Source | Nature | Reprises | Partie |
|---|---|---:|---|
| [`villani-code-main/`](villani-code-main) | Runtime d'agent codant local-first, 21 512 L Python | ~90 | **A** |
| [`pi-main/`](pi-main) | Runtime Pi, 397 645 L TypeScript, MIT | **185** | **B** |
| [`kilocode-main/`](kilocode-main) | Monorepo Effect-TS ~1 M L, fork d'OpenCode, MIT — **prompt et paramètres spécifiques à Ling** | **173** | **C** |
| [`ouroboros-main/`](ouroboros-main) | Agent auto-modifiant, **222 035 L Python**, MIT, papier arXiv — **la machinerie de preuve d'effet** | **~200** | **D** |
| [`prime-agent-main/`](prime-agent-main) | *A Self-Improving RLM Harness*, TypeScript + 4 581 L Python, MIT, papier arXiv — **le continual harness** | **~110** | **E** |
| [`unsloth-main/`](unsloth-main) | Bibliothèque de fine-tuning, ~2,1 M L, **licence mixte dont AGPL** — **la politique d'exposition réseau** | **~110** | **F** |
| [`OpenHands-main/`](OpenHands-main) | Frontend Agent Canvas, ~373 K L TypeScript — **l'admission déclarative** | **~110** | **G** |
| [`SWE-agent-main/`](SWE-agent-main) | Agent codant compact, 14 891 L Python, MIT — **parsers fermés et projection déclarée** | **~95** | **H** |
| [`langfuse-main/`](langfuse-main) | Plateforme d'observabilité LLM, 1,2 M L, MIT (hors `ee/`) — **l'identité d'un résultat et le fencing** | **105** | **I** |

**Deux vues, une seule vérité.** Ce document est organisé par **source puis nature du changement** — c'est le
registre de l'héritage, à lire une fois pour savoir ce qu'on doit à qui.
[`ARCHITECTURE.md`](../docs/ARCHITECTURE.md) regroupe les mêmes reprises **par module**, à lire quand on implémente.
Les lignes sont identiques, l'axe diffère. **Toute correction se fait ici en premier.**

## Les quatre verdicts

Une reprise dit toujours **quoi en faire**. Le verdict est unique, et il dépend d'abord de la langue de la
source : **cinq des neuf dépôts sont en TypeScript**, où « copier » ne veut rien dire.

| Verdict | Ce que ça veut dire | Obligation dans le fichier dérivé |
|---|---|---|
| **Copier** | Python, porté quasi tel quel | notice de licence de la source conservée |
| **Traduire** | TypeScript → Python, ligne à ligne, structure préservée | en-tête `PORTED_FROM: <dépôt>/<fichier>:<lignes>` |
| **Adapter** | l'idée est juste, l'implémentation suppose leur objet de session | relecture obligatoire, aucune copie |
| **Inspirer** | la structure de données vaut mieux que le code | aucune |

Distribution après la requalification du 06:09 — **323 lignes reclassées** : `Copier` des sources TS devient
`Traduire`, et les termes `Porter` et `Transposer`, utilisés avant que le vocabulaire soit fixé, disparaissent.

| Verdict | A Villani | C Kilo | D Ouroboros | E Prime | Total |
|---|---:|---:|---:|---:|---:|
| **Copier** | 91 | — | 136 | 23 | **250** |
| **Traduire** | — | 90 | — | 36 | **126** |
| **Adapter** | 21 | 24 | 18 | 38 | **101** |
| **Inspirer** | 12 | 5 | 11 | 12 | **40** |

**Les cinq parties sans colonne `Verdict`** — B, F, G, H, I — sont des catalogues de notions, écrits avant
que le vocabulaire soit fixé. Plutôt que de qualifier ~600 lignes à l'aveugle, leur verdict est **déclaré au
niveau de la partie** :

| Partie | Défaut | Raison |
|---|---|---|
| **B** Pi | `Adapter` | TypeScript ; contrats de durabilité à réécrire en Python |
| **F** Unsloth | `Adapter` | **licence mixte dont AGPL pour `studio/`** — notions reprises, code réécrit, **aucune copie littérale** |
| **G** OpenHands | `Adapter` | reprises explicitement conceptuelles, aucune copie prévue |
| **H** SWE-agent | `Adapter`, **sauf les quatre reprises prioritaires en `Copier`** | Python MIT, mais l'ossature suppose leur environnement |
| **I** Langfuse | `Adapter` | TypeScript, et **aucune reprise proposée depuis `ee/`** (hors MIT) |

Une ligne promue à `Copier` ou `Traduire` l'est dans le `MODULE.md` du module qui la porte, avec son
pointeur exact. **Le registre propose, le `MODULE.md` engage.**

**Deux statuts s'ajoutent aux quatre verdicts** depuis la passe de simplification du 06:09. Ils remplacent le
verdict dans la cellule, parce que ce qui compte n'est plus *comment* porter mais *si* :

| Statut | Sens | Le pointeur reste |
|---|---|---|
| **Écarté** | la reprise couvre une surface que l'architecture a fermée, ou une notion inapplicable | oui — un retournement de décision doit retrouver la source |
| **Reporté** | la reprise est juste, mais son déclencheur n'existe pas encore (volume, concurrence, multi-fichier) | oui |

**37 lignes marquées `Écarté`, 15 `Reporté`** parmi les quatre parties qui portent une colonne `Verdict`.
Les cinq autres n'en ont pas : leurs familles écartées sont listées dans la section suivante.
Et **19 lignes ciblant `trace` pointent désormais `journal`** — le module a été extrait de `kernel`.

**Un renommage à connaître en lisant les tableaux.** Le module `hostside` a été éclaté le 06:09 en
`lifecycle` (verrou, launchd, custody de processus, garde disque) et `broker` (Git + Telegram, la seule
sortie de données de la machine). Les sections `X.7` de chaque partie couvrent les deux, et les lignes dont
la cible était `hostside` pointent maintenant `lifecycle` — **aucune n'était une reprise Git ou Telegram**.
La répartition définitive de ces lignes se fait dans le `MODULE.md` du module qui les porte.

## Ce que la passe de simplification a écarté

*(06:09 — après examen module par module de la complexité réelle : reprises, fichiers sources à lire,
fonctions et objets.)*

**~380 reprises sur ~1 180 sont sorties du périmètre.** Le fil rouge tient en une phrase : **presque tout ce
qui a été écarté défendait contre un agent libre** — commandes shell à autoriser, assertions écrites par le
modèle, conversation accumulée à compacter, couche multi-fournisseurs. La contrainte dure n°1 et la
décision 6 avaient déjà fermé ces surfaces ; les catalogues les rouvraient par habitude, parce que leurs neuf
auteurs construisaient tous un agent libre.

| Famille écartée | Parties | ~Lignes | Raison |
|---|---|---:|---|
| **Les trois capteurs de faux-vert** | D | 250 | ils supposent un modèle qui compose ses commandes et écrit ses assertions ; le script d'invariant est **rendu par le harness**. La garde est portée seule par *un reçu non écrit retire l'attestation* |
| **Le catalogue de douze parsers** | H | 200 | il existe pour des backends sans sortie structurée native ; une sortie non conforme est **rejetée, jamais récupérée** — récupérer par extraction ferait passer un littéral du modèle par une autre porte |
| **La couche de permission de commande** | A, C | 200 | **le modèle n'émet aucune commande.** Son code *est* exécuté : c'est `sandbox` qui défend, pas la permission. Inclut l'arité shell de Kilo, 161 L |
| **La planification de gate par coût** | A | 150 | `format → lint → typecheck → test` alors que la stack n'a **ni linter ni typechecker** : une seule marche à ordonner |
| **La compaction de contexte** | A, D | 150 | **session neuve par nœud** : aucune conversation à compacter, et un résumé serait du texte du modèle entrant dans le prompt suivant |
| **Le streaming SSE** | A, B | 100 | on ne peut rien faire d'un delta quand *« ne jamais exécuter un JSON partiel ou réparé »*, et l'incident de contexte le plus grave de v1 était un incident de streaming |
| **La politique d'exposition réseau** | F | 120 | `observatory` binde `127.0.0.1` **en dur** : l'interdiction est dans le type, pas dans la configuration |
| **L'abstraction multi-fournisseurs** | B, C | 60 | un fournisseur, un modèle. Inclut `convert_openai_response_to_anthropic`, **du legacy v1 : aucun chemin Anthropic n'existe** |
| **Tous les mécanismes de credential** | B, C, F, G | 60 | **Ollama local n'a aucune authentification** — headers d'auth, `route_fingerprint`, résolution de clé par priorité |
| **Les seuils de réécriture massive** | A | 60 | le splice par plage AST borne le rayon d'action par construction : ce n'est pas un cas à détecter mais un cas impossible |
| **Les bornes de tours** | A | 40 | `ExecutionBudget`, `VILLANI_TASK_BUDGET` — 20 tours, 40 tool calls, 8 outils, alors que le mode `direct` fait **un appel par nœud** |
| **`test_tool_calling`** | D | 40 | sonde une capacité que le mode `direct` n'utilise pas |
| **Le scalaire de priorité et `_RANK_ORDER`** | A | 30 | remplacés par un **tuple lexicographique d'axes nommés** — aucune constante magique, cohérent avec la décision 23 |
| **`SecretRedactingLogFilter`** | D | 20 | la décision 10 exclut `logging` : il n'y a rien à filtrer. **Première reprise écartée pour inapplicabilité pure** |
| **Le tableau `MIGRATIONS`** | C | 80 | le JSONL est append-only : une migration est **un lecteur qui tolère deux versions**, pas un script qui transforme le passé — ce que la contrainte n°6 interdit |
| **Le ledger d'arbre parallèle** | D | 120 | `tree.json` est l'état du domaine (décision 11). Deux notions survivent : `child_result_disposition` et **`cap_children`, la borne de largeur qui manquait** |
| **Les scopes, rollback et label mobile du magasin** | E, I | 350 | ils servent à éditer des `prompt`, et rien n'édite de `prompt` tant que `refinery` est `enabled: false` |

**Et ce qui est `Reporté`, pas écarté** — la reprise est juste, son déclencheur n'existe pas encore :
rotation JSONL et quarantaine base64 (volume), séquence dense et `LedgerResumeState` (corruption),
dépôt Git fantôme (une étape multi-fichier), EWMA et latch d'ancre (dix missions mesurées), index de repo
persistant et reconstruction incrémentale (taille du dépôt de campagne).

---

**Complémentarité — les trois premières sources en détail.** Villani apporte les **garde-fous d'un agent codant sur petit
modèle** : quoi valider, comment rendre un échec lisible, comment ne pas confondre absence d'effet et succès.
Pi apporte les **contrats de durabilité et de reprise d'un runtime de production** : ordre d'écriture,
réconciliation après crash, annulation qui ne tue pas l'effet. Kilo apporte la **transactionnalité
filesystem faite correctement** (snapshot Git fantôme, compare-and-swap, verrou à heartbeat), le
**confinement sans conteneur**, et surtout un **prompt système et des paramètres d'échantillonnage mesurés
sur notre modèle exact**.

> Villani dit **quoi mesurer**. Pi dit **comment ne pas perdre la mesure**. Kilo dit **comment ne pas
> corrompre ce qu'on mesure**, et seul des huit **ce que Ling rate en pratique**. Ouroboros dit **comment
> prouver qu'on a mesuré**. Prime Agent dit **comment le harness s'améliore lui-même**, mais en boucle
> ouverte. Unsloth dit **à quelles conditions ce qu'on a construit a le droit d'être joignable**. OpenHands
> dit **comment admettre une donnée déclarative sans jamais l'évaluer**. SWE-agent dit **comment une
> projection déclare ce qu'elle cache**.

**Trois convergences à neuf sources.** Les neuf implémentent une forme de **patch ou d'interpolation
textuelle approximative**, et les neuf sont écartés au même endroit. Les six runtimes portent un **monolithe
de session ou d'agent** de 1 300 à 12 000 lignes, et les six sont écartés pour la même raison. Et **aucune des
neuf sources n'a d'invariant métamorphique, de mutation-check ni de catalogue fermé de relations** : neuf
dépôts matures, dont deux avec un papier et un à 86,74 % sur Terminal-Bench, neuf fois le même constat.
`verifier/relations`, `verifier/domains` et `verifier/mutation` sont l'apport propre du projet.

**Fiabilité des extractions, et ce qu'elle nous a appris.** Deux extractions ont été **vérifiées avant
absorption**, avec des résultats opposés qui valent d'être comparés.

| | Partie H — SWE-agent | Partie I — Langfuse |
|---|---|---|
| Ancres | valides, mais **descriptions décalées d'une classe** par endroits | **15/15 exactes**, définitions canoniques |
| Couverture | **trois zones entières omises**, dont la plus utile | **carte de couverture par famille**, fichiers cités comptés |
| Honnêteté | affirme une couverture qu'elle n'a pas | **déclare ses propres limites** |

La leçon n'est pas « les petits modèles extraient mal » — c'est que **la forme d'une extraction complète ne
prouve pas sa complétude**, et que la seule extraction auditable est celle qui **quantifie ce qu'elle n'a pas
couvert**. C'est exactement ce que la décision 13 exige de nos propres nœuds, appliqué au travail
documentaire.

**Et une opposition frontale entre deux sources, tranchée.** Pi exécute les commandes contenues dans une
valeur de configuration (`resolve-config-value.ts:10`, écarté) ; OpenHands interdit toute expression évaluable
dans un placeholder (`manifest-template.ts:76`, repris). Même question, deux réponses — la nôtre est la
seconde.

**Et une complémentarité qui ferme une boucle.** Prime Agent implémente l'auto-amélioration mais ne vérifie
jamais qu'elle améliore quoi que ce soit. Nous avons l'autorité de validation qui manque exactement là.
C'est la combinaison qui est neuve, pas la moitié qu'on importe.

---

# PARTIE A — Villani Code

## A1. Pourquoi ce dépôt

Villani Code est un runtime d'agent codant local-first de **21 512 lignes** (plus 13 661 de tests). Il défend
littéralement notre thèse — *« small models do not just need better weights. They need a better runtime »*
(`README.md:9`) — et il la chiffre.

| Résultat | Source |
|---|---|
| Terminal-Bench 2.0 : **44,0 %** avec Qwen3.6 27B, contre 40,1 % pour Claude Code + Sonnet 4.5 | `README.md:13-31` |
| À modèle identique (Qwen3.5 9B) : **63,3 %** contre 43,3 % — 6 tâches gagnées, 0 perdue | `README.md:53-73` |

C'est la meilleure preuve externe disponible que l'hypothèse retenue au cadrage est mesurable. Elle rend
l'entreprise nettement moins spéculative qu'elle ne l'était après l'audit de Pithos v1.

**Convergence de stack non concertée.** `pyproject.toml:11-19` liste `typer`, `httpx`, `pydantic`, `pyyaml` —
trois de nos quatre choix transverses, arrêtés indépendamment avant lecture du dépôt.

**Licence.** Projet personnel, copie libre. L'absence de fichier `LICENSE` dans l'archive ne conditionne
aucune reprise.

---

## A2. Ce que Villani n'a pas

Aucun invariant métamorphique. Aucun mutation-check. Aucune sortie contrainte par JSON Schema. Aucun
catalogue de relations fermé. **Sa validation est « exécuter les commandes du repo et lire le code de
retour ».**

Les décisions 2 et 3 — le contrat comme invariant, la double gate rouge-avant + mutation — sont sans
équivalent chez lui. `verifier/relations`, `verifier/domains` et `verifier/mutation` s'écrivent de zéro.

Ce que Villani apporte, c'est **tout ce qui entoure ce cœur** : quoi valider, comment exécuter, comment
rendre un échec lisible à un 8B, et comment ne jamais confondre une absence d'effet avec un succès.

---

## A3. Ce que la reprise a changé dans la documentation

| Fichier | Avant | Après | Nature du changement |
|---|---:|---:|---|
| `docs/ARCHITECTURE.md` | 225 | 453 | Tableaux *Reprises de Villani* par module, section *Sources de reprise*, section *Ce qu'il ne faut pas reprendre* |
| `docs/EXPLANATIONS.md` | 290 | 490 | 3 décisions amendées (5, 9, 10), 4 ajoutées (12 à 15) |
| `docs/ROADMAP.md` | 70 | 182 | Source `villani/<fichier>:<lignes>` sur chaque item, items du cœur marqués *(neuf)*, phase *Différé — mode agentic* |
| `docs/PROJECT.md` | 105 | 116 | 4 critères de socle ajoutés, périmètre inchangé |
| `resources/villani.md` | 302 | pointeur | Absorbé ici |

### A3.1 — Décisions amendées

**Décision 5 — la satisfaction se périme.** *(`EXPLANATIONS.md` § Décision 5)*
Le marqueur `~/logs/pithos/runtime/*-completed.json` de v1 figeait un rush comme terminé et **ne savait pas se
périmer quand le code changeait** : tous les réveils suivants devenaient des no-op jusqu'à intervention
humaine. Remplacé par une empreinte de repo restreinte aux fichiers de l'outil — elle bouge, la satisfaction
tombe, l'outil repasse par la gate d'invariants. Sécurise aussi l'auto-extension de la décision 7 : un outil
réutilisé est toujours un outil dont l'empreinte tient encore. La granularité d'états passe à sept, dont
**trois formes d'échec distinctes** — « échoué » ne dit pas s'il faut réessayer.
→ `autonomous.py:1014-1042`, `autonomous.py:53-60`, `autonomous_helpers.py:61-64`

**Décision 9 — seuils nommés et snapshot sur disque.** *(`EXPLANATIONS.md` § Décision 9)*
La garde syntaxique attrape la destruction totale ; elle laisse passer la réécriture massive qui compile
encore. `MutationGuardThresholds` la nomme : `max_touched_lines=120`, `max_touched_ratio=0.35`,
`min_lines_for_ratio_guard=40`, avec analyse par `difflib.SequenceMatcher`. Seconde ligne derrière le splice
AST. Et le snapshot transactionnel passe **sur disque** : en mémoire il ne survit pas à un crash du
processus — précisément le moment où il compte.
→ `state_tooling.py:21-122`, `checkpoints.py:18-60`, `patch_apply.py:68-106`

**Décision 10 — le flag `durable` et l'agrégat déjà écrit.** *(`EXPLANATIONS.md` § Décision 10)*
Tous les événements ne sont pas des preuves. v1 ne faisait pas la distinction et son collecteur a produit un
stdout de 1,3 Go. Chaque événement porte désormais un flag `durable` : un spinner est éphémère, une
transition de nœud est durable. S'y ajoutent la reprise des identifiants d'événement après redémarrage et des
compteurs de tokens qui peuvent rester `None` — **un token absent n'est jamais un zéro**, sinon le dashboard
affiche des débits faux. Enfin, l'agrégateur JSONL que notre choix « pas de DuckDB » impose existe déjà, et il
valide son agrégat contre un contrat avant de le servir.
→ `runtime_events.py:28-34`, `event_recorder.py:20-33`, `trace_summary.py:16-51,104-133,439-757,777-820`

### A3.2 — Décisions ajoutées

**Décision 12 — Le prédicat `authoritative`.**
Un seul prédicat partagé décide de ce qui est proposable, modifiable et comptable comme changement. Trois
conséquences : un `.pyc` touché n'est pas un changement, les chemins d'artefacts runtime ne sont jamais
montrés au modèle, et une proposition touchant un chemin non-`authoritative` est éliminée avant toute
inference. Le point de méthode compte autant que la règle : v1 avait cette logique dupliquée dans quatre
modules avec des définitions divergentes.
→ `repo_rules.py:44-91`, `state_execution.py:17-30`, `context_projection.py:9-20`, `autonomy.py:716-722`

**Décision 13 — Aucun succès sans preuve d'effet.**
**Correction du mode d'échec dominant de v1** : sur dix runs `completed`, sept n'avaient produit aucun effet.
Deux mécanismes indépendants — comparaison au contenu antérieur croisée avec `git diff --name-only`, et
artefact d'exécution contenant littéralement `(exit=0)` pour toute validation. Plus la réconciliation des
findings contredits par la preuve directe, et la détection de boucle stérile par empreinte de diagnostic
répétée à l'identique — le signal qui manquait aux six heures de boucle de v1.
→ `autonomy.py:99-126,203-210,261-302`, `autonomous_helpers.py:88-120`

**Décision 14 — Le contexte est un objet inspectable, pas une chaîne.**
v1 assemblait le contexte par concaténation et n'en gardait aucune trace : quand un brief périmé a produit
**12 419 `thinking_delta` consécutifs et zéro tool call**, il a fallu lire le stream brut pour comprendre.
Le contexte devient un inventaire typé : raison d'inclusion ou d'exclusion par élément, pression graduée en
quatre paliers, évictions comptées, dérive détectée activement, compactage par type de source qui préserve
le signal.
→ `context_governance.py:11-31,34-71,83-122,200-220,252-266`, `context_projection.py:23-70`, `context_budget.py:82-93,204-222`

**Décision 15 — Ce que Villani prouve, et ce qu'on n'en reprend pas.**
Consigne les chiffres Terminal-Bench comme preuve externe, l'absence d'invariants métamorphiques chez lui
comme confirmation que les décisions 2-3 sont notre apport propre, et les quatre pièges écartés.

### A3.3 — Critères de socle ajoutés

Quatre entrées dans `PROJECT.md` § *Critères de succès du socle*. **Le périmètre est inchangé ; seuls les
critères se resserrent.**

- Un nœud dont la cible n'a pas effectivement changé ne peut pas être compté vert *(décision 13)*.
- Un chemin non-`authoritative` n'est jamais proposé, écrit, projeté au modèle, ni compté comme changement *(décision 12)*.
- La satisfaction d'un outil vérifié est invalidée dès que l'empreinte de ses fichiers change *(décision 5 amendée)*.
- Le contexte de chaque nœud est un inventaire typé *(décision 14)*.

### A3.4 — Corrections de cohérence

- Les items du cœur `verifier` sont marqués **`(neuf)`** dans la roadmap — relations, domaines, mutations,
  gate rouge-avant — pour qu'on ne cherche pas une source Villani qui n'existe pas.
- Le mode agentique différé est un **exécuteur de feuille LangGraph**, plus une « session Pi outillée »
  (reliquat d'une rédaction antérieure à la décision 6).

---

## A4. Catalogue complet des reprises

**Convention.** Chaque ligne se lit :

```text
cible  ->  resources/villani-code-main/villani_code/<fichier>:<ligne>  ->  notion
```

**Verdicts.** *Copier* — porter quasi tel quel. *Adapter* — l'idée est juste, l'implémentation suppose
l'objet `Runner` de Villani. *Inspirer* — la structure de données vaut mieux que le code.

### A4.1 — `kernel`

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `contracts` | `mission_state.py:12-95` | État sérialisable avec `verified_facts`, `open_hypotheses`, `steps`, `intended_targets`, et `from_dict` défensif — chaque champ recoercé. Modèle direct de notre `Node`. | Inspirer |
| `contracts` | `mission_state.py:114-117` | `new_mission_id()` — horodatage UTC triable **avec sous-seconde**, explicitement pour éviter les collisions dans la même seconde. | Copier |
| `contracts` | `mission_state.py:162-171` | `load_resume_bundle` — la reprise charge état + messages + résumé en un appel typé. | Adapter |
| `codeview` | `indexing.py:69-114` | `RepoIndex.build/save/load/needs_rebuild` — index de fichiers avec symboles et snippet borné, persisté en JSON. | Adapter |
| `codeview` | `indexing.py:117-127` | `compute_repo_fingerprint` — SHA-256 de `path:size:mtime` pour invalider un index sans le relire. Réutilisé par l'index mémoire du dashboard. | Copier |
| `codeview` | `indexing.py:146-150` | `extract_snippet` — lecture bornée en octets **et** en lignes avant tout parsing. | Copier |
| `codeview` | `repo_rules.py:44-51` | `is_ignored_repo_path` — un seul prédicat partagé par le planner, le verifier et le reporting. | Copier |
| `codeview` | `repo_rules.py:54-68` | `classify_repo_path` → `vcs_internal` / `editor_artifact` / `runtime_artifact` / `generated` / **`authoritative`**. Pivot de la décision 12. | Copier |
| `codeview` | `repo_rules.py:71-91` | `is_authoritative_doc_path` — restreint la doc éditable au `README` racine et à `docs/*`. | Adapter |
| `journal` | `runtime_events.py:28-34` | `RuntimeEvent` porte un flag **`durable`** : un événement de statut éphémère ne pollue pas la preuve. | Copier |
| `journal` | `runtime_events.py:8-25` | `RuntimeEventChannel` / `RuntimeEventType` — deux enums fermées : le canal (qui écoute) et le type (quoi). | Copier |
| `journal` | `runtime_events.py:37-127` | `from_runner_event` — table de correspondance unique entre événements bruts et typés, avec repli explicite. | Inspirer |
| `journal` | `event_recorder.py:20-33` | Une ligne JSONL = `ts` + `type` + `phase` + `durable` + `summary` + **payload brut complet**. Le résumé est à côté du brut, jamais à sa place. | Copier |
| `journal` | `trace_summary.py:16-51` | `EventLogger._discover_next_event_id` — les identifiants reprennent après redémarrage en relisant le fichier. | Copier |
| `journal` | `trace_summary.py:104-133` | `normalize_token_usage` — les compteurs peuvent rester `None`. | Copier |
| `kernel` | `state_execution.py:17-30` | `summarize_changes` → `intentional` vs `incidental` via `classify_repo_path`. | Copier |
| `kernel` | `utils.py:22-27` | `is_path_within` par `relative_to` + `ValueError`. Trois lignes, aucun `..` à gérer. | Copier |

### A4.2 — `verifier`

Le cœur — relations, domaines, mutations — est **neuf**. Ce qui suit l'entoure.

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `gates` | `validation_loop.py:110-124` | `infer_validation_scope` — dérive `docs_only`, `formatting_only`, `dependency_changed` des seuls chemins modifiés. Aucun appel modèle. | **Écarté** |
| `gates` | `validation_loop.py:127-154` | `infer_validation_targets` — mappe une source vers ses tests probables avec un **score de confiance** (0.95 direct, 0.65 inféré). | **Écarté** |
| `gates` | `validation_loop.py:157-164` | `infer_targeted_command` — restreint `pytest` aux cibles inférées au lieu de la suite entière. | **Écarté** |
| `gates` | `validation_loop.py:167-169` | `_step_order` — étapes ordonnées par **coût croissant** (format → lint → typecheck → test → build). | **Écarté** |
| `gates` | `validation_loop.py:190-279` | `plan_validation` — sélection d'étapes avec une **raison textuelle par étape retenue**. | **Écarté** |
| `gates` | `validation_loop.py:274-278` | `ValidationEscalationPolicy` — *targeted first, then broaden*. Un changement de dépendance force directement la gate large. | **Écarté** |
| `gates` | `validation_loop.py:282-299` | `summarize_validation_failure` → `failure_class`, `relevant_error_lines`, `recommended_repair_scope`. **C'est le feedback rendu au modèle**, pas du stdout brut. | Copier |
| `gates` | `validation_loop.py:302-329` | `run_validation` — sortie au **premier échec**, callback avant/après chaque étape, durée en `monotonic`. | Copier |
| `gates` | `planning.py:403-411` | `compact_failure_output` — tête + `...` + queue, borné en lignes et caractères. | Copier |
| `gates` | `benchmark/verifier.py:15-29` | `_normalize_verification_command` — réécrit `pytest ...` en `[sys.executable, "-m", "pytest", ...]`. **v1 a payé exactement ce bug.** | Copier |
| `gates` | `benchmark/verifier.py:32-36` | `_is_launch_failure` — exit 127/9009 + « not found » ⇒ **la commande n'existe pas**, ce n'est pas un contrat rouge. | Copier |
| `gates` | `benchmark/verifier.py:39-137` | `run_commands` — chaque exécution archive `stdout`, `stderr` et un `meta.json`. Notre script d'invariant rendu produit le même triplet. | Copier |
| `verifier` | `autonomy.py:62-246` | `VerificationEngine` — vérificateur **adversarial** post-changement, indépendant des tests. | Adapter |
| `verifier` | `autonomy.py:99-126` | `before_contents` vs contenu courant croisé avec `git diff --name-only` ⇒ finding « no effective change ». Pilier de la décision 13. | Copier |
| `verifier` | `autonomy.py:169-188` | Finding `SUSPICIOUS_BREADTH` si `git diff --stat` dépasse 8 fichiers. | Adapter |
| `verifier` | `autonomy.py:203-210` | Empreinte des findings ⇒ `repeated_verification_state`. **Détecte la boucle stérile par la répétition à l'identique du diagnostic.** | Copier |
| `verifier` | `autonomy.py:212-225` | Score de confiance par pénalité de sévérité, borné `[0.05, 0.95]`. Jamais 0 ni 1. | **Écarté** |
| `verifier` | `autonomy.py:261-302` | `_reconcile_findings` — un finding contredit par une preuve directe est retiré, **et le retrait est journalisé**. | Copier |
| `verifier` | `autonomy.py:17-27` | `FindingCategory` — taxonomie fermée de huit catégories de défauts. | Copier |
| `verifier` | `autonomy.py:311-324` | `FailureCategory` — 13 causes fermées, dont `REPEATED_NO_PROGRESS` et `EXCESSIVE_BLAST_RADIUS`. | Copier |
| `verifier` | `autonomy.py:337-387` | `FailureClassifier` — classe par mots-clés **et compte les occurrences** : trois échecs de même catégorie forcent un changement de stratégie. | Copier |
| `verifier` | `autonomous_helpers.py:88-120` | `meets_contract` / `has_real_validation_artifact` — un artefact doit contenir littéralement `(exit=0)`. Pilier de la décision 13. | Copier |

### A4.3 — `bridge`

Villani fournit ce client, écrit et testé. **Il ne lui manque que `response_format`** — point d'insertion
`openai_client.py:75-86`, qui est exactement la cible du spike n°2.

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `bridge` | `openai_client.py:212-234` | `OpenAIClient` — 23 lignes, `httpx`, timeout **300 s** (un local lent n'est pas une panne), streaming et non-streaming séparés. | Copier |
| `bridge` | `openai_client.py:9-13` | `normalize_openai_base_url` — ajoute `/v1` de façon idempotente. | Copier |
| `bridge` | `openai_client.py:75-86` | `build_openai_payload` — **le point d'insertion de `response_format`**, alimenté par `Criterion.model_json_schema()`. | Adapter |
| `bridge` | `openai_client.py:174-209` | `convert_openai_response_to_anthropic` — normalisation vers un format interne unique, `usage` et `stop_reason` compris. | **Écarté** |
| `bridge` | `openai_client.py:89-98` | Mapping `finish_reason` avec `length` distingué de `stop`. **Une génération tronquée n'est pas une génération terminée** — cas nominal sur 16k. | Copier |
| `bridge` | `openai_client.py:101-171` | `openai_stream_to_anthropic_events` — parsing SSE tolérant : ligne vide ignorée, JSON invalide sauté, `usage` capturé en fin. | **Écarté** |
| `bridge` | `context_budget.py:82-93` | `_group_atomic_units` — un `tool_use` et son `tool_result` sont **inséparables** au compactage. | Copier |
| `bridge` | `context_budget.py:204-205` | `_preserve_exact` — un contenu portant `@@` ou `diff --git` n'est **jamais** compacté. Un diff résumé est un diff faux. | Copier |
| `bridge` | `context_budget.py:208-222` | `_summarize_tool_result` — compactage par extraction de signal, jamais par troncature aveugle. | Copier |
| `bridge` | `state_runtime.py:396-437` | `validate_anthropic_tool_sequence` — validation **avant** l'appel réseau. Un message mal formé échoue localement, gratuitement. | Inspirer |

### A4.4 — `workspace`

Le module où Villani est le plus dense : c'est son domaine, et c'est là que v1 a subi son pire incident.

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `workspace` | `state_tooling.py:21-28` | `MutationGuardThresholds` — `120` lignes, ratio `0.35`, plancher `40`. **Des seuils nommés, versionnés, testables.** | **Écarté** |
| `workspace` | `state_tooling.py:89-122` | `_analyze_text_rewrite` — `SequenceMatcher` sur les lignes ⇒ `probable_rewrite`. Détection générique de ce qui a détruit `audio_visualizer.py`. | **Écarté** |
| `workspace` | `state_tooling.py:125-174` | `_analyze_patch_mutation` — même analyse appliquée à un diff, sans l'appliquer. | **Écarté** |
| `workspace` | `state_tooling.py:236-291` | Validation `py_compile` avec message nommant fichier, validateur, exception et action attendue. Chez nous la validation est **avant** écriture ; le format du message est le bon. | Adapter |
| `workspace` | `state_tooling.py:44-86` | Extraction du code depuis un payload enveloppé en blocs ```` ``` ````. **Un petit modèle enveloppe systématiquement sa sortie** — `new_source` y sera exposé malgré la sortie structurée. | Copier |
| `workspace` | `state_tooling.py:177-207` | `_sanitize_tool_input_file_path` — déquote, normalise, résout avant toute décision de politique. | Copier |
| `workspace` | `patch_apply.py:68-106` | **Valider tous les patchs, puis appliquer** (`# apply atomically after validation`, l. 95). | Copier |
| `workspace` | `patch_apply.py:330-333` | `_detect_newline_style` — préserve CRLF si le fichier en avait. | Copier |
| `workspace` | `state_runtime.py:508-590` | `small_model_tool_guard` — cible `authoritative` obligatoire, `Patch` refusé sur fichier absent, **read-before-edit** avec auto-lecture forcée. | Copier |
| `workspace` | `state_runtime.py:479-505` | `_is_strongly_adjacent_path` — définit « proche d'une cible verrouillée » (même dossier, `__init__.py`, même stem, `test_<stem>`). | Adapter |
| `workspace` | `checkpoints.py:18-60` | `CheckpointManager` — snapshot **sur disque** avec `metadata.json`, et `rewind()`. Survit à un crash du processus. | **Reporté** |
| `workspace` | `permissions.py:174-209` | `classify_bash_command` — allowlist par **préfixe de tokens**, refus du chaînage, de la redirection et de la substitution. | **Écarté** |
| `workspace` | `permissions.py:212-233` | `bash_matches` — matching **conscient des opérateurs**, avec le commentaire qui nomme la faille : `to avoid prefix exploits like '&& rm -rf /'`. | **Écarté** |
| `workspace` | `permissions.py:51-107` | `PermissionEngine.evaluate_with_reason` — ordre `deny` → `ask` → `allow`, **chaque décision retourne sa raison**. | **Écarté** |
| `workspace` | `runtime_safety.py:42-55` | `ensure_runtime_dependencies_not_shadowed` — **refuse de démarrer si le repo cible masque une dépendance du harness.** Notre campagne construit un paquet Python : le piège nous vise. | Copier |
| `workspace` | `runtime_safety.py:58-66` | `temporary_sys_path` — contextmanager restaurant `sys.path` intégralement. Le `verifier` importe du code produit. | Copier |
| `workspace` | `command_environment.py:153-260` | `runner_private_roots` / `build_agent_command_environment` — retire de l'environnement tout chemin absolu du harness. | Adapter |
| `workspace` | `benchmark/policy.py:29-57` | `normalize_path` / `comparison_key` / `path_is_within` / `path_matches_glob` — une seule implémentation partagée. | Copier |

### A4.5 — `engine`

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `walk` | `planning.py:215-316` | `analyze_instruction` — **classification entièrement déterministe** : cibles candidates, classes d'action, portée, impact, confiance, `rationale`. Zéro appel modèle. Preuve qu'une grande part de ce qu'on croit devoir demander au modèle se dérive du repo. | Copier |
| `walk` | `planning.py:11-57` | Cinq enums fermées : `PlanRiskLevel`, `ActionClass` (13 valeurs), `EstimatedScope`, `ChangeImpact`, `TaskMode`. | Copier |
| `walk` | `planning.py:319-332` | `classify_plan_risk` — risque dérivé des classes d'action et de la portée, jamais demandé au modèle. | Copier |
| `walk` | `planning.py:388-400` + `validation_loop.py:219-247` | `classify_task_mode`, puis **le mode détermine quelles gates tournent**. | Adapter |
| `walk` | `planning.py:99-142` | `ExecutionPlan.to_human_text` — rendu texte compact réinjectable. Un plan qui ne se rend pas en texte ne sert pas au modèle suivant. | Inspirer |
| `context` | `context_governance.py:11-31` | `ContextInclusionReason` / `ContextExclusionReason` / `ContextPressureLevel` — **chaque élément porte la raison de sa présence ou de son absence.** | Copier |
| `context` | `context_governance.py:34-71` | `ContextItem` (avec `pressure_share`) / `ContextBudgetEstimate` / `ContextInventory`. | Copier |
| `context` | `context_governance.py:252-266` | `_recompute_budget` — quatre paliers de pression (`low` < 0,45 < `moderate` < 0,75 < `high` < 1,0 < `overflow_risk`). Vital avec Ling plafonné à 16k. | Copier |
| `context` | `context_governance.py:200-208` | `prune_for_budget` — éviction FIFO sous pression, chaque éviction enregistrée avec sa raison et comptée. | Copier |
| `context` | `context_governance.py:210-220` | `detect_stale_context` — signaux nommés, dont **réparations répétées avec contexte gonflé**. Le capteur qui aurait attrapé les 12 419 `thinking_delta`. | Copier |
| `context` | `context_governance.py:83-122` | `ContextCompactor` — un compacteur par type de source, chacun avec ses tokens de signal. | Copier |
| `context` | `context_projection.py:9-20` | `_filter_model_facing_paths` — les chemins d'artefacts runtime ne sont **jamais** montrés au modèle. | Copier |
| `context` | `context_projection.py:23-70` | Paquet **structuré** puis rendu texte séparé. Le paquet est traçable, le rendu jetable. | Copier |
| `walk` | `execution.py:6-13` | `ExecutionBudget` — cinq bornes dont `max_no_edit_turns` et `max_reconsecutive_recon_turns`. **Borner l'exploration stérile, pas seulement la durée.** | **Écarté** |
| `walk` | `execution.py:37-43` | `VILLANI_TASK_BUDGET` — valeurs éprouvées : 20 tours, 40 tool calls, **180 s**, 8 tours sans édition, 6 de reconnaissance. Point de départ chiffré pour notre borne murale. | **Écarté** |
| `walk` | `execution.py:15-34` | `ExecutionResult` transporte `intended_targets` **et** `before_contents` — le vérificateur reçoit l'intention et l'état antérieur. | Copier |
| `walk` | `repair.py:61-106` | `execute_repair_loop` — réparation ciblée sur **la seule étape en échec**, puis élargissement. Historique de tentatives réinjecté. | Copier |
| `walk` | `repair.py:11-19` | `RepairContext` — payload en champs bornés, sérialisé en JSON. Le prompt de repair est une structure, pas de la prose. | Copier |
| `walk` | `interrupts.py:7-18` | `InterruptController` — premier signal interrompt, second quitte. Dix-huit lignes. | Copier |
| `engine` | `subagent_runtime.py:19-27` | `build_role_launch_request` — quatre rôles avec **allowlist d'outils, droit d'écriture et exigence de preuve** explicites. `fresh_verifier` n'hérite pas de l'état : il vérifie sans être contaminé. | Copier |
| `engine` | `subagent_runtime.py:30-40` | `render_subagent_brief` — huit lignes fixes, dont `Known facts` et **`Ruled out`**. Transmettre ce qui a été écarté évite de le réexplorer. | Copier |
| `engine` | `subagents.py:22-27` | Sous-agents définis par leurs **interdits** plutôt que par leurs permissions. | Inspirer |
| `engine` | `summarizer.py:9-55` | Résumés de phase déterministes, jamais générés. | Copier |

### A4.6 — `campaign`

Chez Villani, **tout le backlog est déterministe** : le modèle exécute les tâches, il ne les invente pas.
Notre backlog ouvert délègue davantage — ce catalogue est donc autant un socle qu'un contre-modèle utile.

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `registry` | `autonomy.py:390-400` | `Opportunity` — `priority`, `confidence`, `evidence`, `blast_radius`, `task_contract`. **`evidence` est obligatoire** : une opportunité sans preuve n'existe pas. | Copier |
| `registry` | `autonomy.py:523-631` | `discover_opportunities` — **découverte du backlog par heuristiques déterministes**. Zéro appel modèle. | Adapter |
| `registry` | `autonomy.py:423-432` | `_RANK_ORDER` — ordre de priorité **écrit en dur, par titre**. Assumé, lisible, débogable. | **Écarté** |
| `registry` | `autonomy.py:716-722` | `_is_authoritative_opportunity` — élimination avant sélection, donc avant inference. | Copier |
| `registry` | `autonomy.py:403-411` | `TakeoverConfig` — `max_waves=3`, `max_total_task_attempts=6`, `min_confidence=0.60`, `stagnation_cycle_limit=2`. | **Écarté** |
| `registry` | `autonomous.py:53-60` | `TaskLifecycle` — sept états, dont **trois formes d'échec distinctes**. « Échoué » ne dit pas s'il faut réessayer. | Copier |
| `registry` | `autonomous.py:1014-1027` | `_repo_fingerprint_for_task` — empreinte **restreinte à ce qui concerne la tâche**. | Copier |
| `registry` | `autonomous.py:1029-1042` | `_mark_task_satisfied` / `_is_task_satisfied` — satisfaction invalidée dès que l'empreinte bouge. | Copier |
| `proposals` | `autonomous_helpers.py:44-52` | `task_key_for_opportunity` — clé normalisée **avec table d'alias**. Sans alias, « ajouter un parseur » et « créer un outil de parsing » passent toutes deux notre rejet de redondance. | Copier |
| `proposals` | `autonomous_helpers.py:9-26` | `build_wave_candidates` — filtre en cascade puis déduplication par clé en gardant la meilleure priorité. | Copier |
| `proposals` | `autonomous_helpers.py:29-41` | `effective_priority` — `priority*0.7 + confidence*0.3`. Formule visible, ajustable. | **Écarté** |
| `proposals` | `autonomous_helpers.py:61-64` | `retry_limit_for_contract` — le nombre de retries dépend du type de contrat. | Copier |
| `stop` | `autonomous_stop.py:7-12` | `StopDecision` — dont **`planner_churn`** et **`stagnation`**, qui nomment précisément les modes d'échec de v1. | Copier |
| `stop` | `autonomous_stop.py:35-47` | `category_exhaustion_reason` — la raison d'arrêt **énumère ce qui a été examiné**. Un arrêt qui ne dit pas ce qu'il a couvert n'est pas auditable. | Copier |
| `stop` | `autonomous_progress.py:10-36` | Machine à états par catégorie : `discovered` → `attempted`. L'épuisement devient mécanique. | Copier |
| `stop` | `autonomous_progress.py:39-88` | `surface_followups` — une catégorie découverte mais non traitée **génère sa tâche de suivi** avant que l'arrêt soit proposable. | Adapter |
| `campaign` | `autonomous_reporting.py:77-145` | `build_takeover_summary` — distingue changements intentionnels, incidents et **préexistants**. Sans cette notion, on attribue au système des changements qu'il n'a pas faits. | Copier |
| `campaign` | `mcp.py:27-35` | `load_mcp_config` — couches `managed` → `user` → `project` → `local`. **La couche `managed` est écrite par le runtime** : exactement notre décision 7. | Copier |
| `campaign` | `mcp.py:11-24` | `_expand_env` récursif avec `${VAR:-default}`, sans secret en dur. | Copier |
| `campaign` | `project_memory.py:99-142` | `ValidationStep` / `ValidationConfig` — les commandes de validation sont **une donnée persistée**, pas une constante du harness. | Copier |
| `campaign` | `project_memory.py:313-362` | `scan_repo` — dérive `RepoMap` + `ValidationConfig` + `ProjectRules` d'un repo inconnu, une fois, puis persiste. | Adapter |
| `campaign` | `skills.py:16-33` | `discover_skills` — `SKILL.md` à frontmatter YAML, découverte par `rglob`. | Copier |

### A4.7 — `lifecycle` et `broker`

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `lifecycle` | `hooks.py:19-59` | `HookRunner` — hooks `shell` ou `http` renvoyant `{allow, reason, input}`, avec réécriture possible de l'entrée. | Inspirer |
| `lifecycle` | `shells.py:15-41` | Commande **normalisée avant exécution et journalisée sous sa forme normalisée**. | Inspirer |
| `lifecycle` | `command_environment.py:32-48` | `CommandEnvironmentDiagnostics` — l'environnement passé à une commande est diagnostiqué et journalisé. | Adapter |

### A4.8 — `observatory`

Notre choix « pas de DuckDB » impose un agrégateur JSONL. **Villani l'a déjà écrit.**

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `observatory` | `trace_summary.py:439-757` | `aggregate_summary_from_events` — reconstruit **tout** l'agrégat d'un run depuis les seuls JSONL. ~300 lignes, aucune base. Littéralement la fonction que notre API exécute au démarrage. | Copier |
| `observatory` | `trace_summary.py:196-427` | `build_tool_call_records_from_events` — reconstruction **avec la liste des anomalies rencontrées**. Signale ses propres trous au lieu de les combler. | Adapter |
| `observatory` | `trace_summary.py:777-820` | `validate_summary` — l'agrégat est **validé contre un contrat** avant d'être servi. | Copier |
| `observatory` | `trace_summary.py:11-13` | `AGGREGATION_VERSION` / `TOOL_CALL_SCHEMA_VERSION` — l'agrégat porte la version de la logique qui l'a produit. | Copier |
| `observatory` | `trace_summary.py:758-776` | `_build_artifact_manifest` — manifeste des artefacts d'un run, servi tel quel au frontend. | Copier |
| `observatory` | `event_recorder.py:35-59` | `build_digest` — comptage par famille + les 25 derniers événements. | Copier |
| `observatory` | `debug_recorder.py:64-72` | `_safe` — **toute écriture d'observabilité est encapsulée : une panne du recorder ne casse jamais la mission.** Règle absolue. | Copier |
| `observatory` | `debug_recorder.py:87-406` | Vocabulaire d'enregistrement exhaustif, dont **`record_context_compacted`** et `record_mission_state_snapshot`. Liste de référence de ce qu'un runtime doit tracer. | Inspirer |
| `observatory` | `debug_recorder.py:414-446` | `write_final_summary` — un run se termine toujours par un résumé écrit. | Copier |

---

## A5. Ce qui est écarté, et pourquoi

| Source | Poids | Raison |
|---|---:|---|
| `state.py` + `state_runtime.py` + `autonomous.py` | 4 807 L | Trois monolithes construits autour d'un objet `Runner` que tout traverse — `state_runtime.py` prend `runner: Any` en premier argument dans une trentaine de fonctions. C'est le paradigme boucle-d'agent que la décision 6 supprime. **Piocher les notions, jamais l'ossature.** |
| `indexing.py:57-66` | — | `SYMBOL_PATTERNS` : extraction de symboles Python **par regex**. Erreur exacte de v1, qui a coûté l'incident d'arité `smooth_levels(0.0, 0.0, 0.0)`. Notre `codeview` utilise l'AST. Les regex restent acceptables pour les langages non-Python de l'index. |
| `patch_apply.py:231-323` | — | Repli **fuzzy** d'application de patch. Soigné — candidat unique exigé, sinon rejet — mais contredit frontalement « le modèle renvoie une fonction, pas un diff ». Un patch approximatif appliqué avec succès est le risque que le splice AST supprime par construction. |
| `tui/` | 13 fichiers | Textual. Nous avons retenu React/Vite porté de v1. |
| `benchmark/` | 4 264 L | Harnais multi-agents (Claude Code, aider, opencode). Hors périmètre — sauf `verifier.py` et `policy.py`, repris. |
| `anthropic_client.py` | 42 L | Autre fournisseur, hors périmètre souveraineté. |
| `interactive.py`, `live_display.py`, `optional_tui.py`, `status_controller.py` | ~330 L | UX de session interactive. Notre campagne tourne sous LaunchAgent, sans humain devant. |
| `task_memory.py` | 485 L | Mémoire de tâche exposée **comme des tools au modèle**. En mode `direct`, le modèle n'a pas de tools : la mémoire est un objet du harness injecté dans le contexte. L'idée d'une mémoire JSONL reste bonne, la surface d'outil est à jeter. |

---

## A6. Les cinq reprises qui changent la trajectoire

Si rien d'autre n'était repris, ces cinq-là suffiraient à justifier la lecture du dépôt. Chacune ferme un
mode d'échec **mesuré** en v1.

1. **`classify_repo_path` → `authoritative`** — `repo_rules.py:54-68`. Un prédicat unique et partagé qui
   décide de ce qui est proposable, modifiable et comptable. v1 avait cette logique éparpillée dans quatre
   modules avec des définitions divergentes.

2. **Satisfaction invalidée par empreinte** — `autonomous.py:1014-1042`. Une tâche réussie le reste tant que
   le code concerné n'a pas bougé. Remplace le marqueur `*-completed.json` de v1, incapable de se périmer,
   qui a produit des réveils no-op indéfinis.

3. **Preuve d'effet réel** — `autonomy.py:99-126` et `autonomous_helpers.py:110-120`. Ensemble, ils rendent
   impossible le mode d'échec dominant de v1 : **compter comme succès un run qui n'a rien produit** — 7 des
   10 `completed`.

4. **`detect_stale_context`** — `context_governance.py:210-220`. Détecte la dérive de contexte avant qu'elle
   ne bloque le modèle. Le capteur qui manquait aux 12 419 `thinking_delta` consécutifs.

5. **`MutationGuardThresholds` + `_analyze_text_rewrite`** — `state_tooling.py:21-122`. Seuils nommés et
   analyse par `SequenceMatcher` contre la réécriture massive déguisée en édition. Seconde ligne derrière le
   splice AST, contre l'incident qui a détruit un fichier pendant six heures.

---

## A7. Ordre d'exploitation

Aligné sur [`ROADMAP.md`](../docs/ROADMAP.md), où chaque item porte déjà sa source.

| Phase | Reprises |
|---|---|
| **P0** | `repo_rules.py` entier · `indexing.py:69-127,146-150` · `runtime_events.py:8-34` · `event_recorder.py:20-33` · `trace_summary.py:16-51,104-133` · `mission_state.py:12-95,114-117,162-171` · `utils.py:22-27` · `state_execution.py:17-30` · `benchmark/policy.py:29-57` |
| **P1** | `validation_loop.py:110-329` · `benchmark/verifier.py:15-137` · `planning.py:403-411` · `autonomy.py:17-27,62-246,261-387` · `autonomous_helpers.py:88-120` · `project_memory.py:99-142` |
| **P2** | `state_tooling.py:21-122,177-207,236-291,44-86` · `patch_apply.py:68-106,330-333` · `state_runtime.py:479-590` · `checkpoints.py:18-60` · `runtime_safety.py:42-66` · `context_governance.py` entier · `context_projection.py` entier · `execution.py:6-43` · `planning.py:11-57,215-400` · `repair.py:11-106` · `interrupts.py:7-18` · `summarizer.py:9-55` |
| **P3** | `autonomy.py:390-411,523-631,716-722` · `autonomous.py:53-60,1014-1042` · `autonomous_helpers.py:9-64` · `autonomous_stop.py` entier · `autonomous_progress.py` entier · `autonomous_reporting.py:77-145` |
| **P4** | `permissions.py:51-233` · `command_environment.py:32-260` · `hooks.py:19-67` · `shells.py:15-41` |
| **P5** | `trace_summary.py:11-13,196-427,439-820` · `event_recorder.py:35-59` · `debug_recorder.py:64-72,87-446` |
| **P6** | `mcp.py:11-35` · `skills.py:16-33` |
| **Différé** | `subagent_runtime.py:19-40` · `subagents.py:22-27` |

---

# PARTIE B — Pi

## B1. Pourquoi ce dépôt

Pi est le runtime d'agent qui portait Pithos v1 (`pi 0.84.2`, installé en `~/.npm-global/bin/pi`). La
décision 6 l'a retiré du chemin nominal — mais son code reste la meilleure source disponible sur **les
contrats de durabilité et de reprise d'un runtime d'agent réellement exploité en production**.

`1 673 fichiers`, `397 645 lignes`, TypeScript, **licence MIT** à la racine. La provenance doit être
conservée pour toute copie substantielle, y compris les éléments vendored (`export-html/vendor`).

**Ce que Pi apporte que Villani n'a pas :**

- l'**ordre d'écriture** entre journal, projection mémoire et effet externe ;
- la **réconciliation après crash** avec distinction entre *non commencé*, *effet inconnu* et *résultat enregistré* ;
- la frontière réelle de la **contrainte de décodage** (`require` vs `prefer`) et des sorties structurées ;
- le fait qu'**annuler une attente ne tue pas l'opération** ;
- une **matrice de tests de reprise** couvrant chaque état durable.

**Ce que Pi n'a pas, et que Villani a :** la preuve d'effet réel, la détection de contexte périmé, la
classification déterministe de tâche, les seuils de mutation. Les deux sources sont complémentaires, pas
redondantes.

**Note de méthode.** `resources/pi.md` était une étude documentaire : aucun code Pi n'a été copié pour la
produire, et plusieurs entrées sont des **contre-exemples explicites** — des choses que Pi fait et qu'il ne
faut surtout pas reprendre. Elles sont conservées telles quelles ci-dessous : ce sont les plus précieuses.

## B2. Ce que la reprise a changé dans la documentation

| Cible | Nature du changement |
|---|---|
| `EXPLANATIONS.md` | Décision 10 amendée (ne jamais réparer un journal tronqué) · décisions 16 à 19 ajoutées |
| `PROJECT.md` | 3 critères de socle ajoutés, périmètre inchangé |
| `ARCHITECTURE.md` | Reprises Pi ajoutées par module |
| `ROADMAP.md` | Sources `pi/<fichier>:<ligne>` sur les items concernés |

### B2.1 — Décision 10 amendée : ne jamais réparer un journal tronqué

`jsonl/storage.ts:87` détecte correctement une ligne finale incomplète — puis `open` (l. 210) **réécrit le
fichier** pour la supprimer. **Contre-exemple direct de notre contrainte dure n°6** (« les données brutes
sont append-only et ne sont jamais supprimées »). Nous reprenons la détection, jamais la réparation : les
octets bruts sont conservés, le fragment est diagnostiqué, et la mission reprend dans un **nouveau segment
lié au précédent**.

Deux corollaires du même module : **publier sur disque avant de modifier la projection mémoire**
(`storage.ts:253`) — aucun état mémoire ne doit annoncer une transition non persistée — et **scinder les
JSONL sur LF uniquement** (`rpc/jsonl.ts:21`), car `U+2028`/`U+2029` peuvent appartenir à une chaîne JSON.
En Python cela interdit `str.splitlines()` pour ce protocole.

### B2.2 — Décision 16 : persister l'intention avant l'effet externe

**La décision qui rend la reprise possible.** Avant tout appel modèle ou toute modification, le harness
enregistre `tentative`, `id`, `cible`, `digest` et `état attendu` (`drive/generation.ts:132`). Une reprise
peut alors distinguer trois situations qu'aucune trace *a posteriori* ne sépare :

| État | Signification | Action à la reprise |
|---|---|---|
| non commencé | l'intention est écrite, aucun effet | rejouer |
| **effet inconnu** | l'intention est écrite, l'effet a pu avoir lieu | **interroger, jamais rejouer aveuglément** |
| résultat enregistré | l'effet et son verdict sont persistés | continuer |

`drive-tools.test.ts:421` en donne le corollaire opérationnel : **un appel interrompu ne prouve pas que son
effet n'a pas eu lieu.** Une lecture est rejouable, une écriture est à réconcilier, et une publication Git
doit être **interrogée par identifiant avant toute nouvelle tentative**. L'autorisation de rejouer appartient
au harness, jamais au modèle.

La réconciliation vit sur un **chemin distinct du chemin nominal** (`drive/reconcile.ts:132`), et l'état est
vérifié avant tout effet (`restore.ts:131`) : ids, parenté, statut, références aux snapshots et verdicts. Un
état contradictoire est **bloqué avec cause** — il n'est pas corrigé en relançant le modèle.

### B2.3 — Décision 17 : la frontière du modèle a quatre pièges nommés

Quatre entrées Pi durcissent le `bridge` bien au-delà de ce que Villani couvre.

**La contrainte de décodage doit être requise, jamais préférée** (`constrained-sampling.ts:208`). Pi
distingue `require` — échoue si le provider ne supporte pas le mode strict — de `prefer`, qui le désactive
silencieusement. Pour `Criterion` et `Proposal`, le refus explicite est la seule option acceptable : un repli
silencieux ferait retomber la contrainte dure n°1 sans que rien ne le signale.

**Le thinking n'est pas du contenu** (`openai-completions.ts:601`). Pi reconnaît `reasoning_content`,
`reasoning` et `reasoning_text`. `Criterion` et `new_source` ne s'extraient **que du contenu final désigné**,
jamais d'un bloc thinking ni d'une concaténation de toutes les chaînes. Sur un modèle qui produit 12 419
`thinking_delta` d'affilée quand il est bloqué, cette règle n'est pas théorique.

**Une terminaison doit être explicite** (`openai-completions.ts:692`). Un socket fermé avec du JSON
plausible n'est pas une réussite. `length`, `error` et sortie tronquée sont des échecs, et
`raw_stop_reason` est conservé tel quel — un `finish_reason` inconnu reste un échec explicite
(`openai-completions.ts:1550`).

**Le budget réserve la place de la sortie avant l'appel** (`simple-options.ts:15`). Budget = entrée + schéma
+ instructions + sortie + marge. **Si le contrat obligatoire ne tient pas, l'appel est refusé**, il n'est pas
tenté avec l'espoir que ça passe. Sur Ling 16k, la marge se mesure au spike. Corollaire
(`simple-options.ts:75`) : borner le thinking pour qu'il ne consomme pas toute la réponse.

Enfin, **les retries implicites du SDK sont désactivés** (`openai-completions.ts:364`) : `engine` décide du
retry et de son budget. Sans cela, on multiplie SDK × bridge × Prefect — trois couches qui retentent sans se
connaître. C'est un raccordement direct à la frontière posée en décision 11.

### B2.4 — Décision 18 : annuler une attente ne tue pas l'opération

`abort.ts:17` pose le contrat que la borne murale suppose : une course entre une promesse et un timeout
**rend la main sans prouver l'arrêt de l'I/O**. Il faut fermer explicitement le stream ou le client, puis
vérifier la fin.

Le même piège existe côté filesystem, et il est plus grave : `write.ts:69` **libère le verrou à
l'annulation alors que l'écriture peut encore se terminer** — donc une écriture tardive peut atterrir *après*
le rollback. Notre décision 9 promet une restauration à l'octet près ; elle est fausse si on n'attend pas la
fin réelle de l'effet avant de restaurer. Le cas doit être testé explicitement par intercalation.

Corollaire côté engine : **fermer l'admission de nouveaux effets avant de propager l'annulation**
(`effect-gate.ts:31`). À l'expiration de la borne murale, on cesse d'admettre, puis on finalise ce qui est
vert — dans cet ordre.

### B2.5 — Décision 19 : le registre est indexé par empreinte de contrat

`harness-table.ts:105` — **empreinte stable du contrat plutôt qu'un identifiant fourni par le modèle.** Un
outil est identifié par le hash de son contrat canonicalisé, pas par le nom que le modèle a proposé. Cela
ferme une classe entière de redondances que le rejet lexical de la décision 5 laisse passer : deux
propositions de noms différents pour le même contrat collisionnent mécaniquement.

La canonicalisation JSON préalable (`harness-table.ts:66`) est ce qui rend la comparaison structurelle de
schémas fiable — c'est la brique qui manquait au critère « couple (schéma d'entrée, schéma de sortie)
structurellement identique » de la décision 5.

Trois compléments pour l'auto-extension de la décision 7 : **provenance explicite de chaque ressource**
(`source-info.ts:6`), **collisions nommées avec gagnant et ressource ignorée** (`diagnostics.ts:1`), et
**vérification d'intégrité avant d'activer une nouvelle génération** (`bundle-loader.ts:231`). Un outil
n'entre dans la couche `managed` qu'après contrôle, et une collision est un événement journalisé, pas un
écrasement silencieux.

### B2.6 — Critères de socle ajoutés

Trois entrées dans `PROJECT.md`, périmètre inchangé.

- **Aucune ligne JSONL n'est jamais réécrite ni supprimée**, y compris une fin de fichier tronquée : le
  fragment est diagnostiqué et la reprise ouvre un nouveau segment lié.
- **Une reprise distingue non commencé / effet inconnu / résultat enregistré**, et n'exécute jamais un effet
  externe deux fois sans interrogation préalable.
- **Les frontières d'import sont testées comme contrats d'architecture** — `verifier` n'importe jamais le
  bridge ni le modèle, `bridge` n'importe jamais `engine`. Rendu mécanique par un test de graphe d'imports
  (`check-entry-graphs.mjs:33`), au lieu de reposer sur la discipline.

## B3. Catalogue complet des reprises

`S` reprendre au socle · `R` adapter comme référence · `D` phase ultérieure · `X` écarter.
Chemins relatifs à `resources/pi-main/`.

### B3.1 — `kernel`

| S | Source | Notion |
|---|---|---|
| S | `packages/agent/src/harness/session/types.ts:18` | Identités stables, parent explicite, séquence de stockage. Séparer id, parent_id, numéro de séquence, horodatage. Une branche conversationnelle Pi n'est pas notre arbre de travail. |
| S | `packages/agent/src/harness/result.ts:1` | Résultats discriminés à codes fermés : `invalid_schema`, `invalid_symbol`, `timeout`, `interrupted`, `invariant_failed`. **Une exception d'infrastructure ne devient jamais un verdict vert.** |
| S | `packages/agent/src/harness/session/commit.ts:90` | Contrôler ids uniques et parent antérieur **avant** publication. Choisir et tester explicitement notre règle de monotonie. |
| S | `packages/agent/src/harness/session/jsonl/types.ts:4` | Version explicite du format persistant. Versionner `Event`, `tree`, `registry` dès P0 ; refuser une version inconnue avec diagnostic. |
| S | `packages/agent/src/harness/session/jsonl/storage.ts:79` | Une ligne JSONL comme unité logique indivisible au rejeu. Ne rend pas atomiques ensemble `tree.json`, fichiers produit et journal. |
| S | `packages/agent/src/harness/session/jsonl/storage.ts:253` | **Publier sur disque avant de modifier la projection mémoire.** Tester un append refusé. |
| S | `packages/agent/src/harness/session/jsonl/storage.ts:87` | Distinguer fin tronquée et corruption au milieu. **Ne pas reprendre la réparation destructive de `open` l. 210.** |
| S | `packages/coding-agent/src/modes/rpc/jsonl.ts:21` | Framing sur **LF uniquement** et décodage UTF-8 incrémental. Éviter `str.splitlines()`. Borner la taille. |
| S | `packages/coding-agent/src/modes/json-event.ts:20` | Deltas linéaires sans duplication du cumulatif. Doubler une réponse ne doit pas quadrupler le volume de traces. |
| S | `packages/agent/src/harness/utils/usage.ts:14` | Usage en champs distincts (input/output/reasoning/cache), agrégé une fois. **Un compteur absent reste inconnu, pas zéro.** |
| S | `packages/telemetry/src/index.ts:18` | Cycle de vie d'un span indépendant du fournisseur : parent, début, fin, statut, attributs. Mission → nœud → appel/gate. Aucun SDK requis. |
| S | `packages/telemetry/src/memory.ts:54` | Snapshots détachés des objets mutables. **Une trace émise ne doit pas changer quand la source mute.** Tester en mutant après émission. |
| S | `packages/chord/src/json.ts:4` | Sous-ensemble JSON strict et fini. Refuser NaN/Infinity à la frontière des contrats. |
| R | `packages/telemetry/src/noop.ts:3` | Instrumentation facultative — jamais pour désactiver les preuves JSONL obligatoires. |
| D | `packages/ai/src/utils/assistant-message-frame.ts:8` | Frames rejouables, message final autoritatif. Référence pour une feuille agentique ; le contrat nominal reste requête / sortie brute / verdict / usage. |

### B3.2 — `verifier`

| S | Source | Notion |
|---|---|---|
| S | `packages/agent/src/harness/execution/tools.ts:78` | Séparer préparation, admission, exécution, finalisation. La validation d'arguments Pi ne prouve **aucune** relation métamorphique. |
| S | `packages/coding-agent/src/core/tools/bash.ts:25` | Refuser les délais invalides avant de créer un processus : zéro, négatif, infini, dépassement du budget restant. |
| S | `packages/coding-agent/src/utils/child-process.ts:49` | **Fin de processus ≠ fin de ses sorties.** Délai d'inactivité ET deadline absolue ; ne pas attendre indéfiniment le close d'un pipe. |
| S | `packages/agent/src/harness/utils/output-capture.ts:26` | Vue bornée avec métadonnées de troncature : exit_code, cause, totaux, extrait, chemin de l'artefact complet. **L'extrait n'est jamais la preuve.** |
| S | `packages/evals/src/pi-harness.ts:212` | Préserver l'échec initial quand le nettoyage échoue aussi. Pas de suppression du workspace avant sauvegarde des preuves. |
| S | `packages/agent/src/harness/session/testing/conformance/storage.ts:134` | Suite de conformité commune : mêmes contrats testés sur un fake et un répertoire réel, sans interface multi-backends en production. |
| S | `packages/agent/src/harness/session/testing/gating-storage.ts:26` | Injection déterministe d'un crash entre admission et persistance. **Éviter les tests de race fondés sur `sleep`.** |
| S | `packages/agent/src/harness/session/testing/instrumented-storage.ts:6` | Observer les tentatives de commit, pas seulement l'état final. Vérifier qu'une entrée invalide n'a tenté aucune écriture. |
| S | `packages/agent/test/harness/jsonl-storage.test.ts:278` | Corpus de fins tronquées et lignes invalides, **en inversant l'attendu de la réparation Pi**. Ajouter coupure UTF-8, disque plein, échec de rename/fsync. |
| S | `packages/agent/test/harness/runtime/drive-reconcile.test.ts:450` | **Matrice de reprise couvrant chaque état durable** : couper avant/après chaque effet, relancer sans conversation. |
| S | `packages/agent/test/harness/runtime/drive-tools.test.ts:421` | Distinguer effet rejouable et effet de résultat inconnu. Pilier de la décision 16. |
| S | `packages/ai/src/providers/faux.ts:144` | Provider scénarisé sans réseau. Fixer ids/horloge/découpage : **le faux de Pi utilise du hasard par défaut**, il n'est pas déterministe. |
| S | `packages/coding-agent/test/suite/harness.ts:34` | Harness de scénario isolé de la configuration utilisateur. Tester que les credentials machine ne sont pas chargés. |
| S | `packages/protocol/test/framing.test.ts:14` | Fragmentation arbitraire des flux : mêmes octets en un bloc, octet par octet, coupés au milieu d'un caractère. Résultat identique. |
| S | `packages/chord/test/delta.test.ts:19` | Formes de tests pour utilitaires purs : rejeu et immuabilité. **Ne pas injecter leurs valeurs attendues dans les `Criterion` proposés par le modèle.** |
| S | `packages/telemetry/src/testing/conformance.ts:61` | Fermeture d'un span exactement une fois, conservation du résultat, indépendance des snapshots. |
| S | `test.sh:1` | Séparer tests hors ligne et intégrations avec modèle réel. Sélection pytest explicite sans endpoint ni credentials ambiants. |

### B3.3 — `bridge`

| S | Source | Notion |
|---|---|---|
| S | `packages/ai/src/api/constrained-sampling.ts:208` | **`require` et non `prefer`** : refus explicite si le mode strict est indisponible. Ne démontre pas `response_format` sur Ollama `/v1` — le spike reste indispensable. |
| S | `packages/ai/src/api/constrained-sampling.ts:117` | Compatibilité du sous-ensemble JSON Schema réellement envoyé : `$defs`/`$ref`, unions, optional/null, `additionalProperties`. Tester le schéma exact de `Criterion` avec Ling. |
| S | `packages/ai/src/utils/validation.ts:59` | **Contre-exemple** : Pi convertit `null` en 0/false/chaîne vide. Chez nous validation stricte, champs supplémentaires refusés, aucune coercition. Conserver la sortie brute rejetée. |
| S | `packages/ai/src/utils/json-parse.ts:104` | **Ne jamais exécuter un JSON partiel ou réparé.** Accolade manquante ou fallback `{}` ⇒ rejet, pas exécution. |
| S | `packages/ai/src/api/openai-completions.ts:357` | Enregistrer le payload effectif au spike : modèle, `response_format`, messages, plafond, sampling, endpoint. **Ne pas exposer un hook arbitraire au modèle.** |
| S | `packages/ai/src/api/openai-completions.ts:692` | Exiger une terminaison explicite du stream. Un socket fermé avec du JSON plausible n'est pas une réussite. |
| S | `packages/ai/src/api/openai-completions.ts:1550` | Normaliser la cause de fin en conservant `raw_stop_reason`. Un `finish_reason` inconnu reste un échec explicite. |
| S | `packages/ai/src/api/openai-completions.ts:1507` | Normaliser l'usage sans double comptage cache/reasoning. Conserver le JSON brut et une projection documentée. |
| S | `packages/ai/src/api/openai-completions.ts:601` | **Séparer thinking et contenu exploitable.** N'extraire `Criterion`/`new_source` que du contenu final désigné. |
| S | `packages/ai/src/api/openai-completions.ts:364` | **Désactiver les retries implicites du SDK.** Éviter la multiplication SDK × bridge × Prefect. Vérifier le nombre de requêtes au faux serveur sur une 503. |
| S | `packages/ai/src/utils/error-body.ts:38` | Diagnostic borné : type/statut/cause + extrait, corps complet dans l'artefact. **Un 400 de schéma ne se confond pas avec un 503 transitoire.** |
| S | `packages/ai/src/utils/abort-signals.ts:6` | Combiner annulation opérateur et deadline, puis nettoyer les listeners. |
| S | `packages/ai/src/utils/abort.ts:17` | **Annuler l'attente ne tue pas l'opération.** Prévoir fermeture du stream/client et vérification de fin. Conditionne la borne murale réelle. |
| S | `packages/ai/src/api/simple-options.ts:15` | Réserver la place de la sortie avant l'appel. **Si le contrat obligatoire ne tient pas, refuser l'appel.** |
| S | `packages/ai/src/api/simple-options.ts:75` | Borner le thinking pour garder assez de sortie au contrat. Les noms de paramètres Pi ne prouvent pas leur support local. |
| S | `packages/ai/src/utils/estimate.ts:114` | Estimation explicitement distincte de l'usage mesuré. `chars/4` est fragile pour Unicode et code. Journaliser les deux séparément. |
| S | `packages/ai/src/utils/overflow.ts:134` | Classifier dépassement de contexte et sortie trop courte séparément. Un overflow provoque une **réduction déterministe**, pas un retry identique. |
| S | `packages/ai/test/constrained-sampling.test.ts:88` | Fixtures `require`/`prefer` et schémas non supportés. Le succès de ces tests TypeScript ne valide ni Pydantic ni Ollama. |
| S | `packages/ai/test/openai-completions-raw-stop-reason.test.ts:55` | Corpus de raisons terminales connues et inconnues. Ajouter `length` avec JSON syntaxiquement complet : **si le protocole dit tronqué, rien n'est appliqué.** |
| R | `packages/ai/src/utils/sanitize-unicode.ts:21` | Cas Unicode invalides. Décider explicitement rejet ou échappement ; **ne pas corriger silencieusement** un symbole ni les octets d'un fichier cible. |

### B3.4 — `workspace`

| S | Source | Notion |
|---|---|---|
| S | `packages/coding-agent/src/core/tools/edit.ts:192` | Préserver BOM et fins de ligne. Pi normalise tout en LF puis restaure un style global : **insuffisant pour notre promesse à l'octet près** sur fichiers mixtes. |
| S | `packages/coding-agent/src/core/tools/edit-diff.ts:300` | Valider **toutes** les modifications avant d'en appliquer une : unicité et absence d'overlap. Transposer au remplacement d'un `def` unique, décorateurs compris. |
| S | `packages/coding-agent/src/core/tools/edit-diff.ts:357` | **Détecter un patch sans effet.** Comparer les octets avant/après : un no-op n'est pas un progrès. Cause mécanique courte à `engine`, tentative conservée. |
| S | `packages/coding-agent/src/core/tools/edit-diff.ts:207` | **Écarter le fuzzy matching du chemin nominal.** Cible = symbole AST exact + snapshot exact ; un mismatch fait réassembler le contexte ou rejette. |
| S | `packages/coding-agent/src/core/tools/edit-diff.ts:365` | Diff relisible attaché à chaque tentative, produit par `difflib` avant écriture. **Le diff prouve la modification, pas la correction.** |
| S | `packages/coding-agent/src/core/tools/write.ts:69` | **Garder l'exclusivité jusqu'à la fin réelle de l'écriture.** Libérer le verrou à l'annulation permet une écriture tardive après rollback. Tester l'intercalation. |
| S | `packages/coding-agent/src/utils/paths.ts:108` | Inclusion de chemin **par composants**, pas par `startswith` (`/campaign2` n'est pas `/campaign`). Résoudre symlinks et parent existant. |
| S | `packages/coding-agent/src/utils/paths.ts:36` | Détecter un contexte de fichier périmé. Préférer le digest des octets snapshotés ; si le fichier a changé depuis la génération, **ne pas écraser**. |
| S | `packages/agent/src/harness/session/jsonl/storage.ts:94` | Staging puis rename atomique. Temporaire **unique** dans le même filesystem, flush/fsync, `os.replace`, nettoyage sur échec. Le `.tmp` fixe de Pi ne suffit pas. |
| S | `packages/agent/test/harness/tools.test.ts:186` | Mutations concurrentes, annulation, conservation. Ajouter nos exigences absentes de Pi : `def` unique, nom/arité, décorateurs, `async def`, compilation, rollback d'un fichier créé. |
| R | `packages/coding-agent/src/core/tools/file-mutation-queue.ts:32` | Sérialisation par identité réelle du fichier. Utile seulement si des feuilles deviennent concurrentes ; **le fallback sur fichier absent n'est pas une protection TOCTOU.** |

### B3.5 — `engine`

| S | Source | Notion |
|---|---|---|
| S | `packages/agent/src/harness/runtime/drive.ts:29` | Dispatch explicite par état durable. Reprendre la lisibilité des transitions, éviter le runtime complet de lanes/compaction/inbox. |
| S | `packages/agent/src/harness/runtime/drive/generation.ts:132` | **Persister l'intention avant l'effet externe.** Pilier de la décision 16. |
| S | `packages/agent/src/harness/runtime/restore.ts:131` | Restaurer et vérifier la cohérence avant tout effet. Un état contradictoire est **bloqué avec cause**, pas corrigé en relançant le modèle. |
| S | `packages/agent/src/harness/runtime/drive/recovery.ts:44` | Reprise d'un appel orphelin depuis les preuves. Une sortie partielle n'est pas appliquée. **Usage inconnu plutôt que le zéro synthétique de Pi.** |
| S | `packages/agent/src/harness/execution/effect-gate.ts:31` | Fermer l'admission de nouveaux effets **avant** de propager l'annulation. |
| S | `packages/agent/src/harness/runtime/drive/reconcile.ts:132` | Chemin de réconciliation distinct du chemin nominal. |
| S | `packages/agent/src/harness/runtime/drive/terminal.ts:26` | Finalisation terminale commune, résultat immuable. |
| S | `packages/ai/src/utils/retry.ts:224` | **Classification des erreurs indépendante de la politique de retry.** Ce qui est retryable est une propriété de l'erreur, pas du contexte d'appel. |
| S | `packages/ai/src/utils/retry.ts:163` | Retries bornés, observables et annulables. |
| S | `packages/agent/src/agent-loop.ts:177` | Réassembler le contexte **depuis l'état courant**, jamais depuis un brief figé. Convergence exacte avec la décision 14. |
| S | `packages/agent/src/harness/compaction/utils.ts:91` | Feedback compact avec sortie brute accessible par référence. |
| S | `packages/coding-agent/src/core/resource-loader.ts:119` | Provenance et priorité **déterministes** des fichiers d'instructions. |
| R | `packages/agent/src/harness/runtime/drive/retry.ts:6` | Reprise d'un délai de retry déjà programmé après redémarrage. |
| R | `packages/agent/src/harness/compaction/utils.ts:54` | Distinguer fichiers lus et fichiers modifiés dans le contexte. |
| D | `packages/agent/src/agent-loop.ts:487` | Préflight des appels avant exécution, ordre stable des résultats. |
| D | `packages/agent/src/agent-loop.ts:379` | **Un tool call tronqué ne doit jamais être exécuté.** |
| D | `packages/agent/src/agent.ts:125` | Steering et follow-up comme files distinctes. |
| D | `packages/agent/src/harness/compaction/compaction.ts:311` | Compaction préservant les frontières conversationnelles. |
| D | `packages/agent/src/harness/hooks.ts:15` | Contrats de hooks et traitement différencié des erreurs. |

### B3.6 — `campaign`

| S | Source | Notion |
|---|---|---|
| S | `packages/evals/src/vitest-evals/harness-table.ts:66` | **Canonicalisation JSON avant comparaison structurelle.** Brique manquante du critère « schémas structurellement identiques » de la décision 5. |
| S | `packages/evals/src/vitest-evals/harness-table.ts:105` | **Empreinte stable du contrat plutôt qu'un identifiant fourni par le modèle.** Pilier de la décision 19. |
| S | `packages/coding-agent/src/core/source-info.ts:6` | Provenance explicite de chaque ressource. |
| S | `packages/coding-agent/src/core/diagnostics.ts:1` | Collisions nommées, avec gagnant et ressource ignorée. Un écrasement silencieux est un bug. |
| S | `packages/ai/scripts/model-data.ts:42` | Vérifier l'égalité **exacte** de deux inventaires. |
| S | `packages/ai/scripts/model-data.ts:193` | Manifest de versions et empreintes vérifié avant chargement. |
| S | `packages/coding-agent/src/utils/paths.ts:36` | Invalidation d'un outil vérifié quand son fichier change. Convergence exacte avec la décision 5 amendée. |
| S | `packages/coding-agent/examples/extensions/dynamic-tools.ts:27` | Enregistrement dynamique après initialisation. |
| S | `packages/coding-agent/examples/extensions/reload-runtime.ts:30` | Recharger les capacités **à une frontière sûre**, jamais au milieu d'un effet. |
| S | `packages/chord/src/node/bundle-loader.ts:231` | Vérifier l'intégrité avant d'activer une nouvelle génération. |
| S | `packages/evals/src/extensions.eval.ts:110` | **Prouver création, chargement ET appel effectif de la capacité produite.** C'est littéralement la question expérimentale 4, avec son patron de test. |
| S | `packages/tui/src/fuzzy.ts:12` | **Contre-exemple** : ne pas confondre recherche approximative et rejet de redondance. Un score flou ne décide pas d'un rejet mécanique. |
| S | `scripts/diff-model-catalog.mjs:36` | Rapport `added`/`removed`/`changed` entre deux catalogues. |
| S | `scripts/publish-release-announcement.test.mjs:12` | **Une publication tardive ne doit pas rétrograder une génération.** |
| R | `packages/chord/src/facets/host.ts:423` | Préparer et valider le candidat avant de remplacer l'actif. |
| R | `packages/chord/src/facets/host.ts:858` | Détection mécanique des cycles de dépendance. |
| R | `scripts/publish-release-announcement.mjs:10` | Annoncer une version seulement après vérification de sa disponibilité. |
| D | `packages/coding-agent/test/suite/regressions/6162-extension-active-tools-next-turn.test.ts:7` | Une modification du registre devient visible au tour suivant. |
| D | `packages/coding-agent/examples/extensions/structured-output.ts:4` | Arrêter une feuille après son résultat structuré, sans tour final inutile. |

### B3.7 — `lifecycle` et `broker`

| S | Source | Notion |
|---|---|---|
| S | `packages/coding-agent/src/utils/shell.ts:216` | **Arrêter le groupe de processus, pas le seul parent.** |
| S | `packages/coding-agent/src/utils/shell.ts:206` | Nettoyage des descendants suivis lors de l'arrêt. |
| S | `packages/coding-agent/src/core/tools/bash.ts:80` | Exécution injectable avec `cwd` et environnement explicites. |
| S | `packages/coding-agent/src/core/settings-manager.ts:172` | Précédence de configuration **documentée et testée**. |
| S | `packages/coding-agent/src/core/settings-manager.ts:197` | Erreurs de configuration rapportées avec scope et chemin. |
| S | `packages/coding-agent/src/core/auth-storage.ts:25` | Permissions restrictives des fichiers contenant des secrets. |
| S | `packages/coding-agent/src/core/trust-manager.ts:125` | Mise à jour de configuration sous verrou, publication par rename. |
| S | `packages/protocol/src/protocol.ts:49` | Enveloppe de commande : id, cible, résultat discriminé. Directement applicable au broker Telegram. |
| S | `packages/protocol/src/protocol.ts:40` | **Empêcher une commande tardive de viser la nouvelle mission.** Un `/stop` envoyé pendant la mission N ne doit pas tuer la mission N+1. |
| S | `packages/coding-agent/examples/extensions/dirty-repo-guard.ts:10` | Préflight des changements non commités. |
| S | `packages/coding-agent/examples/extensions/git-checkpoint.ts:22` | **Ne pas assimiler un checkpoint Git à notre rollback à l'octet près.** |
| S | `packages/coding-agent/examples/extensions/auto-commit-on-exit.ts:42` | Ne publier que des fichiers explicitement verts. |
| S | `packages/coding-agent/docs/security.md:7` | **Séparer confiance de chargement et confinement d'exécution.** Charger une capacité de confiance ne l'autorise pas à tout faire. |
| R | `packages/coding-agent/src/utils/git.ts:84` | Validation des arguments Git avant passage à la CLI. |
| R | `packages/client/src/client.ts:45` | Corrélation des requêtes et nettoyage des attentes. |
| R | `packages/server/src/transports/unix/listener.ts:299` | **Ne supprimer un socket périmé qu'après vérification de son identité.** |
| R | `packages/server/src/transports/unix/listener.ts:11` | Permissions et fermeture bornée du transport local. |
| R | `packages/coding-agent/src/experimental/mini/shared/rpc.ts:65` | Liveness séparée de la durée d'un appel long. |

### B3.8 — `observatory`

| S | Source | Notion |
|---|---|---|
| S | `packages/agent/src/harness/session/in-memory-storage-state.ts:62` | **Index mémoire reconstruit depuis les enregistrements durables.** Exactement notre choix « pas de DuckDB ». |
| S | `packages/agent/src/harness/session/jsonl/repo.ts:50` | Séparer catalogue de missions et chargement détaillé d'une mission. |
| S | `packages/agent/src/harness/runtime/reducer.ts:22` | Reducer **pur** de projection pour l'interface. |
| S | `packages/coding-agent/src/modes/interactive/components/tree-selector.ts:27` | **Aplatir l'arbre en lignes en conservant parenté et branche active.** Directement la vue d'arbre de P5. |
| S | `packages/coding-agent/src/modes/interactive/components/tree-selector.ts:121` | État de repli séparé des données métier. |
| S | `packages/coding-agent/src/core/export-html/ansi-to-html.ts:63` | **Échapper les traces avant rendu HTML.** Les traces contiennent de la sortie de commande arbitraire. |
| S | `packages/evals/src/vitest-evals/summary.ts:3` | Distinguer résultats scorés, absents, en attente et erreurs. Quatre états, pas deux. |
| S | `packages/evals/src/vitest-evals/harness-table.ts:110` | Grouper un essai par entrée et répétition. |
| S | `packages/evals/src/vitest-evals/reporter.ts:14` | Index JSONL de runs et références d'artefacts. |
| S | `packages/evals/src/vitest-evals/artifacts.ts:87` | **Artefacts associés strictement au run propriétaire.** |
| S | `scripts/stats.ts:86` | Statistiques journalières depuis les JSONL. |
| S | `scripts/tool-stats.ts:112` | Relier appels, résultats, erreurs et volume par outil. |
| S | `scripts/edit-tool-stats.mjs:157` | **Mesurer l'inflation d'un patch par rapport au changement utile.** Métrique directe de la qualité du splice. |
| S | `scripts/edit-tool-stats.mjs:243` | Catégoriser mécaniquement les échecs d'édition. |
| S | `scripts/session-context-stats.mjs:156` | **Occupation du contexte et marge restante par appel.** Instrumentation de la décision 14 sur 16k. |
| R | `packages/agent/src/harness/events.ts:5` | Snapshot et abonnement **sans trou** entre les deux. |
| R | `packages/chord/src/services/state.ts:93` | Détecter une rupture de séquence et redemander un snapshot. |
| R | `packages/agent/src/harness/utils/adaptive-publisher.ts:18` | Coalescer les rafraîchissements UI sous budget de débit. |
| R | `packages/coding-agent/src/utils/fs-watch.ts:17` | **Un watcher défaillant ne doit pas faire tomber l'observatoire.** |
| R | `packages/coding-agent/src/core/export-html/index.ts:35` | Export autonome d'une mission avec preuves et métadonnées. |
| R | `packages/tui/src/fuzzy.ts:99` · `.../session-selector-search.ts:39` | Recherche locale multi-termes, score stable, expressions entre guillemets. |
| R | `packages/evals/src/vitest-evals/summary.ts:212` | Mesures appariées avec couverture explicite. |
| R | `.pi/extensions/tps.ts:13` | Mesurer le débit sur **l'intervalle effectif de génération**, pas la durée totale du run. |
| R | `scripts/cost.ts:52` · `scripts/session-transcripts.ts:37` | Ventilation temporelle ; transcript textuel par blocs bornés. |
| D | `scripts/read-tool-stats.mjs:182` | Détecter lectures complètes répétées et coût du contexte. |

### B3.9 — scripts d'opérabilité et CI

| S | Source | Notion |
|---|---|---|
| S | `scripts/check-entry-graphs.mjs:33` | **Tester les frontières d'import comme contrats d'architecture.** Rend mécaniques nos deux règles structurantes : `verifier` n'importe jamais le modèle, `bridge` jamais la boucle. |
| S | `scripts/check-runtime-deps.mjs:11` | Contrôler qu'une dépendance importée est déclarée au bon endroit. |
| S | `scripts/check-pinned-deps.mjs:5` | Contrôler les versions explicitement figées. Compense l'absence de lock du choix `pip`. |
| S | `scripts/profile-coding-agent-node.mjs:213` | Mesurer un démarrage avec **répétitions, warmup et statistiques**. Patron direct pour le spike Prefect. |
| S | `scripts/coding-agent-consumer.mjs:11` | Tester le package depuis un consommateur hors du dépôt. |
| S | `scripts/create-source-archive.sh:2` | Archive de source reproductible, contrôlée par empreinte. |
| S | `.github/workflows/ci.yml:1` | Chaîne de validation explicite en CI. |
| S | `LICENSE:12` | **Conserver la provenance lors d'une copie substantielle.** Pi est MIT ; vérifier aussi les éléments vendored. |
| R | `scripts/check-browser-smoke.mjs:6` | Smoke test d'un point d'entrée étroit dans son vrai environnement. |
| R | `scripts/check-lockfile-commit.mjs:5` | Rendre une dérive du lock visible à la revue. |
| R | `scripts/local-release.mjs:39` | Préparer un artefact de release vérifiable sans publication. |
| R | `scripts/generate-coding-agent-shrinkwrap.mjs:34` | Inventorier les scripts d'installation des dépendances. |

### B3.10 — Utilitaires purs candidats au produit

Douze utilitaires identifiés comme candidats à la boîte à outils MCP construite par la campagne — **à ne
retenir que lorsqu'un invariant métamorphique discriminant existe pour eux**, jamais par import opportuniste.

| Cible produit | Source | Notion |
|---|---|---|
| `core.json_canonical` | `packages/evals/src/vitest-evals/harness-table.ts:66` | Canonicalisation JSON |
| `core.jsonl_split` | `packages/coding-agent/src/modes/rpc/jsonl.ts:10` | Sérialisation et découpage stricts de records |
| `core.text_truncate` | `packages/agent/src/harness/utils/truncate.ts:132` | Troncature avec bilan octets/lignes |
| `core.text_diff` | `packages/coding-agent/src/core/tools/edit-diff.ts:365` | Diff textuel sans effet de bord |
| `core.ansi_strip` | `packages/coding-agent/src/utils/ansi.ts:46` | Nettoyage de séquences ANSI |
| `core.text_newlines` | `packages/coding-agent/src/core/tools/edit-diff.ts:19` | Normalisation des fins de ligne |
| `core.frontmatter` | `packages/coding-agent/src/utils/frontmatter.ts:29` | Extraction frontmatter + corps Markdown |
| `core.text_search` | `packages/tui/src/fuzzy.ts:12` | Recherche approximative à score explicable |
| `core.html_entities` | `packages/coding-agent/src/utils/html.ts:13` | Décodage d'entités HTML borné |
| `core.json_validate` | `packages/chord/src/json.ts:4` | Validation stricte de valeur JSON |
| `core.path_relation` | `packages/coding-agent/src/utils/paths.ts:108` | Relation lexicale entre chemins |
| `tools.search_files` | `packages/coding-agent/src/core/tools/grep.ts:70` | Recherche de fichiers bornée, sortie structurée |

**Plusieurs sont des candidats naturels au `round_trip`** — `json_canonical`, `jsonl_split`,
`text_newlines`, `frontmatter`, `html_entities` — ce qui en fait un noyau de départ crédible pour la
campagne, avec des invariants métamorphiques évidents.

## B4. Ce qui est écarté de Pi, et pourquoi

| Source | Raison |
|---|---|
| `packages/ai/src/providers/all.ts:48` | Catalogue multicloud et authentification associée. Hors souveraineté. |
| `packages/session-backends/sqlite-node/src/sqlite/storage.ts:49` | Backend SQLite hors périmètre — **les tests de contrats restent utiles**. |
| `packages/protocol/src/cbor/encoder.ts:211` | CBOR et protocole Pi ne remplacent pas MCP. |
| `packages/chord/src/api.ts:19` | Pas de runtime de plugins dans le marcheur. |
| `packages/coding-agent/src/experimental/mini/README.md:104` | Prototype `mini` : **fan-out quadratique et annulation incomplète**, documentés par ses propres auteurs. |
| `packages/coding-agent/src/experimental/radius-relay.ts:7` | Relais distant et coordination multi-processus, différés. |
| `packages/coding-agent/src/core/resolve-config-value.ts:10` | **Ne pas exécuter les commandes incluses dans une valeur de configuration.** Surface d'exécution non voulue. |
| `packages/coding-agent/examples/extensions/protected-paths.ts:19` | **Un filtre de sous-chaîne de chemin ne constitue pas une autorisation.** Contre-exemple à ne pas confondre avec la décision 12. |
| `packages/coding-agent/examples/extensions/permission-gate.ts:13` | Les regex de commandes dangereuses sont des exemples d'UI, pas une politique. |
| `packages/coding-agent/examples/extensions/gondolin/index.ts:47` | Sandbox / micro-VM : référence seulement, hors périmètre matériel. |
| `packages/tui/src/tui.ts:111` | Pas de seconde interface terminal complète. |
| `packages/coding-agent/examples/extensions/doom-overlay/README.md:1` | Démos, overlays et assets graphiques. |
| `scripts/release.mjs:28` | Release automatique npm/Git hors de notre broker. |
| `packages/coding-agent/src/modes/interactive/session-share.ts:25` | **Ne pas exporter les traces vers un service distant.** Contraire à la contrainte dure n°5. |
| `packages/coding-agent/examples/extensions/subagent/index.ts:34` | Sous-agents isolés : référence pour le mode `agentic` différé, pas une multiplication de Ling au socle. |

## B5. Les cinq reprises Pi qui changent la trajectoire

1. **Persister l'intention avant l'effet** — `drive/generation.ts:132`. Sans ça, une reprise ne peut pas
   distinguer *non commencé* d'*effet inconnu*, et rejouer devient un pari. C'est la brique qui rend la
   contrainte dure n°4 réellement tenable.

2. **`require` et non `prefer`** — `constrained-sampling.ts:208`. Un repli silencieux sur la contrainte de
   décodage ferait retomber la contrainte dure n°1 sans qu'aucune trace ne le signale.

3. **Annuler l'attente ne tue pas l'opération** — `abort.ts:17` et `write.ts:69`. Notre promesse de
   restauration à l'octet près est fausse tant qu'on n'attend pas la fin réelle de l'effet avant de restaurer.

4. **Empreinte de contrat plutôt qu'identifiant du modèle** — `harness-table.ts:105`. Ferme une classe de
   redondances que le rejet lexical de la décision 5 laisse passer.

5. **Frontières d'import testées comme contrats** — `check-entry-graphs.mjs:33`. Nos deux règles
   structurantes cessent d'être de la discipline et deviennent un test.

## B6. Ordre de portage Pi

| Phase | Reprises |
|---|---|
| **P0** | Contrats de frames et d'identités · commit JSONL validé · **détection sans réparation** de fin tronquée · framing LF · versions de format · usage en champs distincts · snapshots détachés |
| **P1** | Capture de sortie bornée · fin de processus ≠ fin de sorties · délais validés · conformité de stockage · injection de crash déterministe · matrice de reprise · faux provider scénarisé |
| **P2** | `require` sur le schéma · thinking séparé du contenu · terminaison explicite · budget réservant la sortie · retries SDK désactivés · préservation BOM/EOL · patch sans effet · exclusivité jusqu'à fin d'écriture · staging + rename |
| **P3** | Persistance de l'intention · réconciliation sur chemin distinct · admission fermée avant annulation · empreinte de contrat · canonicalisation JSON · provenance et collisions · intégrité avant activation |
| **P4** | Groupe de processus · précédence de configuration · permissions des secrets · enveloppe de commande et commande tardive · préflight dépôt sale |
| **P5** | Index mémoire reconstruit · catalogue vs détail · reducer pur · aplatissement d'arbre · échappement HTML · scripts de statistiques |
| **CI** | Frontières d'import · dépendances déclarées · versions figées · profil de démarrage avec warmup |

---

# PARTIE C — Kilo Code

## C1. Pourquoi ce dépôt

Monorepo **TypeScript** de ~1 M lignes, 34 paquets, fork d'OpenCode, bâti sur Effect-TS. **Licence MIT sans
ambiguïté** (`LICENSE:1-4`, `package.json:128`).

Rien ne se copie littéralement dans un harness Python. Ce qui s'extrait, ce sont des **mécanismes, seuils
nommés, taxonomies fermées et modes d'échec documentés**, souvent accompagnés du commentaire qui explique
l'incident les ayant produits. C'est un corpus de garde-fous industriels, pas une architecture à imiter.

**173 reprises**, chemins relatifs à `resources/kilocode-main/packages/`.

### C1.1 — La découverte : Kilo maintient une famille `ling` de bout en bout

**C'est l'apport le plus directement exploitable des trois sources.** Notre modèle de campagne est
`pithos/ling-3.0-tiny:8b-16k` ; Kilo a un prompt système dédié et des paramètres d'échantillonnage mesurés
pour cette famille.

| Élément | Source | Valeur |
|---|---|---|
| Détection de famille | `opencode/src/kilocode/model-match.ts:1-6` | `includes("ling")` moins une liste d'exclusions (`kling`, `bling`, `spelling`, `multilingual`) |
| Prompt dédié | `opencode/src/session/system.ts:62,86` → `prompt/ling.txt` | 129 lignes |
| `temperature` | `opencode/src/provider/transform.ts:605` | **0.3** |
| `top_p` | `opencode/src/provider/transform.ts:617` | **0.95** |
| `top_k` | `opencode/src/provider/transform.ts:629` | **20** |

Notre `ARCHITECTURE.md` ne fixait **aucun** paramètre d'échantillonnage. Ces trois valeurs sont un point de
départ mesuré par un tiers sur la même famille de modèle, retenu tel quel jusqu'à contre-mesure.

### C1.2 — `ling.txt` est un catalogue daté de modes d'échec de Ling

Sept nous concernent directement, **y compris en mode `direct` où le modèle n'a pas de tools**.

| Source | Mode d'échec observé | Conséquence pour nous |
|---|---|---|
| `ling.txt:109-115` | Ling **recopie les préfixes `N: ` de numérotation** dans son payload d'édition | Notre `codeview` rend des lignes numérotées : le splice AST doit **strip ces préfixes de `new_source` avant parse**, sinon tout échoue silencieusement |
| `ling.txt:23` | Ling **tronque le code généré** | Confirme la nécessité de distinguer `finish_reason: length` de `stop`, et impose une garde de complétude sur `new_source` |
| `ling.txt:21` | Ling émet des tours à **`content` vide** | Une réponse vide n'est pas une réponse : échec de nœud, jamais succès muet |
| `ling.txt:20,82` | Ling **appelle un outil pour signaler qu'il a fini** au lieu de s'arrêter | Mode de non-terminaison de v1 ; en `direct` il devient « renvoie une structure vide plutôt que signaler l'impossibilité » |
| `ling.txt:84` | Sur « No changes to apply », Ling **retente ou cherche autre chose à changer** | **Exactement la boucle stérile de v1.** Notre garde : un splice sans effet ⇒ nœud rouge immédiat, jamais une seconde tentative |
| `ling.txt:6,108` | Ling **omet un champ requis** et **abrège les noms de paramètres** (`old_string` pour `oldString`) | Justifie `response_format` strict, et un message d'erreur qui répète le nom exact attendu |
| `ling.txt:69` | Sur « vérifie », Ling **part chercher un fichier de spec externe** déduit du nom de fichier | Le contexte de nœud doit dire explicitement que le critère **est** l'invariant, et rien d'autre |

Deux notions de rédaction transposables telles quelles :

- `ling.txt:22-25` — **la politique de longueur est conditionnelle à la tâche** : réponse conversationnelle
  < 4 lignes, génération de code complète et non tronquée, tâche mixte = les deux règles. Une consigne
  « sois concis » unique est précisément ce qui fait tronquer un petit modèle.
- `ling.txt:49-59` — « Planning before coding » : lister les étapes en texte brut, court, puis les suivre
  dans l'ordre. C'est notre phase `decompose`, formulée en prompt.

### C1.3 — Ce que Kilo apporte que les deux autres sources n'ont pas

1. **La transactionnalité filesystem faite correctement** — dépôt Git fantôme comme snapshot,
   compare-and-swap sur contenu de fichier, verrou multi-processus à heartbeat. Villani copiait des fichiers
   dans un répertoire horodaté ; c'est strictement plus faible.
2. **Le confinement d'exécution sans conteneur** — `sandbox-exec` macOS plus une garde in-process sur chaque
   écriture. Notre `PROJECT.md` avait écarté le *runtime conteneurisé*, pas le sandbox natif.
3. **La normalisation de JSON Schema pour le décodage contraint** — le point exact du spike n°2.

**Ce que Kilo n'a pas non plus**, comme Villani et Pi : aucun invariant métamorphique, aucun mutation-check,
aucun catalogue de relations fermé. `verifier/relations`, `verifier/domains` et `verifier/mutation` restent
intégralement l'apport propre du projet.

## C2. Ce que la reprise a changé dans la documentation

| Cible | Nature du changement |
|---|---|
| `EXPLANATIONS.md` | Décisions 9 et 17 amendées · décisions 20 et 21 ajoutées |
| `PROJECT.md` | 2 critères ajoutés · précision de périmètre sur le sandbox natif |
| `ARCHITECTURE.md` | Paramètres d'échantillonnage fixés · sources de reprise |
| `ROADMAP.md` | Spike n°2 gagne un prérequis · items P0/P2/P4/P7 |

### C2.1 — Décision 9 amendée : le snapshot devient un dépôt Git fantôme

`opencode/src/snapshot/index.ts:107,111,406-408,465-501` — `git init` dans un `--git-dir` **hors projet**,
`write-tree` pour capturer, `read-tree` + `checkout-index` pour restaurer, **validation de tous les hashes
avant de toucher un seul fichier**, et échec fatal plutôt que restauration partielle.

Strictement supérieur au `CheckpointManager` par copie de Villani (`checkpoints.py:18-60`) : adressé par
contenu, dédupliqué, atomique, et gratuit à conserver dans le temps. Le dépôt fantôme vit hors du workspace,
donc il n'apparaît jamais dans `git status` du produit ni dans les diffs de la campagne.

**Complément indispensable — `writeIfUnchanged`** (`core/src/file-mutation.ts:144-158`), un
**compare-and-swap sur le contenu**, sous verrou par chemin canonique et section `uninterruptible`
(`:79-83`). Notre contrainte dure n°3 couvre la restauration ; elle ne couvre pas la **détection d'un
changement concurrent au moment d'écrire**. Un CAS transforme « on a écrasé quelque chose sans le savoir »
en `StaleContentError` typé. Ni Villani ni v1 ne l'ont.

### C2.2 — Décision 17 amendée : normaliser le schéma avant de le contraindre

`opencode/src/tool/json-schema.ts:28-88` — **c'est l'outillage manquant du spike n°2.**

Pydantic v2 émet des `$defs` et des `$ref` pour toute enum et tout modèle imbriqué — donc pour
`Criterion.relation`, `Criterion.domain` et toute structure de `Proposal`. Les backends de décodage
contraint s'en accommodent mal, et un `integer` sans bornes fait échouer certaines grammaires.

Conséquence directe : **`Criterion.model_json_schema()` ne peut pas être envoyé tel quel.** La contrainte
dure n°1 repose sur un schéma que le serveur accepte réellement ; la normalisation doit être écrite et testée
**avant** de mesurer `response_format` avec Ling. Le spike n°2 gagne donc un prérequis.

### C2.3 — Décision 20 : le prompt et les paramètres sont des données mesurées, pas des réglages

Trois valeurs d'échantillonnage — `temperature 0.3`, `top_p 0.95`, `top_k 20` — mesurées par un tiers sur
notre famille de modèle exacte, et un catalogue de sept modes d'échec observés avec leurs contre-mesures.

Le point de méthode : **ces valeurs sont versionnées comme une donnée du projet, pas dispersées dans le
code**, et toute modification exige une contre-mesure. Deux des sept modes d'échec touchent le chemin
nominal et doivent être traités **avant la première ligne du `bridge`** :

- le strip des préfixes `N: ` sur `new_source` — sans lui, chaque splice échoue au parse ;
- la garde de complétude contre la troncature — sans elle, un `def` tronqué mais syntaxiquement valide passe.

Le mode `ling.txt:84` est le plus important pour l'architecture : **sur « aucun changement à appliquer »,
Ling retente ou cherche autre chose à changer.** C'est le générateur de la boucle stérile de v1, documenté
indépendamment sur le même modèle. Notre garde est déjà posée (décision 13, patch sans effet ⇒ nœud rouge) ;
cette observation la confirme comme non négociable.

### C2.4 — Décision 21 : confinement d'exécution sans conteneur

Notre `verifier` exécute du code écrit par le modèle en `subprocess`. `PROJECT.md` a écarté le **runtime
conteneurisé** — mesuré inexploitable sur ce matériel en v1 — mais pas le confinement natif.

`kilo-sandbox/` fournit `sandbox-exec` macOS : natif, zéro installation, et **le profil de base — la partie
coûteuse à dériver — est fourni** (`seatbelt-base.ts:1-4`). Doublé d'une garde in-process sur chaque
opération d'écriture, avec refus des descripteurs de fichier inscriptibles (`filesystem.ts:107-158`).

Placé en **P7** : le sandbox conditionne l'exécution autonome non supervisée, pas le socle. Il remonte en P2
si le premier réveil supervisé montre que le `verifier` exécute du code produit touchant des chemins
inattendus.

### C2.5 — Critères de socle ajoutés

- **Une écriture concurrente est détectée au moment d'écrire**, pas seulement réparée après : un
  compare-and-swap sur le contenu snapshoté échoue en `StaleContentError` typé.
- **Le schéma envoyé au modèle est normalisé et testé** : `$defs`/`$ref` résolus, bornes explicites,
  vérifié contre le backend réel avant toute campagne.

## C3. Catalogue complet des reprises

### C3.1 — `kernel`

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `contracts` | `core/src/util/error.ts:3-72` | `NamedError.create` — classe d'erreur portant **un schéma**, forme filaire `{name, data}`, et `isInstance` testant **par nom, pas par prototype**. Une erreur sérialisée en JSONL et relue par le dashboard reste identifiable. | Traduire |
| `contracts` | `opencode/src/mcp/index.ts:107-128` | `Status` = union discriminée fermée `connected`/`disabled`/`failed(error)`/`needs_auth`/`needs_client_registration`. **La santé d'un serveur est une énumération, pas un booléen.** Modèle du statut de `ToolEntry`. | Traduire |
| `contracts` | `opencode/src/worktree/index.ts:49-88` | Sept erreurs typées pour un module de 630 L, unionées en un type `Error`. Taxonomie d'échec **par opération**, pour que l'appelant branche. | Inspirer |
| `contracts` | `kilo-memory/src/schema.ts:187-227` | `parse()` défensif : un coerceur par type avec fallback, et **une version incompatible lève** au lieu d'être coercée silencieusement. Modèle du `from_dict` de `Node`. | Traduire |
| `contracts` | `kilo-memory/src/schema.ts:174-185` | `persist()` **omet délibérément les `limits`** : constantes du harness, jamais relues du disque. Séparer dans un même fichier d'état ce que l'opérateur possède de ce que le harness possède. | Traduire |
| `contracts` | `kilo-memory/src/schema.ts:206-211` | Planchers à 1000 ms sur `minIntervalMs`/`timeoutMs` : **un zéro dans un champ de budget est un interrupteur silencieux**. Applicable à notre borne murale et à l'intervalle de réveil. | Traduire |
| `contracts` | `kilo-memory/src/schema.ts:14` | « Topics are assigned **by rule (never by the LLM)** ». Confirmation externe de notre contrainte dure n°1, écrite par un tiers. | Inspirer |
| `codeview` | `opencode/src/tool/read.ts:394-435` | `collect()` — lecture en flux avec **trois plafonds indépendants** : lignes, `MAX_LINE_LENGTH = 2000`, `MAX_BYTES = 50 KB`. Retourne `cut` et `more` **distincts**. | Traduire |
| `codeview` | `opencode/src/tool/read.ts:352-364` | Lignes préfixées `N: ` et **marqueur de fin explicite** `(End of file - total N lines)`. Le modèle sait s'il a tout vu. À croiser avec `ling.txt:109`. | Traduire |
| `codeview` | `opencode/src/tool/read.ts:146-190` | `isBinaryFile` — extensions, puis BOM UTF-16/32, puis octet NUL, puis **> 30 % de non-imprimables**. Quatre passes, aucune dépendance. | Traduire |
| `codeview` | `opencode/src/util/filesystem.ts:210-262` | `findUp`/`up`/`globUp` — remontée vers une racine d'arrêt, avec `rootFirst` pilotant la précédence. Mécanisme des règles par répertoire. | Traduire |
| `codeview` | `core/src/util/hash.ts:3-11` | `Hash.fast` (SHA-1, clés de cache) vs `Hash.sha256` (contenu). **Deux intentions nommées** plutôt qu'un hash générique. | Traduire |
| `journal` | `opencode/src/util/filesystem.ts:84-113` | Écriture atomique par temporaire + `rename`, nom temporaire portant **pid + timestamp + suffixe aléatoire** ; `ENOENT` ⇒ `mkdir -p` puis retente. Sérialisation de `tree.json` et `registry.json`. | Traduire |
| `journal` | `opencode/src/bus/index.ts:41-56` | Le commentaire **est** la notion : `subscribe` acquiert l'abonnement **au `yield*`, pas à la première lecture**, la forme paresseuse perdant les publications intermédiaires. Tests « RACE » dédiés. Piège d'un bus + tail de dashboard. | Traduire |
| `journal` | `opencode/src/bus/index.ts:75-89` | Le finaliseur **publie `InstanceDisposed` avant d'éteindre le PubSub**. Un flux se termine toujours par un événement terminal, jamais par du silence. | Traduire |
| `journal` | `opencode/src/storage/storage.ts:53-64` | Stockage minimal `read`/`write`/`update(key, fn)`/`list(prefix)`/`remove`, clé = `string[]` → chemin. **Une clé hiérarchique est un chemin ; le magasin est un arbre de JSON.** | Traduire |
| `journal` | `opencode/src/storage/storage.ts:81` | `MIGRATIONS` — tableau ordonné avec compteur entier persisté. Nécessaire à `journals/` et au format de `registry.json`. | **Écarté** |
| `journal` | `opencode/src/storage/storage.ts:67-73` | `missing(err)` — normalise « fichier absent » à travers `ENOENT` **et** l'erreur typée. Deux formes d'absence, un seul prédicat. | Traduire |
| `kernel` | `core/src/util/token.ts:3-5` | `CHARS_PER_TOKEN = 4` — grossier, mais **une seule constante partagée** par tout le budget de contexte. À fixer pour Ling. | Traduire |
| `kernel` | `core/src/util/wildcard.ts:3-14` | Glob → RegExp en 12 lignes. Subtilité : un motif finissant par `" .*"` devient `"( .*)?"`, donc **`"git diff *"` matche aussi `"git diff"` sans argument**. | Traduire |
| `kernel` | `core/src/policy.ts:36-42` | `evaluate(action, resource, fallback)` — `findLast` sur des statements wildcard, **fallback fourni par l'appelant**. Moteur allow/deny complet en 49 lignes. | Traduire |
| `kernel` | `opencode/src/session/summary.ts:12-70` | `unquoteGitPath` — décodage octal C **à la frontière d'affichage**. Évitable en amont par le prélude git (`git/index.ts:6-18`). | Inspirer |

### C3.2 — `verifier`

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `gates` | `opencode/src/lsp/diagnostic.ts:3-28` | `report()` — **seules les erreurs (`severity === 1`) sont montrées au modèle**, plafonnées à `MAX_PER_FILE = 20`, suivies de `... and N more`, dans un bloc `<diagnostics file="...">`. Les avertissements sont du bruit pour un 8B ; la troncature est visible. **Format cible de notre rendu d'échec d'invariant.** | Traduire |
| `gates` | `opencode/src/tool/truncate.ts:87-149` | Au-delà des plafonds, **le texte intégral est écrit dans un fichier** et l'aperçu porte son chemin plus l'instruction pour le récupérer. Rien n'est jamais détruit. | Traduire |
| `gates` | `opencode/src/tool/truncate.ts:14-15` | `MAX_LINES = 2000` **et** `MAX_BYTES = 50 KB` : deux plafonds appliqués, et le message dit **lequel** a été atteint. | Traduire |
| `gates` | `opencode/src/tool/truncate.ts:131-137` | L'instruction de récupération **s'adapte à ce que l'appelant peut faire**. | Inspirer |
| `gates` | `opencode/src/tool/truncate.ts:12,53-66` | Rétention 7 jours purgée **par mtime** sur une boucle horaire forkée dont l'échec est journalisé, jamais propagé. | Traduire |
| `gates` | `opencode/src/git/index.ts:6-18` | **Chaque invocation de git reçoit un prélude fixe** : `--no-optional-locks`, `core.autocrlf=false`, `core.fsmonitor=false`, `core.longpaths=true`, `core.quotepath=false`. Rend git déterministe quelle que soit la config utilisateur. | Traduire |
| `gates` | `opencode/src/git/index.ts:22-30` | `fail(err)` — un échec de *spawn* normalisé en `{exitCode: 1, stderr}`. **Les appelants n'ont jamais deux formes d'erreur.** | Traduire |
| `gates` | `opencode/src/git/index.ts:64-70,128` | `maxOutputBytes` par exécution, `truncated` porté dans le résultat. **Le lanceur de processus borne, l'appelant sait.** | Traduire |
| `gates` | `opencode/src/git/index.ts:80-101` | `kind(code)` — code porcelain → `added`/`deleted`/`modified`, avec `??` et `U` traités explicitement. | Traduire |
| `gates` | `opencode/src/format/index.ts:44-52,74-119` | Formatteurs déclarés par extension avec détection de disponibilité, exécutés après édition ; échec journalisé, jamais fatal. | Adapter |
| `verifier` | `http-recorder/src/matching.ts:73-106` | Appariement de requêtes enregistrées : méthode, URL normalisée, corps canonicalisé. Base d'un faux bridge rejouable. | Adapter |
| `verifier` | `http-recorder/src/cassette.ts:17-51` | Cassettes versionnées avec rédaction des secrets à l'enregistrement. | Adapter |
| `verifier` | `http-recorder/` (1 579 L) | Paquet entier : cassettes HTTP + WebSocket, appariement, rédaction, versionnement. Modèle pour rejouer une campagne sans Ollama. | Adapter |
| `verifier` | `opencode/src/session/retry.ts:35-176` | Classification d'erreur séparée de la politique, backoff borné, annulation propagée. Convergent avec `pi/retry.ts:163,224`. | Traduire |

### C3.3 — `bridge`

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `bridge` | `opencode/src/tool/json-schema.ts:28-88` | **`normalize()` — l'outillage manquant du spike n°2.** Résolution des `$defs`/`$ref` que Pydantic v2 émet pour toute enum et tout modèle imbriqué. | Traduire |
| `bridge` | `opencode/src/tool/json-schema.ts:83-85` | Un `integer` sans bornes fait échouer certaines grammaires de décodage contraint : bornes explicites obligatoires. | Traduire |
| `bridge` | `opencode/src/tool/json-schema.ts:121-158` | Validation du schéma résultant avant envoi. | Traduire |
| `bridge` | `opencode/src/tool/json-schema.ts:8-19` | Sous-ensemble de mots-clés réellement supporté, déclaré explicitement. | Traduire |
| `bridge` | `opencode/src/provider/transform.ts:588-631` | **`temperature 0.3`, `top_p 0.95`, `top_k 20` pour la famille `ling`.** Mesuré par un tiers sur notre modèle. | Traduire |
| `bridge` | `opencode/src/session/system.ts:46-88` · `kilocode/model-match.ts:1-6` | Sélection du prompt par famille de modèle, avec liste d'exclusions (`kling`, `bling`, `spelling`, `multilingual`). | **Écarté** |
| `bridge` | `opencode/src/session/prompt/ling.txt` (129 L) | **Le catalogue des modes d'échec de Ling et leurs contre-mesures.** Voir § C1.2. | Traduire |
| `bridge` | `opencode/src/provider/transform.ts:28-29,171-196` | Transformations par fournisseur isolées derrière une frontière unique. | **Écarté** |
| `bridge` | `opencode/src/provider/transform.ts:294-306,464-498` | Normalisation des messages et des blocs de contenu avant envoi. | **Écarté** |
| `bridge` | `opencode/src/session/overflow.ts:11-20` | Détection de dépassement de contexte séparée des autres erreurs. Convergent avec `pi/overflow.ts:134`. | Traduire |
| `bridge` | `opencode/src/tool/tool.ts:25-33,100-142` | Contrat d'outil : schéma, description, exécution, et validation d'entrée séparée de l'exécution. | Adapter |
| `bridge` | `codemode/src/tool-schema.ts:35-107` | Génération de schéma depuis des types, avec sous-ensemble contrôlé. | Inspirer |
| `bridge` | `opencode/src/provider/transform.ts:21` | Point d'entrée unique de toute transformation sortante. | Traduire |

### C3.4 — `workspace`

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `snapshot` | `opencode/src/snapshot/index.ts:107,111` | **`git init` dans un `--git-dir` hors projet** — le dépôt fantôme n'apparaît jamais dans le `git status` du produit. | **Reporté** |
| `snapshot` | `opencode/src/snapshot/index.ts:406-408` | `write-tree` pour capturer : adressé par contenu, dédupliqué, gratuit à conserver. | **Reporté** |
| `snapshot` | `opencode/src/snapshot/index.ts:465-501` | `read-tree` + `checkout-index` pour restaurer, avec **validation de tous les hashes avant de toucher un fichier** et **échec fatal plutôt que restauration partielle**. | **Reporté** |
| `snapshot` | `opencode/src/snapshot/index.ts:526-547` | Nettoyage borné des snapshots anciens. | **Reporté** |
| `snapshot` | `opencode/src/snapshot/index.ts:46,297-315` | Capture incrémentale sur les seuls chemins déclarés. | **Reporté** |
| `snapshot` | `opencode/src/snapshot/index.ts:44,336-355` | Comparaison de deux snapshots sans matérialiser les fichiers. | **Reporté** |
| `snapshot` | `opencode/src/snapshot/index.ts:216-217` | Exclusions explicites du snapshot. | **Reporté** |
| `snapshot` | `opencode/src/session/revert.ts:78-118` | Revert par snapshot avec vérification préalable et journalisation de ce qui a été restauré. | **Reporté** |
| `workspace` | `core/src/file-mutation.ts:144-158` | **`writeIfUnchanged` — compare-and-swap sur le contenu.** Transforme « on a écrasé sans le savoir » en `StaleContentError` typé. | Traduire |
| `workspace` | `core/src/file-mutation.ts:79-83` | Verrou par **chemin canonique** et section `uninterruptible` autour de l'écriture. | Traduire |
| `workspace` | `core/src/file-mutation.ts:53-66,124-142,198-204` | Résolution de chemin, création de parents, nettoyage sur échec. | Traduire |
| `workspace` | `opencode/src/tool/edit.ts:744-764` | Détection d'un fichier modifié depuis la lecture, avant application. | Traduire |
| `workspace` | `opencode/src/tool/edit.ts:49-72,117-125,164-166` | Contrats d'édition : unicité du motif, refus si ambigu, comptage des occurrences. | Traduire |
| `workspace` | `opencode/src/tool/edit.ts:222-228` | Refus d'une édition sans effet. | Traduire |
| `workspace` | `opencode/src/tool/edit.ts:30-46` | Rendu du diff d'une édition pour la trace. | Traduire |
| `workspace` | `opencode/src/patch/index.ts:398-425,460-484` | Application de patch avec validation préalable de toutes les hunks. | Traduire |
| `workspace` | `opencode/src/patch/index.ts:48-53,176-183,575-684` | Parsing strict, normalisation des chemins, gestion des fins de ligne. | Traduire |
| `workspace` | `opencode/src/tool/read.ts:88-101,251-263` | Lecture bornée avec offset et limite, refus des fichiers binaires. | Traduire |
| `sandbox` | `kilo-sandbox/src/seatbelt-base.ts:1-4` | **Le profil `sandbox-exec` de base** — la partie coûteuse à dériver, fournie. | Traduire |
| `sandbox` | `kilo-sandbox/src/seatbelt.ts:34-73` | Composition du profil : racines autorisées en lecture, en écriture, réseau. | Traduire |
| `sandbox` | `kilo-sandbox/src/seatbelt.ts:46` | Détection de disponibilité de `sandbox-exec` avant de s'y fier. | Traduire |
| `sandbox` | `kilo-sandbox/src/profile.ts:1-33` | Profil déclaratif compilé vers la syntaxe seatbelt. | Traduire |
| `sandbox` | `kilo-sandbox/src/path.ts:11-33` | Normalisation des chemins pour le profil. | Traduire |
| `sandbox` | `kilo-sandbox/src/context.ts:16-70` | Contexte d'exécution confinée : racines, variables, cwd. | Traduire |
| `sandbox` | `kilo-sandbox/src/filesystem.ts:107-230` | **Garde in-process sur chaque opération d'écriture**, en complément du sandbox OS. | Traduire |
| `sandbox` | `kilo-sandbox/src/filesystem.ts:151-158` | **Refus des descripteurs de fichier inscriptibles.** | Traduire |
| `sandbox` | `kilo-sandbox/src/backend.ts:32-73` | Abstraction du backend de confinement, avec repli explicite si indisponible. | Adapter |
| `sandbox` | `opencode/src/kilocode/sandbox/config.ts:39-60` | Configuration du sandbox par déclaration, pas par code. | Adapter |
| `permission` | `opencode/src/permission/index.ts:102-154` | Évaluation de permission avec raison, ordre de précédence, et `ask` par défaut. | **Écarté** |
| `permission` | `opencode/src/permission/index.ts:314-332,470-476` | Réponses persistées et portée d'une autorisation. | **Écarté** |
| `permission` | `opencode/src/permission/arity.ts:1-161` | **Arité des commandes shell** : combien d'arguments une commande accepte, pour détecter une injection par argument surnuméraire. | **Écarté** |
| `permission` | `opencode/src/tool/shell.ts:280-285,387-457` | Découpage d'une ligne shell en commandes, avec opérateurs et substitutions traités explicitement. | **Écarté** |
| `permission` | `opencode/src/agent/subagent-permissions.ts:14-27` | Permissions d'un sous-agent dérivées de celles du parent, jamais élargies. | **Écarté** |
| `workspace` | `opencode/src/skill/discovery.ts:72-152` | Découverte de capacités avec précédence par répertoire et détection de collision. | Adapter |

### C3.5 — `engine`

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `context` | `opencode/src/session/compaction.ts:269-324` | Compaction avec **frontières de tour préservées** et résumé inséré, jamais une troncature au milieu. | Traduire |
| `context` | `opencode/src/session/compaction.ts:207-264,123-146` | `select()` + `splitTurn()` — **la queue conservée est choisie par unités atomiques**, pas par nombre de messages. | Traduire |
| `context` | `opencode/src/session/compaction.ts:43,97-102,304-305` | Seuils de déclenchement nommés et budget réservé au résumé. | Traduire |
| `context` | `opencode/src/session/compaction.ts:78-94,348-390,490-500` | Marquage des messages compactés, idempotence de la compaction, garde contre la double compaction. | Traduire |
| `context` | `kilo-memory/src/recall/recall.ts:141-238` | Rappel de mémoire par pertinence avec budget, et **traçabilité de ce qui a été rappelé et pourquoi**. | Adapter |
| `context` | `core/src/instruction-context.ts:30-72` | Assemblage des instructions par provenance et précédence déterministes. | Traduire |
| `walk` | `opencode/src/session/run-state.ts:56-73,139-168` | État de run explicite avec transitions nommées et persistance. | Traduire |
| `walk` | `opencode/src/agent/agent.ts:168-329` | Définition d'agent : outils autorisés, modèle, prompt, budget — **par déclaration, pas par code**. | Adapter |
| `walk` | `opencode/src/agent/agent.ts:445-459,515-521` | Résolution de l'agent effectif et héritage de configuration. | Adapter |
| `walk` | `opencode/src/tool/task.ts:36-95` | Délégation à une sous-tâche avec budget propre et résultat structuré. | Adapter |
| `engine` | `opencode/src/question/index.ts:28-32,90-124` | Question à l'opérateur comme **objet persistant avec cycle de vie**, pas comme un prompt bloquant. Modèle pour la proposition d'arrêt. | Traduire |

### C3.6 — `campaign`

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `registry` | `opencode/src/tool/registry.ts:332-374` | Registre d'outils avec résolution par nom, détection de collision et provenance. | Traduire |
| `registry` | `opencode/src/permission/index.ts:505-549` | Portée d'une autorisation liée à une ressource identifiée. | Adapter |
| `registry` | `opencode/src/mcp/index.ts:64-128` | Cycle de vie d'un serveur MCP et **statut en union fermée**. | Traduire |
| `proposals` | `kilo-memory/src/recall/topics.ts:21,26-96` | **Moteur lexical sans dépendance** : recouvrement de termes tolérant aux formes fléchies. Socle du rejet de proposition redondante, meilleur que `difflib` seul. | Traduire |
| `proposals` | `kilo-memory/src/recall/recall.ts:168-192` | Scoring de pertinence explicable, chaque contribution nommée. | Adapter |
| `proposals` | `http-recorder/src/matching.ts:11-36` | Canonicalisation avant comparaison. Convergent avec `pi/harness-table.ts:66`. | Traduire |
| `campaign` | `opencode/src/skill/index.ts:71-77,110-147,186-190` | Chargement de capacités, validation du frontmatter, activation. | Adapter |
| `config` | `opencode/src/config/parse.ts:8-72` | Parsing de configuration avec erreurs portant scope et chemin. | Traduire |
| `config` | `opencode/src/config/variable.ts:43-118` | Substitution de variables **bornée**, sans exécution de commande. Contre-exemple utile face à `pi/resolve-config-value.ts:10`. | Traduire |
| `config` | `opencode/src/config/managed.ts:20-68` | **Couche de configuration écrite par le runtime**, distincte de celle de l'opérateur. Convergent avec `pi/mcp.ts:27` et notre décision 7. | Traduire |

### C3.7 — `lifecycle` et `broker`

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `verrou` | `core/src/util/flock.ts:148-240` | **Verrou de fichier à heartbeat et verrou breaker.** Notre `RunLock` v1 décide de la péremption par liveness de PID : deux prétendants peuvent conclure simultanément que le verrou est périmé et le casser ensemble. Le heartbeat règle l'éviction à tort d'une section longue, le breaker règle la course. | Traduire |
| `verrou` | `core/src/util/flock.ts:25-37,103-107` | Écriture en `wx` pour détecter un verrou compromis. | Traduire |
| `verrou` | `core/src/util/flock.ts:212-221` | Libération sûre même après péremption constatée. | Traduire |
| `git` | `opencode/src/git/index.ts:6-18` | Prélude fixe rendant git déterministe. Voir § C3.2. | Traduire |
| `git` | `opencode/src/worktree/index.ts:102-113` | Création de worktree isolée avec nettoyage garanti. | Adapter |
| `telegram` | `kilo-memory/src/capture/redact.ts:2-42,44-79,105-111` | **Rédaction de secrets** par motifs nommés, appliquée avant persistance. À appliquer à nos deux frontières brokerisées et à des JSONL qui ne sont jamais effacés. | Traduire |
| `lifecycle` | `core/src/util/retry.ts:9-24` | Backoff borné réutilisable. | Traduire |
| `lifecycle` | `core/src/util/which.ts:6-16` | Résolution d'exécutable dans le `PATH`, sans shell. | Traduire |
| `lifecycle` | `opencode/src/kilocode/sandbox/network.ts:13-23` | Politique réseau du sandbox : allowlist explicite. | Adapter |

### C3.8 — `observatory`

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `observatory` | `opencode/src/session/summary.ts:85-99,170-176` | Résumé de session dérivé des événements, avec champs absents laissés absents. | Traduire |
| `observatory` | `opencode/src/lsp/diagnostic.ts:20-28` | Format de rendu des diagnostics, réutilisable pour l'affichage d'un échec d'invariant. | Traduire |
| `observatory` | `core/src/util/error.ts:3-72` | Erreurs identifiables par nom après sérialisation. Voir § C3.1. | Traduire |
| `observatory` | `opencode/src/bus/index.ts:41-89` | Abonnement sans trou et terminaison explicite. Voir § C3.1. | Traduire |
| `observatory` | `opencode/src/storage/storage.ts:53-58` | Magasin arborescent de JSON, lisible sans outil. | Traduire |
| `observatory` | `http-recorder/` | Rejeu d'une campagne complète sans Ollama, pour développer le dashboard. | Adapter |

### C3.9 — Le produit

| Cible | Source | Notion |
|---|---|---|
| `tools/<outil>.py` | `opencode/src/tool/tool.ts:53-64` | Contrat minimal d'un outil : nom, description, schéma, exécution. |
| `tools/<outil>.py` | `opencode/src/tool/json-schema.ts:8-118` | Génération et normalisation du schéma exposé. |
| `core/<outil>.py` | `opencode/src/mcp/index.ts:181-185` | Frontière entre le cœur pur et la coquille protocolaire. |

## C4. Ce qui est écarté de Kilo Code, et pourquoi

| Source | Poids | Raison |
|---|---:|---|
| `opencode/src/tool/edit.ts:271-671` | 400 L | **Neuf stratégies de remplacement flou en cascade.** Contredit frontalement « le modèle renvoie une fonction, pas un diff » et notre splice AST exact. Même verdict que le fuzzy de Villani et de Pi — **trois sources, trois fois écarté**. |
| `opencode/src/patch/index.ts:486-511` | — | `generateUnifiedDiff` — le commentaire l'avoue : *« Simple diff generation - in a real implementation... »*. |
| `kilo-indexing/` | 23 611 L | Indexation sémantique par embeddings, magasins vectoriels (Qdrant, LanceDB), six fournisseurs. Hors périmètre et hors souveraineté. |
| `codemode/src/interpreter/runtime.ts` | 3 465 L | **Interpréteur JavaScript embarqué** permettant au modèle d'appeler les outils par code. Surface d'exécution exactement contraire à la décision 6. |
| `opencode/src/kilocode/` | 51 895 L | Surface produit propre à Kilo : Agent Manager, cloud, presence, board, claw, console, daemon. |
| `kilo-vscode/`, `tui/`, `ui/`, `session-ui/`, `kilo-ui/`, `kilo-web-ui/`, `storybook/` | 265 110 L+ | Interfaces. Nous avons React porté de v1. |
| `kilo-gateway/`, `provider/provider.ts`, `plugin/{xai,openai,digitalocean,...}` | 2 137 L+ | Catalogue multicloud et authentification. Hors souveraineté — même verdict que `pi/providers/all.ts:48`. |
| `mcp/oauth-provider.ts`, `oauth-callback.ts`, `auth.ts`, `core/src/oauth/` | — | OAuth pour serveurs MCP distants. Nos outils sont locaux. |
| `opencode/src/lsp/` | 3 339 L | Client LSP complet. Notre `verifier` n'a pas besoin d'un serveur de langage — **sauf le format de rendu des diagnostics, repris**. |
| `effect-drizzle-sqlite/`, `effect-sqlite-node/`, `storage/db.ts` | — | Couche SQLite. Écartée explicitement par la décision 10. |
| `kilo-jetbrains/`, `containers/`, `nix/`, `acp/`, `share/`, `sync/` | — | Intégrations et distribution. |

## C5. Les six reprises Kilo qui changent la trajectoire

1. **Le prompt Ling et ses paramètres d'échantillonnage** — `prompt/ling.txt`, `transform.ts:605,617,629`.
   Un tiers a documenté sept modes d'échec de **notre modèle exact** et les a chiffrés (`0.3 / 0.95 / 20`).
   Deux touchent le chemin nominal : les préfixes `N: ` recopiés, et la troncature du code généré.
   **À traiter avant d'écrire la première ligne du `bridge`.**

2. **Le snapshot est un dépôt Git fantôme** — `snapshot/index.ts:107-111,406-408,465-501`. Adressé par
   contenu, dédupliqué, atomique, validation de tous les hashes avant de toucher un fichier. Strictement
   supérieur au `CheckpointManager` par copie de Villani.

3. **`normalize()` de JSON Schema** — `tool/json-schema.ts:28-88`. **L'outillage manquant du spike n°2**,
   à porter avant même de tester `response_format` avec Ling.

4. **Le confinement d'exécution sans conteneur** — `kilo-sandbox/`. `sandbox-exec` natif macOS, profil de
   base fourni, doublé d'une garde in-process. **Notre `PROJECT.md` avait écarté les conteneurs, pas ceci.**

5. **`writeIfUnchanged` — le compare-and-swap sur fichier** — `file-mutation.ts:144-158,79-83`. Notre
   contrainte n°3 couvre la restauration, pas la détection d'un changement concurrent **au moment d'écrire**.

6. **Le verrou à heartbeat et breaker** — `flock.ts:148-240`. Notre `RunLock` v1 décide par liveness de PID :
   deux prétendants peuvent casser le verrou simultanément. Régime nominal = réveil launchd toutes les trois
   heures sans humain devant la machine.

**Deux mentions honorables, gratuites** : le moteur lexical de `recall/topics.ts` comme socle du rejet de
redondance, et `capture/redact.ts` appliqué à nos deux frontières brokerisées et à des JSONL jamais effacés.

## C6. Ordre de portage Kilo

Chemins relatifs à `resources/kilocode-main/packages/`.

| Phase | Reprises |
|---|---|
| **S — spikes** | `opencode/src/tool/json-schema.ts:8-158` **avant tout test de `response_format`** · `provider/transform.ts:588-631` · `session/prompt/ling.txt` · `kilocode/model-match.ts:1-6` |
| **P0** | `util/filesystem.ts:84-113,210-262` · `core/src/util/error.ts:3-72` · `token.ts:3-5` · `wildcard.ts:3-14` · `hash.ts:3-11` · `storage/storage.ts:53-81` · `bus/index.ts:41-89` · `kilo-memory/src/schema.ts:174-227` · `mcp/index.ts:107-128` |
| **P1** | `lsp/diagnostic.ts:3-28` · `tool/truncate.ts:12-15,87-149` · `git/index.ts:6-30,64-101` · `http-recorder/` · `session/retry.ts:35-176` · `format/index.ts:44-52,74-119` |
| **P2** | `snapshot/index.ts` entier · `session/revert.ts:78-118` · `core/src/file-mutation.ts:32-204` · `tool/edit.ts:49-72,119-125,744-764` · `patch/index.ts:48-53,176-183,398-425,460-484` · `tool/read.ts:88-101,146-190,251-435` · `session/compaction.ts:43,97-146,207-324,490-500` · `core/src/instruction-context.ts:30-72` · `session/overflow.ts:11-20` |
| **P3** | `kilo-memory/src/recall/topics.ts:21-96` · `recall/recall.ts:141-238` · `skill/index.ts:71-147` · `config/parse.ts:8-72` · `config/variable.ts:43-118` · `config/managed.ts:20-68` |
| **P4** | `core/src/util/flock.ts:25-37,103-240` · `kilo-memory/src/capture/redact.ts:2-111` · `util/retry.ts:9-24` · `util/which.ts:6-16` · `worktree/index.ts:102-113` · `session/run-state.ts:139-168` · `question/index.ts:28-32,90-124` |
| **P5** | `session/summary.ts:85-99,170-176` · `tool/edit.ts:30-46` · `storage/storage.ts:53-58` |
| **P6** | `tool/registry.ts:332-374` · `permission/index.ts:102-154,470-549` · `permission/arity.ts:1-161` · `agent/agent.ts:168-329,445-521` · `agent/subagent-permissions.ts:14-27` · `skill/discovery.ts:72-152` |
| **P7** | `kilo-sandbox/` entier · `kilocode/sandbox/config.ts:39-60` · `tool/shell.ts:139-143,280-285,387-457` |

Le sandbox est en **P7** parce qu'il conditionne l'exécution autonome non supervisée, pas le socle. Il
remonte en **P2** si le premier réveil supervisé montre que le `verifier` exécute du code produit touchant
des chemins inattendus.

## C7. Attribution

**MIT** — `Copyright (c) 2026 Kilo Code`, `Copyright (c) 2025 opencode`. Aucune restriction sur les entrées
*Copier*. Conserver l'attribution MIT en en-tête de tout module porté quasi littéralement : en pratique
`kilo-sandbox/src/seatbelt-base.ts` (le profil), `core/src/util/flock.ts` (le verrou) et
`opencode/src/tool/json-schema.ts` (la normalisation de schéma).

---

# PARTIE D — Ouroboros

## D1. Pourquoi ce dépôt

Agent généraliste open-source à identité persistante et **base de code auto-modifiante**, publié par Anton
Razzhigaev (AIRI) avec un papier associé — *« Ouroboros: A Self-Developing Frontier Coding Agent with
Reviewed Core Evolution »*, 🔗 [arXiv 2608.08311](https://arxiv.org/abs/2608.08311). Version inspectée 6.114.0.
**MIT**, `Copyright (c) 2026 Anton Razzhigaev`.

| | Lignes | Remarque |
|---|---:|---|
| Runtime `ouroboros/` | 222 035 | **Python 3.10+, tout est portable** |
| `supervisor/` | 27 922 | queue, workers, git, cycle de vie |
| Tests | 332 108 | **ratio test/runtime ≈ 1,3** |
| Documentation + `BIBLE.md` | 10 011 | dont `ARCHITECTURE.md` = 688 Ko |

Résultats auto-reportés avec traces publiques : Terminal-Bench 2.1 à **86,74 %** avec Opus-5 (Claude Code +
Fable 5 : 83,8 %), OSWorld-Verified à **90,69 %**, CL-Bench rang 1. Chaque ligne se lit « modèle **plus**
harness » — la thèse de Villani, re-chiffrée un cran plus haut.

**Contrairement aux trois autres sources, tout est en Python.** Il n'y a rien à transposer : les modules
cités s'ouvrent, se lisent et se portent. Le point de friction est **la taille**, pas le langage.

### D1.1 — Ce qui rend ce dépôt décisif pour nous

C'est **le seul des quatre qui a construit une machinerie complète pour répondre à « comment savoir qu'un
agent autonome a réellement produit un effet »** — notre décision 13, poussée deux crans plus loin que
Villani. Là où Villani compare `before_contents` au contenu courant, Ouroboros a :

- un **reçu de vérification attesté par l'hôte**, écrit dans le même acte que l'exécution ;
- une **relation de réconciliation prouvée transitive**, après avoir mesuré qu'une chaîne de repli ne l'est
  pas ;
- **trois capteurs de faux-vert**, dont aucun ne change le verdict.

Il fait aussi tourner une **campagne d'évolution auto-dirigée sur son propre code**, sous une constitution
écrite (`BIBLE.md`) qui interdit explicitement d'affaiblir le système immunitaire pour réduire la friction.
C'est notre campagne, mais sur le harness au lieu du produit.

**Ce qu'Ouroboros n'a pas non plus** — quatre sources, quatre fois le même constat : aucun invariant
métamorphique, aucun mutation-check, aucun catalogue fermé de relations. Sa validation reste « exécuter une
commande déclarée et lire le code de retour » ; mais il a construit **tout l'appareil de preuve autour** de
ce code de retour, et c'est précisément ce qui manquait à v1.

### D1.2 — Convention

`our/` = `ouroboros/` · `sup/` = `supervisor/` · `sk/` = `skills/` · `od/` = `docs/` · `pk/` = `packaging/`,
relatifs à `resources/ouroboros-main/`.

Verdicts : **Porter** (code Python déjà écrit, portage quasi littéral) · **Adapter** (l'implémentation
suppose le `ToolContext` ou le plan supervisor) · **Inspirer** (c'est la structure ou l'invariant qui vaut).

## D2. Ce que la reprise a changé dans la documentation

| Cible | Nature du changement |
|---|---|
| `EXPLANATIONS.md` | Décisions 5, 8, 13 et 17 amendées · décisions 22 à 25 ajoutées |
| `PROJECT.md` | 2 critères ajoutés · le 16 k passe d'hypothèse à mesure |
| `ROADMAP.md` | **Spike n°2 reformulé** · spikes 4 et 5 ajoutés · phase P8 |

### D2.1 — Décision 17 amendée : `response_format` est une intention, pas une garantie

**L'avertissement le plus important des quatre sources.** `our/llm.py:2241-2250`, docstring littérale :

> *`response_format` is optional request **intent** on the OpenAI-compatible/OpenRouter lanes: local,
> Anthropic-native, and GigaChat routes **ignore it**, and a provider rejection **strips it** via the
> optional-parameter retry — callers must keep a text-parse fallback.*

Et `response_format` figure dans `_OPTIONAL_DROPPABLE_PARAMS` (`our/llm.py:183-186`) : la ladder de retry a
le droit de le **retirer** pour faire passer l'appel.

**Notre contrainte dure n°1 ne peut donc pas reposer sur la contrainte de décodage côté serveur.** Elle doit
reposer sur une **revalidation locale contre le schéma exact envoyé** — `our/request_wire_custom_validation.py`,
170 lignes, le module le plus directement utile de tout le dépôt pour notre `bridge`. Il émet un reçu liant
quatre digests (`candidate` / `catalog` / `schema` / `arguments`) et cinq codes d'erreur fermés.

La règle qui va avec, énoncée par Ouroboros pour ce module : *« validation failure may prove wire acceptance
but cannot authorize tool execution »*. **L'acceptation par le transport n'est pas une autorisation
d'exécution.**

Un détail d'une ligne qui ferme une classe de bugs : `parse_constant=_reject_non_json_constant`
(`:85-87`). **`json.loads` accepte `NaN`, `Infinity` et `-Infinity` par défaut.** Un modèle qui émet `NaN`
dans un domaine de génération passerait un `json.loads` naïf et atteindrait Hypothesis.

### D2.2 — Décision 13 amendée : le reçu attesté, et les trois capteurs de faux-vert

**`verify_and_record`** (`our/tools/verify.py:553-850`) — le modèle *déclare* un contrat de vérification ;
l'hôte *exécute* la commande **et** écrit un reçu durable, dans le même appel. Le succès et sa preuve cessent
d'être deux choses séparées, pour un coût marginal de zéro tour.

Trois points qui nous manquaient :

- **Un reçu non écrit retire l'attestation, pas seulement l'écriture** (`:59-66`) : *« le check a peut-être
  tourné, mais aucun reçu durable n'a été enregistré ; ne traite pas cette vérification comme attestée »*.
- **L'échappatoire honnête existe et est typée.** `no_visible_machine_contract` enregistre le meilleur proxy
  **et son risque résiduel**. Chez nous un nœud sans critère exécutable est scindé ou `blocked` — plus
  strict, et c'est bien — mais la catégorie « vérifiable seulement par jugement » n'a aujourd'hui aucun
  véhicule de trace. Elle en aura besoin pour les nœuds bloqués.
- **`delegation_zero_run` n'est pas une preuve** : une décision de cycle de vie reste visible dans le paquet
  de reçus mais **ne supprime jamais le drapeau « pas de preuve »**.

**Les trois capteurs de faux-vert.** Aucun ne change le verdict ; tous écrivent un drapeau que le relecteur
lit.

1. **Masquage du code de sortie** (`:116-155`) — détecte dans un check `sh -c` les constructions qui
   blanchissent le vrai exit : tube terminal vers un filtre (`| tail`, `| grep` — POSIX : l'exit d'un
   pipeline est celui du **dernier** étage), `|| true`, `>/dev/null`. Tokenisation `shlex` avec
   `punctuation_chars="|&<>"` pour voir `pytest -q|tail` sans espace, et pour ne pas signaler un `|` entre
   guillemets. **Notre suite de régression accumulée est faite de commandes persistées : une commande avec
   `| tail` est verte pour toujours.**
2. **Cycle de vie des artefacts** (`:368-433`) — après le check, l'hôte re-sonde chaque chemin déclaré.
   Attrape le check qui **construit puis supprime** le livrable qu'il vient d'attester. La sonde tourne sur
   la même surface que le check ; un chemin absolu ou traversant n'est pas sondé, sinon le drapeau devient un
   oracle sur des fichiers cachés.
3. **Provenance du critère** (`:632-641`) — `criterion_source ∈ {task_stated, agent_defined}`, **défaut
   `agent_defined`** : une provenance non déclarée ne se lit jamais comme énoncée par la tâche. Chez nous un
   critère est toujours proposé par le modèle, mais le `seed` et les invariants de régression accumulés sont,
   eux, `task_stated`. **La distinction porte directement la question expérimentale n°4.**

**Ce qu'on ne reprend pas** : Ouroboros fait de `receipt_absent` un **drapeau advisory qui garde le résultat
`solved`** — *« never a downgrade — anti-oscillation »*. Notre décision 13 fait l'inverse. Les deux positions
sont défendables pour des raisons différentes : Ouroboros tourne sur des modèles frontières et craint
l'oscillation ; nous tournons sur un 8B et notre mode d'échec mesuré est **le succès fantôme** — 7
`completed` sur 10. **Notre lecture stricte reste la bonne**, mais il faut s'attendre au coût qu'Ouroboros
nomme : des nœuds qui refont le même travail parce que la preuve n'a pas été captée. Le remède qu'il
applique — **le drapeau est binaire et ne s'accumule pas** — est à reprendre même en gate dure.

### D2.3 — Décision 22 : une identité est une clé typée, jamais une chaîne de repli

`our/_outcome_receipts.py:154-300` et la règle en prose dans `od/DEVELOPMENT.md:127-180`.

Le problème : un reçu rouge doit pouvoir être réconcilié par un vert ultérieur **de la même vérification**.
Comment savoir que deux reçus nomment la même chose ? La première implémentation était une **chaîne de
repli** — matcher sur `criterion_id`, sinon sur le texte du `check`, sinon sur l'ensemble des `paths`. Elle a
été retirée avec cette justification, qui vaut d'être citée :

> *A chain is not an equivalence relation. It was not transitive — `{c1, check}` matched `{check}`,
> `{check}` matched `{c2, check}`, while `c1` and `c2` are explicitly different criteria — so one check-only
> green reconciled two distinct reds, and the outstanding set came out order-dependent. **No care at the call
> sites can repair a relation that is not an equivalence.***

La forme retenue : **une seule clé typée `(kind, value)`**. Le `kind` est la chose la plus spécifique que le
reçu porte réellement ; une fois choisi, aucun second composant n'est consulté. La relation devient le noyau
d'une fonction — réflexive, symétrique, transitive par construction — et elle échoue dans la **direction
sûre** : strictement moins de réconciliations.

**Cette règle s'applique directement à notre clé anti-redondance de proposition** (décisions 5 et 19), qui a
exactement la même forme et courait exactement le même risque.

Trois raffinements, chacun né d'un incident :

- **Le rendu du texte fait partie de son identité** (`:50-64`). Passer de `" ".join(argv)` à `shlex.join` a
  corrigé la non-injectivité (`["echo","a b"]` et `["echo","a","b"]` rendaient la même chaîne) mais a
  **rouvert le trou dans l'autre sens** : un vieux rouge et un nouveau vert écrits par deux rendus différents
  se lisaient pareil. Solution : un **tampon de version du rendu** stocké à côté du texte, toute valeur
  inconnue étant son propre espace de noms — un futur rendu est automatiquement incomparable, sans
  modification de code.
- **La normalisation ne jette jamais un octet dont l'identité dépend** (`:131-152`). `canonical_path_set`
  déduplique et trie, **et rien d'autre** : un espace de fin est un octet légal de nom de fichier, et le
  rogner a laissé une observation verte de `"a.md"` fermer une rouge de `"a.md "`. L'ordre est
  **canonicaliser → rendre → borner**, jamais rendre → dédupliquer : le rendu est lossy, donc dédupliquer
  après lui jette des valeurs distinctes pendant que le compteur d'omissions dit zéro.
- **Ce qui décide doit être ce qui est rapporté** (`:344-394`). La divulgation re-dérivait l'autorité au lieu
  de lire celle qui décide. Une preuve attestée par l'hôte qui **ment sur sa propre base** est exactement la
  classe de défaut que cette surface existe pour éliminer.

### D2.4 — Décision 23 : le résultat n'est pas un statut, c'est un produit d'axes

`our/outcomes.py:83-244`. Le résultat d'une tâche est **six axes séparés** — `lifecycle`, `execution`,
`objective`, `review`, `artifacts`, `verification` — plus l'absorption des enfants.

L'intérêt est dans les **vocabulaires de non-échec** (`:284-295`) : un blocage de politique
(`refused_out_of_scope`), une sortie cosmétique, un outil qui répond honnêtement `{"ok": false}` **ne sont
pas des échecs**. Chacun de ces cas a été mesuré en train de se faire passer pour une panne d'outil.

Chez nous la métrique de campagne est « outils vérifiés livrés / cycles consommés ». Sans cette séparation,
un cycle où Ollama était injoignable, un cycle où la proposition était redondante et un cycle où le modèle a
produit un critère tautologique comptent tous les trois comme échec. **Ce sont trois choses différentes, et
la deuxième est un succès du garde-fou.**

### D2.5 — Décision 24 : le filtre de pression interne

`BIBLE.md:412-429`. Le test qu'aucun critique persistant ne peut contourner :

> *Does the proposed change make a class of failure structurally impossible, or does it weaken the immune
> system to remove friction? If the latter — decline or redesign before acting.*

Et la règle qui l'accompagne : **auto-initié ne veut pas dire auto-exempté.** Une idée que le système génère
lui-même passe par les mêmes filtres qu'une demande externe.

Notre campagne propose ses propres outils et son propre arrêt. **C'est le prédicat qui manque à notre gate de
proposition** : une proposition qui *retire une gate* doit être rejetée par la même mécanique qui rejette une
proposition redondante.

### D2.6 — Décision 5 amendée : la récurrence se compte, elle ne se jette pas

`our/improvement_backlog.py:285-374` — un doublon n'est jamais jeté : il incrémente `count`/`last_seen`,
**rouvre** un item clos, et **élève le rang** (`priorité + récurrence`).

Notre décision 5 jette une proposition répétée. **C'est de l'information sur ce que le système croit devoir
faire, et elle est détruite au moment exact où elle deviendrait un signal d'arrêt informé.** Amendement : un
doublon rejeté trois fois n'est pas du bruit, c'est un signal — le compter dans le registre et le faire
remonter dans la proposition d'arrêt, au lieu de l'effacer.

Deux mécanismes qui vont avec : le vivier de candidats est **déterministe, classé et plafonné à 20 avant tout
appel modèle** (`:199-220`), et la fermeture d'items se fait **sur commit, par le code** (`:423-455`), pas
par le modèle.

### D2.7 — Décision 8 amendée : deux réserves murales, pas une

`our/task_pacing.py:199-224`. **Confondre la fenêtre d'émission et la réserve en pourcentage a amputé 54
minutes d'une tâche de 6 heures.**

Deux choses distinctes : « ne plus **démarrer** une gate qu'on ne peut pas finir » (réserve en pourcentage,
calibrée par **EWMA des durées observées** — `max(plancher, 1,5 × EWMA)`, `alpha=0.5`) et « **finaliser** les
nœuds verts » (fenêtre d'émission). Plus un **latch de l'ancre de départ** (`:233-245`) : sans lui, chaque
snapshot ré-ancre le total sur « maintenant » et la réserve se dégrade silencieusement vers son plancher.

### D2.8 — Décision 25 : discipline de dépôt

Notre `ARCHITECTURE.md` visait « ~3 000 lignes de harness » — cible portée à ~5 900 le 06:09 après comptage
des portages, puis ramenée à ~5 230 par la passe de simplification — et ajoutait honnêtement *« ordres de grandeur cibles, pas des mesures »*. **Rien ne
l'applique.**

`our/review.py:292-830` + `our/size_ratchet_manifest.py` — un manifeste **généré** de la dette de taille,
avec transition **shrink-only** vérifiée par une gate pytest : module cible ~1 000 lignes, gate dure à 1 600,
bande 1 001–1 500 à **justification obligatoire et immuable** dont l'abandon « blanchit la justification »,
comptes d'octets qui ne peuvent que décroître, correspondance **exacte** avec l'inventaire vivant.

Et la règle de comportement, qui vaut autant que la gate :

> *Treat a size gate as pressure to reduce total complexity, not as a design reason for a helper or sibling
> module. Relocating the same complexity, or stripping contract-bearing comments, diagnostics, or tests to
> buy bytes, is not paydown. If neither a safe simplification nor a natural boundary exists, **report the
> ratchet conflict instead of gaming or silently raising the cap**.*

À lire les yeux ouverts : `GIANT_PATHS` compte **49 entrées**, dont `our/loop.py` à 6 379 lignes. Le ratchet
n'a pas empêché la dette — il l'a **rendue visible, bornée et décroissante**. C'est déjà beaucoup plus que ce
que nous avons.

Deux invariants documentaires transposables tels quels (`BIBLE.md:564-622`) : **DRY/SSOT étendu aux docs**
— *« a self-describing system that says two different things about itself cannot see its own contradiction »*
— et le **seuil de relisibilité** : *« if code, prompts, or docs grow toward the point where strong
whole-repo review no longer fits inside the reviewer's context, simplify the system »*. **Pour un relecteur à
16 k, c'est la contrainte la plus dure de tout le projet.**

### D2.9 — Critères de socle ajoutés

- **Une identité d'enregistrement est une clé typée, jamais une chaîne de repli** : la relation de
  réconciliation est une équivalence, vérifiée réflexive / symétrique / transitive par test.
- **La sortie du modèle est revalidée localement contre le schéma exact envoyé** avant toute exécution :
  l'acceptation par le transport n'autorise rien.

## D3. Catalogue complet des reprises

### D3.1 — `journal` — les primitives d'écriture durable

| Source | Notion | Verdict |
|---|---|---|
| `our/utils.py:232-274` | `_atomic_overwrite` — sibling `.{nom}.tmp.<pid>.<tid>.<uuid>` puis `os.replace`. Un SIGKILL entre création et rename laisse le fichier **existant intact**, jamais tronqué. Bits de permission préservés. | Copier |
| `our/utils.py:212-230` | `replace_atomic` — retry borné sur `PermissionError` **seulement**. POSIX reste un syscall unique, sans sleep. | Copier |
| `our/utils.py:276-338` | `write_bytes_atomic` / `write_text_atomic` / `atomic_write_json`, `fsync` **optionnel et explicite**. Un `os.write` partiel est détecté, pas ignoré. | Copier |
| `our/utils.py:340-380` | `sweep_stale_temp_files` — les temporaires orphelins d'un kill dur sont récupérés par balayage d'âge. Sans lui, un crash par mission laisse un fichier mort par écriture. | Copier |
| `our/utils.py:395-455` | `update_json_locked` — read-modify-write **sous un seul verrou tenu**, relecture du disque **dans** le verrou. `TimeoutError` sur échec : *« proceeding unlocked would silently reintroduce the race »*. | Copier |
| `our/utils.py:463-612` | `append_jsonl` renvoie **`bool`**, jamais un succès simulé. `require_lock=True` pour les flux d'autorité : ceux-là ne se rabattent **pas** sur un append non verrouillé. | Copier |
| `our/utils.py:457-461` | `jsonl_append_lock_path` — verrou sidecar nommé par le SHA-256 du chemin résolu, partagé entre writers et rotation. | Copier |
| `our/utils.py:151-169` | `jsonl_generation_signature` — identité d'une **génération** de fichier (hash de la première ligne + taille), pour que writer et reader détectent une rotation à l'identique. | Copier |
| `our/utils.py:1381-1410` | Deux primitives de bornage aux contrats **distincts** : aperçu avec **plancher anti-gaspillage** (une coupe qui économise moins que son propre marqueur est refusée) vs preuve durable. | Copier |
| `sup/state.py:918-1000` | Rotation JSONL avec lecteurs conscients de l'archive. Notre `live.log` en aura besoin dès la dixième mission. | **Reporté** |
| `our/usage_ledger.py:228-302` | `_validate_records` — **séquence dense** (`seq` strictement incrémental, un trou est une corruption) plus une **machine à états par entité** validée au replay. | Copier |
| `our/usage_ledger.py:200-226` | `_quarantine_tail` — la queue déchirée est encodée en base64 dans un `*.quarantine.jsonl`. **On reprend la quarantaine, pas la troncature** — voir conflit n°8. | **Reporté** |
| `our/usage_ledger.py:355-477` | `LedgerResumeState` — validation **incrémentale** : un lecteur ayant déjà validé un préfixe passe la prochaine `seq` attendue, au lieu de tout relire. | **Reporté** |
| `our/usage_ledger.py:41-48` | Deux exceptions typées : fail-closed vs histoire structurellement invalide. **Un registre corrompu ne se lit pas « comme vide ».** | Copier |
| `our/observability.py:48-192` | Reconnaissance de clé secrète par **quatre couches** : noms exacts, suffixes (`_API_KEY`, `_TOKEN`), suffixes composés, marqueurs de segment, plus motifs de valeur et de paramètre d'URL. | Copier |
| `our/observability.py:1083-1087` | `redact_projection` — **une** fonction traversant n'importe quelle structure, renvoyant la valeur rédigée **et la liste des rédactions effectuées**. | Copier |
| `our/observability.py:33-34,238-257` | Modes privés POSIX explicites (`0o600`/`0o700`) avec prédicat de support. La trace forensique n'est pas lisible par les autres utilisateurs. | Copier |
| `our/observability.py:1452-1470` | `SecretRedactingLogFilter` — un filtre `logging` qui rédige, pour que le chemin *non* instrumenté ne fuite pas non plus. | **Écarté** |
| `our/observability.py:1378-1450` | La rétention des blobs est une **fonction nommée**, pas un `find -delete` dans un cron. | Copier |
| `our/_outcome_receipts.py:462-530` | `disclosed_list_projection` — borner une **liste** obéit à la même règle que borner une chaîne : le slice porte le **compte omis** et un **hash durable de l'ensemble complet**. | Copier |

### D3.2 — `kernel/codeview`

| Source | Notion | Verdict |
|---|---|---|
| `our/code_intelligence.py:73-115` | `FileFact` / `CodeInventory` — projection structurelle **dérivée seulement** : la source est lue pour être parsée, **jamais mise en cache**. `coverage` = comptage par disposition. | Copier |
| `our/code_intelligence.py:485-555` | `_file_fact` — ordre des gardes : échappement de chemin (symlink résolu inclus) → sensible → taille → NUL dans les 4 premiers Ko → parse. **Chaque refus produit une disposition nommée.** L'index ne ment jamais par omission. | Copier |
| `our/code_intelligence.py:548-551` | `structural_unavailable:<lang>` — un langage connu sans grammaire disponible est **déclaré**, jamais rabattu sur des regex. | Copier |
| `our/code_intelligence.py:583-635` | Reconstruction incrémentale par **SHA-256 de contenu** (pas mtime) : un digest inchangé réutilise son `FileFact`. | Copier |
| `our/code_intelligence.py:116-121` | Clé de cache = SHA-256 du chemin racine résolu. Deux workspaces ne partagent jamais un index. | Copier |
| `our/code_intelligence.py:737-764` | `impact_files` — fermeture d'imports/références bornée en profondeur, **chaque fichier avec sa raison** (`imports depth N`, `references <sym>`, `target`). | Copier |
| `our/code_intelligence.py:766-800` | `relevant_files` — sélection par score déterministe **avec raison textuelle par fichier**. **Zéro appel modèle pour construire le contexte.** | Copier |
| `our/code_intelligence.py:261-270` | `_signature` — signature AST d'une fonction/classe. Notre gate d'arité s'y branche directement. | Copier |
| `our/code_intelligence.py:556-582` | Un `.env`, une clé, un `.pem` n'entrent **jamais** dans l'inventaire, donc jamais dans le contexte. | Copier |
| `our/code_search_rg.py:1-304` | Recherche `ripgrep` optionnelle, **chaque match post-filtré** par les gates protégé/secret. La recherche ne contourne pas la politique de chemins. | Adapter |

### D3.3 — `verifier` — reçus, identité, gate hermétique, attribution

| Source | Notion | Verdict |
|---|---|---|
| `our/tools/verify.py:553-850` | `verify_and_record` — l'hôte exécute **et** atteste dans le même appel. Le reçu porte `status`, `returncode`, `matched`, `check`, `check_rendering`, `summary`, `duration_ms`, `signal`. | Copier |
| `our/tools/verify.py:68-75` | `_CONTRACT_KINDS` — six kinds fermés, dont l'échappatoire honnête `no_visible_machine_contract` et la décision `delegation_zero_run`, structurellement non-probante. | Inspirer |
| `our/tools/verify.py:59-66` | `_receipt_custody_failure` — **un reçu non écrit retire l'attestation.** | Copier |
| `our/tools/verify.py:85-110` | `_EXPECTED_MATCH_KINDS` — `substring` / `exact` / `exact_line` / `json_equals` / `bytes_equal`. Le mode de comparaison est une énumération fermée, pas une convention. | Copier |
| `our/tools/verify.py:282-366` | `bytes_equal` — comparaison octet à octet avec **hexdump borné autour de la première divergence**. Forme « golden file » qu'un `substring` sous-vérifie silencieusement. | Adapter |
| `our/tools/verify.py:322-330` | `cmp` sort 0=égal, 1=différent, **>1 = panne d'outillage**. Généralisation de `_is_launch_failure` de Villani. | Copier |
| `our/tools/verify.py:311-321` | **Aucune coercition `or` sur un code de retour** : `None or 0` lisait un résultat inconnu comme un succès. | Copier |
| `our/tools/verify.py:116-155` | **Capteur 1 — masquage d'exit.** Tube terminal vers un filtre, `\|\| true`, `>/dev/null`. Tokenisation opérateur-consciente. Drapeau seul, jamais le verdict. | **Écarté** |
| `our/tools/verify.py:368-433` | **Capteur 2 — cycle de vie des artefacts.** Sonde après-seulement des chemins déclarés : attrape le build-puis-delete. Chemin absolu ou `..` non sondé. | **Écarté** |
| `our/tools/verify.py:632-641` | **Capteur 3 — `criterion_source`**, défaut `agent_defined`. | **Écarté** |
| `our/tools/verify.py:44-49` | Deux bornes distinctes : `_RECEIPT_OUTPUT_CAP = 20000` (preuve durable) et `_TOOL_OUTPUT_CAP = 4000` (transport vers le modèle). **La preuve n'est pas bornée par le budget de contexte.** | Copier |
| `our/_outcome_receipts.py:154-215` | `ReceiptIdentity` — trois composants **indépendants**, dérivés **une fois**, puis utilisés pour comparaison, hash, comptage et projection. Trois notions subtilement différentes ne peuvent plus diverger. | Copier |
| `our/_outcome_receipts.py:216-266` | **Une** clé typée `(kind, value)`. *A chain is not an equivalence relation.* | Copier |
| `our/_outcome_receipts.py:273-287` | `IDENTITY_KINDS` — table fermée **totale**, y compris pour le kind « aucune identité ». Un quatrième kind ajouté sans sa ligne lève `KeyError` : la gate qui fonctionne. | Copier |
| `our/_outcome_receipts.py:50-64` | `check_rendering` — le **rendu** fait partie de l'identité. Un rendu inconnu est son propre espace de noms, donc sûr sans changement de code. | Copier |
| `our/_outcome_receipts.py:131-152` | `canonical_path_set` — dédup + tri, **verbatim sinon**. Canonicaliser → rendre → borner, jamais l'inverse. | Copier |
| `our/_outcome_receipts.py:395-460` | Un reçu **sans clé** garde la règle ancienne ; deux reçus sans clé ne sont **jamais** égaux, même entre eux. *Indiscernables n'est pas connu-égal.* | Copier |
| `our/_outcome_receipts.py:344-394` | Décideur et rapporteur lisent **la même projection**. Une preuve qui décrit faussement sa propre base est le défaut que la surface existe pour éliminer. | Copier |
| `our/_outcome_receipts.py:687-806` | `_outstanding` / `unreconciled_failed` — l'ensemble des vérifications **encore ouvertes**, calculé une fois. C'est notre « nœud qui ne peut pas se déclarer vert ». | Copier |
| `our/preflight_runner.py:1189-1330` | `run_hermetic_pytest` — **worktree git jetable**, candidat = capture `--binary` durcie + copie des non-suivis, budget partagé, sortie au premier rouge. | Copier |
| `our/preflight_runner.py:414-447` | `_apply_diff` — `-c core.autocrlf=false -c core.eol=lf`, `--binary`, `--unidiff-zero`. Une capture fidèle aux octets doit atterrir sur un checkout qui l'est aussi. | Copier |
| `our/preflight_runner.py:448-480` | `_copy_untracked` — `os.fsdecode` (surrogateescape), confinement `relative_to` des deux côtés. Un nom non-UTF-8 ne disparaît pas en silence. | Copier |
| `our/preflight_runner.py:576-625` | `_preflight_env` — scrub des variables du harness, secrets, `GH_*` et **tout `PYTEST_*`**, puis ré-injection contrôlée. **Un vert sous une variable héritée est indiscernable d'un vrai vert.** | Copier |
| `our/preflight_runner.py:500-575` | Sonde à **nonce** : *« the difference between "the argv said -n" and "concurrency actually happened" »*. Une gate qui ne peut pas prouver son mode ne l'annonce pas. | Inspirer |
| `our/preflight_runner.py:626-748` | Vérification des plugins requis **avant** que le moindre code candidat soit sur le disque, avec remédiation nommée. | Adapter |
| `our/preflight_runner.py:389-412` | `_head_tracks_tests` — distingue « pas de suite » de « ce candidat a supprimé la suite ». Une ref illisible **bloque**. | Copier |
| `our/preflight_runner.py:1234-1242` | Un budget de rendu non positif **refuse de lancer la gate** : un diagnostic non rendu se lit comme un succès. | Copier |
| `our/preflight_runner.py:99-103,142-176` | Séquences ANSI retirées avant tout matching ; motifs de crash **ancrés en début de ligne nettoyée** — un test dont l'assertion *mentionne* un crash recevait une remédiation confiante et fausse. | Copier |
| `our/commit_admission.py:30-228` | Préflights déterministes d'admission au commit : compilation des `.py` stagés, synchronisation des métadonnées de version, tests avec preuve. | Adapter |
| `our/mutation_attribution.py:447-525` | `attributed_git_candidates` — candidats = changés **moins** sales-au-baseline ; blockers typés `baseline_missing` / `baseline_stale` / `baseline_surface_ambiguous` / `baseline_dirty_overflow`. | Copier |
| `our/mutation_attribution.py:335-426` | `clean_eligible = not blockers`. **La preuve est une liste de raisons, et son absence est un fait, pas un verdict.** | Copier |
| `our/mutation_attribution.py:676-800` | **Époques de baseline** : ré-ancrage strict (ancêtre de HEAD **et** intervalle disjoint des chemins sales). Sans ça, `baseline_stale` coince toutes les missions après le premier commit. | Copier |
| `our/mutation_attribution.py:85-108` | `--porcelain=v1 -z --untracked-files=all` avec **les deux côtés** d'un rename. Une ligne malformée lève, elle n'est pas ignorée. | Copier |
| `our/mutation_attribution.py:126-158` | `_path_fingerprint` — empreinte d'**un chemin connu exact**, sans jamais parcourir un parent ; `kind ∈ {missing, symlink, file, directory, other}`. | Copier |
| `our/mutation_attribution.py:31-35,213-220` | Un worktree poubelle rend le baseline **honnêtement inutilisable** (`dirty_overflow`) plutôt que coûteusement approximatif. | Copier |
| `our/review_evidence.py:17-66` | **Indépendance de la preuve** : quels fichiers de vérification l'agent a lui-même écrits. Étiqueté honnêtement « état du worktree » faute de baseline. | Copier |
| `our/review_evidence.py:66-80` | **Parité de preuve** : la borne du décideur suit celle de l'acteur. *Un juge affamé produit des verdicts « non montré », donc des boucles.* | Copier |
| `our/review_evidence.py:83-105` | Deux formes d'« ouvert » : jamais répondu, et **répondu par l'agent mais non tranché**. Une réfutation déposée est une prétention, pas un règlement. | Copier |
| `our/outcomes.py:430-470` | Deux signaux structurels distincts : `receipt_absent` (effets réels, aucune attestation) et `expected_output_ungrounded` (livrable déclaré, zéro tool call). | Adapter |

### D3.4 — `bridge`

| Source | Notion | Verdict |
|---|---|---|
| `our/request_wire_custom_validation.py:107-170` | Revalidation locale contre **le schéma exact envoyé**, reçu liant `candidate`/`catalog`/`schema`/`arguments` par SHA-256. **L'acceptation par le transport n'autorise pas l'exécution.** | Copier |
| `our/request_wire_custom_validation.py:15-22` | Cinq codes fermés — `invalid_json`, `arguments_not_object`, `unknown_tool`, `invalid_schema`, `schema_validation_failed`. Cinq raisons de rejet, pas un booléen. | Copier |
| `our/request_wire_custom_validation.py:85-87` | `parse_constant` refusant `NaN`/`Infinity`. **Une ligne, une classe de littéral illégal fermée avant Hypothesis.** | Copier |
| `our/request_wire_custom_validation.py:89-105` | Tout échec de construction/résolution de schéma est contenu à sa frontière et devient `invalid_schema`. `jsonschema` n'a pas de base commune publique pour ces erreurs. | Copier |
| `our/request_wire_custom_validation.py:24-42` | Reçu **parser-issued** : le constructeur refuse toute instanciation hors parseur. Une attestation ne se fabrique pas côté appelant. | Inspirer |
| `our/llm.py:2241-2250` · `:183-186` | `response_format` est une **intention** que la ladder de retry a le droit de retirer et que certaines routes ignorent. | Inspirer |
| `our/context_budget.py:38-93` | Un dépassement de contexte est reconnu **par code structuré d'abord**, texte ensuite ; un code structuré l'emporte toujours. Sépare « prompt trop grand » de « sortie trop grande ». | Copier |
| `our/local_model.py:579-617` | `health_check` — le `n_ctx` réel est **lu sur `/v1/models`** (`meta.n_ctx_train`), pas supposé. | Copier |
| `our/local_model.py:618-700` | `test_tool_calling` — **sonde de capacité** d'un serveur local : chat de base, tool call réel, `tokens_per_sec` mesuré. Ne jamais supposer une capacité : la sonder. | **Écarté** |
| `our/capability_evidence.py:52-158` | La fenêtre de contexte est une **preuve sourcée** (`confirmed`/`asserted`/`unprobeable`/`failed`) liée à une empreinte de route. `unknown` ⇒ fail-closed. | Adapter |
| `our/capability_evidence.py:204-248` | `route_fingerprint` — credentials **exclus** de l'identité de route ; headers beta/routing inclus. | **Écarté** |
| `our/capability_evidence.py:159-203` | `require_fresh` **explicite au site d'appel** : autoriser exige la fraîcheur, dégrader ne l'exige pas. *« An outage must never erase a prior confirmed record. »* | Copier |

### D3.5 — `workspace`

| Source | Notion | Verdict |
|---|---|---|
| `our/tools/edit_ops.py:79-157` | `_resolve_edit_target` — **canonicalisation du chemin en PREMIER**, puis root, puis artefacts protégés, puis runtime protégé. *« A guard that judges a different string than the one that executes is not a guard. »* | Copier |
| `our/tools/edit_ops.py:208-239` | `_partial_write_failure` — préfixe distinct des refus de validation : une mutation partielle réelle reste un échec d'**exécution**. | Copier |
| `our/tools/edit_ops.py:573-677` | `edit_batch` — chaque édition déclare son **nombre d'occurrences attendu** ; un écart annule le lot **entier avant écriture**. La forme sûre de « replace all ». | Copier |
| `our/tools/edit_ops.py:678-698` | `_syntax_check` — `compile()` pour `.py`, `json.loads` pour `.json`, et le `ValueError` nu de `compile()` (octet NUL) rapporté **contre le format réellement testé**. | Copier |
| `our/tools/edit_ops.py:699-730` | `_unified_diff` avec **note explicite sur la newline finale** : ne jamais rapporter « aucun changement textuel » pour un fichier dont les octets ont changé. | Copier |
| `our/shell_parse.py:1-60` | Parseurs argv **partagés par tous les garde-fous**, pour que la garde inspecte exactement ce qui s'exécute. | Copier |
| `our/tools/write_shape.py:1-40` | **Un seul seam** décide si une ligne de commande est *write-shaped*, avant que toute garde d'écriture n'agisse. | Copier |
| `our/git_shell_policy.py:19-40` | `GIT_READONLY_SUBCOMMANDS` — classification structurelle des sous-commandes git. Notre broker git en a besoin. | Copier |
| `our/argv_budget.py:1-120` | **Budget argv+env en octets encodés** : cap par chaîne et total via `sysconf`. | Adapter |
| `our/argv_budget.py:88-95` | Le noyau mesure la chaîne **avec son NUL** : tester `contenu > limite` laissait passer le cas exact-frontière, qui échouait ensuite en `E2BIG`. | Copier |
| `our/runtime_mode_policy.py:1-40` | `SAFETY_CRITICAL_PATHS` — liste **nommée** de chemins que le mode courant n'a pas le droit de réécrire, séparée des chemins runtime protégés. | Copier |
| `our/protected_artifacts.py:1-30` | Artefacts « boîte noire » : un binaire de référence est **exécutable mais non lisible en octets** — comparer ses octets, c'est les lire. | Inspirer |

### D3.6 — `engine`

| Source | Notion | Verdict |
|---|---|---|
| `our/task_tree_ledger.py:34-48,170-302` | **Ledger d'arbre append-only par racine**, kinds fermés, `needs_parent_attention` **dérivé du kind et non déclaré**. Un append non écrit renvoie un échec typé. | Copier |
| `our/task_tree_ledger.py:618-655` | Curseur `(ts, ids vus)` : le parent avance un curseur au lieu de relire l'historique. Les timestamps égaux sont admis une fois. | Copier |
| `our/task_tree_ledger.py:108-168,393-433` | `child_result_disposition` — le parent enregistre par enfant `integrated` / `irrelevant` / `deferred`, **lié au SHA-256 du résultat**. Un résultat qui change périme la disposition. | Copier |
| `our/task_tree_ledger.py:580-617` | Pagination portant un **hash de snapshot**, et déclaration explicite quand le ledger a bougé pendant la capture. | Copier |
| `our/task_tree_ledger.py:384-391` | Identité de contenu stable d'une ligne (JSON canonique trié + SHA-256), partagée par tous les curseurs. | Copier |
| `our/task_tree_ledger.py:49,656-705` | `delegation_constraint` à directives fermées (`halt_fanout`, `cap_children`, `require_lane`, `block_surface`). | Adapter |
| `our/task_tree_ledger.py:59-61` | Bornes explicites : 4 000 caractères par entrée, **2 Mo par ledger**. Un ledger plein refuse **avec le message qui dit quoi faire**. | Copier |
| `our/task_pacing.py:199-224` | **Deux réserves distinctes** : fenêtre d'émission et réserve en pourcentage. Les confondre a amputé 54 min d'une tâche de 6 h. | Copier |
| `our/task_pacing.py:148-198` | Réserve calibrée par **EWMA des durées observées** (`max(plancher, 1,5 × EWMA)`, `alpha=0.5`), depuis les événements de timing déjà écrits. | **Reporté** |
| `our/task_pacing.py:87-110` | `has_deadline=False` **désactive l'axe temps entièrement** plutôt que de simuler un infini. `spendable_sec` = le temps au-dessus de la réserve. | Copier |
| `our/task_pacing.py:233-245` | **Latch de l'ancre de départ** : sans lui, chaque snapshot ré-ancre le total sur « maintenant » et la réserve se dégrade vers son plancher. | **Reporté** |
| `our/task_pacing.py:260-279` | Une gate coûteuse ne démarre que si elle **tient au-dessus de la réserve**, avec une raison typée. | Copier |
| `our/task_pacing.py:377-380,423-524` | `CostCeiling` — quatre états typés. **`None` n'est pas surchargé** pour signifier à la fois « illimité » et « épuisé ». | **Reporté** |
| `our/task_pacing.py:398-422` | Quand le chiffre faisant autorité est indisponible, la substitution est **divulguée**, jamais silencieuse. | Copier |
| `our/deadline_utils.py:1-328` | Seam **transport contre logique** : le timeout d'un outil réseau et le jalon logique de la boucle ne sont pas la même horloge. | Copier |
| `our/context_layout.py:69-136` | `generate_doc_nav_map` — carte de navigation H2–H4 à sous-arbres complets : représentation **sans perte** d'un document trop gros, jamais un `[:N]`. | Adapter |
| `our/context_compaction.py:280-344,681-738` | Unités atomiques `tool_use`/`tool_result` inséparables (confirme Villani), sélection sous budget, **checkpoint de réclamation**. | **Écarté** |
| `our/context_compaction.py:410-417` | `_SUMMARY_CONTRACT_DIGEST` — **le contrat du résumeur est haché** : un résumé produit sous un ancien contrat est reconnaissable. | **Écarté** |
| `our/context_budget.py:171-254` | Table de seuils **par store** — un nouveau store append-only doit s'y enrôler dans le même commit. | Copier |
| `od/DEVELOPMENT.md:914-985` | **Aucune troncature silencieuse** : marqueur visible, plancher anti-gaspillage, borner une liste = borner une chaîne. La troncature protège le contexte du modèle, **jamais la lecture de l'humain**. | Inspirer |
| `od/DEVELOPMENT.md:970-985` | **Pas de gate « seulement si touché »** pour les artefacts de gouvernance : ils entrent inconditionnellement dans les flux de raisonnement. | Inspirer |
| `our/outcomes.py:503-568` | `reviewable_effect_projection` — modèle d'**exclusion** (seul le scratch est exempt), pas d'énumération des roots livrables : la gate reste complète quand les roots évoluent. | Copier |
| `sup/terminal_delivery.py:255-270,336-395` | Retour **typé** : `True` = durablement suivi, `False` = trou de durabilité réel. La lecture d'application **déclare ses propres lignes illisibles** au lieu de les compter comme absentes. | Copier |

### D3.7 — `campaign`

| Source | Notion | Verdict |
|---|---|---|
| `our/improvement_backlog.py:285-374` | **La récurrence n'est jamais jetée** : un doublon incrémente `count`/`last_seen`, **rouvre** un item clos, et élève le rang. | Copier |
| `our/improvement_backlog.py:199-220` | Le vivier de candidats est **déterministe, classé et plafonné (20) avant tout appel modèle**. Le modèle ne voit jamais le backlog brut. | Copier |
| `our/improvement_backlog.py:221-284` | Deux phases : snapshot sous verrou **partagé**, verrou relâché, appel LLM **hors verrou**, puis passe exacte sous verrou exclusif. | Copier |
| `our/improvement_backlog.py:423-455` | `close_backlog_items` — fermeture **sur commit, par le code**, jamais par le modèle. | Copier |
| `our/improvement_backlog.py:502-560` | Toilettage **déclenché par la taille**, plafonné, non conditionné à une erreur. Un backlog qui grossit se nettoie mécaniquement. | Adapter |
| `our/semantic_dedup.py:1-140` | Dédup sémantique **après** miss exact, sur candidats structurels seulement, modèle renvoyant **un id d'une liste fermée** validé exactement, **fail-open**. Voir conflit n°3. | Adapter |
| `our/semantic_dedup.py:52-62` | Le bornage pour comparaison porte un **marqueur visible** et ne touche jamais l'artefact durable — seulement la vue que le juge lit. | Copier |
| `our/evolution_fingerprint.py:1-42` | Module **feuille sans dépendances** dont la seule raison d'être est que compteur et gate lisent la même empreinte. **Notre clé de redondance a trois lecteurs.** | Copier |
| `our/tools/registry.py:1862-2005` | `capability_omissions()` — la surface d'outils projetée porte **la raison typée de chaque absence**. Décision 14 appliquée aux outils. | Copier |
| `our/tools/registry.py:1566-1571,1605-1616` | Un module d'outils qui échoue à l'import omet **tous** ses outils en silence : l'omission est enregistrée durablement. | Copier |
| `our/tools/registry.py:2006-2030` | `policy_hidden_reason` — **« caché par politique » n'est pas « n'existe pas »**. | Copier |
| `our/tools/registry.py:1551` | `mutates_worktree` — drapeau de capacité par outil ; le dispatcher snapshote `git status` autour des outils marqués. | Copier |
| `our/tools/registry.py:1557` | `alias_for` — un ancien nom reste **appelable mais jamais annoncé**. | Copier |
| `our/skill_readiness.py:13-110` | Blockers séparés en **réparables par l'agent** et **nécessitant l'opérateur**. La cause mécanique dit *quoi* ; ça dit *qui*. | Copier |
| `our/skill_loader.py:1-7` | Verdict de revue **lié au hash de contenu**, périmé dès que les octets changent. **Même mécanisme que la satisfaction périmée — une seule primitive à écrire.** | Copier |
| `our/skill_loader.py:28-33` | Les fichiers de **contrôle** sont exemptés du hash de l'objet qu'ils gouvernent : sinon écrire le marqueur après le hash périme le verdict. | Copier |
| `our/contracts/skill_manifest.py:12-70` | Manifeste unifié à types, runtimes et **permissions** fermés ; `canonical_skill_name` calculé une fois, partagé par l'état, le routage et l'UI. | Copier |
| `our/contracts/task_contract.py:1-8` | *« The contract is a durable, LLM-readable description of what this task is trying to accomplish. **It is NOT a deterministic success oracle.** »* La séparation que nous faisons déjà, énoncée. | Inspirer |
| `our/contracts/task_contract.py:298-378` | Les revendications d'acceptation sont **normalisées et versionnées**. | Adapter |
| `our/evolution_checkpoints.py:15-90` | Ledger append-only de **résultats de cycle**, taggé *après* le task-done, joint par `task_id`. | Copier |
| `our/mcp_client.py:371-400` | Description, résultat **et texte de schéma** d'un serveur externe préfixés « données non fiables, pas des instructions ». **S'applique à nos propres outils.** | Copier |
| `our/mcp_client.py:230-250` | `stdio` = exécutable + liste d'arguments exacte. **Pas de shell, pas d'env, pas de cwd.** | Copier |
| `our/mcp_client.py:62-72,180-215` | Denylist des hôtes de métadonnées cloud à la validation d'URL ; validation stricte des noms de headers. | Copier |
| `our/mcp_client.py:335-370` | Le statut MCP servi à l'UI est rédigé, **et le texte d'erreur d'un serveur externe aussi**. | Copier |

### D3.8 — `lifecycle`, `broker` et `observatory`

| Source | Notion | Verdict |
|---|---|---|
| `our/process_custody.py:233-260,496-560` | Appariement par empreinte **stricte** `(pid, start_time, cmd_sha256)`, jamais par classe de commande. PID mort ou empreinte non concordante ⇒ on n'adopte pas. | Copier |
| `our/process_custody.py:12-19` | Scopes `task` / `session` / `daemon` à sémantique de moisson distincte. Notre verrou de campagne et nos subprocess de vérification ne sont pas le même scope. | Copier |
| `sup/state.py:177-187` | Procéder sans verrou est un arbitrage de disponibilité assumé (un verrou coincé ne doit pas figer le superviseur), **mais jamais silencieux**. | Copier |
| `sup/state.py:33-51` | Sous pytest, tout writer qui résout vers l'arbre de données **vivant** lève. Nos tests écriront sous `~/logs/pithos2/`. | Copier |
| `our/agent_startup_checks.py:823-915` | `verify_system_state` — une vérification de démarrage qui émet **un seul événement JSONL typé** portant chaque contrôle et un verdict global. | Copier |
| `our/agent_startup_checks.py:916-929` | Réconciliation limitée aux **propriétaires prouvés morts d'une génération antérieure**. Un TTL n'autorise jamais un renvoi payant. | Copier |
| `our/agent_startup_checks.py:710-805` | `hot_store_growth_notes` — tripwire déterministe sur la croissance des stores chauds, surfacé au démarrage **et** à chaque tour. | Copier |
| `pk/systemd/ouroboros.service:1-24` | **Aucune politique de redémarrage** : *« the launcher owns its crash fuse and treats a panic exit as a complete stop until the owner starts Ouroboros again. »* Directement applicable à nos LaunchAgents. | Copier |
| `pk/systemd/README.md:1-40` | Un seul chemin de lancement par instance, verrou d'instance **partagé** par les deux chemins ; l'installation n'active ni ne démarre jamais l'unité. | Copier |
| `sk/telegram/lib/telegram_api.py:39-75` | Deux erreurs typées : `TelegramRequestRejected` (réponse négative explicite, `transient` = 429/5xx) et `TelegramTransportError` (pas de réponse). | Copier |
| `sk/telegram/lib/telegram_api.py:61-75` | Backoff **monotone partagé** par le poller et le notifier : 5 s → doublement → 60 s, **remis à l'initial par tout tour réussi**. | Copier |
| `sk/telegram/lib/telegram_api.py:24-36,82-113` | Découpe de texte en **unités UTF-16**, pas en caractères : la limite Telegram est en UTF-16 et un emoji en compte deux. | Copier |
| `sk/telegram/lib/telegram_state.py:37-70` | `_jsonl_tail` renvoyant `(lignes, un_préfixe_a_été_omis)` — un tail borné **déclare** son omission. | Copier |
| `od/DEVELOPMENT.md:494-541` | Invariant **Projection over replay** : un lecteur *par interaction* ne rejoue jamais un store qui grandit. Par-boot est autorisé. **Notre choix « index JSONL au démarrage » est conforme** — voir conflit n°7. | Copier |
| `our/observability.py:262-340` | `write_blob` / `read_blob_ref` — au-delà d'un seuil le payload devient un **ref content-addressé** ; le résumé porte le ref, jamais la copie. | Copier |
| `our/_outcome_receipts.py:529-670` | `receipt_identity_projection` et `verification_receipt_ledger_row` — projection destinée au relecteur portant **le compte omis et un hash durable de l'identité complète** ; une ligne de registre par reçu, prête pour le dashboard. | Adapter |
| `our/outcomes.py:1387-1525` | `build_verification_ledger` — registre par tâche construit depuis **les seuls faits d'exécution faisant autorité**, jamais une reformulation. | Adapter |
| `sup/state.py:772-917` | `status_text` — rendu texte compact de l'état complet, réutilisé par le CLI, Telegram et le dashboard. **Une seule vue, trois transports.** | Copier |

### D3.9 — Discipline de dépôt

| Source | Notion | Verdict |
|---|---|---|
| `our/review.py:19-26,292-830` · `our/size_ratchet_manifest.py` | **Ratchet de taille** : manifeste généré, dette shrink-only, bande à justification obligatoire et immuable, comptes d'octets décroissants, correspondance exacte avec l'inventaire vivant. | Adapter |
| `our/review.py:540-602` | `validate_manifest_transition` — baselines immuables, dette nouvelle = erreur, justification abandonnée = « blanchiment ». Forme **paire** (base contre tip), pas d'archéologie d'historique. | Copier |
| `od/DEVELOPMENT.md:463-471` | Une gate de taille est une **pression à réduire la complexité totale**, pas une raison d'extraire un module frère. En conflit, **signaler**. | Inspirer |
| `BIBLE.md:564-622` | DRY/SSOT étendu aux docs, prompts, configs ; emplacements canoniques **nommés** ; **seuil de relisibilité** comme signal de conception. | Inspirer |
| `BIBLE.md:412-429` | **Filtre de pression interne.** *Self-started does not mean self-exempt.* | Copier |
| `od/DEVELOPMENT.md:127-180` | **Anti-pattern : identité dérivée du contenu pour un enregistrement créé par l'hôte.** L'identité est capturée à l'ingress et passée par valeur ; un hash de contenu ne sert que de contrôle d'intégrité. Quatre incidents en série avant la règle. | Copier |
| `BIBLE.md:679-726` | Invariant de release, et **opérations exemptes de gate** : un rollback mécanique restaure un état déjà revu ; le bloquer piégerait l'agent avec du code cassé qu'il ne peut pas annuler. | Copier |

## D4. Ce qu'il ne faut pas reprendre d'Ouroboros

| Source | Poids | Raison |
|---|---:|---|
| `our/loop.py`, `our/llm.py`, `our/tools/registry.py`, `sup/workers.py`, `sup/events.py`, `server.py` | ~23 500 L | Les cinq monolithes. Notions justes, ossature supposant le plan superviseur multiprocess et le `ToolContext` à trente champs. |
| Couche `delegate_*` / `claudexor_*` — **sauf `delegate_pending.py`** | ~12 000 L | Custody de sessions d'agents délégués. Notre mode `direct` n'a pas de sous-session, et la souveraineté exclut un runtime tiers dans la boucle. |
| `usage_accounting.py` + `pricing.py` + `cost_projection.py` | ~3 500 L | Comptabilité **monétaire** multi-fournisseurs. Notre modèle est local et gratuit, notre budget est mural. Le substrat `usage_ledger.py` est repris, la politique non. |
| `review_*.py` / `triad_review.py` | ~10 000 L | **Revue multi-modèles à quorum. Contredit frontalement la décision 2** : notre autorité est un invariant exécuté, pas un jury. Seuls `review_evidence.py` et le ratchet de `review.py` sont repris. |
| `our/gateway/` + `web/` | ~70 000 L | Boundary HTTP/WS et SPA complets. Nous portons le React de v1. |
| `devtools/benchmarks/` | 34 622 L | Adaptateurs Terminal-Bench / OSWorld / SWE-bench / GAIA. |
| `consciousness.py`, `reflection.py`, `memory.py`, `consolidator.py` | — | Conscience de fond, mémoire biographique, identité persistante. **C'est la thèse d'Ouroboros, pas la nôtre** : notre continuité est l'arbre plus le registre, sans mémoire narrative. |
| `extension_loader.py` + `marketplace/` | ~4 000 L | Chargeur de plugins in-process. Notre auto-extension passe par la config MCP (décision 7). |
| `our/safety.py:1-8` | — | La garde de sécurité **appelle un light-model** sur les outils inconnus. **Contredit l'esprit de la contrainte dure n°1** : une décision de politique prise par un modèle. La partie déterministe reste valable. |
| Le `-p xdist -p timeout` forcé de `preflight_runner` | — | Spécifique à pytest-xdist. **La notion** — une gate doit prouver qu'elle a tourné dans le mode annoncé — est reprise ; l'implémentation non. |

## D5. Conflits frontaux avec les décisions actées

| # | Notre décision | Position d'Ouroboros | Arbitrage |
|---|---|---|---|
| 1 | **13** — sans preuve d'effet, un nœud n'est pas vert | `receipt_absent` est un drapeau advisory **qui garde `solved`**, *« never a downgrade — anti-oscillation »* | **Garder notre gate dure.** Notre mode d'échec mesuré est le succès fantôme, pas l'oscillation. Reprendre le drapeau **binaire non accumulant** même en gate dure. |
| 2 | **5** — trois rejets consécutifs déclenchent l'arrêt | La récurrence n'est **jamais jetée** : elle incrémente un compteur, rouvre un item clos, élève le rang | **Amender.** Un doublon rejeté trois fois est un signal, pas du bruit. Compter la récurrence dans le registre et la faire remonter dans la proposition d'arrêt. |
| 3 | **5** — rejet lexical, **aucune** inference | Fingerprint exact d'abord, puis **un** appel light-model à **choix fermé, validé exactement, fail-open** | **Question ouverte.** L'appel respecte la contrainte n°1 à la lettre (choix dans une énumération fermée). Le lexical rate les reformulations. À trancher après mesure du taux de faux négatifs. |
| 4 | **8** — une seule borne murale | **Deux réserves distinctes** ; les confondre a amputé 54 min d'une tâche de 6 h | **Amender** — voir § D2.7. |
| 5 | **Spike n°2** — vérifier que `response_format` est appliqué strictement | `response_format` est une **intention** que le retry peut retirer et que certaines routes ignorent | **Reformuler le spike** — voir § D2.1. |
| 6 | `PROJECT.md` — Ling 16 k, « sans re-benchmark » | La fenêtre est une **preuve sourcée** ; `unknown` ⇒ fail-closed | **Compatible.** « Sans re-benchmark » porte sur la qualité du modèle, pas sur ses paramètres de service. Lire `n_ctx_train` sur `/v1/models`. |
| 7 | **10** — index JSONL en mémoire au démarrage | *Projection over replay* : par-boot autorisé, **par-interaction** non ; un nouveau store chaud s'enrôle dans la table de seuils **dans le même commit** | **Compatible, à durcir** avec l'enrôlement obligatoire et le tripwire de croissance. |
| 8 | Critère — aucune ligne JSONL jamais réécrite ni supprimée | `_quarantine_tail` préserve la queue déchirée en base64 **puis tronque** le fichier | **Garder notre règle.** Reprendre la quarantaine base64, **pas** la troncature : nouveau segment lié. |
| 9 | Critère — frontières d'import testées | Aucun équivalent : frontières documentées et surveillées par revue | **Garder notre règle.** Ses cycles d'import documentés montrent précisément ce qu'une gate absente laisse passer. |

## D6. Les neuf reprises prioritaires

Classées par « ferme un mode d'échec mesuré de v1 » d'abord. **Total estimé ~1 650 lignes portées** sur une
cible de 3 000 — cohérent avec la note d'`ARCHITECTURE.md` : *« une part significative n'est pas à écrire
mais à porter »*.

| # | Reprise | Ferme | Effort |
|---|---|---|---:|
| 1 | **Identité de vérification = clé typée**, tampon de rendu, projection partagée décideur/rapporteur | La réconciliation non transitive. **Notre clé de redondance a exactement cette forme.** | ~180 L |
| 2 | **Reçu attesté par l'hôte** : exécuter et attester dans le même acte ; un reçu non écrit retire l'attestation | Les 7 `completed` sans effet de v1 | ~200 L |
| 3 | **Attribution de mutation avec époques de baseline** | Attribuer au système des changements qu'il n'a pas faits, et le `baseline_stale` qui coince tout après le premier commit | ~250 L |
| 4 | **Registre append-only à séquence dense**, machine à états validée, queue en quarantaine (sans troncature) | Un JSONL corrompu qui se lit « comme vide », et la relecture intégrale à chaque lecture | ~220 L |
| 5 | **Deux réserves de budget mural**, seconde calibrée par EWMA, latch de l'ancre | L'amputation de la queue de chaque mission longue | ~90 L |
| 6 | **`disposition` sur chaque fichier du codeview** + `relevant_files`/`impact_files` avec raison | L'index qui ment par omission, et le contexte construit sans trace de pourquoi | ~200 L |
| 7 | **Gate hermétique** : worktree jetable, scrub d'environnement, refus de démarrer sans budget de rendu | La régression verte parce que l'environnement l'a rendue verte | ~250 L |
| 8 | **Ratchet de taille** shrink-only avec justification obligatoire | La cible « ~3 000 lignes » qui reste déclarative, et le seuil de relisibilité à 16 k | ~200 L |
| 9 | **Machinerie de la décision 16** : « effet inconnu » dérivé, « effectué » et « encore dû » en une transaction | La reprise qui rejoue un effet abouti | ~60 L |

**Les deux notions qui n'ont pas de ligne de code chez nous et qui devraient en avoir une** : le **filtre de
pression interne** (décision 24) et la **récurrence comptée** (décision 5 amendée).

## D7. Ordre de portage Ouroboros

| Phase | Reprises |
|---|---|
| **S** | `our/request_wire_custom_validation.py` entier (spike n°2 reformulé) · `our/local_model.py:579-617` (spike n°4) · `our/preflight_runner.py:1189-1330` (spike n°5) |
| **P0** | `our/utils.py:151-169,212-612,1381-1410` · `our/usage_ledger.py:41-48,200-477` · `our/observability.py:33-192,262-340,1083-1087,1378-1470` · `our/_outcome_receipts.py:50-64,131-300,344-460,462-530` · `our/outcomes.py:83-142,284-295` · `sup/state.py:33-51,918-1000` |
| **P1** | `our/tools/verify.py` entier · `our/preflight_runner.py:99-176,389-480,500-748,1189-1330` · `our/mutation_attribution.py:31-158,213-800` · `our/review_evidence.py:17-105` · `our/_outcome_receipts.py:687-806` · `our/commit_admission.py:30-228` |
| **P2** | `our/tools/edit_ops.py:79-157,208-239,573-730` · `our/shell_parse.py` · `our/tools/write_shape.py` · `our/argv_budget.py` · `our/runtime_mode_policy.py` · `our/code_intelligence.py:73-121,261-270,485-635,737-800` · `our/context_compaction.py:280-417,681-738` · `our/context_budget.py:38-93,171-254` · `our/context_layout.py:69-136` · `our/task_pacing.py:87-279,377-524` · `our/deadline_utils.py` |
| **P3** | `our/improvement_backlog.py:199-374,423-560` · `our/evolution_fingerprint.py` · `our/semantic_dedup.py:52-62` · `our/skill_loader.py:1-33` · `our/skill_readiness.py:13-110` · `our/contracts/skill_manifest.py:12-70` · `our/evolution_checkpoints.py:15-90` |
| **P4** | `our/process_custody.py:12-19,233-560` · `our/agent_startup_checks.py:710-929` · `pk/systemd/*` · `sk/telegram/lib/*` · `sup/state.py:177-187` |
| **P5** | `our/outcomes.py:1387-1525` · `our/_outcome_receipts.py:529-670` · `sup/state.py:772-917` · `our/task_tree_ledger.py:580-655` |
| **P6** | `our/tools/registry.py:1551-1571,1605-1616,1862-2030` · `our/mcp_client.py:62-72,180-250,335-400` |
| **P8** | `our/review.py:19-26,292-830` · `our/size_ratchet_manifest.py` · `od/DEVELOPMENT.md:127-180,463-471` · `BIBLE.md:412-429,564-622,679-726` |

## D8. Attribution

**MIT**, `Copyright (c) 2026 Anton Razzhigaev`. `CITATION.cff` demande la citation du papier
(🔗 [arXiv 2608.08311](https://arxiv.org/abs/2608.08311)) en cas d'usage en recherche. Portage littéral licite
avec conservation de la notice MIT dans le fichier dérivé.

---

# PARTIE E — Prime Agent

## E1. Pourquoi ce dépôt

Runtime d'agent codant de **Prime Intellect**, publié sous le slogan *« A Self-Improving RLM Harness »*
(🔗 [arXiv 2608.23552](https://arxiv.org/abs/2608.23552)). **MIT**, *Copyright (c) 2025 Mario Zechner /
Copyright (c) 2026 Prime Intellect*.

| | Lignes | Remarque |
|---|---:|---|
| TypeScript runtime | 173 298 | dont `coding-agent/src` = 125 780 |
| Tests TypeScript | 180 514 | ratio test/runtime > 1 |
| **Runtime Python `rlm/`** | **4 581** | **directement portable** |
| `SKILL.md` bundled | 1 026 | format identique au nôtre |

**Point de friction n°1 : c'est du TypeScript.** Presque tout est à **transposer**, pas à copier. La seule
exception, mais elle est majeure : `prime-agent-runtime/src/rlm/harness.py` (820 L) est **l'implémentation
Python de référence du continual harness**.

Alias : `ca/` = `packages/coding-agent/src/` · `rt/` = `prime-agent-runtime/src/rlm/` ·
`ag/` = `packages/agent/src/` · `sk/` = `packages/coding-agent/skills/`.

Verdicts : **Porter** (Python, littéral) · **Transposer** (notion juste, implémentation TS à réécrire) ·
**Inspirer** · **Écarter**.

### E1.1 — Ce qu'il apporte que les quatre autres n'ont pas

**C'est le seul dépôt qui implémente l'auto-amélioration au fil du cycle de vie de bout en bout.** Deux
abstractions revendiquées :

- le **RLM** — le contexte est une variable, outils et sous-agents sont des appels de fonction dans un REPL
  Python persistant ;
- le **Continual Harness** — prompts supplémentaires, mémoires, descriptions de skills et specs de
  sous-agents sont **de l'état durable que l'agent raffine par petites mises à jour adossées à des preuves**.

Le magasin porte quatre familles d'entrées, et trois d'entre elles ont un analogue direct chez nous :

| Famille | Contenu | Analogue Pithos |
|---|---|---|
| `prompt` | notes supplémentaires — **le prompt de base est immuable** | politique de nœud |
| `memory` | faits, décisions, échecs, préférences | mémoire de campagne |
| `skill` | capacité installée, avec `reference` et `arguments` | **entrée `registry.json`** |
| `subagent` | spec de délégation réutilisable | mode `agentic` différé |

**La règle qui rend le mécanisme sûr tient en trois lignes** (`ca/core/refinement/refinement.ts:680-682`) :
`validateEdit` refuse tout edit dont l'`id` est `base_system_prompt`. Le prompt de base n'est jamais réécrit,
seule la couche supplémentaire l'est. **C'est ce qui sépare « harness qui s'améliore » de « harness qui se
détruit ».**

### E1.2 — Le mécanisme, en huit points

| # | Étape | Source | Notion |
|---|---|---|---|
| 1 | Déclenchement | `ca/core/settings-manager.ts:23-28,905-920` | `enabled`, `turnInterval`, `compact`, `cooldownMs` — quatre valeurs clampées. **Le raffinement n'est jamais un appel libre du modèle.** |
| 2 | Gate de revue | `ca/core/refinement/refinement.ts:963-1012` | Un premier appel **bon marché** (4 096 tokens) répond `{shouldRefine, rationale, instructions}`. Le raffinement coûteux ne part que s'il est approuvé. |
| 3 | Prompt de revue | `:175-185` | *« Reject one-off noise, unsupported hypotheses, and transient tool outputs. »* La gate est explicitement **anti-bruit**, pas pro-mémorisation. |
| 4 | Planification | `:880-948` | `planRefinement` produit une **proposition d'edits, sans muter quoi que ce soit**. |
| 5 | Application | `:716-811` | Pure sur l'état passé ; un edit invalide est **enregistré `applied: false` avec son `error`** au lieu de faire échouer le lot. |
| 6 | Détection de conflit | `:735-749` | `baselineState` capturé **avant** l'appel modèle. Si l'entrée a changé pendant la génération, l'edit est refusé. |
| 7 | Persistance + audit | `:345-359,374-379` | Write-temp + `renameSync`, mode 0600 préservé ; historique JSONL append-only **hors du fichier d'état**. |
| 8 | Rebuild | `ca/core/agent-session.ts:8495-8496` | **L'amélioration prend effet au tour suivant, sans redémarrage.** |

**Le rollback** (`:813-845`) reconstruit une proposition inverse depuis les `before`/`after` de chaque edit,
**en ordre inverse**. C'est ce qui autorise à laisser un modèle faible écrire dans l'état du harness.

**Le scope** (`:269-343`) : deux magasins, global et local par session, superposés avec préfixage
`local:`/`global:` en cas de collision. Pendant un raffinement local, les entrées globales sont **lecture
seule**, et l'auto-refine n'écrit **jamais** en global.

### E1.3 — Trois écarts à nommer avant de porter

1. **Le raffinement de Prime Agent est piloté par la trajectoire conversationnelle** — 80 000 caractères de
   conversation sérialisés (`:906`). Notre décision 6 supprime la session agentique : **il n'y a pas de
   trajectoire**, il y a un arbre de nœuds avec leurs verdicts. Le substrat de preuve change complètement, et
   80 Ko ne rentrent pas dans 16 k.
2. **Le modèle écrit du texte libre dans l'état durable.** `content` est une chaîne arbitraire. Une entrée de
   harness atteint le **prompt**, pas l'**exécution** : la contrainte dure n°1 n'est pas violée — mais il faut
   le dire explicitement plutôt que l'invoquer à tort.
3. **Aucune vérification que le raffinement améliore quoi que ce soit.** `expectedOutcome` est une phrase
   générée, jamais évaluée. **Le mécanisme est une boucle ouverte** — précisément le mode d'échec que v1 a
   payé.

## E2. Ce que la reprise a changé dans la documentation

| Cible | Nature du changement |
|---|---|
| `ARCHITECTURE.md` | **Neuvième module `refinery`** |
| `EXPLANATIONS.md` | Décisions 6 et 7 amendées · décision 26 ajoutée |
| `ROADMAP.md` | **Phase P9 — Auto-amélioration** · spikes 6 et 7 · items P0 à P6 |

### E2.1 — Décision 26 : le continual harness, et la gate d'effet qui le ferme

Neuvième module, sous `campaign` dans l'ordre d'autorité, **~250 lignes**.

```text
refinery/store.py      HarnessEntry + HarnessState, portés de rt/harness.py
refinery/propose.py    proposition d'edits (déterministe d'abord, modèle en dernier recours)
refinery/gate.py       LA DIFFÉRENCE : accepter un edit seulement s'il est mesurablement bon
```

**Ce que Prime Agent donne tel quel** : le modèle de données versionné, les deux scopes, l'écriture atomique,
l'historique JSONL, le rollback par `before`/`after`, la détection de conflit par état de base, la détection
d'écriture concurrente par `mtime`, l'immuabilité du prompt de base, la gate de revue à deux modèles en
cascade, la cooldown, et les garde-fous de parsing JSON.

**Ce qu'on ajoute, et qui n'existe nulle part dans aucun des cinq dépôts :**

- Un edit `memory` ou `prompt` est **candidat**, pas appliqué. Il reste en **`shadow`** et n'entre au prompt
  qu'après N missions où le taux de nœuds verts ne s'est pas dégradé. **La gate rouge-avant a un analogue
  direct ici : l'entrée doit avoir un effet mesurable, sinon elle est rejetée comme tautologique.**
- Un edit `skill` **est déjà notre `registry.json`**. L'entrée de registre gagne `version`,
  `created_at`/`updated_at`, `source` et l'historique de raffinement — et **notre empreinte de vérification
  donne à Prime Agent la péremption qui lui manque**.
- L'`evidence` d'un événement de raffinement n'est pas la rationale générée mais **l'identifiant du nœud et
  le verdict d'invariant** qui l'ont produite. La règle `Opportunity.evidence` obligatoire de Villani,
  appliquée au raffinement.

Ordre de construction, cohérent avec l'inversion de la roadmap : **la gate avant le magasin, le magasin avant
l'appel modèle.**

**Défaut inversé** : `enabled: false` au socle. Prime Agent active l'auto-refine par défaut tous les 25 tours
— il tourne sur des modèles frontières, nous avons un 8B. Activation manuelle après mesure sur les dix
premières missions. Et la cooldown se compte **en nœuds terminés, pas en minutes** : sur une mission bornée en
temps mural, une cooldown de 20 minutes est mal calibrée.

**Placement** : le raffinement tourne **en fin de mission**, après finalisation et avant le rapport. Pas de
disconnect/reconnect à gérer, et le substrat de preuve est complet.

### E2.2 — Décision 7 amendée : `mcp.reload` ferme la boucle d'auto-extension

`rt/mcp.py:397-416,483-491` — **fermeture et réouverture d'un serveur MCP sans redémarrer le kernel**, sous
verrou par nom, génération courante remplacée atomiquement.

C'est le chaînon manquant de la décision 7. Notre formulation disait qu'un outil `verified` « devient
appelable par les nœuds suivants » — sans dire *quand*. Avec `reload`, il devient appelable **dans la mission
en cours**, ce qui rend la question expérimentale 4 mesurable dans une seule mission plutôt qu'entre deux
réveils.

Deux compléments : les outils sont **découverts au runtime et filtrés** par `enabledTools`/`disabledTools`
(`:261-283`) — un outil retiré du registre cesse d'être appelable sans redéploiement — et l'installation se
fait **par hash de `pyproject.toml`, en ordre topologique des dépendances**, avec un fichier de version dans
le venv (`ca/core/kernel/bootstrap.ts:554-560,738-813`).

### E2.3 — Décision 6 : Prime Agent est le contre-modèle le plus complet

À nommer explicitement, parce que c'est le seul dépôt qui prend l'option inverse **jusqu'au bout** : un seul
outil `ipython`, le modèle écrit du Python qui lit, édite, exécute et délègue dans un REPL persistant.

**On garde la décision 6.** Mais Prime Agent montre ce qu'on abandonne — la composition, la délégation
native, l'état qui survit entre les tours — et ce qu'on gagne : aucune surface d'exécution ouverte, aucun
REPL à sécuriser, et un modèle 8B qui n'a jamais à écrire de code de contrôle. Le rapport de force est clair
sur un modèle frontière ; il l'est dans l'autre sens sur un 8B.

Conséquence pratique : `rt/repl.py` est écarté pour son protocole de kernel IPC (~600 des 1 166 lignes), mais
`_snapshot_state`/`_restore_state` et le patron d'écriture atomique sont repris.

## E3. Catalogue complet des reprises

### E3.1 — `kernel`

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `journal` | `ca/core/event-log.ts:15-29` | **`EventLog` — substrat JSONL append-only crash-safe.** Le commentaire de tête est le contrat entier : append en une seule écriture `O_APPEND`, `fsync` à la demande. | Adapter |
| `journal` | `ca/core/event-log.ts:143-183` | `repairTailSync` — la réparation n'a lieu **qu'à l'append, jamais à la lecture** (*« a viewer may replay a live writer's log »*). Notre règle est encore plus stricte : nouveau segment lié, jamais de troncature. | Inspirer |
| `journal` | `ca/core/event-log.ts:158-175` | Tous les offsets sont des **offsets d'octets sur buffers bruts** — les indices de chaîne divergent dès le premier caractère UTF-8 multi-octets. | Adapter |
| `journal` | `ca/core/event-log.ts:39-52` | La vérification de taille et l'allocation voient **le même fd** : une croissance concurrente ne peut pas contourner la borne. `maxBytes`/`maxRecords` échouent en fermé. | Adapter |
| `journal` | `ca/core/semantic-edges.ts:6-28,82-95` | Journal d'événements bruts **plus un pli pur** qui en dérive les arêtes de causalité. Les événements sont écrits **avant les effets qu'ils décrivent** ; une arête n'est matérialisée que quand sa cible finit. | Inspirer |
| `journal` | `ca/core/semantic-edges.ts:426-470` | `deriveSemanticEdges` — pli pur, avec `pending` rendu quand une requête échoue. Un échec ne perd pas la causalité, il la reporte. | Inspirer |
| `journal` | `ca/core/semantic-edges.ts:118-149` | `hashTurnBody` — *« la réutilisation d'`Idempotency-Key` n'est sûre que pour un retry octet-identique »*. Notre politique d'idempotence Telegram et Git en dépend. | Traduire |
| `contracts` | `ca/core/refinement/refinement.ts:34-48` | `HarnessEntry` avec `version` incrémenté et `created_at` conservé à l'update. **Un `ToolEntry` de registre doit porter la même histoire.** | Adapter |
| `contracts` | `ca/core/goals.ts:10` | `GoalStatus` — **`budget_limited` est un statut, pas un échec.** Exactement notre décision 8 et la décision 23. | Traduire |
| `contracts` | `ca/core/goals.ts:100-123` | Type guard structurel **avant** toute désérialisation. Chez nous c'est Pydantic ; la discipline « ne jamais faire confiance à ce qu'on relit » est la même. | Inspirer |
| `codeview` | `ca/core/kernel/bootstrap.ts:686-712` | `hashRuntimeSource` — identité du runtime = **hash de contenu de tous les `.py` + `pyproject.toml`**. Tout changement de code ou de dépendance invalide automatiquement. | Adapter |

### E3.2 — `verifier`

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `gates` | `ca/core/autonomous.ts:284-348` | `runAutonomousQualityGates` — les gates tournent **avant que la session ait le droit de se terminer**, dans l'ordre déclaré, sortie au premier rouge. | Adapter |
| `gates` | `ca/core/autonomous.ts:294-311` | **Ne pas relancer une gate si l'arbre de travail n'a pas bougé.** Le compteur de tentative avance, le message dit pourquoi. **Ferme les six heures de boucle stérile de v1, à coût nul.** | Adapter |
| `gates` | `ca/core/autonomous.ts:374-423` | Empreinte d'arbre = `status --porcelain=v1 -z -uall --no-renames` + `diff --binary HEAD` + hash des non-suivis, avec **pathspec d'exclusion des artefacts**. | Adapter |
| `gates` | `ca/core/autonomous.ts:402-417` | **Un snapshot partiel est un non-snapshot** : sortie tronquée, timeout ou exit non nul ⇒ pas d'empreinte, donc pas d'égalité, donc la gate est relancée. Le repli est sûr. | Traduire |
| `gates` | `ca/core/autonomous.ts:446-469` | Un lien symbolique est hashé **par sa cible**, un non-fichier par `mode:size:mtime`, une erreur devient `error:<message>` **dans le hash** au lieu d'être avalée. | Adapter |
| `gates` | `ca/core/autonomous.ts:350-360` | Le feedback rendu au modèle porte **commande, tentative sur maximum, sortie bornée, horodatage ISO**. | Adapter |
| `gates` | `ca/core/autonomous.ts:581-586` | `outputAlreadyTruncated` propagé depuis le sous-processus : on n'annonce pas « tronqué » deux fois pour la même sortie. | Traduire |
| `verifier` | `ca/core/autonomous.ts:80,88-91` | `AutonomousDecision.reason` = `missing_terminal_evidence` / `gate_failed` / `not_needed` / `limit_reached`. **La décision porte sa raison**, pas un booléen. | Traduire |
| `verifier` | `ca/core/autonomous.ts:186-194` | **Les tokens de lecture de cache ne comptent pas dans le budget** : les compter cumulativement épuise le budget bien avant que le travail soit fait. | Traduire |
| `verifier` | `ca/core/refinement/refinement.ts:673-714` | `validateEdit` — validation **par cas fermés**, chaque refus renvoyant sa phrase. | Adapter |

### E3.3 — `bridge`

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `bridge` | `ca/core/refinement/refinement.ts:570-589` | `isIncompleteJson` — distingue une réponse **tronquée** (chaîne non fermée, profondeur > 0) d'une réponse **malformée**. `JSON.parse` décrit le fragment ; ceci nomme la cause. | Adapter |
| `bridge` | `:604-631` | `extractJsonObject` — trois voies : objet nu, bloc ```` ```json ````, découpe par accolades, avec re-diagnostic **sur le texte original**. **C'est le repli obligatoire quand la contrainte de schéma n'est pas appliquée** (décision 17). | Adapter |
| `bridge` | `:637-663` | Normalisation **sans jeter les champs invalides**, pour que la validation d'application puisse les nommer. | Traduire |
| `bridge` | `:199-205` | Budget de sortie **dérivé du modèle** (`min(model.maxTokens, plafond)`), avec le commentaire expliquant qu'une constante tronquerait « exactement les propositions multi-edits qui comptent le plus ». | Traduire |
| `bridge` | `:921-926` | **Forcer le mode non-raisonnant** pour tout appel devant rendre du JSON structuré. *« Un modèle qui dépense son budget en thinking ne rend pas de JSON final. »* Ling émet du raisonnement. | Traduire |
| `bridge` | `:936-941` | `stopReason === "length"` traité comme une **erreur nommée distincte**, avec un message qui dit quoi faire. Convergent avec Villani et Ouroboros. | Traduire |
| `bridge` | `ag/agent-loop.ts:106-143` | `PostTurnResult<T>` — statut discriminé plutôt qu'un `null` surchargé. | Inspirer |
| `bridge` | `ag/agent-loop.ts:47-79` | `raceWithAbort` — course entre l'opération et le signal, avec capture du rejet pour ne pas laisser d'exception non gérée. Convergent avec `pi/abort.ts:17`. | Inspirer |

### E3.4 — `workspace`

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `workspace` | `ca/core/refinement/refinement.ts:345-359` | Temp nommé `<pid>.<uuid>.tmp` **dans le même répertoire**, `renameSync` atomique, **mode du fichier existant préservé** (0600 pour un état de harness). | Adapter |
| `workspace` | `rt/repl.py:661-680` | `stage_temp` — temps uniques par `mkstemp` dans le répertoire cible, avec le piège nommé : *« a fixed '.tmp' name could alias the other final path »*. | Copier |
| `workspace` | `rt/repl.py:681-690` | **Stager les deux temps avant de remplacer quoi que ce soit** : tout échec jusqu'au premier `replace` laisse la paire précédente intacte. | Copier |
| `workspace` | `ca/core/tools/truncate.ts:1-38` | Troncature à **deux limites indépendantes**, la première atteinte gagne, **jamais de ligne partielle**, et la troncature **rend son bilan** (`truncatedBy`, totaux, limites appliquées). | Adapter |
| `workspace` | `ca/core/tools/truncate.ts:67,153,249` | `truncateHead` / `truncateTail` / `truncateLine` — **trois fonctions nommées plutôt qu'un `truncate(mode=...)`**. Conforme à notre règle « pas de booléen qui pilote le comportement ». | Traduire |
| `workspace` | `rt/bash.py:60-104` | **Buffer de sortie borné tête + queue roulante avec marqueur d'octets jetés.** Ferme le collecteur v1 à 1,3 Go et toute exécution de code produit qui imprime en boucle. | Copier |
| `workspace` | `rt/bash.py:711-727` | Code de sortie récupéré par **canal de statut sur fd dédié**, pas par le code de retour du shell. Une commande qui laisse un descendant vivant ne fausse plus le verdict. | Copier |
| `workspace` | `rt/bash.py:699-709` | `printf` résolu sur le **PATH système par défaut**, avec six lignes expliquant qu'une fonction shell homonyme casserait le protocole. | Copier |
| `workspace` | `rt/bash.py:740-751` | `_signal_group` — `True` quand le signal est délivré **ou** que le groupe est déjà mort ; `False` seulement s'il n'a pas été délivré. | Copier |
| `workspace` | `rt/bash.py:731` | `NO_COLOR=1`, `TERM=dumb`, `CLICOLOR=0`, `FORCE_COLOR=0` sur tout sous-processus. **Notre `verifier` parse du pytest : les codes ANSI dans un contre-exemple le cassent.** | Copier |
| `workspace` | `ca/core/kernel/bootstrap.ts:439-472` | Verrou-répertoire à côté du venv, pour que deux sessions concurrentes n'installent pas en même temps. | Adapter |
| `workspace` | `ca/core/orphan-process-journal.ts:24-50` | Journal append-only `{pid, ownerPid, kernelPid, processStartId, active}` avec `fsync`. *« Process identity is pid + start time. »* | Adapter |
| `workspace` | `rt/mcp.py:26-95` | `_StderrTail` — stderr d'un serveur enfant en **tail borné (8 Ko / 40 lignes)**, strip ANSI et caractères de contrôle. | Copier |
| `workspace` | `rt/mcp.py:28` | `_SAFE_ENV` — l'environnement d'un serveur stdio est réduit à `HOME`, `PATH`, `TMPDIR`, `TEMP`, `TMP`. Version radicale du `runner_private_roots` de Villani. | Copier |
| `workspace` | `rt/mcp.py:249-261` | Rédaction du stderr diagnostique : les valeurs de configuration ≥ 4 caractères sont masquées ; **si une valeur est plus courte, tout le stderr est supprimé**. | Copier |

### E3.5 — `engine`

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `walk` | `ag/agent-loop.ts:304-450` | **Points d'extension nommés dans la boucle** (`shouldStopAfterTurn`, `getSteeringMessages`, `getFollowUpMessages`, `getContinuationMessages`) : une boucle, plusieurs politiques. | Adapter |
| `walk` | `ag/agent-loop.ts:404-410` | *« Steering drained by this poll owns the turn boundary; stop only when it was empty. »* **Une interruption arrivée au moment de l'arrêt gagne contre l'arrêt.** Précédence explicite. | Traduire |
| `walk` | `ca/core/autonomous.ts:45-46` | Prompt de continuation pour un contexte sans humain : *« If you believe you are blocked, prove it with host-observable evidence. »* | Inspirer |
| `walk` | `ca/core/autonomous.ts:48-61` | `DEFAULT_AUTONOMOUS_LIMITS` — 3 continuations / 12 tours / 80 000 tokens / 30 min ; gates 3 retries / 5 min. Point de départ chiffré. | Inspirer |
| `walk` | `ca/core/autonomous.ts:227-252` | **Les gates sont interrogées avant les limites.** Une gate verte arrête proprement même s'il reste du budget ; une gate rouge sur budget épuisé est nommée comme telle. | Traduire |
| `walk` | `ca/core/autonomous.ts:135-155` | Activer l'autonomie **remet à zéro tous les compteurs et efface le dernier échec de gate**. Un redémarrage ne traîne pas l'état de la session précédente. | Traduire |
| `context` | `ca/core/compaction/compaction.ts:375-425` | `findCutPoint` — marche arrière en accumulant les tokens, coupe au **premier point valide** au-delà du seuil, jamais sur un résultat d'outil. | Adapter |
| `context` | `:334-352` | Une coupe **au milieu d'un tour** est nommée comme telle et déclenche un résumé de préfixe. | Traduire |
| `context` | `:181-210` | **Usage réel du dernier message assistant + estimation des messages postérieurs seulement.** On n'estime que ce qu'on ne peut pas mesurer. | Traduire |
| `context` | `:123-132` | L'output compte dans le contexte du tour suivant. Erreur classique, corrigée nommément. | Traduire |
| `context` | `:425-457` | Format de résumé **imposé section par section** : `Goal` / `Constraints & Preferences` / `Progress`. | Adapter |
| `context` | `:461-470` | **Mettre à jour** un résumé existant plutôt que le régénérer. | Adapter |
| `context` | `:458-459` | Quand un état hors-contexte survit à la compaction, le résumé doit **le dire au modèle**, sinon il redéfinit ce qu'il a déjà. | Traduire |
| `context` | `ca/core/compaction/utils.ts:24-71` | La liste des fichiers lus et modifiés est **extraite déterministement** et réinjectée. Zéro appel modèle. | Adapter |
| `engine` | `rt/repl.py:607-660` | `_snapshot_state` — sérialisation **par variable, indépendamment** : un objet non sérialisable est sauté **et rapporté**, au lieu d'abandonner tout le snapshot. | Copier |
| `engine` | `ca/core/kernel/state-snapshot.ts:19-37` | `SnapshotResult` / `RestoreResult` — `saved`, `skipped[{name, reason}]`, `pruned`, `bytes`. **La restauration rapporte ce qu'elle n'a pas pu revivre.** | Adapter |
| `engine` | `ca/core/side-question.ts:25,42-70` | Poser une question **sans polluer la conversation courante** : contexte recloné, outils interdits par le prompt **et** par le code. | Inspirer |

### E3.6 — `campaign` et `refinery`

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `refinery/store` | `rt/harness.py:94-122` | `HarnessEntry` / `RefinementEvent` en dataclass. À passer en Pydantic v2 — la structure est la bonne. | Copier |
| `refinery/store` | `rt/harness.py:199-275` | `load()` **défensif champ par champ** : type faux ⇒ défaut, `title`/`content` non-`str` ⇒ entrée sautée, fichier corrompu ⇒ état vide. **Un magasin écrit par un modèle doit se relire sans jamais lever.** | Copier |
| `refinery/store` | `rt/harness.py:179-197` | `_sync_from_disk` — relit si le `st_mtime_ns` a bougé. **Le kernel garde l'état en mémoire pendant que le host réécrit le même fichier** ; chez nous, dashboard, broker Git et mission concourent. | Copier |
| `refinery/store` | `rt/harness.py:129-139` | Une entrée `skill` **doit** porter un import et un callable. **Une capacité non appelable n'entre pas au registre.** | Copier |
| `refinery/store` | `rt/harness.py:60-68` | `_strip_scope_prefix` — accepte verbatim les ids affichés `local:`/`global:`. **Le modèle recopie ce qu'il a lu ; le harness le tolère au lieu de le refuser.** | Copier |
| `refinery/store` | `rt/harness.py:722-769` | `overview()` — rendu texte compact borné par famille, `args=`/`ref=` tronqués. C'est ce qui entre dans le prompt. | Copier |
| `refinery/propose` | `rt/harness.py:705-720` | `plan_refinement` — plan **déterministe en trois étapes, zéro appel modèle** : diagnostiquer / modifier la plus petite entrée utile / rejouer et enregistrer. | Copier |
| `refinery/store` | `rt/harness.py:145-177` | Mode `in_memory` comme **repli sûr quand la résolution de chemin échoue** : construire le repli ne peut pas relever l'erreur d'origine. | Copier |
| `refinery` | `ca/core/refinement/refinement.ts:680-682` | **Immuabilité du prompt de base** — trois lignes qui séparent « s'améliore » de « se détruit ». | Traduire |
| `refinery` | `:716-811,735-749` | Application pure sur l'état passé ; edit invalide **enregistré et non fatal** ; conflit détecté par état de base capturé avant l'appel. | Adapter |
| `refinery` | `:813-845` | **Rollback par reconstruction inverse** depuis les `before`/`after`, en ordre inverse. | Adapter |
| `refinery` | `:429-520` | Rendu **borné par famille** (6 entrées), compteur de débordement `+N more`, et les **cinq derniers raffinements visibles dans le prompt** — l'agent voit son propre historique d'amélioration. | Adapter |
| `refinery` | `:141-147` | Politique de portée (local par défaut) et **table de routage vers la plus petite famille pertinente** : délégation récurrente ⇒ subagent, procédure récurrente ⇒ skill, fait ⇒ memory. | Traduire |
| `refinery` | `:281-343` | `loadHarnessState` s'exécute **à chaque construction de prompt** ; corrompu ⇒ état vide. `mergeHarnessStates` superpose avec préfixage **seulement en cas de collision**. | Adapter |
| `registry` | `ca/core/goals.ts:125-181` | **Le modèle voit son budget restant**, il ne le devine pas. Un objectif persistant se réinjecte par un message de contexte, pas par mutation du prompt. | Traduire |
| `registry` | `ca/core/goals.ts:75-94` | Objectif borné à 4 000 caractères, budget entier positif. **Validation à l'entrée, pas à l'usage.** | Traduire |
| `campaign` | `rt/mcp.py:397-416,483-491` | **`reload(server)` — un outil vérifié devient appelable dans la mission en cours**, sans redémarrage. Décision 7 amendée. | Copier |
| `campaign` | `rt/mcp.py:261-294` | Découverte au runtime filtrée par `enabledTools`/`disabledTools` ; verrou d'appel par serveur, timeout, refus explicite si l'outil est inconnu ou désactivé. | Copier |
| `campaign` | `rt/mcp_base.py:307-333` | `_parse_result` — **point unique de désérialisation** d'un résultat MCP. Notre invariant `schema_conform` en a besoin. | Copier |
| `campaign` | `ca/core/kernel/bootstrap.ts:738-813` | Installation **par hash de `pyproject.toml`**, résolution des dépendances inter-skills, **ordre topologique**. | Adapter |
| `campaign` | `ca/core/kernel/bootstrap.ts:554-560,816-821` | Fichier de version dans le venv portant l'identité du runtime **et** la liste des skills installés. | Adapter |
| `campaign` | `ca/core/skills.ts:122-161` | **Nom d'outil = nom du répertoire parent**, `[a-z0-9-]`, ≤ 64 car. ; **description vide ⇒ outil non chargé**. | Traduire |
| `campaign` | `ca/core/skills.ts:202-255` | Détection à quatre conditions (`SKILL.md`, `pyproject.toml` racine, nom d'import valide, `src/<import>/__init__.py`). Une seule forme acceptée. | Traduire |
| `campaign` | `ca/core/skills.ts:443-475` | **Seules les métadonnées entrent au prompt de démarrage** ; le contrat complet est chargé à la demande. Divulgation progressive. | Traduire |
| `campaign` | `sk/skill-creator/references/python-skills.md` | **Le contrat complet d'un skill Python** : layout `src/`, `pyproject.toml` hatch, convention `run()`. Directement applicable au produit. | Inspirer |
| `campaign` | `rt/skill.py:14-37` | Pont skill Python → commande shell en 37 lignes, avec message d'erreur nommant la contrainte. | Copier |

### E3.7 — `lifecycle` et `broker`

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `verrou` | `ca/core/session-lease.ts:160-263` | **Verrou de mission par `pid` + heure de démarrage du processus.** Ferme le PID recyclé que le `RunLock` v1 ne savait pas distinguer. | Adapter |
| `verrou` | `:196-200` | `processStartId` absent ou illisible ⇒ **le détenteur est présumé vivant**. Le repli protège le travail en cours plutôt que le nettoyage. | Traduire |
| `verrou` | `:251-263` | Récupération d'un verrou périmé par **renommage atomique** vers `<dir>.stale-<pid>-<uuid>` puis suppression. Deux processus ne peuvent pas réclamer le même. | Adapter |
| `verrou` | `:36-60` | `release()` idempotent, **ne supprime que si le token correspond toujours**. Un verrou récupéré par un autre processus n'est pas détruit par le premier. | Traduire |
| `réveil` | `ca/core/cron-jobs.ts:1591-1598` | **`nextRunAt` est avancé à la réclamation, pas à la fin d'exécution.** Un job déjà réclamé est marqué `lastSkippedAt` : **les ticks manqués sont coalescés, jamais empilés.** | Adapter |
| `réveil` | `:758-775,1612-1620` | `recoverInterruptedDispatches` — au démarrage, les dispatches restés ouverts sont réconciliés. C'est notre item P0. | Adapter |
| `réveil` | `:966-999` | En cas d'exception pendant la réclamation, les dispatches déjà réclamés sont **explicitement remis en réconciliation** avant de propager. | Traduire |
| `réveil` | `:1000-1050` | **Une file par session cible** : deux jobs de la même session ne se marchent pas dessus. | Inspirer |
| `réveil` | `:1053-1077` | Un seul timer vers le prochain job dû, clampé, re-planifié après chaque exécution. **Pas de tick périodique.** | Adapter |
| `réveil` | `:25-27,1350-1378` | **Politique de délivrance pendant une mission active** : `steer` (interrompre le tour) vs `follow_up` (attendre la fin). | Traduire |
| `réveil` | `:1115-1120` | Intervalle minimum rejeté **à l'analyse**. Une borne basse dans le parseur vaut mieux qu'un garde dans la boucle. | Traduire |
| `lifecycle` | `ca/core/orphan-process-journal.ts:53-80` | Le journal est rejoué pour trouver les processus **encore actifs**, appariés par `pid` + `processStartId`. | Adapter |
| `lifecycle` | `ca/core/settings-manager.ts:187,355,523` | Deux couches fusionnées récursivement, **chaque couche gardant son erreur de parsing propre**. | Traduire |
| `lifecycle` | `ca/migrations.ts:1-3,31-60` | Migrations one-shot renommant la source en `<fichier>.migrated` **plutôt que la supprimer**, et sautant si la cible existe. | Traduire |

### E3.8 — `observatory`

| Cible | Source | Notion | Verdict |
|---|---|---|---|
| `observatory` | `ca/core/context-tree.ts:76-105` | **Usage propre du nœud vs usage total du sous-arbre**, calculé récursivement. Notre vue d'arbre en a besoin. | Adapter |
| `observatory` | `:250-320` | **L'arbre est reconstruit depuis les répertoires sur disque**, sans passer par le processus vivant. | Adapter |
| `observatory` | `:161-197` | Le statut d'un nœud est **dérivé de la branche d'entrées, jamais stocké**. Un statut stocké ment dès qu'un enfant change. | Traduire |
| `observatory` | `:55-74` | Libellé de nœud borné à 80 caractères, dérivé du premier message. Rendu lisible sans champ dédié. | Traduire |
| `observatory` | `ca/core/event-log.ts:73-111` | `replaySync(parse)` — **le parseur est injecté par le consommateur**, qui décide ce qu'il rejette et ce qu'il saute. Un même journal sert plusieurs vues. | Adapter |
| `observatory` | `ca/core/semantic-edges.ts:383-424` | La lecture renvoie **les événements valides et la longueur valide**, ce qui permet à l'écrivain de reprendre au bon offset. | Traduire |
| `observatory` | `sk/agent-observe/SKILL.md` | **Surface d'observation strictement en lecture seule, bornée par la famille** (parent, frères, enfants directs), `limit` 1-50 et `max_chars` 80-2000 imposés. | Inspirer |
| `observatory` | `ca/core/refinement/refinement.ts:508-517` | **L'historique d'auto-amélioration est visible dans le prompt lui-même** : `recent refinements: N`, les 5 derniers, `+N older`. | Traduire |

## E4. Ce qu'il ne faut pas reprendre de Prime Agent

| Source | Lignes | Raison |
|---|---:|---|
| `ca/core/agent-session.ts` | 12 136 | Le monolithe : session, queue, outils, compaction, goals, cycle de vie des enfants et raffinement dans une classe. **Cinquième dépôt, cinquième monolithe** — les notions sont bonnes, l'ossature est ce que notre découpe refuse. |
| `ca/modes/interactive/` | ~20 000 | TUI. |
| `ca/modes/daemon/` | ~25 000 | Superviseur multi-processus, leases, backpressure. Hors périmètre : une mission à la fois, sous verrou. `session-lease.ts`, `cron-jobs.ts` et `orphan-process-journal.ts` sont repris, le reste non. |
| `ca/modes/acp/`, `ca/modes/rpc/`, `ca/core/sdk.ts` | ~4 000 | Protocoles d'intégration. Aucun client externe. |
| `packages/ai/` | ~30 000 | Couche multi-fournisseurs. **Contraire à la souveraineté** — Villani fournit déjà le client OpenAI-compatible. |
| `packages/tui/` | ~12 000 | Bibliothèque terminal. |
| `ca/core/agent-traces.ts` | 1 170 | **Upload de traces vers un service distant.** Contraire à la contrainte dure n°5. |
| `ca/core/telemetry.ts` | 794 | Télémétrie produit. Même raison. |
| `auth-storage.ts`, `prime-inference-auth.ts`, `oauth.ts` | ~2 700 | OAuth et keychains. Aucun secret distant dans la boucle. |
| `ca/core/package-manager.ts` | 2 444 | Chargement d'extensions depuis npm et Git. Notre extension passe par le registre. |
| `ca/core/extensions/` | ~3 100 | Système d'extensions à hooks. **Point d'extension prématuré pour ~3 000 L de harness.** |
| `rt/_winjob.py` | 378 | Windows. |
| `rt/repl.py` § kernel IPC | ~600 | Protocole de kernel IPC, pompe d'événements. **Nous n'avons pas de REPL persistant** (décision 6). |
| `ca/core/refinement/refinement.ts:906` | 1 | `serializeConversation(...).slice(-80_000)`. **Inapplicable** : pas de trajectoire, et 80 Ko ne rentrent pas dans 16 k. |

## E5. Conflits frontaux avec les décisions actées

| Notion Prime Agent | Décision concernée | Arbitrage |
|---|---|---|
| **Tout est programmatique** : un seul outil `ipython`, le modèle écrit du Python qui lit, édite, exécute et délègue | **6** — mode `direct` | **Garder la décision 6.** Prime Agent est le contre-modèle le plus complet ; le rapport de force s'inverse sur un 8B — voir § E2.3. |
| Le modèle écrit du **texte libre** dans l'état durable | **Contrainte dure n°1** | **Compatible, à énoncer.** Une entrée de harness atteint le *prompt*, pas l'*exécution*. La frontière défendue n'est pas la même. |
| Le raffinement est une **boucle ouverte** — `expectedOutcome` jamais évalué | Critère de socle sur le mutation-check | **Fermer la boucle.** C'est l'apport propre du projet appliqué à l'auto-amélioration — voir décision 26. |
| **Sous-agents natifs**, specs de délégation comme quatrième famille | **6** — mode `agentic` différé | **Différer.** La famille `subagent` reste vide au socle : le magasin la supporte, rien ne l'alimente. |
| **Auto-refine activé par défaut**, tous les 25 tours | Prudence sur un 8B | **Inverser le défaut** : `enabled: false`, activation après mesure sur dix missions. |
| **Cooldown de 20 minutes** | **8** — borne murale | **Compter en nœuds terminés, pas en minutes.** |
| Raffinement **pendant** la session | **8** — finaliser les nœuds verts | **Déplacer en fin de mission**, après finalisation, avant le rapport. |
| Skills en `pip install -e` dans un venv partagé | **4** — le harness ne dépend jamais de FastMCP | **Compatible**, à condition d'un venv **distinct** de celui du harness. `ensure_runtime_dependencies_not_shadowed` reste requis. |

## E6. Les six reprises prioritaires

| # | Reprise | Source | Ce qu'elle ferme |
|---|---|---|---|
| 1 | **Le continual harness complet** — magasin scopé, versionné, rollbackable, prompt de base immuable | `rt/harness.py:94-820` · `refinement.ts:34-1031` | *« L'agent peut-il s'améliorer au fil de son cycle de vie ? »* — **la seule réponse implémentée des cinq dépôts** |
| 2 | **Ne pas relancer une gate sur un arbre de travail inchangé** | `ca/core/autonomous.ts:294-311` | Les six heures de boucle stérile de v1, **à coût nul** |
| 3 | **Verrou par `pid` + heure de démarrage** | `ca/core/session-lease.ts:160-263` | Le PID recyclé que le `RunLock` v1 ne savait pas distinguer |
| 4 | **Réclamation de tick avant délivrance, ticks manqués coalescés** | `ca/core/cron-jobs.ts:702-707,1584-1610` | Le réveil launchd qui rejoue ou empile après une suspension machine |
| 5 | **Buffer de sortie borné tête + queue** | `rt/bash.py:60-104` | Le collecteur v1 à 1,3 Go, et toute exécution de code produit qui imprime en boucle |
| 6 | **`mcp.reload(server)`** | `rt/mcp.py:397-416` | Le chaînon manquant de la décision 7 : un outil vérifié appelable **dans la mission en cours** |

**Ce que Prime Agent n'a pas** — cinquième dépôt, cinquième fois : aucune relation métamorphique, aucun
générateur de domaine, aucun mutation-check, aucune sortie contrainte par JSON Schema. Et surtout **aucune
vérification que le raffinement améliore quoi que ce soit**. Nous avons l'autorité de validation qui ferme
cette boucle : **c'est la combinaison qui est neuve, pas la moitié qu'on importe.**

## E7. Ordre de portage Prime Agent

| Phase | Reprises |
|---|---|
| **S** | Spike 6 : portage de `rt/harness.py` en Pydantic v2 — vérifier que la relecture défensive survit à la traduction, **Pydantic lève là où l'original dégrade** · Spike 7 : chronométrer l'empreinte d'arbre de travail (`ca/core/autonomous.ts:374-423`) |
| **P0** | `ca/core/event-log.ts:15-52,143-183` · `ca/core/goals.ts:10,100-123` · `ca/core/semantic-edges.ts:118-149` |
| **P1** | `ca/core/autonomous.ts:80-91,186-194,284-360,374-469,581-586` |
| **P2** | `rt/bash.py:60-104,699-751` · `rt/repl.py:607-690` · `ca/core/tools/truncate.ts:1-38,67-249` · `ca/core/compaction/compaction.ts:123-210,334-470` · `ca/core/compaction/utils.ts:24-71` · `ag/agent-loop.ts:304-450` · `ca/core/kernel/state-snapshot.ts:19-37` |
| **P3** | `ca/core/refinement/refinement.ts:141-147` · `ca/core/skills.ts:122-161,443-475` |
| **P4** | `ca/core/session-lease.ts:36-263` · `ca/core/cron-jobs.ts:702-707,758-775,966-1120,1350-1378,1584-1620` · `ca/core/orphan-process-journal.ts:24-80` · `ca/core/settings-manager.ts:187-523` · `ca/migrations.ts:31-60` |
| **P5** | `ca/core/context-tree.ts:55-320` · `ca/core/event-log.ts:73-111` · `sk/agent-observe/SKILL.md` |
| **P6** | `rt/mcp.py:26-95,249-294,397-416,483-491` · `rt/mcp_base.py:307-333` · `ca/core/kernel/bootstrap.ts:439-472,554-560,686-712,738-821` · `ca/core/skills.ts:202-255` · `rt/skill.py:14-37` |
| **P9** | `rt/harness.py` entier · `ca/core/refinement/refinement.ts` entier · `ca/core/goals.ts:75-181` |

## E8. Attribution

**MIT**, *Copyright (c) 2025 Mario Zechner / Copyright (c) 2026 Prime Intellect*. Aucun point ouvert : le
portage littéral est licite avec conservation de la notice MIT dans le fichier dérivé — en pratique
`rt/harness.py`, `rt/bash.py` et `rt/mcp.py`, les trois blocs Python repris le plus près du texte d'origine.

---

# PARTIE F — Unsloth

## F1. Pourquoi ce dépôt, et pourquoi il est différent

**5 386 entrées, ~2 161 259 lignes.** Unsloth n'est **pas** un runtime d'orchestration de nano-étapes : c'est
une bibliothèque de fine-tuning. Les kernels CUDA, l'entraînement RL et l'optimisation MoE sont hors
périmètre par construction.

**Sa valeur pour nous est ailleurs, et elle est réelle** : `unsloth_cli/` et `studio/backend/` contiennent une
infrastructure d'**exposition réseau, de cycle de vie de processus, de politique d'outils MCP et de gestion
de secrets** qu'aucune des cinq sources précédentes ne couvre avec ce niveau de détail. C'est le seul dépôt
qui traite frontalement la question « à quelles conditions un service local a-t-il le droit d'être joignable
de l'extérieur ».

Statuts : **S** socle à reprendre · **A** adapter · **I** inspirer · **X** écarter.
Chemins relatifs à `resources/unsloth-main/`.

### F1.1 — Le point de licence, à trancher

**C'est la seule source des six qui n'est pas MIT de bout en bout.** Le dépôt **mélange une licence AGPL pour
Studio** avec d'autres notices ; l'étude d'extraction le note explicitement (`LICENSE:1`) :

> Toute copie substantielle exige une revue juridique fichier par fichier.

Les reprises les plus directement utiles — `studio/backend/lan_access.py`,
`studio/backend/cloudflare_tunnel.py`, `studio/backend/mcp_server.py` — sont précisément celles qui vivent
sous `studio/`. Deux remarques factuelles :

- Les obligations AGPL se déclenchent à la **distribution** ou à la **mise à disposition via un réseau**.
  Un harness personnel exécuté localement, non distribué, ne les déclenche pas.
- Le contenu repris ici est en très large majorité de nature **conceptuelle** — un prédicat, un ordre
  d'opérations, une règle. Les entrées marquées *Inspirer* et *Adapter* ne posent aucune question ; seules
  les entrées **S** portées quasi littéralement le feraient.

**Décision retenue** : reprendre les notions, réécrire le code. Aucune copie littérale depuis `studio/`.

### F1.2 — Ce que ce dépôt apporte que les cinq autres n'ont pas

1. **Une politique d'exposition réseau complète** — prédicat `is_public_address` partagé par le bind,
   l'affichage et la politique d'outils ; détection d'adresse externe incluant résolution DNS et IP littérale ;
   normalisation des binds wildcard **avant** d'évaluer l'exposition.
2. **Le cycle de vie complet d'un service local exposé** — readiness observable sous deadline, arrêt
   idempotent, fermeture de tous les sockets partiellement ouverts sur échec de bind, et **jeton de
   génération pour qu'une ancienne instance ne tue pas la nouvelle**.
3. **La garde des répertoires système** — `_system_dir_guard.py` protège les chemins de configuration contre
   les écritures de l'agent, dimension que notre décision 12 (`authoritative`) ne couvrait pas.
4. **Les bornes de ressources matérielles** — espace disque mesuré **avant** écriture, transformé en `blocked`
   mécanique ; nettoyage de cache entre étapes ; parallélisme dérivé des ressources avec repli mono-processus.

## F2. Ce que la reprise a changé dans la documentation

| Cible | Nature du changement |
|---|---|
| `EXPLANATIONS.md` | Décisions 8, 12 et 21 amendées · **décision 27 ajoutée** |
| `PROJECT.md` | 2 critères ajoutés |
| `ROADMAP.md` | Items P0, P2, P4, P5, P7bis |

### F2.1 — Décision 27 : la politique d'exposition réseau

`PROJECT.md` diffère l'ouverture LAN du dashboard, et v1 l'avait diffèrée aussi — sans jamais écrire de
politique. « Différé » n'est pas une règle : c'est l'absence de règle, et elle se transforme en ouverture
accidentelle au premier `--host 0.0.0.0` tapé pour déboguer.

Unsloth écrit la politique complète, et elle tient en quatre pièces :

- **Un prédicat unique `is_public_address`** (`studio/backend/lan_access.py:213`) partagé par le bind,
  l'affichage et la politique d'outils. Trois consommateurs, une seule définition — sinon l'un des trois
  finit par autoriser ce que les deux autres refusent.
- **La détection d'adresse externe couvre la résolution DNS et l'IP littérale**
  (`unsloth_cli/_tool_policy.py:19`), et les **binds wildcard sont normalisés avant évaluation**
  (`:108`). Un `0.0.0.0` qui se lit « local » parce que personne ne l'a normalisé est la faille type.
- **L'exposition des outils dépend de l'adresse de bind** (`_tool_policy.py:165`) : une surface d'outils
  accessible en loopback ne l'est pas automatiquement en LAN. Chez nous, le dashboard est en lecture seule —
  mais le serveur MCP construit par la campagne, lui, expose des outils.
- **L'énumération des adresses LAN n'inclut jamais aveuglément loopback ni les interfaces hôte-only**
  (`lan_access.py:72`).

S'y ajoute le cycle de vie, qui vaut pour tout service local que le harness démarre : **ne jamais considérer
le spawn comme un succès** — attendre une readiness observable sous deadline (`cloudflare_tunnel.py:507`) —
fermer **tous** les sockets partiellement ouverts sur échec de bind en conservant la cause (`:370`), et
arrêter avec un **jeton d'admission/génération** pour qu'une ancienne instance ne tue pas la nouvelle
(`:930`).

Ce dernier point est directement applicable à notre LaunchAgent : deux réveils rapprochés, le premier lent à
mourir, et le second se fait tuer par le nettoyage du premier.

### F2.2 — Décision 8 amendée : un seul deadline propagé

`unsloth/dataprep/synthetic.py:162,172` — **un seul deadline monotonique de mission, propagé à toutes les
sous-opérations**, plutôt que des timeouts indépendants qui s'additionnent.

Notre décision 8 pose deux réserves murales ; elle ne disait pas comment ce budget atteint un `subprocess` de
vérification ou une requête au modèle. Sans propagation, chaque sous-opération a son propre timeout, et la
somme dépasse la borne de mission — exactement le cas où une mission de 20 minutes se termine à 35.

Corollaire du même module (`:52`) : **terminaison récursive d'un arbre de processus avec timeout de
nettoyage**. Sixième source à le dire, après Pi, Kilo et Prime Agent : on arrête le groupe, jamais le seul
parent.

### F2.3 — Décision 12 amendée : la garde des répertoires système

Le prédicat `authoritative` décide de ce qui est *proposable et modifiable dans le workspace*. Il ne dit rien
des chemins **hors workspace** — `~/.config`, `~/Library`, les répertoires système.

`unsloth_cli/_system_dir_guard.py` ajoute cette seconde ligne : une liste nommée de répertoires système et de
chemins de configuration protégés contre toute écriture de l'agent, indépendamment du prédicat de workspace.
Notre `verifier` exécute du code écrit par le modèle en `subprocess` : ce code n'a aucune raison de toucher
`~/.prefect`, `~/Library/LaunchAgents` ou la configuration Git globale.

### F2.4 — Décision 21 amendée : le confinement a une dimension réseau

Notre décision 21 retient `sandbox-exec` pour le confinement **filesystem** de l'exécution du code produit.
Le profil seatbelt de Kilo porte aussi une politique réseau (`kilo/opencode/src/kilocode/sandbox/network.ts`),
mais nous ne l'avions pas nommée.

Le code produit exécuté par le `verifier` n'a **aucune raison légitime d'ouvrir une socket**. La politique
réseau du profil est donc « refus par défaut », et la seule exception envisageable — un outil MCP dont le
cœur pur fait un appel — est précisément ce que la décision 4 interdit : le cœur est pur, la coquille porte
l'I/O, et la coquille n'est pas ce qui tourne sous invariant.

### F2.5 — Critères de socle ajoutés

- **Aucun service local n'est déclaré prêt sur la base de son spawn** : une readiness observable est attendue
  sous deadline, et un arrêt confirme son état de sortie.
- **L'espace disque est vérifié avant écriture d'un snapshot, d'une trace ou d'un artefact** ; l'insuffisance
  est un `blocked` mécanique avec cause, jamais une exception d'écriture.

## F3. Catalogue des reprises

### F3.1 — `kernel`

| S | Source | Notion |
|---|---|---|
| S | `unsloth/device_type.py:62,100` | Résolution **unique** du backend derrière un prédicat mis en cache ; comptage des devices une seule fois, configuration impossible refusée **avant lancement**. |
| A | `unsloth/device_type.py:238` | Snapshot de statistiques matérielles pour diagnostiquer timeout, OOM et absence de progrès — **jamais une preuve de correction**. |
| S | `unsloth/device_type.py:257` | Nettoyage explicite du cache entre deux nano-étapes ou après échec, **sous contrôle de `lifecycle`**. |
| A | `unsloth/disk_utils.py:83` | Mesurer l'espace libre **avant** écriture ; transformer l'insuffisance en `blocked` mécanique. |
| A | `unsloth/disk_utils.py:109` | Estimer la taille logique d'un artefact avant export, pour réserver le budget disque. |
| S | `unsloth/disk_utils.py:120` | Rediriger les temporaires vers un emplacement contrôlé quand l'environnement impose un filesystem éphémère. |
| S | `unsloth/dataset_num_proc.py:1` | Parallélisme déterminé **à partir des ressources**, avec borne et **repli mono-processus**. |
| S | `unsloth/chat_templates.py:1885` | **Choix et normalisation du chat template centralisés** : l'exécuteur ne reçoit jamais un template arbitraire du modèle. Converge avec la contrainte dure n°1. |
| A | `unsloth/chat_templates.py:2168` | Retirer les tokens spéciaux d'une vue de prompt **avant comparaison ou archivage**, pour éviter des faux changements. |
| A | `unsloth/chat_templates.py:2370` | Déduire les EOS effectifs du tokenizer et **les consigner dans le contrat d'exécution**. |
| S | `unsloth/utils/hf_hub.py:27,47` | Résolution de métadonnées par **fonction pure et sérialisable** ; lister sans charger les poids. |
| A | `unsloth/models/loader_utils.py:1694,1900` | Détecter explicitement le mode **offline** et l'inscrire dans l'événement de mission ; réinitialiser les sessions après erreur pour qu'**un état global contaminé ne traverse pas les missions**. |
| S | `unsloth/models/loader_utils.py:2079,2156` | Retry offline **avec diagnostic typé** ; vérifier la présence locale des fichiers **avant tout appel réseau**. |

### F3.2 — `verifier`

| S | Source | Notion |
|---|---|---|
| S | `tests/test_torchao_nf4tensor_move.py:191` | **Tester l'absence d'import eager d'une dépendance optionnelle.** Applicable à nos frontières d'import : le test de graphe de la décision 22 y trouve son complément. |
| S | `tests/test_torchao_nf4tensor_move.py:152` · `tests/test_peft_symbol_backfill.py:96` | **Idempotence des correctifs et des patches d'initialisation** : un mécanisme de compatibilité exécuté deux fois ne modifie plus l'état. |
| A | `tests/test_peft_symbol_backfill.py:136` | Annoncer explicitement une fonction de mapping manquante, **avec une catégorie de panne exploitable**. |
| A | `tests/test_deliberate_crashes_suppress_cores.py:140` | Éviter les introspections AST coûteuses dans les chemins de test ; **borner les diagnostics**. |
| S | `unsloth/models/loader_utils.py:1522` | Refuser une combinaison incompatible **avant exécution**, plutôt que laisser le backend échouer tard. |
| S | `unsloth/models/loader_utils.py:180` | **Normaliser les kwargs pour que deux configurations sémantiquement égales aient la même empreinte.** Directement applicable à notre clé de redondance (décision 22). |
| A | `unsloth/models/loader_utils.py:326` | Résolution avec **repli explicite et raison** — utile pour expliquer un `blocked`. |
| S | `unsloth/models/rl.py:973,987` | **Empreinte d'un dataset borné, invalidée dès qu'une mutation change le contenu** ; token de mutation pour invalider un cache entre deux cycles. Même mécanisme que notre satisfaction périmée. |
| A | `unsloth/models/rl.py:906,1005` | Contrôler une limite **après matérialisation** et vérifier que la borne tient **au moment de l'usage**, pas seulement à la déclaration. |
| X | `unsloth/models/rl_replacements.py:526` | Remplacements regex de fonctions tierces : **trop fragiles**. Conserver l'idée d'un patch versionné, pas le mécanisme. |

### F3.3 — `bridge` et le produit MCP

| S | Source | Notion |
|---|---|---|
| S | `studio/backend/mcp_server.py:86` | **Fabrique FastMCP unique avec liste d'outils explicitement enregistrée.** Aligne directement la surface du produit sur `registry.json`. |
| S | `studio/backend/mcp_server.py:20` | Middleware bearer token **exact, non vide et ASCII**, validé avant toute exposition distante. |
| S | `studio/backend/mcp_server.py:77` | **Borner (`clamp`) les entiers fournis par MCP avant appel de route.** Ne jamais faire confiance au client. |
| S | `studio/backend/mcp_server.py:97` | Outil de statut **read-only** comme sonde de santé minimale. |
| A | `studio/backend/mcp_server.py:126` | **Séparer les outils de lecture des outils de mutation.** Deux familles, deux politiques. |
| S | `studio/backend/mcp_server.py:166` | **Valider une recette sans lancer le job** : une gate de schéma avant mutation. |
| A | `studio/backend/mcp_server.py:70` | Convertir les réponses Pydantic en JSON plat avant émission MCP, pour conserver une **trace portable**. |
| S | `unsloth_cli/_inference.py:259` | **Séparer texte visible et thinking** avant projection d'une réponse. **Sixième source à le dire.** |
| S | `unsloth_cli/_inference.py:318` | Transformer une erreur de stream en **exception structurée avant d'écrire un événement de succès**. |
| S | `unsloth_cli/_inference.py:634,650` | **Refuser les URL hors loopback** pour les connexions de contrôle locales ; **vérifier l'identité du serveur** avant de lui transmettre une requête. |
| A | `unsloth_cli/_inference.py:616,752` | Découverte d'un serveur local avec candidats loopback et timeout court ; `ensure_loaded` **séparé** du streaming. |
| A | `unsloth_cli/commands/start.py:1591` | Résoudre une clé par **priorité documentée** (cache, configuration, environnement) — **jamais par le modèle**. |
| S | `unsloth_cli/claude_subagent_mcp.py:60,84,135` | Pont stdio vers un agent local : tâche bornée, **sortie capturée et bornée avant inclusion dans la trace**, arrêt propre du child **et de son groupe**. |
| S | `unsloth_cli/codex_subagent_mcp.py:85` | **Aucune détection implicite du provider** : contrat de tâche stable, variante explicite. |
| A | `unsloth_cli/pi_subagent.ts:67` | **Limiteur de slots concurrents** pour sous-agents, à adosser au budget de mission. Utile au mode `agentic` différé. |
| S | `unsloth_cli/pi_subagent.ts:105` | Signaux envoyés **au process group**, pas seulement au parent. |

### F3.4 — `workspace` et `lifecycle` — la politique réseau

| S | Source | Notion |
|---|---|---|
| S | `unsloth_cli/_tool_policy.py:165` | **Politique unique décidant si des outils peuvent être exposés**, selon l'adresse de bind et le mode sécurisé. |
| S | `unsloth_cli/_tool_policy.py:19` | Détection d'adresse externe **incluant résolution DNS et IP littérale**, avant ouverture réseau. |
| S | `unsloth_cli/_tool_policy.py:108` | **Normaliser les binds wildcard avant** d'évaluer l'exposition. Un `0.0.0.0` non normalisé qui se lit « local » est la faille type. |
| S | `studio/backend/lan_access.py:213` | Prédicat **`is_public_address` partagé** par le bind, l'affichage et la politique d'outils. Trois consommateurs, une définition. |
| S | `studio/backend/lan_access.py:72` | Énumérer les adresses LAN **sans inclure aveuglément** loopback ni interfaces hôte-only. |
| S | `studio/backend/lan_access.py:370` | Sur échec de bind, **fermer tous les sockets partiellement ouverts et conserver la cause**. |
| S | `studio/backend/lan_access.py:350` | Synchroniser l'état de confiance réseau avec **l'état réel du listener**, jamais avec le seul flag CLI. |
| S | `studio/backend/lan_access.py:423,497` | Arrêt **idempotent** libérant tous les sockets ; décision d'accès **par requête**, centralisée et testable. |
| S | `studio/backend/cloudflare_tunnel.py:507` | **Ne jamais considérer le spawn comme un succès** : attendre une readiness observable sous deadline. |
| S | `studio/backend/cloudflare_tunnel.py:354,516` | Vérifier une URL par **probe** avant de l'annoncer prête ; **confirmer l'état de sortie** avant de finaliser. |
| S | `studio/backend/cloudflare_tunnel.py:930` | Arrêt avec **jeton d'admission/génération** pour qu'une ancienne instance ne tue pas la nouvelle. Directement applicable à deux réveils launchd rapprochés. |
| A | `studio/backend/cloudflare_tunnel.py:217,400` | Téléchargement d'un binaire externe **dans un cache contrôlé uniquement**, avec vérification d'existence ; encapsulation en objet à `start`/`wait_for_ready`/`stop`/`is_running`. |
| S | `unsloth_cli/_system_dir_guard.py:1` | **Protéger les répertoires système et les chemins de configuration** contre les écritures de l'agent. Seconde ligne derrière le prédicat `authoritative`. |
| S | `unsloth_cli/commands/start.py:1507` | **Écriture texte privée avec permissions restrictives** pour secrets et tokens. |
| A | `unsloth_cli/commands/start.py:1498,1569` | Écriture JSON privée atomique ; **tester une clé contre le serveur avant de la mémoriser**. |
| S | `unsloth_cli/commands/start.py:1191` | **Ne pas tuer un serveur encore utilisé par une session active** : le propriétaire est explicite. |
| S | `unsloth/dataprep/synthetic.py:52,148,162` | **Terminaison récursive d'un arbre de processus** avec timeout de nettoyage ; readiness attendue explicitement ; **deadlines monotoniques partagés** entre subprocess, serveur et nettoyage. |
| A | `unsloth/dataprep/raw_text.py:56,98,346` | Détecter le format **avant lecture** ; chunking à longueur et chevauchement explicites ; validation de dataset **avant écriture**. |
| S | `unsloth/dataprep/raw_text.py:125` | Chunking préservant les **frontières sémantiques**, avec stride mesuré. |

### F3.5 — `engine`

| S | Source | Notion |
|---|---|---|
| S | `unsloth/dataprep/synthetic.py:172` | **Un seul deadline de mission propagé à toutes les sous-opérations**, plutôt que des timeouts indépendants qui s'additionnent. |
| A | `unsloth/dataprep/synthetic.py:177` | Encapsuler l'état d'un service dans un kit avec **`cleanup` garanti par contexte**. |
| S | `unsloth_cli/_inference.py:310` | **Collecter un stream sans perdre le texte déjà reçu** quand la connexion se ferme prématurément. |
| A | `unsloth_cli/_inference.py:351` | Backend abstrait minimal (`stream`, `close`) pour brancher Ollama ou un serveur local. |
| S | `unsloth_cli/_inference.py:426,508` | **Séparer choix du backend et chargement effectif** ; chaque étape observable ; token optionnel séparé de la configuration. |
| S | `unsloth/models/loader_utils.py:102,443` | Device map déterministe ; **nom canonique résolu séparément du chargement**, pour journaliser la cible. |
| S | `unsloth/utils/packing.py:719` | **Masquer les labels aux frontières de séquences** pour empêcher une validation de traverser deux exemples. Analogue direct : un invariant ne doit pas déborder sur le nœud voisin. |
| A | `unsloth/utils/packing.py:165,572` | Activer une optimisation **seulement si le verifier l'autorise** ; conserver les métadonnées reliant une sortie à son entrée. |
| S | `unsloth_cli/commands/start.py:900` | **Affichage de progression borné et séparé du journal durable.** Ne pas confondre UI et preuve. |
| S | `unsloth_cli/commands/start.py:1157` | Shutdown d'un serveur subprocess **centralisé et idempotent**. |
| A | `unsloth_cli/commands/start.py:1088,1755,1880` | Chargement asynchrone avec fermeture contrôlée si la mission expire ; **comparer les settings avant réutilisation**, sinon forcer un rechargement. |

### F3.6 — `campaign` et `observatory`

| S | Source | Notion |
|---|---|---|
| A | `unsloth/registry/registry.py:20,56` | Registry **typé** avec métadonnées ; **enregistrement explicite par famille plutôt que découverte dynamique** depuis le modèle. Analogue direct de notre registre d'outils. |
| S | `unsloth/dataprep/raw_text.py:318` | **Nettoyage textuel déterministe avant génération** d'un invariant ou d'un prompt. |
| A | `unsloth/dataprep/raw_text.py:307,328` | Préprocesseur **séparé du loader**, sans effet caché ; extraction de sections **par motifs fermés**. |
| S | `unsloth/dataprep/synthetic.py:459` | Découper un corpus en **unités traitables avant lancement**. |
| A | `unsloth/dataprep/synthetic.py:517` | Génération QA à paramètres bornés et sortie inspectable — **candidat pour produire des fixtures, jamais une preuve**. |
| S | `unsloth/models/rl.py:921` | Vérifier qu'une borne tient **avant toute itération coûteuse**. |
| A | `unsloth/models/rl.py:1036` | **Inspecter la première ligne sans consommer un flux**, pour valider sa forme. |
| S | `studio/backend/mcp_server.py:263` | Agréger plusieurs sondes d'état **en parallèle** puis restituer un snapshot cohérent. |
| S | `unsloth_cli/commands/start.py:1145,1152` | Queue récente de logs **bornée en lignes**, et **rédaction systématique des tails avant projection** à l'utilisateur ou au modèle. Troisième source. |
| S | `unsloth_cli/_inference.py:69` | **Distinguer erreur différée côté serveur, corps incomplet et erreur HTTP** dans l'affichage. Trois causes, trois messages. |
| A | `unsloth_cli/_inference.py:882` | Refus de connexion avec **raison courte et stable, exploitable dans un finding**. |
| A | `studio/backend/lan_access.py:479` · `cloudflare_tunnel.py:686` | Endpoint de statut **read-only** : adresse, port, état, erreur, génération — **sans jamais exposer le token de contrôle**. |
| A | `studio/backend/startup_banner.py:1` | Bannière de démarrage lisible : endpoints, mode réseau, **avertissement sur l'exposition des outils**. |

### F3.7 — Scripts

| S | Source | Notion |
|---|---|---|
| A | `unsloth_cli/commands/start.py:415` | Construire les flags CLI **en liste structurée** : pas de shell quoting, commande archivable. |
| A | `unsloth_cli/commands/start.py:832` | Client HTTP JSON commun avec timeout, statut et **corps d'erreur borné**. |
| A | `unsloth_cli/commands/inference.py:21` · `train.py:51` | Commande mince **déléguant à un backend testable** : options, validation, puis création d'un runner. Ne pas enfouir la logique dans la CLI. |
| A | `unsloth_cli/config.py:1` · `options.py:1` | Configuration centralisée et sérialisable ; **options définies une fois et projetées** vers le contrat interne. |
| A | `unsloth_cli/commands/export.py:16` | Lister les cibles avant export et **refuser une cible ambiguë**. |

## F4. Ce qu'il ne faut pas reprendre d'Unsloth

| Source | Raison |
|---|---|
| `unsloth/kernels/` (fused CUDA, MoE grouped GEMM) | Non portable vers un harness Python, dépendant du matériel, et **ne valide aucune nano-étape**. |
| `unsloth/models/rl.py:149` — patches GRPO/vLLM, reprise de checkpoint | Spécifique à l'entraînement. **Ne pas introduire cette dépendance dans la boucle d'outils.** |
| `unsloth/optimizers/q_galore_projector.py:115` | Optimise l'entraînement, **n'apporte aucune preuve d'invariant**. |
| `unsloth/models/rl_replacements.py:526` | **Réécriture regex de fonctions de bibliothèques tierces.** Trop fragile pour le cœur — sixième source, sixième famille de patch textuel écartée. |
| `studio/frontend/` | Volumineux, **sans autorité sur la vérité ni les traces**. React porté de v1 est retenu. |
| `docker/Dockerfile` | Contredit le chemin local natif retenu au socle. |
| `LICENSE` | **AGPL pour Studio mêlée à d'autres notices** — voir § F1.1. |

## F5. Les quatre reprises prioritaires

| # | Reprise | Source | Ce qu'elle ferme |
|---|---|---|---|
| 1 | **La politique d'exposition réseau complète** — prédicat partagé, DNS et IP littérale, binds wildcard normalisés | `_tool_policy.py:19,108,165` · `lan_access.py:72,213` | « LAN différé » qui n'est pas une règle mais l'absence de règle, et se transforme en ouverture accidentelle |
| 2 | **Readiness observable, jamais le spawn** + **jeton de génération à l'arrêt** | `cloudflare_tunnel.py:507,930` | Le service annoncé prêt qui ne l'est pas, et l'ancienne instance qui tue la nouvelle |
| 3 | **Un seul deadline propagé** à toutes les sous-opérations | `synthetic.py:162,172` | La mission de 20 minutes qui finit à 35 parce que chaque sous-opération avait son propre timeout |
| 4 | **Garde des répertoires système** | `_system_dir_guard.py:1` | Le code produit exécuté en `subprocess` qui touche `~/.prefect` ou `~/Library/LaunchAgents` |

**Ce qu'Unsloth n'a pas non plus** — sixième dépôt, sixième fois : aucun invariant métamorphique, aucun
mutation-check, aucun catalogue fermé de relations.

## F6. Ordre de portage Unsloth

| Phase | Reprises |
|---|---|
| **P0** | `device_type.py:62,100,257` · `disk_utils.py:83,109,120` · `dataset_num_proc.py:1` · `chat_templates.py:1885,2168` · `hf_hub.py:27,47` · `loader_utils.py:1694,2079,2156` |
| **P1** | `tests/test_torchao_nf4tensor_move.py:152,191` · `tests/test_peft_symbol_backfill.py:96` · `loader_utils.py:180,1522` · `rl.py:921,973,987` |
| **P2** | `synthetic.py:52,148,162,172` · `raw_text.py:56,98,125,318,346` · `packing.py:719` · `_inference.py:259,310,318` |
| **P4** | `_tool_policy.py:19,108,165` · `lan_access.py:72,213,350,370,423,497` · `cloudflare_tunnel.py:354,507,516,930` · `_system_dir_guard.py:1` · `start.py:1191,1498,1507,1569` |
| **P5** | `mcp_server.py:263` · `start.py:900,1145,1152` · `_inference.py:69,882` · `lan_access.py:479` |
| **P6** | `mcp_server.py:20,70,77,86,97,126,166` · `registry.py:20,56` |
| **P7bis** | Politique réseau du profil de confinement — refus par défaut pour le code produit sous invariant |
| **Différé** | `pi_subagent.ts:67,105` · `claude_subagent_mcp.py:60,84,135` — mode `agentic` |

## F7. Attribution

**Licence mixte, dont AGPL pour `studio/`.** Aucune copie littérale depuis `studio/` : les notions sont
reprises, le code est réécrit. Les modules sous `unsloth/` et `unsloth_cli/` portent d'autres notices, à
vérifier fichier par fichier si un portage littéral devenait souhaitable. Voir § F1.1.

---

# PARTIE G — OpenHands Agent Canvas

## G1. Pourquoi ce dépôt

**2 212 entrées, ~373 367 lignes**, TypeScript / React / Electron. C'est le **frontend Agent Canvas**
d'OpenHands — le SDK Python, l'agent-server et le runtime vivent ailleurs.

Septième source, et la deuxième non-runtime après Unsloth. Sa valeur n'est donc pas dans une boucle d'agent
mais dans **la frontière entre ce qui est déclaré et ce qui est exécuté** : c'est le seul des sept dépôts à
formaliser un **contrat d'admission de données déclaratives** de bout en bout — validation, placeholders
fermés, accumulation d'erreurs par chemin de champ, interdiction de toute expression évaluable.

Statuts : **S** socle · **A** adapter · **I** inspirer · **X** écarter.
Chemins relatifs à `resources/OpenHands-main/`.

### G1.1 — Les quatre apports propres

1. **L'admission déclarative complète** (`src/manifests/manifest-validation.ts`, ~600 L) — identifiants
   validés par regex avant insertion au registre, markup interdit dans tout texte fourni par une extension,
   commandes restreintes à un alphabet **sans métacaractères shell**, chemins de source restreints à des
   préfixes autorisés, énumérations fermées pour les modes et les types de champ, bornes dures de longueur, et
   **un accumulateur d'erreurs avec chemin de champ qui retourne toutes les violations en une fois**.
2. **Les placeholders fermés, sans expression évaluable** (`manifests/types.ts:30` ·
   `manifest-template.ts:65,76`) — deux espaces de noms fermés (`form`, `automation`), interpolation
   **conservant le type** quand le placeholder occupe tout le champ, et interpolation textuelle **sans jamais
   évaluer d'expression**. C'est le contre-exemple exact de `pi/resolve-config-value.ts:10`, qui exécute des
   commandes contenues dans une valeur de configuration.
3. **La compatibilité de backend versionnée** (`api/agent-server-compatibility.ts`) — version minimale
   compatible, codes d'erreur fermés, refus **avant toute mission**, et **une version inconnue traitée comme
   un état distinct, jamais comme la version courante**.
4. **L'idempotence des lancements enfants** (`services/child-conversation-launch.ts:205`) — claim idempotent
   d'un tool call parent : **une demande ne peut pas être exécutée deux fois**. C'est notre décision 16
   appliquée au lancement d'une sous-tâche.

**Ce qu'OpenHands n'a pas non plus** — septième dépôt, septième fois : aucun invariant métamorphique, aucun
mutation-check, aucun catalogue fermé de relations.

## G2. Ce que la reprise a changé dans la documentation

| Cible | Nature du changement |
|---|---|
| `EXPLANATIONS.md` | Décisions 16, 17 et 27 amendées · **décision 28 ajoutée** |
| `PROJECT.md` | 1 critère ajouté |
| `ROADMAP.md` | Items P0, P1, P3, P4, P5 |

### G2.1 — Décision 28 : l'admission déclarative

Notre `Proposal` et notre `registry.json` sont des données déclaratives produites par un modèle faible et
consommées par le harness. Les décisions 5, 19 et 22 disent **comment décider qu'une proposition est
redondante** ; aucune ne dit **comment une proposition est admise en tant que donnée bien formée**.

OpenHands écrit ce contrat, et il tient en six règles.

- **Les identifiants sont validés par regex avant insertion au registre** (`manifest-validation.ts:25`).
- **Le markup est interdit dans tout texte fourni par une extension** (`:28`). Chez nous : dans tout texte
  produit par le modèle et destiné à être rendu — au contexte d'un nœud, au dashboard, à Telegram.
- **Les commandes déclaratives sont restreintes à un alphabet sans métacaractères shell** (`:42,165`), et
  toute syntaxe shell est refusée. Notre suite de régression accumulée est faite de commandes persistées :
  cette règle est le complément du capteur de masquage d'exit d'Ouroboros — l'un refuse `| tail` à
  l'admission, l'autre le détecte à l'exécution.
- **Les chemins de source sont restreints à des préfixes autorisés** (`:44`) et **vérifiés relatifs, sans
  échappement possible du workspace** (`:148`).
- **Les modes et les types de champ sont des énumérations fermées** (`:51`), et tout message rendu au contexte
  porte une **borne dure de longueur** (`:65`).
- **Une fonction publique unique de validation** renvoyant `{valid, errors}` (`:576`), et une gate locale
  rapide **avant tout appel réseau ou création de job** (`manifest-local-validation.ts:167`).

**Et la règle qui change notre comportement de rejet** (`:93`) : un **accumulateur d'erreurs avec chemin de
champ**, qui retourne **toutes les violations en une fois**.

Nos rejets s'arrêtent aujourd'hui à la première règle qui échoue. Sur un modèle à 16 k, chaque cycle de
re-génération coûte une session complète : renvoyer une seule violation à la fois transforme une proposition
à trois défauts en trois cycles. L'accumulateur les renvoie ensemble, avec le chemin exact de chaque champ
fautif. C'est gratuit à implémenter et cela divise mécaniquement le coût des propositions mal formées.

S'y ajoute une carte d'erreurs par champ (`automation-setup.ts:403`) permettant de **corriger une proposition
sans rejouer tout le cycle**.

### G2.2 — Les placeholders sont fermés, et rien n'est évalué

Corollaire direct de la contrainte dure n°1, appliqué aux données déclaratives plutôt qu'à l'exécution.

Deux espaces de noms fermés (`manifests/types.ts:30`), et deux règles d'interpolation :

- quand un placeholder **occupe tout le champ**, la valeur est substituée **en conservant son type**
  (`manifest-template.ts:65`) — pas de conversion silencieuse en chaîne ;
- l'interpolation textuelle **n'évalue aucune expression** (`:76`) ; la lecture d'une valeur imbriquée se fait
  **par chemin fermé** (`:21`).

Le contre-exemple est déjà dans notre registre : `pi/resolve-config-value.ts:10`, écarté en partie B
précisément parce qu'il **exécute les commandes contenues dans une valeur de configuration**. Deux sources,
deux positions opposées sur la même question — et la nôtre est tranchée.

### G2.3 — Décision 17 amendée : le backend est vérifié avant la mission

Notre `bridge` suppose Ollama joignable et compatible. Le spike n°4 lit `n_ctx_train` sur `/v1/models`, mais
rien ne dit ce qui se passe si le serveur est plus ancien que ce que le contrat exige.

`api/agent-server-compatibility.ts` écrit la règle : **une version minimale compatible, des codes d'erreur
fermés, et un refus avant toute mission** (`:19,81`). Trois points de forme :

- **Une version inconnue est un état distinct, jamais la version courante** (`:95`). C'est la même famille
  que « un token absent n'est jamais un zéro » et que le `unknown ⇒ fail-closed` d'Ouroboros.
- **La comparaison de versions est sémantique**, jamais un tri lexicographique (`:252`).
- **Le cache d'informations backend est explicitement invalidé au changement d'hôte** (`:144`), et un cache
  court par hôte évite les probes répétées (`:149`).

Enfin, **une erreur typée distingue backend absent, backend indisponible et détail de connexion** (`:50`) :
trois causes, trois messages, trois remédiations — au lieu d'un « Ollama ne répond pas » qui recouvre un
serveur éteint, un port occupé et un modèle non chargé.

### G2.4 — Décision 16 amendée : le claim idempotent

La décision 16 pose qu'un appel interrompu ne prouve pas que son effet n'a pas eu lieu, et qu'un effet
externe doit être **interrogé** avant d'être rejoué. OpenHands ajoute la face amont du même contrat :
**un claim idempotent au moment de la demande** (`child-conversation-launch.ts:205`) — une demande de
lancement ne peut pas être exécutée deux fois, quel que soit le nombre de fois où elle est reçue.

Chez nous, cela s'applique à trois endroits : le lancement d'un nœud enfant, la promotion d'un outil au
statut `verified`, et la création d'une PR. Les trois sont des effets à identité connue **avant** exécution ;
le claim les rend rejouables sans risque.

Deux compléments du même module : les paramètres sont **validés avant toute mutation** (`:110`), et
**l'indisponibilité du lien parent/enfant produit une note explicite** (`:241`) plutôt qu'un silence.

### G2.5 — Décision 27 amendée : hooks d'arrêt et leases périmées

Trois reprises de `scripts/dev-safe.mjs` complètent le cycle de vie de service.

- **Un registre de hooks d'arrêt exécutés à toute sortie** (`dev-process-utils.mjs:131`). Notre mission a
  quatre effets à défaire — verrou, subprocess de vérification, serveur MCP de la campagne, watch du
  dashboard — et chacun se libère aujourd'hui à un endroit différent.
- **Les leases de conversations périmées sont libérées au démarrage** (`dev-safe.mjs:1177`), pas à l'arrêt.
  Un crash ne laisse jamais un verrou orphelin bloquer le réveil suivant.
- **Un port libre est trouvé par bind explicite sur loopback** (`:218,266`), et plusieurs ports sont vérifiés
  avant de démarrer le stack — pas de « probablement libre ».

Et une reprise de sécurité : **la clé d'API est générée côté hôte, jamais par le modèle** (`:72`), puis
persistée dans un fichier au chemin contractuel (`:123`).

### G2.6 — Critère de socle ajouté

- **Une proposition mal formée reçoit toutes ses violations en une fois**, chacune avec le chemin exact du
  champ fautif — jamais la première rencontrée.

## G3. Catalogue des reprises

### G3.1 — `kernel`

| S | Source | Notion |
|---|---|---|
| S | `src/api/agent-server-config.ts:1,203,209` | **Répertoire de travail par défaut centralisé** ; workspace d'une conversation construit depuis une base contrôlée et un identifiant opaque ; **une fonction unique de chemin**, réutilisée par `engine` et `observatory`. |
| A | `src/api/agent-server-config.ts:25,55` | Normaliser une URL de backend (valeurs vides, variantes triviales) et **canonicaliser un hostname avant comparaison** de provenance. |
| S | `src/api/agent-server-config.ts:273` | Headers d'authentification construits **en un seul point**. |
| S | `src/api/agent-server-compatibility.ts:19,50,81` | Version minimale compatible, **codes d'erreur fermés**, refus avant mission ; erreur typée distinguant **backend absent, indisponible et détail de connexion**. |
| S | `src/api/agent-server-compatibility.ts:95` | **Une version inconnue est un état distinct, jamais la version courante.** |
| A | `src/api/agent-server-compatibility.ts:252` | Comparaison **sémantique** de versions, jamais lexicographique. |
| A | `src/api/agent-server-adapter.ts:475,546` | **Tags à clés réservées** reliant campagne, source et run ; projection stable vers une vue filtrée. |
| S | `src/manifests/types.ts:30` | **Espaces de placeholders fermés** — aucune expression libre. |
| S | `src/manifests/types.ts:90` | Nom de fichier de configuration de bundle **canonique**. |
| A | `src/manifests/types.ts:380` | Énumérations fermées pour les filtres et tris de l'observatory. |

### G3.2 — `verifier` — l'admission déclarative

| S | Source | Notion |
|---|---|---|
| S | `src/manifests/manifest-validation.ts:25` | **Identifiants validés par regex avant insertion au registre.** |
| S | `:28` | **Markup interdit** dans tout texte fourni par une extension. |
| S | `:42,165` | **Commandes déclaratives restreintes à un alphabet sans métacaractères shell** ; toute syntaxe shell refusée. Complément du capteur de masquage d'exit d'Ouroboros. |
| S | `:44` | **Chemins de source restreints à des préfixes autorisés.** |
| S | `:51` | Modes de setup et types de champ **énumérés explicitement**. |
| S | `:65` | **Borne dure de longueur** pour tout message rendu au contexte. |
| S | `:93` | **Accumulateur d'erreurs avec chemin de champ : toutes les violations retournées en une fois.** |
| S | `:148` | Chemin vérifié **relatif et sans échappement** du workspace. |
| S | `:373` | Champ obligatoire imposé pour les déclencheurs qui en ont besoin. |
| S | `:407,566` | Vérification d'un bundle **avant empaquetage** ; détection rapide d'un bloc de setup admissible. |
| S | `:576` | **Fonction publique unique de validation**, renvoyant `{valid, errors}`. |
| A | `:226,313` | Contraintes validées **séparément** du schéma de présentation ; unicité et forme des champs de formulaire. |
| S | `src/manifests/interface-validation.ts:103` | **Même patron d'admission** pour une seconde famille de manifests — la règle est réutilisée, pas réécrite. |
| A | `src/manifests/interface-validation.ts:709` | Valider une interface complète **avant de l'exposer** à l'observatory. |
| S | `src/manifests/manifest-local-validation.ts:24` | **Caractères dangereux interdits** dans les expressions de formulaire locales. |
| A | `src/manifests/manifest-local-validation.ts:167` | **Gate locale rapide avant tout appel réseau** ou création de job. |
| A | `src/manifests/manifest-error-map.ts:75,127` | Normaliser les erreurs distantes vers **les chemins de champs du contrat local**, pour les rendre exploitables par le modèle. |

### G3.3 — `bridge`

| S | Source | Notion |
|---|---|---|
| S | `src/api/agent-server-client-options.ts:22,38,52` | Erreur dédiée quand aucun backend n'est configuré ; host et port **normalisés avant construction** ; **fabrique typée des options — aucune URL assemblée dans l'appelant**. |
| S | `src/api/agent-server-compatibility.ts:144,158` | Cache d'informations backend **explicitement invalidé au changement d'hôte** ; déterminer **mécaniquement** si un outil est annoncé par le backend. |
| A | `src/api/agent-server-compatibility.ts:149` | Cache court de `/server_info` **indexé par hôte**, pour éviter les probes répétées. |
| A | `src/api/agent-server-adapter.ts:136` | **Liste fermée d'outils par défaut** — ne jamais accepter une liste arbitraire du modèle. |
| S | `src/api/agent-server-adapter.ts:143` | **Borner `max_iterations`** avec une valeur de repli sûre. |
| S | `src/api/agent-server-adapter.ts:205,245` | Services runtime récupérés **avant** composition du contexte ; endpoints rendus sous forme de **suffixe système explicite et borné**. |
| S | `src/api/agent-server-adapter.ts:668,706` | Politique de confirmation des outils **séparée des settings bruts** ; **prédicat unique d'inclusion**. |
| S | `src/api/agent-server-adapter.ts:824` | **Contexte agent structuré plutôt qu'une chaîne opaque.** Converge avec la décision 14. |
| S | `src/api/agent-server-adapter.ts:1151` | **Secrets isolés**, jamais mélangés aux métadonnées publiques. |
| A | `src/api/agent-server-adapter.ts:1174,1335` | Fabrique de requête **séparée du transport** ; requête de planification **distincte** de la conversation d'exécution. |

### G3.4 — `workspace` et `engine`

| S | Source | Notion |
|---|---|---|
| S | `src/services/child-conversation-launch.ts:110` | **Paramètres validés avant toute mutation.** |
| S | `:205` | **Claim idempotent d'un tool call parent : une demande ne peut pas être exécutée deux fois.** |
| A | `:241` | **Note explicite** quand le lien parent/enfant n'est pas disponible — jamais un silence. |
| S | `:272,365` | Lancement avec **paramètres d'isolation contrôlés** ; polling avec **intervalle et timeout nommés**. |
| S | `:459,505` | Résultat rapporté sous forme **succès/échec guidé** ; **point d'entrée unique** pour l'action. |
| A | `src/constants/child-conversation.ts:26` | **Modes d'isolation énumérés** (`worktree`, `shared`) au lieu d'un booléen implicite. Conforme à notre règle de style. |
| S | `src/constants/child-conversation.ts:37` | **Refuser la fonctionnalité si le backend est trop ancien.** |
| S | `src/services/canvas-ui.ts:53` | Router les actions vers des **opérations nommées**, jamais vers des chemins arbitraires. |
| S | `src/stores/use-event-store.ts:17,41,92` | Identifiant et timestamp extraits **avec repli explicite** ; tri **seulement quand l'ordre entrant l'exige** ; **append pur**. |
| A | `src/hooks/use-websocket.ts:19` | Backoff de reconnexion borné, **délai initial et maximum nommés**. |
| S | `src/api/agent-server-adapter.ts:592,600` | Settings **normalisés avant comparaison ou persistance** ; **un secret vide est traité comme absent**, il n'écrase jamais une valeur existante. |
| S | `src/api/agent-server-adapter.ts:1033` | Settings de conversation et settings d'agent construits **en deux couches**. |
| S | `src/api/agent-server-compatibility.ts:341` | **Probe locale du backend avant activation d'une mission.** |

### G3.5 — `campaign`

| S | Source | Notion |
|---|---|---|
| S | `src/manifests/manifest-registry.ts:19` | **Registry construit à partir d'entrées validées, sans découverte implicite.** Troisième source à le dire. |
| S | `src/manifests/manifest-template.ts:21,65,76` | Lecture de valeur imbriquée **par chemin fermé** ; interpolation **conservant le type** quand le placeholder occupe tout le champ ; **interpolation textuelle sans évaluation d'expression**. |
| S | `src/manifests/manifest-bundle.ts:29` | Fichiers d'un bundle résolus **par identifiant contrôlé**. |
| A | `src/manifests/manifest-bundle.ts:68` | Empaquetage **après calcul des chemins exécutables autorisés**. |
| S | `src/manifests/automation-setup.ts:44,86` | Endpoints construits **depuis le manifest**, jamais par concaténation dispersée ; existence **vérifiée avant création**. |
| S | `src/manifests/automation-setup.ts:353` | **Corps de preflight séparé de la création effective.** |
| A | `src/manifests/automation-setup.ts:403` | **Carte d'erreurs par champ** pour corriger une proposition **sans rejouer tout le cycle**. |
| S | `src/manifests/automation-insights.ts:144` | Santé dérivée de **prédicats de statut fermés**. |
| A | `src/manifests/automation-insights.ts:236,337` | Filtres et tris comme **fonctions pures** ; tuiles calculées depuis des résumés déjà chargés. |

### G3.6 — `lifecycle` et `broker`

| S | Source | Notion |
|---|---|---|
| S | `scripts/dev-safe.mjs:72,123` | **Clé d'API générée côté hôte, jamais par le modèle** ; fichier de clé persistante au chemin contractuel. |
| S | `scripts/dev-safe.mjs:218,266` | **Port libre trouvé par bind explicite sur loopback** ; plusieurs ports vérifiés **avant** de démarrer le stack. |
| S | `scripts/dev-safe.mjs:896,915` | Disponibilité d'un serveur attendue **avec timeout** ; spawn encapsulé dans **une abstraction unique**. |
| S | `scripts/dev-safe.mjs:1177` | **Leases de conversations périmées libérées au démarrage**, pas à l'arrêt. Un crash ne bloque jamais le réveil suivant. |
| A | `scripts/dev-safe.mjs:433,569` | Commande construite **en liste d'arguments** ; configuration dérivée d'un `cwd` et d'un environnement contrôlés. |
| S | `scripts/dev-process-utils.mjs:13,85` | Existence d'un processus testée **sans supposer son état** ; **signal envoyé à l'arbre**, pas au seul parent. Cinquième source. |
| S | `scripts/dev-process-utils.mjs:131` | **Registre de hooks d'arrêt exécutés à toute sortie.** |
| S | `scripts/proxy-utils.mjs:69,206` | `/server_info` traité **séparément** pour enrichir la topologie ; fabrique de handlers **centralisant erreurs et timeouts**. |
| S | `electron/main.mjs:262,618` | **Readiness de l'agent-server vérifiée séparément de la readiness UI** ; démarrage du stack encapsulé dans **une phase unique et observable**. |
| A | `electron/main.mjs:462,596` | Ligne de log **nettoyée avant affichage ou persistance** ; logs routés **avec niveau et nom de service**. |
| S | `scripts/dev-extra-backend.mjs:80` | **Probe générique de readiness HTTP avec deadline.** |
| A | `scripts/download-uv.mjs:107` | **Version d'outil résolue avant téléchargement** — ne jamais suivre une URL non versionnée. |

### G3.7 — `observatory`

| S | Source | Notion |
|---|---|---|
| S | `src/manifests/automation-insights.ts:81` | **Statuts terminaux énumérés avant agrégation.** |
| A | `:86,165` | **Prédicat de succès distinct du prédicat d'échec** ; durée compacte formatée **sans perdre la valeur nulle**. |
| S | `src/api/agent-server-compatibility.ts:302` | Message d'incompatibilité **stable et actionnable**. |
| A | `src/api/agent-server-compatibility.ts:214` | **Version serveur et version SDK affichées séparément.** |
| A | `src/stores/metrics-store.ts:21` | **État métrique vide explicite**, évitant les `undefined` dans les cartes. |
| S | `src/services/telemetry.ts:104,224,416` | **Hard-disable de la télémétrie indépendant du consentement applicatif** ; configuration depuis **un seul service propriétaire** ; état de consentement exposé par une **API stable**. |
| A | `src/services/telemetry.ts:209` · `src/services/telemetry-context.ts:33` | Propriétés comparées **avant mutation** pour éviter les événements redondants ; propriétés normalisées **sans données brutes**. |
| A | `src/stores/use-workspace-mutation-counter.ts:41` | **Cache-buster explicite après mutation** du workspace. |
| S | `src/constants/server-connection-error.ts:1` | Message d'erreur de connexion **constant**. |

## G4. Ce qu'il ne faut pas reprendre d'OpenHands

| Source | Raison |
|---|---|
| `src/root.tsx` et l'UI React | **Ne doit pas pénétrer le cœur Python** ni devenir une dépendance de validation. React porté de v1 est retenu. |
| `electron/main.mjs:356` — fenêtre Electron | Hors périmètre du serveur MCP et de l'observatory. |
| `src/services/telemetry.ts:273` — PostHog / télémétrie cloud | **Incompatible avec la contrainte dure n°5.** Seuls les **contrats de consentement** sont repris. |
| `docker/Dockerfile` | Docker est une option d'isolation OpenHands, **pas une raison de modifier le chemin natif déjà décidé**. |
| `src/api/agent-server-adapter.ts:1174` — appels frontend | Les endpoints appartiennent au SDK officiel, **pas au harness**. |

## G5. Les quatre reprises prioritaires

| # | Reprise | Source | Ce qu'elle ferme |
|---|---|---|---|
| 1 | **L'accumulateur d'erreurs avec chemin de champ** — toutes les violations en une fois | `manifest-validation.ts:93` | Une proposition à trois défauts qui coûte trois sessions à 16 k au lieu d'une |
| 2 | **L'admission déclarative complète** — regex, alphabet sans métacaractères shell, préfixes autorisés, bornes de longueur | `manifest-validation.ts:25-165,576` | Une proposition bien formée n'est plus une hypothèse ; c'est une gate |
| 3 | **Placeholders fermés, aucune expression évaluée** | `manifest-template.ts:21,65,76` | La surface d'exécution cachée dans une valeur de configuration — contre-exemple direct de `pi/resolve-config-value.ts:10` |
| 4 | **Claim idempotent d'une demande** | `child-conversation-launch.ts:205` | La face amont de la décision 16 : un effet à identité connue ne s'exécute pas deux fois |

## G6. Ordre de portage OpenHands

| Phase | Reprises |
|---|---|
| **P0** | `src/manifests/types.ts:30,90` · `src/api/agent-server-config.ts:1,203,209,273` · `src/api/agent-server-compatibility.ts:19,50,95,252` |
| **P1** | `src/manifests/manifest-validation.ts` entier · `src/manifests/interface-validation.ts:103` · `src/manifests/manifest-local-validation.ts:24,167` · `src/manifests/manifest-error-map.ts:75,127` |
| **P2** | `src/services/child-conversation-launch.ts:110,205,241,459,505` · `src/constants/child-conversation.ts:26,37` · `src/stores/use-event-store.ts:17,41,92` |
| **P3** | `src/manifests/manifest-registry.ts:19` · `manifest-template.ts:21,65,76` · `manifest-bundle.ts:29` · `automation-setup.ts:44,86,353,403` |
| **P4** | `scripts/dev-safe.mjs:72,123,218,266,896,915,1177` · `scripts/dev-process-utils.mjs:13,85,131` · `scripts/dev-extra-backend.mjs:80` · `electron/main.mjs:262,618` |
| **P5** | `automation-insights.ts:81,86,144,165,236` · `src/services/telemetry.ts:104,224,416` · `src/api/agent-server-compatibility.ts:214,302` |
| **P6** | `src/api/agent-server-adapter.ts:136,143,668,706,824,1151` · `src/api/agent-server-compatibility.ts:144,149,158,341` |

## G7. Attribution

Le dépôt inspecté est le frontend Agent Canvas. **Aucune copie de code n'est faite** : les reprises sont
conceptuelles — un prédicat, un ordre de validation, une énumération fermée. Vérifier la licence du dépôt
avant tout portage littéral, ce qui n'est prévu pour aucune entrée de ce catalogue.

---

# PARTIE H — SWE-agent

## H1. Audit de l'extraction avant intégration

**L'extraction `resources/swe-agent.md` a été produite par un petit modèle et vérifiée avant absorption.**
Verdict : **utilisable, mais incomplète et imprécise sur les descriptions.** Le détail, parce qu'il informe
la confiance à accorder aux autres extractions.

### Ce qui est juste

- **Toutes les ancres testées pointent vers un fichier et une ligne existants** — 22 vérifiées sur les deux
  moitiés du document, zéro chemin mort, zéro numéro de ligne hors fichier. C'est le point le plus important
  et il est acquis.
- Le volume annoncé est correct : **414 fichiers** hors `.git` (le document dit « 414 entrées » ; il y a en
  réalité 530 entrées dont 116 répertoires — terminologie floue, chiffre juste).
- La licence est correctement identifiée : **MIT**.
- La structure par module suit notre `ARCHITECTURE.md`, et les statuts `X` sont pertinents.

### Ce qui est faux ou imprécis

| Problème | Détail |
|---|---|
| **Descriptions décalées d'une classe** | Dans `tools/parsing.py`, 3 ancres sur 8 nomment la classe voisine : `:72` est `ActionParser` mais annoncé « action-only » (qui est en `:97`) ; `:371` est `FunctionCallingParser` mais annoncé « table de fonctions autorisées » ; `:543` est `BashCodeBlockParser` mais annoncé « borné à un code block **unique** » (qui est `SingleBashCodeBlockParser`, en `:574`). |
| **Ancres imprécises** | Plusieurs pointent au milieu d'un corps plutôt que sur une définition : `agents.py:1091` tombe sur une ligne interne, `run_replay.py:52` et `run_batch.py:80` sur des docstrings de champ, `log.py:41`, `open_pr.py:52` et `common.py:118` sur des lignes d'implémentation. Zone correcte, ancre non canonique. |
| **Volumétrie en lignes surestimée** | ~40 566 annoncées contre ~34 618 mesurées sur les extensions texte principales. Écart d'environ 15 %. |

### Ce qui manque — et c'est le vrai défaut

**Trois zones entières du dépôt ne sont citées nulle part**, soit environ **3 000 lignes** parmi les plus
pertinentes pour nous. Le document affirme pourtant en clôture que « les tools et trajectoires ont été
parcourus ».

| Zone omise | Lignes | Pourquoi c'est un problème |
|---|---:|---|
| **`tools/`** — les outils réels | ~900 | `windowed/lib/windowed_file.py` (315 L) est **le module le plus directement applicable à notre `workspace`** : fenêtre bornée, `undo_edit`, et un résultat de mutation qui porte son compte. `windowed/lib/flake8_utils.py` (144 L) relocalise les erreurs de lint après édition. |
| **`tests/`** entier | ~1 700 | 14 fichiers. Les extractions Pi et Ouroboros ont montré que les tests sont une source de contrats de comportement de premier ordre ; ici, aucun. |
| **`sweagent/types.py`** | 102 | **Le vocabulaire de contrats du dépôt** — `StepOutput`, `TrajectoryStep`, `HistoryItem`, `AgentInfo`, `AgentRunResult`. C'est ce qu'un module `kernel/contracts` doit lire en premier. |
| `sweagent/utils/patch_formatter.py` | 152 | Projection bornée d'un fichier autour d'un diff, avec fusion d'intervalles. Directement notre `engine/context`. |
| `sweagent/agent/hooks/abstract.py` | 139 | Treize hooks nommés du cycle de vie. Seuls les hooks *environment* sont cités, pas ceux de l'agent. |
| `sweagent/run/run.py`, `agent/extra/shell_agent.py`, `sweagent/__init__.py` | ~370 | Non cités. |

**Ces omissions ont été comblées ci-dessous** ; les entrées concernées portent la mention *(hors extraction)*.
Les descriptions décalées de `parsing.py` sont corrigées.

### Conséquence de méthode

Une extraction par petit modèle produit des **ancres fiables** et des **descriptions approximatives**, et
elle **couvre le répertoire principal en ignorant la périphérie**. C'est exactement le profil d'erreur que
notre décision 13 anticipe : un travail qui *paraît* complet — il en a la forme, la volumétrie et la
structure — sans l'être. La vérification a coûté vingt minutes ; elle a récupéré trois zones dont la plus
utile du dépôt.

## H2. Pourquoi ce dépôt

**414 fichiers, ~34 618 lignes de texte, 14 891 lignes de Python. MIT.** Le plus petit des huit dépôts,
et le plus lisible : `mini-SWE-agent` lui succède, mais l'implémentation présente reste une référence
compacte du cycle **problème → environnement → action structurée → observation → patch → évaluation**.

**Ce qu'il apporte de propre :** la séparation `Agent` / `SWEEnv`, un **catalogue de douze parsers fermés**
pour lire la sortie d'un modèle qui ne sait pas faire du tool calling natif, des **history processors
composables**, et la **rejouabilité d'une trajectoire sans rappeler le modèle**.

**Ce qu'il n'a pas non plus** — huitième dépôt, huitième fois : aucun invariant métamorphique, aucun
mutation-check, aucun catalogue fermé de relations.

## H3. Ce que la reprise a changé dans la documentation

| Cible | Nature du changement |
|---|---|
| `EXPLANATIONS.md` | Décisions 9 et 14 amendées · **décision 29 ajoutée** |
| `PROJECT.md` | 1 critère ajouté |
| `ROADMAP.md` | Items P0, P1, P2, P5 |

### H3.1 — Décision 29 : une projection dit toujours ce qu'elle cache

*(entièrement issue de la zone omise par l'extraction)*

Notre `codeview` projette les fichiers cibles dans le contexte d'un nœud. Il les projette **entiers ou
tronqués**, et dans le second cas rien ne dit au modèle ce qui manque.

`tools/windowed/lib/windowed_file.py:150-175` donne la forme correcte. Une fenêtre de fichier rendue au
modèle porte trois éléments en plus du texte :

```text
[File: src/core/parse.py (312 lines total)]     ← ligne de statut
(48 more lines above)                            ← ce qui précède
  49:def parse(text: str) -> dict:               ← la fenêtre, numérotée
  ...
(184 more lines below)                           ← ce qui suit
```

**Le modèle sait toujours ce qu'il ne voit pas.** C'est trois lignes de rendu, et cela supprime la classe
entière des raisonnements fondés sur « le fichier fait ce que j'ai lu ». Sur Ling, dont un mode d'échec
documenté est de partir chercher un fichier de spécification externe quand le contexte semble incomplet
(`kilo/ling.txt:69`), rendre l'incomplétude *explicite* est directement utile.

Deux compléments de la même zone :

- **La fusion d'intervalles avant projection** (`sweagent/utils/patch_formatter.py:28-49`). Quand plusieurs
  hunks touchent des lignes proches, projeter chacun avec son contexte produit trois fois le même bloc.
  `_merge_intervals` fusionne les plages chevauchantes **avant** rendu. Notre projection autour d'un diff en
  a besoin dès qu'un nœud touche deux fonctions voisines.
- **Un `context_length` explicite et un `linenos` explicite** (`patch_formatter.py:147`), plutôt qu'un
  découpage implicite.

### H3.2 — Décision 9 amendée : une mutation rend son bilan chiffré

*(hors extraction)*

`windowed_file.py:36-52` — une opération de remplacement retourne un `ReplacementInfo` portant
`first_replaced_line`, `n_search_lines`, `n_replace_lines` et **`n_replacements`** ; une insertion retourne
un `InsertInfo` portant `first_inserted_line` et `n_lines_added`.

Notre décision 9 vérifie *qu'une écriture n'a pas détruit le fichier*. Elle ne dit rien de **combien** elle a
changé. Le bilan chiffré est ce qui permet trois choses que nous n'avons pas :

- comparer le nombre de remplacements effectués au **nombre attendu** — la règle de Kilo
  (`edit-diff.ts:300`), qui annule le lot entier en cas d'écart, mais avec le compteur qui la rend
  vérifiable ;
- alimenter la métrique d'**inflation de patch** d'Ouroboros (`edit-tool-stats.mjs:157`) sans instrumenter
  séparément ;
- détecter un splice qui a touché **zéro** ligne, sans relire le fichier.

S'y ajoute `undo_edit` (`:276`) : une opération d'annulation **au niveau du fichier**, distincte du rollback
transactionnel de mission. Utile entre deux tentatives d'un même nœud, là où restaurer le snapshot complet
serait disproportionné.

### H3.3 — Décision 14 amendée : `thought`, `action`, `observation` sont trois champs

*(hors extraction)*

`sweagent/types.py:15-31` — `StepOutput` sépare `query`, `thought`, `action`, `output`, `observation`,
`execution_time`, `exit_status`, `state`, `tool_calls` et `thinking_blocks` en **champs distincts**, jamais
concaténés. Et `HistoryItem` (`:56-74`) impose un
`message_type: Literal["thought", "action", "observation"]` **obligatoire**.

Six sources nous ont dit de séparer le thinking du contenu exploitable. SWE-agent va un cran plus loin : la
séparation n'est pas un traitement appliqué à une chaîne, **c'est la forme du contrat**. Un `StepOutput` mal
formé est rejeté par le type, pas par une heuristique de parsing.

Détail qui compte pour le rendu : `to_template_format_dict` (`:33-41`) **exclut explicitement**
`tool_calls`, `tool_call_ids` et `state` du dictionnaire de formatage, tout en aplatissant `state` au niveau
racine. Ce qui sert au template et ce qui sert à la machine ne sont pas le même objet.

### H3.4 — Critère de socle ajouté

- **Toute projection partielle d'un fichier dans le contexte déclare ce qu'elle omet** : chemin, nombre
  total de lignes, et nombre de lignes au-dessus et en dessous de la fenêtre.

## H4. Catalogue des reprises

`S` socle · `A` adapter · `I` inspirer · `X` écarter.
Chemins relatifs à `resources/SWE-agent-main/`. Les entrées *(hors extraction)* sont celles que l'audit a
récupérées.

### H4.1 — `kernel`

| S | Source | Notion |
|---|---|---|
| S | `sweagent/types.py:15-31` *(hors extraction)* | **`StepOutput` — `thought`, `action`, `output`, `observation` en champs distincts**, jamais concaténés, plus `execution_time`, `exit_status`, `state`, `thinking_blocks`. La séparation est la forme du contrat, pas un traitement. |
| S | `sweagent/types.py:33-41` *(hors extraction)* | `to_template_format_dict` — **ce qui sert au template n'est pas ce qui sert à la machine** : `tool_calls` et `state` exclus du rendu, `state` aplati à la racine. |
| S | `sweagent/types.py:56-74` *(hors extraction)* | `HistoryItem` avec `message_type` **obligatoire** en littéral fermé, et des `tags` que les processeurs ajoutent pour marquer un traitement spécial. |
| A | `sweagent/types.py:82-100` *(hors extraction)* | `AgentInfo` / `AgentRunResult` — résultat de run typé, distinct de l'état interne. |
| S | `sweagent/agent/models.py:55` | Configuration de retry **Pydantic typée**, valeurs par défaut explicites. |
| S | `sweagent/agent/models.py:66` | Contrat de modèle **provider-agnostic**, paramètres d'appel séparés de l'agent. |
| A | `sweagent/agent/models.py:273,292` | Compteurs globaux de tokens et coût **conservés hors du message modèle** ; statistiques par instance. |
| S | `sweagent/agent/problem_statement.py:26` | **Protocol de problème minimal** permettant plusieurs sources sans coupler l'agent. |
| A | `sweagent/agent/problem_statement.py:68,101,294` | Problème borné et sérialisable ; chargé depuis un fichier **avec provenance explicite** ; fabrique unique convertissant une entrée simplifiée. |
| S | `sweagent/utils/serialization.py:36` | **Fusion récursive de dictionnaires de configuration**, sans écraser silencieusement les sous-clés. |
| S | `sweagent/utils/config.py:30` | **Retirer les chemins absolus avant d'écrire une trace partageable.** |
| S | `sweagent/utils/files.py:8` | Loader tolérant à l'absence, **utilisé uniquement aux frontières**. |
| A | `sweagent/run/common.py:24` | Troncature **récursive** des chaînes de configuration avant affichage. |

### H4.2 — `verifier` — le catalogue de parsers fermés

*Descriptions corrigées par l'audit.*

> **ÉCARTÉ EN BLOC — 06:09.** Ce catalogue existe parce que SWE-agent supporte des backends **sans sortie
> structurée native**. Nous avons un seul chemin : `response_format` json_schema sur `/v1`, revalidé
> localement contre le schéma exact envoyé. **Une sortie non conforme est rejetée, jamais récupérée par
> extraction.** ~200 L. Deux notions survivent et passent dans `bridge` : `parsing.py:371` — **rejeter un
> appel de fonction inconnu** — et `parsing.py:457` — **localiser l'erreur JSON** plutôt que rendre le stdout
> brut. Les pointeurs ci-dessous restent valides si le mode `agentic` rouvre la question.

| S | Source | Notion |
|---|---|---|
| S | `sweagent/tools/parsing.py:52` | `AbstractParseFunction` — interface séparant **texte modèle, action et erreur de parsing**. |
| S | `sweagent/tools/parsing.py:72,97` | `ActionParser` et **`ActionOnlyParser`** — le second pour quand **aucune pensée libre ne doit atteindre l'exécution**. *(l'extraction attribuait « action-only » à `:72`)* |
| A | `sweagent/tools/parsing.py:109,168` | `ThoughtActionParser` et sa **variante XML**, pour un backend sans tool calling natif. |
| A | `sweagent/tools/parsing.py:225` | `XMLFunctionCallingParser` — function calling **exprimé en XML**. *(l'extraction le décrivait comme le parser FC générique)* |
| S | `sweagent/tools/parsing.py:371` | `FunctionCallingParser` — **rejette les appels de fonction inconnus**. *(l'extraction annonçait « table de fonctions autorisées »)* |
| A | `sweagent/tools/parsing.py:457` | `JsonParser` — **erreurs localisées** plutôt que stdout brut. |
| S | `sweagent/tools/parsing.py:543,574` | `BashCodeBlockParser` et **`SingleBashCodeBlockParser`**, borné à un bloc unique. *(l'extraction attribuait « unique » à `:543`)* |
| A | `sweagent/tools/parsing.py:324,354` *(hors extraction)* | `EditFormat` (spécialisation de `ThoughtActionParser`) et `Identity` — **le parser identité est nommé**, pas implicite. |
| S | `sweagent/tools/commands.py:33,79` | Clés attendues d'un format de commande **extraites avant rendu** ; commande déclarative à **arguments typés et description générée**. |
| S | `sweagent/tools/tools.py:29,227` | **Blocklist et allowlist au niveau configuration** ; handler unique qui filtre, exécute et **normalise** le résultat. |
| A | `sweagent/tools/utils.py:8,75` | Garde contre les **entrées multi-lignes ambiguës** ; documentation générée depuis les signatures, sans duplication manuelle. |
| S | `sweagent/agent/agents.py:199` | **Exceptions internes distinctes** : action bloquée, retry, forfeit, timeout global. Quatre causes, quatre types. |
| S | `sweagent/agent/agents.py:443` | `DefaultAgent` dont `forward` **sépare appel modèle et exécution d'action**. |
| A | `sweagent/agent/reviewer.py:30,559` | Modèle de soumission et résultat de revue **séparés du résultat d'exécution** ; boucle de scoring **à retry borné** quand le reviewer produit une sortie invalide. |
| S | `tools/windowed/lib/flake8_utils.py:26,92` *(hors extraction)* | `Flake8Error` typée et `format_flake8_output` — et surtout `_update_previous_errors` (`:59`) qui **relocalise les erreurs de lint après une édition**, les numéros de ligne ayant bougé. |

### H4.3 — `bridge`

| S | Source | Notion |
|---|---|---|
| S | `sweagent/agent/agents.py:60` | **Template de prompt versionné** et paramétrable par backend. |
| A | `sweagent/agent/agents.py:149` | Configuration d'agent minimale : modèle, tools, historique, limites. |
| A | `sweagent/agent/action_sampler.py:16,23,49` | Sortie d'action Pydantic conservant **texte, action et métadonnées séparément** ; interface remplaçable ; sous-agent de consultation **séparé du chemin principal**. |
| S | `sweagent/agent/models.py:311,875` | Classe abstraite avec **point d'appel commun** ; fabrique depuis configuration fermée. |
| A | `sweagent/agent/models.py:578` | Adaptateur LiteLLM — **reprendre l'interface, pas la dépendance provider**. |
| S | `sweagent/agent/history_processors.py:74,85` | Processeur par défaut **composable et sérialisable** ; fenêtre des dernières observations **à borne explicite**. |
| A | `sweagent/agent/history_processors.py:179,215` | **Tagger les observations liées à un tool call pour préserver la causalité** ; fenêtre fermée supprimant l'historique le plus ancien **selon une règle testable**. |
| A | `sweagent/agent/history_processors.py:261` | Cache-control attaché aux messages **sans modifier leur contenu métier**. |
| S | `sweagent/agent/history_processors.py:305` | Suppression **par regex bornée et configurable** pour réduire le contexte. |
| A | `sweagent/agent/history_processors.py:340` | Observations image traitées **séparément du texte**. |

### H4.4 — `workspace`

| S | Source | Notion |
|---|---|---|
| S | `tools/windowed/lib/windowed_file.py:150-175` *(hors extraction)* | **`get_window_text` avec ligne de statut et compteurs pré/post** : `[File: X (N lines total)]`, `(N more lines above)`, `(N more lines below)`. **Le modèle sait toujours ce qu'il ne voit pas.** Décision 29. |
| S | `tools/windowed/lib/windowed_file.py:36-52` *(hors extraction)* | `ReplacementInfo` / `InsertInfo` — **une mutation rend son bilan chiffré** : ligne de départ, lignes cherchées, lignes remplacées, **nombre de remplacements**. |
| S | `tools/windowed/lib/windowed_file.py:276` *(hors extraction)* | `undo_edit` — annulation **au niveau du fichier**, distincte du rollback transactionnel de mission. |
| A | `tools/windowed/lib/windowed_file.py:228,240,264,270` *(hors extraction)* | `find_all_occurrences`, `replace` avec `reset_first_line`, `goto`, `scroll` — navigation bornée à sémantique nommée. |
| S | `sweagent/environment/swe_env.py:24,51` | Contrat d'environnement séparant **deployment, repo, setup commands et timeout** ; wrapper mince — **l'agent ne connaît pas le runtime concret**. |
| S | `sweagent/environment/swe_env.py:78,112` | **Copie profonde de configuration avant création d'une instance isolée** ; démarrage qui initialise, reset, puis exécute les commandes de préparation. |
| A | `sweagent/environment/swe_env.py:103` | Hooks d'environnement **injectables aux étapes du lifecycle**. |
| S | `sweagent/environment/repo.py:31,236` | Commandes de **reset vers un commit de base connu** ; fabrique repo depuis une entrée simplifiée et contrôlée. |
| A | `sweagent/environment/repo.py:42,77` | Repo préexistant comme source locale **sans clone implicite** ; chemins **explicitement validés**. |
| S | `sweagent/environment/hooks/abstract.py:1` | Protocole de hooks **sans import inverse**. |
| S | `sweagent/agent/hooks/abstract.py:10-53` *(hors extraction)* | **Treize hooks nommés du cycle de vie de l'agent** — `on_step_start`, `on_actions_generated`, `on_action_started`, `on_action_executed`, `on_step_done`, `on_model_query`, `on_query_message_added`… plus `CombinedAgentHook` (`:56`) qui compose sans que l'appelant sache combien il y en a. |
| S | `sweagent/utils/github.py:17,53` | Exception dédiée aux URL invalides ; **parser l'URL sans laisser la forme brute pénétrer le cœur**. |

### H4.5 — `engine`

| S | Source | Notion |
|---|---|---|
| S | `sweagent/agent/agents.py:224,242` | Classe abstraite avec **lifecycle commun et état explicite** ; **fabrique déterminée par configuration, sans introspection du modèle**. |
| A | `sweagent/agent/agents.py:257` | Retry **séparé du comportement nominal**. |
| S | `sweagent/run/run_single.py:55,125` | Contrat d'une **action unique** — mappe directement sur une nano-étape ; runner séparant config, environnement, agent et sauvegarde. |
| A | `sweagent/run/run_single.py:210` | **Point d'entrée CLI qui ne contient pas la logique métier.** |
| S | `sweagent/run/run_batch.py:75` | Configuration batch Pydantic à options **déclaratives**. |
| A | `sweagent/run/run_batch.py:137,427` | Boucle **interrompable avec exception de break dédiée** ; exécution depuis une configuration **déjà validée**. |
| S | `sweagent/run/run_replay.py:46,66` | **Configuration de replay indépendante du runner original** ; **rejouer une trajectoire sans rappeler le modèle** pour les étapes enregistrées. Directement notre besoin de rejeu de campagne. |
| A | `sweagent/run/run_shell.py:40` | Runner shell minimal pour **diagnostiquer l'environnement hors agent**. |
| A | `sweagent/run/common.py:370` | Sauvegarde des prédictions **append-safe**, par instance et trajectoire. |
| S | `sweagent/run/_progress.py:25,33` | Libellés de progression tronqués **sans ralentir l'exécution** ; gestionnaire **séparé des traces de preuve**. |
| S | `sweagent/utils/patch_formatter.py:28-49` *(hors extraction)* | **`_merge_intervals` — fusion des plages chevauchantes avant projection.** Sans elle, deux hunks voisins projettent trois fois le même bloc. |
| S | `sweagent/utils/patch_formatter.py:98,147` *(hors extraction)* | `_get_hunk_lines(context_length)` et `get_files_str(context_length, linenos)` — **projection bornée autour d'un diff, paramètres explicites**. |

### H4.6 — `campaign` et `observatory`

| S | Source | Notion |
|---|---|---|
| S | `sweagent/run/batch_instances.py:32,39` | **Source d'instances abstraite** ; instance typée avec **identifiant et problème séparés**. |
| A | `sweagent/run/batch_instances.py:48,67,195` | Parser de slice `start:stop` pour un **sous-ensemble reproductible** ; filtrage **avant consommation de ressources**. |
| S | `sweagent/run/compare_runs.py:8,69` | Résoudre l'ensemble des runs terminés ; **comparer deux campagnes en distinguant mêmes résultats et divergences**. |
| S | `sweagent/run/merge_predictions.py:13` | Fusionner plusieurs sorties **sans réécrire les trajectoires sources**. |
| S | `sweagent/run/remove_unfinished.py:13` | Identifier les runs inachevés — **dry-run par défaut**. |
| A | `sweagent/run/run_traj_to_demo.py:27,35` | Transformer une **trajectoire validée en démonstration réutilisable**, conversion contrôlée. |
| S | `sweagent/run/hooks/swe_bench_evaluate.py:1` · `hooks/apply_patch.py:1` | Évaluation post-run et application de patch **isolées du runner**. |
| S | `sweagent/inspector/server.py:15,39,168` | Section problème ajoutée au rendu ; **état de sortie ajouté explicitement** ; trajectoire chargée en **structure JSON portable**. |
| A | `sweagent/inspector/server.py:61,147,188,205` | Patches affichés **séparément du texte** ; résumé compact d'actions ; **résultat absent chargé comme état lisible plutôt qu'exception opaque** ; statut **déduit des artefacts présents**. |
| A | `sweagent/inspector/static.py:86,155` | Arbre de fichiers relatif pour naviguer dans un diff ; **vue statique partageable sans backend actif**. |
| S | `sweagent/run/quick_stats.py:16` | Résumé de campagne **sans charger tous les détails dans le contexte modèle**. |

### H4.7 — `lifecycle` et `broker`

| S | Source | Notion |
|---|---|---|
| S | `sweagent/tools/tools.py:41,56` | **Blocklist de commandes interactives ou dangereuses** ; blocklist exacte contre les **shells imbriqués**. |
| S | `sweagent/environment/swe_env.py:130` | **Timeout distinct par commande de setup**, pas un timeout global unique. |
| A | `sweagent/environment/swe_env.py:124` | Commandes de setup exécutées **dans la même session shell** que l'agent. |
| S | `sweagent/utils/log.py:44,93` | Handler centralisé **avec nom de thread et contexte** ; file handler ajouté ou retiré **par identifiant**, sans reconfigurer tout le logging. |
| S | `sweagent/utils/jinja_warnings.py:4` | **Avertir d'une syntaxe de template probablement erronée avant l'appel modèle.** Une session perdue sur une accolade mal fermée est une session perdue. |
| A | `sweagent/inspector/server.py:221,295` | Handler HTTP **read-only** ; répertoire et port **explicitement fournis**. |

## H5. Ce qu'il ne faut pas reprendre de SWE-agent

| Source | Raison |
|---|---|
| `sweagent/environment/swe_env.py:16` — SWE-ReX / Docker | Dépendance d'infrastructure lourde. **Garder l'interface d'environnement, pas le runtime** — cohérent avec l'abandon de Docker en v1. |
| `sweagent/agent/models.py:578` — LiteLLM | Surface multi-provider contraire au chemin Ollama local unique. |
| `sweagent/run/batch_instances.py:270` — SWE-bench | Benchmark externe, **pas le catalogue fermé d'invariants**. |
| `sweagent/agent/action_sampler.py:153` — comparaison de trajectoires par LLM | **Ne peut pas remplacer la double gate hors modèle** (décision 3). Même verdict que la revue à quorum d'Ouroboros. |
| `sweagent/run/hooks/open_pr.py` | Publication GitHub — nous avons le broker Git de v1. |
| `sweagent/inspector/server.py:295` — inspector monolithique | Remplacé par l'observatory séparé et read-only. |
| `tools/web_browser/` (~450 L) *(hors extraction)* | Navigateur piloté. Hors périmètre, et surface réseau contraire à la décision 21 amendée. |

## H6. Les quatre reprises prioritaires

| # | Reprise | Source | Ce qu'elle ferme |
|---|---|---|---|
| 1 | **Une projection dit ce qu'elle cache** — statut, lignes au-dessus, lignes en dessous | `windowed_file.py:150-175` *(hors extraction)* | Le raisonnement du modèle sur un fichier qu'il croit avoir vu en entier |
| 2 | **Une mutation rend son bilan chiffré** — `n_replacements`, lignes ajoutées | `windowed_file.py:36-52` *(hors extraction)* | Le splice qui touche zéro ligne, et le contrôle « nombre d'occurrences attendu » qui n'avait pas de compteur |
| 3 | **Fusion d'intervalles avant projection** | `patch_formatter.py:28-49` *(hors extraction)* | Le même bloc projeté trois fois quand deux hunks sont voisins |
| 4 | **`thought` / `action` / `observation` en champs typés distincts** | `types.py:15-74` *(hors extraction)* | La séparation du thinking comme heuristique de parsing plutôt que comme forme du contrat |

**Les quatre viennent de la zone que l'extraction avait omise.**

## H7. Ordre de portage SWE-agent

| Phase | Reprises |
|---|---|
| **P0** | `sweagent/types.py:15-100` · `utils/serialization.py:36` · `utils/config.py:30` · `utils/files.py:8` · `agent/models.py:55,66,273` · `agent/problem_statement.py:26` · `agent/hooks/abstract.py:10-56` |
| **P1** | `tools/parsing.py` entier · `tools/commands.py:33,79` · `tools/tools.py:29,41,56,227` · `tools/utils.py:8,75` · `agent/agents.py:199` · `tools/windowed/lib/flake8_utils.py:26,59,92` |
| **P2** | `tools/windowed/lib/windowed_file.py:36-52,150-175,228-280` · `utils/patch_formatter.py:28-49,98,147` · `agent/history_processors.py:74,85,179,215,305` · `environment/swe_env.py:24,51,78,112,130` · `environment/repo.py:31,236` |
| **P3** | `run/batch_instances.py:32,39,48,67` · `run/compare_runs.py:8,69` · `run/merge_predictions.py:13` · `run/remove_unfinished.py:13` |
| **P4** | `utils/log.py:44,93` · `utils/jinja_warnings.py:4` · `utils/github.py:17,53` |
| **P5** | `run/run_replay.py:46,66` · `run/quick_stats.py:16` · `inspector/server.py:15,39,168,188,205` · `inspector/static.py:86,155` · `run/_progress.py:25,33` |

## H8. Attribution

**MIT.** Portage littéral licite avec conservation de la notice. Le dépôt signale que `mini-SWE-agent` lui
succède ; les reprises ci-dessus portent sur l'implémentation présente dans l'archive inspectée.

---

# PARTIE I — Langfuse

## I1. Audit de l'extraction

**Vérifiée avant absorption, comme la partie H.** Verdict opposé : **extraction de qualité, honnête sur ses
propres limites.**

| Contrôle | Résultat |
|---|---|
| Fichiers réguliers annoncés — **5 704** | **exact** |
| Liens symboliques annoncés — **9** | **exact** |
| Version déclarée — **4.30.0** | **exacte** (`package.json`) |
| Lignes de texte — 1 209 171 annoncées | 1 221 342 mesurées, **écart 1 %** (le document exclut 20 fichiers binaires) |
| **Ancres `fichier:ligne`** | **15 vérifiées, 15 exactes** — toutes pointent sur la **définition canonique**, et la notion décrite correspond au symbole |
| Empreinte SHA-256 de l'inventaire | **non reproduite** avec la convention devinée — la spécification du format de chemin et de l'ordre de tri manque pour la rejouer. Le compte de fichiers étant exact, il s'agit d'un défaut de documentation, pas d'un inventaire divergent |

Le document **déclare lui-même ses limites** : *« l'inventaire est exhaustif ; l'analyse sémantique est
ciblée »*, *« ce document ne prétend pas à une lecture ligne par ligne des 1,2 million de lignes »*. Il
fournit une **carte de couverture par famille avec le nombre de fichiers cités par famille** — donc il rend
visible ce qu'il ne couvre pas, ce qui est exactement ce que la partie H n'avait pas fait.

**Différence de méthode qui vaut d'être notée.** L'extraction H affirmait une couverture qu'elle n'avait pas ;
celle-ci quantifie sa couverture et nomme les familles laissées de côté. Le second comportement est le seul
auditable — et il correspond à ce que la décision 13 exige de nos propres nœuds.

## I2. Pourquoi ce dépôt

Plateforme d'observabilité LLM, **1 209 171 lignes**, TypeScript/React/worker, version 4.30.0.
**MIT pour le socle**, avec exceptions commerciales sous `ee/`, `web/src/ee/` et `worker/src/ee/`
(`LICENSE:5`, `ee/LICENSE:13`) — **aucune reprise proposée depuis ces chemins**.

**105 mappages** — 88 *adapter*, 4 *inspirer*, 13 *écarter* — sur **67 fichiers cités**, couvrant **les neuf
modules**, `refinery` compris. C'est la première extraction produite **après** la décision 26, et elle en
tient compte.

### I2.1 — L'apport propre

Le dépôt apporte une chaîne complète que nous n'avions nulle part ailleurs :

> **observation → évaluation identifiée → résultat versionné → lecture reproductible**

Quatre zones où il est le plus fort :

1. **L'identité d'un résultat, distincte de son identité de transport** — ce qui permet de republier sans
   recompter.
2. **Le cycle de vie d'un run avec fencing** — claim conditionnel, heartbeat à perte de propriété explicite,
   classification pure de péremption, et réconciliation protégée contre un heartbeat renouvelé.
3. **La lecture bornée de grosses traces** — projection compacte par défaut, arbre résistant aux doublons,
   durée de span distincte de l'enveloppe du sous-arbre.
4. **Le versionnement de prompts avec label mobile** — directement applicable à `refinery`.

**Ce qu'il n'a pas non plus** — neuvième dépôt, neuvième fois : aucun catalogue fermé de relations
métamorphiques, aucune gate rouge-avant/vert-après, aucun mutation-check. Le document le dit lui-même :
*« aucun runner acceptant du `sourceCode` libre ne devient l'oracle Pithos »*.

## I3. Ce que la reprise a changé dans la documentation

| Cible | Nature du changement |
|---|---|
| `EXPLANATIONS.md` | Décisions 13, 16, 26, 27 et 28 amendées · **décision 30 ajoutée** |
| `PROJECT.md` | 1 critère ajouté |
| `ROADMAP.md` | Items P0, P1, P2, P3, P4, P5, P9 |

### I3.1 — Décision 30 : l'identité logique n'est pas l'identité de transport

**La décision qui manquait entre la 16 et la 22.**

La décision 22 pose qu'une identité est une clé typée. La décision 16 pose qu'une demande d'effet est
réclamée avant exécution. Aucune ne dit ce qui se passe quand **la publication d'un résultat déjà calculé
échoue et doit être retentée**.

Langfuse sépare deux identités (`evalScoreIds.ts:6` · `evalScoreEvent.ts:21`) :

| Identité | Nature | Comportement au retry |
|---|---|---|
| **résultat** | déterministe — UUID v5 sur `(exécution, nom, occurrence)` | **stable** |
| **transport** | renouvelée à chaque tentative | **change** |

**Conséquence : on peut republier autant de fois qu'il le faut sans jamais compter deux résultats.** Chez
nous, l'identité de résultat est la clé typée `(mission, nœud, tentative, relation)` de la décision 22 ; ce
qu'il faut ajouter, c'est l'identité de transport séparée, renouvelée, et **le fait qu'elle ne participe
jamais à la comparaison**.

Deux corollaires du même module :

- **Les métadonnées de provenance de l'hôte sont écrites après les données de l'appelant**
  (`evalScoreEvent.ts:54`), dans un **espace de champs réservé**. Un champ de provenance n'est jamais
  écrasable par la charge utile.
- **L'autorité interne n'est pas attribuable par l'API publique** (`scores.ts:18`) : l'énumération des
  sources acceptées en création publique **exclut** la valeur réservée aux évaluateurs. Chez Ouroboros,
  `criterion_source` avait un défaut sûr ; ici c'est **le schéma d'admission qui rend la valeur inatteignable**.
  C'est strictement plus fort, et c'est la forme à retenir pour le champ de provenance de nos verdicts.

### I3.2 — Décision 16 amendée : le fencing du cycle de vie

`runLifecycle.ts` donne le contrat complet, et il est plus dur que le nôtre sur trois points.

- **Le claim est conditionnel et une seule transition réussit** (`:37`). Nous avions le claim idempotent
  d'OpenHands ; ici c'est un CAS sur l'état. Réserve du document, à retenir : **un CAS de statut n'est pas à
  lui seul un jeton de propriété** — il faut la génération.
- **Le heartbeat retourne une perte de propriété explicite** (`:64`), pas un booléen ambigu. Après perte, **on
  arrête les écritures et on propage la demande d'annulation**. C'est la face manquante de notre décision 18 :
  savoir qu'on a perdu la main est aussi important que savoir annuler.
- **La classification de péremption est pure et à quatre causes** (`:702`) : délai de queue dépassé, durée
  maximale atteinte, heartbeat perdu, attente d'approbation expirée — **et la durée maximale l'emporte sur le
  heartbeat**. Un run qui bat encore mais dure trop est périmé quand même.
- **La réconciliation est protégée contre un heartbeat renouvelé** (`:673`) : la transition n'est réappliquée
  que si l'état observé n'a pas changé depuis la lecture. **Une lecture de run périmé ne donne pas le droit de
  tuer une nouvelle incarnation.** C'est exactement le risque de deux réveils launchd rapprochés que la
  décision 27 nomme.

### I3.3 — Décision 13 amendée : publier la preuve avant la transition terminale

`evalCompletion.ts:23` — le code **écrit les résultats, les publie, puis marque l'exécution terminée**. Notre
décision 13 exige un reçu attesté ; celle-ci ajoute **l'ordre** : la preuve durable locale précède le verdict
terminal, et la réconciliation au démarrage rattrape une interruption entre les deux.

Et un contre-exemple explicitement écarté (`codeEvalExecution.ts:363`, statut **X**) : un `catch` qui
**journalise l'échec de trace et continue**. Acceptable pour une télémétrie secondaire, **inacceptable pour la
preuve primaire** — si la trace de l'exécution n'a pas pu être écrite, le verdict n'est pas attesté. C'est la
même règle que le `_receipt_custody_failure` d'Ouroboros, vue depuis son contre-exemple.

Complément : `evalExecutionMetrics.ts:14` sépare **le résultat d'infrastructure de la qualité évaluée**.
Calcul exécuté, cause de panne, verdict et effet sont quatre axes — confirmation directe de la décision 23.

### I3.4 — Décision 28 amendée : deux confirmations et un contre-exemple

**Confirmation forte de l'accumulateur d'erreurs.** `jsonSchemaValidation.ts:58` valide contre un **schéma
compilé réutilisé pour un lot**, et retourne `path` / `message` / `keyword`. Mais la configuration voisine
(`:25`, statut **X**) **ne renvoie que la première erreur et désactive la validation des formats** — le
document la marque explicitement comme *« incompatible avec notre admission exhaustive »*. Deux sources
indépendantes disent maintenant la même chose, et celle-ci en donne le contre-exemple.

**Refus des segments de chemin dangereux** (`OtelIngestionProcessor.ts:107`) : `__proto__`, `constructor`,
`prototype` sont refusés lors de la reconstruction d'une structure imbriquée. En Python le vecteur diffère,
mais la règle se transpose en **grammaire fermée de chemins** — ce qui est déjà la forme de la décision 28.

**Interpolation sans expressions** (`prompts.ts:14`) : le moteur remplace des **noms de clés**, y compris
contenant un point, **sans résolution de propriété profonde**. Troisième source sur ce point après OpenHands
et le contre-exemple de Pi.

### I3.5 — Décision 26 amendée : versions, label mobile et cache

`refinery` reçoit quatre reprises directes.

- **Une version est créée avec ses dépendances, publiées ensemble** (`createPrompt.ts:93`) — version, type,
  tags et liens en une seule opération.
- **Le label mobile est séparé de la version immuable** (`updatePromptLabels.ts:3`). C'est exactement notre
  paire `shadow` / `active` : le contenu est versionné et immuable, **et seul le déplacement du label
  `active` est soumis à la gate d'effet**.
- **Le graphe de dépendances est borné en cycles et en profondeur** (`PromptService/index.ts:242`), et il faut
  **tracer les versions réellement résolues de toutes les dépendances**, pas seulement le nom de la racine.
- **La clé de cache distingue label et version** (`:204`) — sinon la version numérique `2` et le label `"2"`
  collisionnent. Chez nous : tuple typé `(scope, kind, id, version)`, jamais une chaîne concaténée. C'est la
  décision 22 appliquée au cache.

### I3.6 — Décision 27 amendée : Host, Origin, et le lock à trois états

- **Validation de `Host` et `Origin` avant traitement MCP** (`mcp/server/security.ts:70`), **sans reprendre
  l'échappatoire `allowedHosts=["*"]`**, et avec la règle : **l'absence d'en-tête `Origin` n'est pas une
  preuve de confiance**.
- **Le lock a trois états**, pas deux (`RedisLock.ts:4`) : acquis, détenu par autrui, **indisponible**. Et le
  défaut de Langfuse — `onUnavailable = proceed` — est explicitement marqué comme **inadapté à nos écritures
  critiques : indisponible doit bloquer.** Un verrou dont on ne sait pas l'état n'autorise rien.
- **La libération est conditionnée à l'identité du propriétaire** (`RedisLock.ts:55`) : comparer le jeton
  avant suppression **et avant renouvellement**. Troisième source sur ce point.

### I3.7 — Le manifest est le commit point

`handleBlobStorageIntegrationProjectJob.ts:1433` — **le manifest est écrit après tous les fichiers, et le
curseur de synchronisation n'avance qu'ensuite**. Un export sans manifest est un export incomplet, par
construction et sans ambiguïté.

Transposé chez nous : le marqueur de complétude d'une mission — celui que le réveil suivant lit — s'écrit
**en dernier**, après le journal, l'arbre et les artefacts, et par `rename` atomique. C'est la version
« export » de l'ordre déjà posé par la décision 16.

### I3.8 — Critère de socle ajouté

- **Republier un résultat déjà calculé ne le compte jamais deux fois** : l'identité logique du résultat est
  déterministe et l'identité de transport est renouvelée à chaque tentative.

## I4. Catalogue des reprises

`A` adapter · `I` inspirer · `X` écarter. Chemins relatifs à `resources/langfuse-main/`.
Les identifiants `LF***` sont ceux de l'extraction source.

### I4.1 — `kernel`

| ID | Source | Notion |
|---|---|---|
| LF001 | `packages/shared/src/domain/observations.ts:5` | Observation typée et **causalité explicite** : appel modèle, outil et évaluation séparés ; mission, nœud, tentative, parent et horodatages conservés. |
| LF002 | `packages/shared/src/domain/scores.ts:4` | **La source d'un résultat est distincte de sa valeur.** Une source « évaluateur » peut désigner un LLM judge : **elle ne certifie pas un invariant**. |
| LF003 | `packages/shared/src/domain/scores.ts:18` | **L'autorité interne n'est pas attribuable par l'API publique** — l'énumération d'admission exclut la valeur réservée. Plus fort qu'un défaut sûr. |
| LF004 | `packages/shared/src/domain/score-configs.ts:5` | Configuration de score : noms, types, **bornes numériques et catégories explicites**, unicité des labels. |
| LF005 | `packages/shared/src/server/evals/evalScoreIds.ts:6` | **Identité déterministe d'un résultat** (UUID v5 sur un tuple), stable à travers les retries. Décision 30. |
| LF006 | `worker/src/features/evaluation/evalScoreEvent.ts:21` | **Identité de transport renouvelée, identité de résultat déterministe.** Republier sans recompter. |
| LF007 | `worker/src/features/evaluation/evalScoreEvent.ts:54` | **Métadonnées de provenance de l'hôte écrites après la charge utile**, dans un espace de champs réservé. |
| LF008 | `packages/shared/src/domain/observations.ts:82` | **Mesure fournie distincte de mesure calculée** : valeur, origine et disponibilité. Ne pas reprendre les agrégats qui **convertissent une absence en zéro**. |
| LF009 | `packages/shared/src/server/otel/OtelIngestionProcessor.ts:133` | **Budget transactionnel** avant reconstruction de métadonnées imbriquées — compter les emplacements, trous d'index compris. |
| LF010 | `packages/shared/src/server/otel/OtelIngestionProcessor.ts:107` | **Refus des segments de chemin dangereux** (`__proto__`, `constructor`, `prototype`). En Python : grammaire fermée de chemins. |

### I4.2 — `verifier`

| ID | Source | Notion |
|---|---|---|
| LF011 | `packages/shared/src/server/evals/codeEvalDispatcherTypes.ts:139` | **Frontière explicite entre orchestration et exécuteur** — contrat entrée / résultat / erreur. Remplacer `code.source` par une relation admise. |
| LF012 | `…codeEvalDispatcherTypes.ts:60` | Contexte d'exécution typé et borné : scope, runtime, identité, payload. **Caps en octets à la vraie frontière d'exécution.** |
| LF013 | `…codeEvalDispatcherTypes.ts:131` | **Résultat structuré non vide** — un booléen ou un score numérique ne constitue pas à lui seul un verdict. |
| LF014 | `…codeEvalDispatcherTypes.ts:161` | **Taxonomie d'erreurs de l'exécuteur** : source invalide, timeout, erreur du code, réponse invalide. **Les retries se déterminent depuis la cause.** |
| LF015 | `worker/src/features/evaluation/evalExecutionDeps.ts:128` | Dépendances injectables — horloge, stockage, lancement de processus. **Ne pas mettre `callLLM` dans le même objet que le verifier.** |
| LF016 | `worker/src/features/evaluation/evalCompletion.ts:23` | **Publier la preuve avant la transition terminale.** Décision 13 amendée. |
| LF017 | `…codeBased/executeCodeBasedEvaluation.ts:20` | Exécution reliée à **une version et à sa trace** : protocole, relation, empreinte de code, entrée. |
| LF018 · **X** | `packages/shared/src/server/evals/codeEvalExecution.ts:363` | **Contre-exemple** : un `catch` qui journalise l'échec de trace et continue. Acceptable en télémétrie, **inacceptable pour la preuve primaire**. |
| LF019 | `packages/shared/src/utils/jsonSchemaValidation.ts:58` | **Schéma compilé réutilisé pour un lot**, erreurs avec `path` / `message` / `keyword`. |
| LF020 · **X** | `…jsonSchemaValidation.ts:25` | **Contre-exemple direct de la décision 28** : cette configuration ne renvoie que **la première erreur** et désactive la validation des formats. |
| LF021 | `scripts/code-eval-runners/python/code_based_eval_handler.py:188` | Diagnostic Python **avec type et ligne du code exécuté**, en plus de stderr brut. Petit port utile pour notre enveloppe de subprocess. |
| LF022 · **X** | `…code_based_eval_handler.py:109` | **`exec` n'est pas une isolation.** Le modèle ne choisit jamais le code exécuté chez nous. |
| LF023 · **X** | `packages/shared/src/server/evals/localCodeEvalDispatcher.ts:17` | Runner VM local : **plusieurs timeouts locaux et un `Promise.race` ne constituent ni une deadline globale ni un arrêt des effets**. |

### I4.3 — `bridge`

| ID | Source | Notion |
|---|---|---|
| LF024 | `packages/shared/src/utils/prompts.ts:14` | **Interpolation de variables sans expressions** — remplacement de noms de clés, y compris avec un point, **sans résolution de propriété profonde**. Troisième source. |
| LF025 | `packages/shared/src/features/prompts/parsePromptDependencyTags.ts:18` | Référence par **nom et version ou label**, résolue avant l'appel, **versions concrètes tracées**. Le modèle ne choisit jamais une référence arbitraire. |
| LF026 | `worker/src/features/tokenisation/usage.ts:31` | **Tokenisation locale avec incertitude explicite** — usage fourni distinct de l'estimation de préflight. Les branches multi-provider ne qualifient pas Ling. |
| LF027 | `packages/shared/src/in-app-agent/server/toolErrors.ts:8` | **Une erreur d'outil se déduit d'un signal structuré, jamais d'une chaîne contenant « error ».** |
| LF028 | `…toolErrors.ts:56` | **Déballage conservateur d'une réponse MCP** : un seul bloc textuel déballé, tableaux multimodaux et marqueur d'erreur préservés. |

### I4.4 — `workspace`

| ID | Source | Notion |
|---|---|---|
| LF029 | `packages/shared/src/server/services/safeBlobKeySegment.ts:16` | **Découpe UTF-8 respectant les frontières de codepoints.** À n'appliquer qu'aux aperçus, **jamais au contenu probant**. |
| LF030 | `…safeBlobKeySegment.ts:46` | **ID logique séparé du nom de stockage.** Réserve reprise : un hash tronqué à 64 bits ne prouve pas l'injectivité. |
| LF031 | `worker/src/features/observation-field-overflow/processObservationFieldOverflow.ts:35` | **Référence publiée seulement après upload réussi** ; en cas d'échec, la valeur reste en place. |
| LF032 | `worker/src/features/blobstorage/manifest.ts:22` | **Manifest versionné de complétude** : fichiers, formats, tailles, intervalle **demi-ouvert**. Ajouter empreintes et génération. |
| LF033 | `worker/src/features/blobstorage/handleBlobStorageIntegrationProjectJob.ts:1433` | **Le manifest est le commit point** — écrit après tous les fichiers, curseur avancé ensuite. |
| LF034 | `worker/src/features/blobstorage/gzipStream.ts:28` | Flux compressé : **attendre la fin côté lisible pour ne pas perdre le trailer**. |
| LF103 · **X** | `worker/src/services/ClickhouseWriter/index.ts:180` | La division de batch est une bonne référence de backpressure ; **la troncature du dernier enregistrement trop gros est à écarter**. |

### I4.5 — `engine`

| ID | Source | Notion |
|---|---|---|
| LF035 | `packages/shared/src/in-app-agent/server/runLifecycle.ts:37` | **Claim conditionnel — une seule transition réussit.** Réserve : un CAS de statut n'est pas à lui seul un jeton de propriété. |
| LF036 | `…runLifecycle.ts:64` | **Heartbeat à perte de propriété explicite** (retour *fenced*, pas un booléen) ; arrêt des écritures et propagation de l'annulation. |
| LF037 | `…runLifecycle.ts:93` | **Transition terminale conditionnelle**, métrique comptée **une fois et seulement si la transition est acceptée**. |
| LF038 | `…runLifecycle.ts:702` | **Classification pure des runs périmés** à quatre causes ; **la durée maximale l'emporte sur le heartbeat**. |
| LF039 | `…runLifecycle.ts:673` | **Réconciliation protégée contre un heartbeat renouvelé.** Une lecture de run périmé ne donne pas le droit de tuer une nouvelle incarnation. |
| LF040 | `…persistence.ts:154` | **Événements et état terminal dans la même unité de publication.** Reprendre la cohérence, pas le SQL. |
| LF041 | `…persistence.ts:700` | **Flush limité au préfixe capturé avant l'attente** — les événements ajoutés pendant la persistance sont conservés. |
| LF042 | `…eventCompaction.ts:35` | Coalescence des deltas **contigus du même message** — pour projection, jamais pour le brut. |
| LF043 | `worker/src/features/evaluation/retryObservationNotFound.ts:30` | Retry avec **compteur et âge global conservés** ; chez nous l'âge s'inscrit dans la deadline de mission. |
| LF044 | `worker/src/features/evaluation/evalExecutionMetrics.ts:14` | **Résultat d'infrastructure orthogonal à la qualité évaluée.** Confirme la décision 23. |
| LF090-092 | `…runLifecycle.test.ts:72,128,300` | Scénarios de régression : **heartbeat renouvelé entre lecture et réconciliation**, aucun résultat publié si l'admission échoue, **course entre claim et annulation**. |

### I4.6 — `campaign` et `refinery`

| ID | Source | Notion |
|---|---|---|
| LF045 | `web/src/features/mcp/core/define-tool.ts:112` | **Définition d'outil et validation runtime au même endroit** ; Pydantic reste la source unique, l'accord schéma/handler est testé. |
| LF046 | `…define-tool.ts:69` | Profil de schéma MCP **explicitement restreint** — rejette unions et intersections, exige un objet. Choix de serveur, pas interdiction du protocole. |
| LF047 | `web/src/features/mcp/server/registry.ts:82` | **Registre explicite, collisions détectées avant publication**, y compris à l'intérieur d'un même lot. |
| LF048 | `…registry.ts:149` | **La gate de disponibilité s'applique à l'appel direct**, pas seulement à la découverte. Masquer n'est pas interdire. |
| LF049 | `…registry.ts:170` | Permission de lecture ou allowlist — **ne pas faire confiance à un `readOnlyHint` fourni par du code généré**. |
| LF050 | `web/src/features/mcp/core/run-mcp-tool.ts:13` | Instrumentation par outil et **classe de faute** : requête invalide distincte de panne serveur. |
| LF051 | `packages/shared/src/server/repositories/dataset-items.ts:285` | **Valider l'état fusionné après un update partiel** ; distinguer champ absent et `null` explicite. |
| LF052 | `…dataset-items.ts:1308` | **Lecture à version temporelle figée** — comparer deux configurations sur le même corpus. |
| LF053 | `worker/src/features/experiments/experimentServiceClickhouse.ts:73` | Identité d'item et tentative **reliées au run**, items existants retrouvés au redémarrage. |
| LF054 · **X** | `worker/src/features/experiments/scheduleExperimentEvals.ts:37` | **Planification best-effort** : l'erreur est loggée sans invalider l'appelant. À écarter pour une gate de livraison. |
| LF055 | `web/src/features/prompts/server/actions/createPrompt.ts:93` | **Version créée avec ses dépendances, publiées ensemble.** |
| LF056 | `…utils/updatePromptLabels.ts:3` | **Label mobile séparé d'une version immuable** — notre paire `shadow`/`active`, où seul le déplacement du label passe la gate. |
| LF057 | `packages/shared/src/server/services/PromptService/index.ts:242` | Graphe de dépendances **borné en cycles et profondeur** ; tracer **les versions réellement résolues**, pas le nom de la racine. |
| LF058 | `…PromptService/index.ts:227` | Génération de cache invalidant un ensemble **sans supprimer toutes les clés** ; résolution des créations concurrentes par « premier gagnant ». |
| LF059 | `…PromptService/index.ts:204` | **Clé de cache distinguant label et version** — sinon la version `2` et le label `"2"` collisionnent. Décision 22 appliquée au cache. |
| LF060 | `…createPrompt.ts:242` | **Un échec secondaire après commit ne doit pas faire croire à un échec de la création durable** — ni provoquer un doublon. |
| LF061 | `worker/src/features/evaluation/deterministicSampling.ts:6` | **Cohorte déterministe par hash** : SHA-256, 53 premiers bits, seuil demi-ouvert. Une cible garde sa cohorte. |
| LF062 · **I** | `web/src/features/score-analytics/server/buildScoreComparisonQuery.ts:50` | Comparer candidat et base **sur les mêmes missions, corpus et versions**, en affichant appariés, manquants et dénominateur. |
| LF093-098 | tests `deterministicSampling`, `gzipStream`, `mcp-define-tool`, `treeBuilding` | Vecteur de référence de hash, **cohortes emboîtées quand le taux augmente**, export multichunk **décompressé à l'octet près**, champ nommé `anyOf` restant légal comme donnée, résistance aux IDs dupliqués, **enfant asynchrone terminant après son parent**. |

### I4.7 — `lifecycle` et `broker`

| ID | Source | Notion |
|---|---|---|
| LF063 | `worker/src/utils/RedisLock.ts:55` | **Libération conditionnée à l'identité du propriétaire** — comparer le jeton avant suppression **et avant renouvellement**. |
| LF064 | `worker/src/utils/RedisLock.ts:4` | **Lock à trois états** : acquis, détenu par autrui, **indisponible**. Le défaut `onUnavailable = proceed` est **inadapté : indisponible doit bloquer**. |
| LF065 | `worker/src/utils/PeriodicExclusiveRunner.ts:69` | Renouvellement de lease **mutualisé et limité en fréquence**, perte typée. |
| LF066 | `packages/shared/src/server/ingestion/processEventBatch.ts:116` | **Admission d'un lot avec résultat par événement** et inventaire des rejets. |
| LF067 | `…processEventBatch.ts:283` | **Persistance des payloads avant mise en queue** — un upload échoué empêche l'enqueue. |
| LF068 | `worker/src/features/blobstorage/inFlightExports.ts:30` | **Registre des opérations en cours pour l'arrêt** : handle inscrit, retiré en `finally`, attente bornée. |
| LF069 | `worker/src/scripts/replayIngestionEventsV2/replay.ts:182` | Script opérateur : **dry-run, retry, rate limit et sémaphore**, débit borné indépendamment de la concurrence. |
| LF070 · **X** | `…replay.ts:377` | **Checkpoint non sûr** : le compteur inclut les lots en erreur et **ne représente pas un préfixe contigu**. |
| LF071 | `web/src/features/mcp/server/security.ts:70` | **Validation de `Host` et `Origin`** — sans l'échappatoire `allowedHosts=["*"]`, et **l'absence d'`Origin` n'est pas une preuve de confiance**. |
| LF104 | `LICENSE:5` | **Frontière de licence définie par les chemins** : MIT pour le socle, exceptions `ee/`, `web/src/ee/`, `worker/src/ee/`. |

### I4.8 — `observatory`

| ID | Source | Notion |
|---|---|---|
| LF072 | `web/src/features/mcp/server/observations/schema.ts:137` | **Projection compacte par défaut** : identité, type, statut, temps, liens ; entrées/sorties/métadonnées **chargées à la demande**. |
| LF073 | `…schema.ts:182` | **Pagination bornée et champs explicitement admis**, wildcard exclusif. |
| LF074 | `…tools/listObservations.ts:385` | **Une lecture coûteuse est subordonnée à un périmètre** : nœud, mission, identifiant ou intervalle **exigés avant gros IO**. |
| LF075 | `…listObservations.ts:443` | `limit+1` pour `hasMore` ; **curseur opaque** adapté aux journaux — génération de segment et offset vérifié. |
| LF076 | `…schema.ts:225` | **Projection pure indépendante de la collecte** ; les champs absents restent visibles ; une troncature d'aperçu **se déclare**. |
| LF077 | `web/src/features/traces/fns/treeBuilding.ts:111` | **Déduplication cohérente entre arbre et détail** — un ID dupliqué crée sinon un graphe multiparent explosif. |
| LF078 | `…treeBuilding.ts:164` | **Parcours itératif avec ensemble `visited`**, agrégation bottom-up, garde contre les visites multiples. |
| LF079 | `…getSubtreeDurationOverflowMs.ts:23` | **Durée du span distincte de l'enveloppe temporelle du sous-arbre** — `max(fin) − min(début)` quand des enfants dépassent le parent. **Ne pas sommer les durées.** |
| LF080 | `…IOPreview/fns/jsonViewSizeGate.ts:78` | **Sérialisation unique** réutilisée pour la taille, l'aperçu et le téléchargement ; échec de sérialisation → erreur visible. |
| LF081 | `…jsonViewSizeGate.ts:59` | **Budget de rendu en nœuds distinct du budget en caractères** — une chaîne énorme est une ligne, un JSON imbriqué des milliers. |
| LF082 | `packages/shared/src/features/query/server/queryBuilder.ts:140` | **Catalogue fermé d'agrégations** : compteurs, percentiles, histogrammes. Reprendre le contrat de requête validée, pas le query builder. |
| LF083 | `web/src/features/score-analytics/lib/statistics-utils.ts:169` | **Accord avec effectif et données absentes explicites** ; retourner « inconnu » sans observations. |
| LF084 · **I** | `…statistics-utils.ts:38` | Mesure d'accord corrigée du hasard — **ne pas copier sans revue**, le cas dégénéré est délicat. |
| LF085 | `worker/src/services/IngestionService/index.ts:1240` | **Ordre déterministe de fusion des événements.** Chez nous : ordre par séquence hôte. |
| LF086 · **X** | `…IngestionService/index.ts:1211` | **Correction silencieuse d'une durée négative** — à écarter : une fin antérieure au début est **une anomalie à conserver et à montrer**. |
| LF087 · **I** | `packages/shared/src/server/ingestion/sampling.ts:6` | Échantillonnage cohérent au niveau trace — **interdit sur les traces brutes**, utile en analyse dérivée seulement. |
| LF088 | `packages/shared/src/utils/IORepresentation/parseIO.ts:3` | **Le compactage est une tentative explicite ; son échec rend l'original.** |
| LF089 · **X** | `packages/shared/src/utils/json.ts:9` | **Réparation textuelle de pseudo-JSON** — à écarter de l'admission : remplacer `True`/`False`/`None` et les apostrophes **peut changer une chaîne valide métier**. |

## I5. Ce qu'il ne faut pas reprendre de Langfuse

| Source | Raison |
|---|---|
| `docker-compose.yml:6` — Postgres, ClickHouse, Redis, MinIO | **Stack distribuée incompatible** avec les JSONL sans projection SQL de la décision 10. |
| `docker-compose.yml:26` — télémétrie activée par défaut | Contraire à la contrainte dure n°5. |
| `codeEvalDispatchers.ts:32` — exécuteur AWS Lambda | Backend distant hors du chemin nominal. **Ne pas introduire un compte cloud pour qualifier notre verifier.** |
| `normalized-io/README.md:10` | Le README dit lui-même que le parser **n'est pas assez validé en production**. |
| `ee/`, `web/src/ee/`, `worker/src/ee/` | **Périmètre Enterprise commercial** — aucune copie sous hypothèse MIT. |
| Auth, RBAC, organisations, facturation, connecteurs Slack/PostHog | Plateforme multi-tenant. Hors périmètre d'un harness local mono-utilisateur. |
| Retention / deletion cleaners | **Mission de suppression incompatible avec la conservation append-only.** La maintenance ne peut viser que des projections dérivées. |

## I6. Les cinq reprises prioritaires

| # | Reprise | Source | Ce qu'elle ferme |
|---|---|---|---|
| 1 | **Identité de résultat déterministe, identité de transport renouvelée** | `evalScoreIds.ts:6` · `evalScoreEvent.ts:21` | Le résultat compté deux fois parce que sa publication a été retentée |
| 2 | **Réconciliation protégée contre un heartbeat renouvelé** | `runLifecycle.ts:673,702` | Une lecture de run périmé qui tue une nouvelle incarnation — deux réveils launchd rapprochés |
| 3 | **Le manifest est le commit point** | `handleBlobStorage…:1433` | Le marqueur de complétude écrit avant que tout soit écrit |
| 4 | **Lock à trois états, indisponible bloque** | `RedisLock.ts:4,55` | Le verrou dont on ne sait pas l'état et qui laisse pourtant passer |
| 5 | **Durée de span distincte de l'enveloppe du sous-arbre** | `getSubtreeDurationOverflowMs.ts:23` | La vue d'arbre qui somme des durées concurrentes et ment sur le temps réel |

## I7. Ordre de portage Langfuse

| Phase | Reprises |
|---|---|
| **P0** | LF001-LF008, LF010 · LF019 · LF044 |
| **P1** | LF011-LF017, LF021 · LF090-LF092 |
| **P2** | LF029-LF034 · LF041-LF043 · LF024, LF026-LF028 |
| **P3** | LF045-LF053 · LF085 |
| **P4** | LF035-LF040 · LF063-LF068, LF071 |
| **P5** | LF072-LF083, LF088 · LF097-LF098 |
| **P9** | LF055-LF061 · LF093-LF094 |

## I8. Attribution

**MIT pour le socle** (`LICENSE:5`), avec exceptions commerciales sous `ee/`, `web/src/ee/` et
`worker/src/ee/` (`ee/LICENSE:13`) — **aucune reprise n'est proposée depuis ces chemins**. Conserver les
notices si un port substantiel est réalisé.

---

## J — GVS5H : intégration sélective, 13:09

Archive : `resources/GVS5H-master/`. Les chemins de code ci-dessous sont relatifs à
`codebase/v2-current/escalation/`. Relecture du code ; les résultats du papier ne constituent
pas une validation de Ling 8B. L'évaluation initiale reste dans [GVS5H.md](GVS5H.md).

| ID | Source | Verdict | Décision et état |
|---|---|---|---|
| J001 | `multiagent.py:62-84` | **Adapter** | Appels, tokens rapportés et troncatures agrégés dans observatory. Refus de budget avant requête séparé ; modes trial/selftest/probe séparés. |
| J002 | `regrade.py:25-78` | **Adapter** | Engine ajoute un rapport durable par tentative avec RecordKey ; observatory garde l'historique. Aucun remplacement d'un ancien verdict, aucun reçu rétrospectif. |
| J003 | `multiagent.py:261` | **Inspirer** | Done sans artefact insuffisant : déjà couvert plus fortement par transaction, facts et reçu durable dans run_attempt. |
| J004 | `multiagent.py:430-435` | **Reporté** | Au branchement du marcheur, détecter le non-progrès par nœud, critère et empreintes observées. La comparaison du texte de tâche n'est pas portée. Le dashboard compte les empreintes finales inchangées. |
| J005 | `multiagent.py:290-310` | **Écarté** | Réécriture des notes par le modèle : incompatible avec l'inventaire déterministe et les preuves append-only. |
| J006 | `multiagent.py:274-288` | **Écarté** | Résumé du thinking tronqué par un appel supplémentaire : aucun résumé généré ne devient le contexte suivant. |
| J007 | `orchestrator.py:196-205` | **Écarté** | Repli du contenu absent vers reasoning : bridge conserve le brut mais refuse son exécution. |
| J008 | `multiagent.py:412-476` | **Écarté** | Boucle manager/worker, MAX_ITERS et finalisation par nouvel appel modèle : la borne de Pithos reste murale. |

**Correction de l'extraction initiale.** `passed_before_regrade` ne garantit pas à lui seul
un historique append-only : la source écrit des résultats regradés et peut remplacer un sidecar
lors d'un nouveau passage. La notion est **adaptée**, pas copiée dans journal. Aucun outil de
re-scoring n'est ajouté sans protocole de re-scoring défini.

`NOTICE.md` distingue code MIT, papier/données CC BY 4.0 et énoncés tiers exclus de cette licence.
Aucun corpus ni code de ce dépôt n'est embarqué. Le benchmark ne valide pas nos relations métamorphiques.

## K — Graphify : contexte et documentation, 13:09

Archive : `resources/graphify-main/`. L'évaluation complète reste dans [graphify.md](graphify.md).
Les décisions suivantes remplacent ses propositions préalables.

| ID | Source | Verdict | Décision et état |
|---|---|---|---|
| K001 | `graphify/serve.py:1186-1210` | **Adapter** | Notice d'omission en tête de ContextPacket, comptes par raison fermée. Livré et testé ; notice et séparateur comptent dans le budget, contrairement à la source. |
| K002 | `tests/test_architecture_doc.py:1-87` | **Adapter** | Table livré/prévu dans ARCHITECTURE, lue par tests/doc_check.py. 20 interfaces livrées, 11 modules ; signatures contrôlées sans exécuter de code du document. Injections et garde contre un inventaire vide. |
| K003 | `graphify/benchmark.py:1-152` | **Inspirer** | Mesures depuis usage de bridge, séparées des estimations. Capacité absente inconnue, capacité déclarée asserted. Aucun gain token estimé par BFS présenté comme mesure du prompt effectif. |
| K004 | `graphify/paths.py:29-90` | **Écarté** | Écriture atomique moins forte que la transaction livrée ; aucun remplacement de workspace/journal. |
| K005 | graphe, cache, résolution tree-sitter, serveur MCP | **Écarté** | Aucune dépendance Graphify/NetworkX/tree-sitter ; le banc possède une sélection déterministe sans besoin de ce graphe. |

Code réécrit depuis les notions, aucune copie littérale. `NOTICE` annonce Apache 2.0 et les
contributions MIT antérieures. Aucun graphe, export ou envoi réseau de Graphify n'a été exécuté.
