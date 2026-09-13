# GVS5H — évaluation

**Décision courante — 13:09 : intégration sélective autorisée et réalisée**, cataloguée dans
[IMPORT_REPORT.md](IMPORT_REPORT.md) § J. Appels/troncatures, mesures sourcées et rapports de
vérification conservés sont intégrés. La garde de non-progrès attend le marcheur complet ; elle
comparera les faits, pas seulement une tâche répétée. Les notes réécrites, résumés de thinking et
replis reasoning→content sont écartés. `passed_before_regrade` inspire un historique de rapports,
pas une copie de regrade.py : ce dernier ne garantit pas des sidecars append-only.
Les sections suivantes conservent les propositions et conclusions antérieures à cette décision.

**Statut** : dépôt inspecté, **aucune extraction cataloguée dans `IMPORT_REPORT.md`**. Ce fichier est une
évaluation d'intérêt, pas un pointeur de sortie comme [`ouroboros.md`](ouroboros.md) ou
[`swe-agent.md`](swe-agent.md). Les verdicts ci-dessous sont **proposés**, pas actés.

**Niveau de preuve** : 2 — lecture intégrale des 2 165 L de `codebase/v2-current/`, du `NOTICE.md`, du
`README.md` et des sections Méthode / Résultats / Discussion / Limites / Annexes du papier. **Rien n'a été
exécuté.** Les chiffres cités sont ceux que le papier déclare, pas des mesures faites ici.

---

## 1. Ce que c'est

*Zero-Shot Self-Orchestration with Ledger-Based Control Improves Coding in Language Models*
(Gao, Khosrowshahi, Khosrowshahi, Sun, Lee, Lee — 2026, soumission ICLR 2027).

Un **manager et des workers qui sont le même modèle, appelé chaque fois en contexte frais**, coordonnés
uniquement par un répertoire de fichiers sur disque. Rien n'est appris, rien n'est fine-tuné : la
coordination *est* le filesystem.

```text
<ws>/task.md       l'énoncé
<ws>/plan.md       le plan du manager      (borné à 4 000 caractères)
<ws>/tasks.json    la liste de tâches      (bornée à 12 entrées)
<ws>/notes.md      les idées retenues      (borné à 8 000 caractères, RÉÉCRIT à chaque tour)
<ws>/solution.py   la solution courante
<ws>/transcript.jsonl  un enregistrement par appel modèle
```

Les workers ne se parlent jamais. Chacun voit le grand livre plus **la seule tâche** que le manager lui
assigne. Le résultat annoncé : Qwen3.8-27B passe de 69,2 % à 92,4 % de pass@1 sur les 100 problèmes *hard*
les plus récents de LiveCodeBench, en poids ouverts servis localement.

**C'est la thèse de Pithos, mesurée par quelqu'un d'autre, sur un autre benchmark, avec un protocole
statistique sérieux.** C'est la raison principale de l'intérêt de ce dépôt.

## 2. Volumétrie et licence

| | Mesure |
|---|---:|
| Taille totale | **285 Mo** |
| Fichiers | **28 997** |
| Code du scaffold `v2-current` | **2 165 L** Python (7 fichiers) |
| Code du scaffold `v1-be9dfa2` | **1 159 L** Python (3 fichiers) |
| `runs/` — données de campagne | **279 Mo**, 301 fichiers de résultats, **4 446 grands livres** portant un `notes.md` |
| Fork LiveCodeBench | `codebase/livecodebench/`, non retenu |

**Licence, par chemin** — le `NOTICE.md` est explicite et fiable :

| Chemin | Licence | Ce que ça autorise |
|---|---|---|
| `codebase/v2-current/`, `codebase/v1-be9dfa2/`, `paper_plot_script/` | **MIT** (`LICENSE`) | portage littéral licite, notice conservée |
| `paper/`, `assets/`, `runs/` | **CC BY 4.0** | réutilisation avec citation du papier |
| `codebase/livecodebench/` | MIT + Apache-2.0 tiers | non retenu, aucune reprise proposée |
| énoncés `runs/**/ws/**/task.md` | **AtCoder / LeetCode / Codeforces** — pas CC BY | à ne jamais redistribuer |

`Copyright (c) 2026 Persis Capital Inc.` Le code utile tient en **2 165 lignes MIT** : le dépôt est petit
là où il compte et lourd là où on n'a rien à prendre.

## 3. Reprises proposées

### 3.1 `engine` — le grand livre borné

| Source | Verdict | Notion |
|---|---|---|
| `multiagent.py:412-476` | **Adapter** | la boucle manager→worker : plan, idéation, gestion, tâche unique, vérification, finalisation |
| `multiagent.py:430-435` | **Copier** | **garde de non-progrès** : si le manager réémet mot pour mot la tâche qu'il vient de donner, la boucle s'arrête |
| `multiagent.py:261` | **Copier** | **invariant d'état** : `done` avec aucun artefact produit est réécrit en `continue` |
| `multiagent.py:187`, `:350` | **Adapter** | plan et notes **bornés à l'écriture**, pas au prompt — le contexte ne peut pas croître sans bornes |
| `multiagent.py:290-310` | **Adapter** | les notes sont **réécrites en entier** par chaque worker, pas appendées : « ce que vous omettez est perdu » |
| `multiagent.py:274-288` | **Adapter** | **résumé de coupure** : un worker coupé au plafond de tokens a sa réflexion partielle résumée par un appel court et frais, pour que ses idées atteignent quand même le manager |

Les trois premières lignes sont les plus directement portables : ce sont des gardes de ~3 lignes chacune,
formulées comme des invariants du harness, pas comme des consignes au modèle. Elles vont dans `walk`.

⚠️ **Ce sont des prochaines actions, pas des modifications.** Vérifié : `src/engine/walk.py` ne porte à ce
jour que l'admission (`is_verifiable`) et la scission (`split_node`, `decompose`). **La boucle d'exécution
n'est pas écrite** — le module est à 507 L pour une cible de 1 050. Ces gardes n'ont donc rien à corriger :
elles sont à écrire en même temps que la boucle, par l'agent `engine`, avec leur test d'abord.

**Le contraste qui compte pour `engine`.** Leur `MAX_ITERS = 10` est un budget de tours ; notre contrainte
dure n°4 est un **temps mural**. Leur boucle finalise par un appel modèle supplémentaire ; la nôtre doit
finaliser ce qui est vert et rester reprenable. La forme est la même, l'unité de budget diffère — c'est une
**Adaptation**, pas une copie.

### 3.2 `bridge` — la ladder de reprise, et ce qu'elle mesure

`orchestrator.py:87-227` est la fonction la plus dense du dépôt : 140 lignes qui traitent, une par une, les
façons dont un appel modèle échoue **sans échouer proprement**.

⚠️ **Relu contre `src/bridge/client.py` : le vocabulaire de l'échec y est déjà, et sous une forme
meilleure.** La première rédaction proposait quatre `Copier` ici ; trois tombent. Le résultat négatif est
conservé (§ 9 du protocole).

`Outcome` (`client.py:29-34`) est un **StrEnum fermé** — `completed`, `truncated`, `unknown_stop`,
`transport_error`, `budget_refused` — là où GVS5H accumule des clés *ad hoc* dans un dict `meta`. La
correspondance est directe :

| Notion GVS5H | État dans `bridge` |
|---|---|
| `infra_exhausted` — l'infra n'a jamais répondu | **`Outcome.transport_error`**, `client.py:161-165` — typé, pas un drapeau |
| `finish_reason == "length"` distingué d'une réponse propre | **`Outcome.truncated`**, `client.py:172` — et `exploitable` est vidé : *« une génération tronquée n'est pas une génération terminée »* |
| `meta["discarded"]` — chaque tentative consignée avec sa raison | `_record()` consigne **toute** issue, y compris `budget_refused` avant l'appel, avec `raw_stop_reason`, `usage` et `body_excerpt` |
| Le `finish_reason` brut conservé à côté de l'issue interprétée | `raw_stop_reason` conservé **en plus** de `outcome`, `client.py:170-176` |

**Et une divergence délibérée qu'il ne faut surtout pas « corriger ».** GVS5H fait
`if not content: content = reasoning` (`orchestrator.py:205`) — c'est précisément ce qui explique leur
finding § 4.3, que la plupart des générations coupées « contiennent quand même du code » : l'extracteur
récupère le raisonnement faute de réponse. `bridge` refuse cela explicitement (`_split_thinking`,
`client.py:109` : *« rien n'est jamais extrait du raisonnement »*). **Leur repli est une source de
faux-verts ; notre refus est la bonne position.** Le noter pour qu'aucun agent ne « porte » ce repli.

Restent quatre candidates, et **aucune n'est applicable en l'état** :

| Source | Verdict | Pourquoi |
|---|---|---|
| `orchestrator.py:208-221` — écrêtage détecté (`length` à < 90 % du plafond = le provider a menti) | **Écarté** | Suppose un gateway multi-provider. `bridge` parle à **une** route loopback, modèle épinglé. Le § 6 interdit la gestion d'erreur pour un scénario impossible |
| `orchestrator.py:150-176` — 400 « contexte dépassé » retenté à plafond réduit, `retry-after` sur 429 | **Écarté** | Pas de quota ni de gateway en local. `call()` documente *« aucun retry implicite : l'issue typée suffit »* — et c'est un choix, pas un oubli |
| `orchestrator.py:324` — `reasoning_is_summary` | **Reporté** | La notion est juste (§ 4.1) mais son déclencheur — deux producteurs pour un même champ — n'existe pas : un seul modèle local. À ressortir si `bridge` gagne une seconde route |
| `orchestrator.py:57-85` — client Ollama `urllib` pur, 29 lignes | **Inspirer** | Sans objet : `bridge` est déjà à 179 L avec `httpx`, et `httpx` est déclaré dans sa *Stack* |

**Aucune modification de `src/bridge/` n'est justifiée par ce dépôt.**

### 3.3 `verifier` — ce qu'ils ont, et ce qu'ils n'ont pas

`multiagent.py:368-410` exécute les tests publics de l'énoncé en **sous-processus réel** et renvoie au
manager un verdict traité comme vérité de terrain : un échec **écrase** un `done` (`:447-451`).

C'est exactement l'inversion que fonde notre première règle d'import — la couche qui décide de la vérité est
en dessous de celle qui parle au modèle. **Verdict : Inspirer.** Leur vérificateur consomme des tests
*fournis par le benchmark* ; le nôtre génère ses entrées à partir d'une relation nommée dans un catalogue
fermé. Il n'y a rien à copier, mais la démonstration que le harness doit pouvoir contredire le modèle est
faite, chiffrée, et elle a coûté des points à leur propre arme.

**Et le trou reste le nôtre** : aucun invariant métamorphique, aucun mutation-check, aucun catalogue fermé
de relations. Le dixième dépôt inspecté confirme ce que les neuf premiers disaient déjà — `relations`,
`domains` et `mutation` sont un apport propre au projet.

### 3.4 `journal` et `observatory` — l'appareil de preuve

Le format de trace mérite une lecture attentive. `multiagent.py:62-84` écrit une ligne JSONL par appel
modèle, portant : rôle, requête complète, réponse, raisonnement, `finish_reason`, tokens d'entrée et de
sortie, provider servi, nombre de tentatives, tentatives rejetées, `infra_exhausted`.

Les fichiers de résultats (`runs/**/results/*.json`) portent par problème : `status`, `finish_reason`,
`completion_tokens`, **`truncated_calls`**, `n_calls`, le chemin du grand livre, `passed`, et
`passed_before_regrade`.

| Notion | Verdict | Pour qui |
|---|---|---|
| Un enregistrement par appel, append-only, requête **et** réponse conservées | **Inspirer** | `journal` — c'est déjà notre format |
| `passed_before_regrade` conservé à côté de `passed` | **Copier** | `journal` — **un re-scoring n'écrase jamais le verdict précédent, il s'ajoute** |
| `truncated_calls` / `n_calls` comme agrégats de premier ordre | **Adapter** | `observatory` — le taux de coupure est un indicateur, pas une anecdote |
| `_classify_status` (`run_bench.py:48`) séparant parseable / statut | **Inspirer** | `observatory` |

`passed_before_regrade` est la reprise la plus économique du dépôt : **un champ**, et la trace devient
auditable après changement d'évaluateur. Notre journal est append-only par contrainte dure n°6 ; ce champ
en est l'application au cas particulier de la revalidation.

### 3.5 `campaign` — le corpus de trajectoires

`runs/` contient **4 446 grands livres réels** (`plan.md`, `notes.md`, `tasks.json`, `solution.py`) produits
par neuf configurations de modèles sur cent problèmes, en cinq passes, sous CC BY 4.0.

**Verdict : Inspirer, et uniquement en lecture.** C'est un corpus d'étude pour la question que pose Pithos —
à quoi ressemble une trajectoire quand un petit modèle travaille par nano-étapes — et le seul du genre qu'on
ait sous la main. Les `notes.md` de `q38_multiagent_p1` montrent ce qu'un 27B écrit quand on lui demande de
curer ses propres notes : des bullets `- **Sujet :** …`, un modèle de coût, des pièges listés, un plan de
harnais de test. C'est lisible et c'est dense.

⚠️ **Les énoncés `task.md` ne sont pas sous CC BY** — ils appartiennent à AtCoder, LeetCode et Codeforces.
Lire, ne pas redistribuer, ne pas copier dans `docs/`.

## 4. Les trois découvertes qui valent le détour

### 4.1 Le champ qui empêche un faux-vert d'analyse

`orchestrator.py:324` pose `meta["reasoning_is_summary"] = True` sur la route Anthropic, avec ce commentaire
en clair dans `multiagent.py:73-75` :

> Anthropic renvoie un **résumé** de la réflexion ; vLLM et DashScope renvoient la vraie chaîne de pensée
> dans le même champ. Sans ce drapeau les deux sont indiscernables sur disque, et toute analyse ultérieure
> de la longueur ou du contenu de la réflexion comparerait silencieusement un résumé à une transcription.

C'est **la décision 13 appliquée à un champ de sérialisation**. Deux valeurs de nature différente arrivent
sous le même nom ; sans discriminant, l'agrégat est faux et rien ne le signale. Notre journal a exactement
cette exposition partout où un champ peut venir de deux producteurs.

**Verdict : Copier la notion**, comme règle de format dans `journal` : *un champ dont la sémantique dépend du
producteur porte son producteur.*

### 4.2 Le vérificateur qui certifie une mauvaise réponse

Annexe *A correction to the LiveCodeBench evaluator*. L'évaluateur de LiveCodeBench n'exécute pas le
candidat en sous-processus : il le lance en mémoire avec un `sys.stdin` simulé, dont la vue binaire
implémentait `readline()` par `inputs.split(b"\n")[0]` — **une expression sans état, qui renvoie la première
ligne à chaque appel.**

Conséquence en chaîne, et c'est là que ça devient intéressant pour nous :

1. Un programme correct lisant par `sys.stdin.buffer.readline()` échouait, quelle que soit sa justesse.
2. Le vérificateur du scaffold v2, lui, lance un **vrai sous-processus** — où `readline()` fonctionne.
3. **Le manager était donc informé que sa solution passait les tests publics, pour des programmes que le
   correcteur déclarait ensuite faux.** Le seul signal externe de la boucle certifiait une mauvaise réponse.
4. L'exposition n'est pas un décalage constant : 311 des 3 456 sorties utilisent l'idiome, **97 % d'entre
   elles notées fausses contre 20 % pour les autres**. Le bug pénalise les modèles dont le style le
   déclenche, et laisse les autres intacts.

C'est le **faux-vert par divergence de véhicule d'exécution** : deux exécutions du même code, l'une en
processus avec un double, l'autre en sous-processus réel, donnant des verdicts opposés.

**Ce que ça vaut pour nous.** Notre `verifier` exécute par `subprocess` et n'a d'I/O que sur ce qu'il a
produit — la forme exacte du bug ne peut pas nous arriver. Mais la leçon générale nous concerne
directement : **un double d'entrée/sortie qui n'est pas un vrai flux est un capteur de faux-vert en
puissance**, et l'écart ne se voit que si quelqu'un compare les deux véhicules. À verser en note dans le
corpus de frontière, et à retenir pour les doubles de `tests/doubles/`.

### 4.3 Un budget trop grand dégrade le modèle

Section Discussion, et c'est le résultat le plus utile pour un harness qui tourne sur 16 Go :

> Huit des quatorze appels Qwen3.8-27B qui ont dépensé un budget complet de 250 k tokens sans produire de
> code **s'effondrent en répétition** — sur `abc399_e`, **7 743 copies d'une même ligne** — la plupart
> inventant des cas limites contre une solution candidate et y répondant tour à tour, des centaines à des
> milliers de fois, sans jamais terminer.

Et son corollaire, contre-intuitif : la plupart des générations coupées **contiennent quand même une
solution complète**, écrite dans le flux de raisonnement avant l'arrivée du plafond. Le modèle avait
répondu, puis avait parlé au-delà du plafond en revérifiant sa réponse.

> Borner chaque appel garde le travail loin du plafond et le met sur disque.

**C'est l'argument quantifié de la nano-étape.** Il ne dit pas que découper est plus élégant : il dit qu'un
appel non borné sur un modèle de cette taille **se dégrade**, et que le grand livre externe est la mémoire
que le plafond de tokens ne peut pas tronquer. À verser dans `docs/EXPLANATIONS.md` comme mesure externe à
l'appui de la contrainte dure n°2.

## 5. Les deux améliorations qu'ils annoncent sans les implémenter

La Discussion nomme deux ajouts « peu coûteux et sans entraînement », en réponse à leur propre cas d'échec
(LCB 3765 : l'idéation identifie la bonne optimisation, se convainc qu'elle est trop risquée, et commet un
plan plus lent qu'un worker implémente ensuite avec un bug) :

1. **Workers à perspective fraîche.** Chaque worker hérite des notes et de la solution courante, donc une
   mauvaise approche initiale ancre tout l'aval. Lancer certains workers sur l'énoncé brut, sans contexte
   antérieur, donnerait au manager une tentative indépendante à comparer.
2. **Vérifier plutôt que faire confiance.** Le manager accepte le rapport d'un worker sur la base d'un
   contrôle contre les exemples de l'énoncé ; une solution confiante et fausse se propage sans contrôle et
   peut écraser une réponse intermédiaire correcte.

Le point 2 **est déjà notre architecture** : c'est la première règle d'import et la contrainte dure n°3
(une nano-étape non verte restaure son fichier cible à l'octet près). Ils décrivent en prospective ce que
`verifier` et `workspace` font par construction.

Le point 1, en revanche, est **une idée que nous n'avons pas**, et elle est bon marché : notre contexte de
nœud est construit par `engine` et hérité en descendant l'arbre. Un nœud dont le contexte est délibérément
amputé de l'historique de ses frères est une variante à un paramètre près.

⚠️ **Ne pas l'implémenter au socle.** C'est une **Reprise reportée** au sens du § 8 : l'idée est juste, son
déclencheur — une mesure de redondance sur l'arbre qui montre l'ancrage — n'existe pas encore. Elle
appartient à `refinery`, qui est `enabled: false`.

## 6. Ce qui est à écarter

| Quoi | Pourquoi |
|---|---|
| `orchestrator.py:336-468` — le routeur multi-provider (Groq, OpenRouter, OpenAI, DashScope, Anthropic, CLI Claude) | **Contrainte dure n°5.** Aucune donnée ne quitte la machine. Seule la branche Ollama nous concerne |
| `orchestrator.py:474-531` — `solve_layer` / `escalate`, la ladder solveur↔critique multi-modèles | Un critique modèle qui approuve ou rejette, c'est précisément **la vérité rendue au modèle**. Inversion de notre première règle d'import |
| `_format_rule` (`multiagent.py:27-33`) — « LE FORMAT EST OBLIGATOIRE, votre réponse est parsée par un programme » | **Contrainte dure n°1.** Ils parsent du markdown en sections par regex parce qu'ils n'ont pas de décodage contraint. Nous avons un schéma côté serveur ; une consigne de format en langue naturelle est le mode d'échec que `bridge` existe pour supprimer |
| `_extract_py` / `_sections` / `_bullets` (`multiagent.py:94-138`) | Même raison. Ce sont des parseurs de sortie libre : de la dette, pas une reprise |
| `codebase/livecodebench/` | Dépendance tierce lourde, licence composite, aucun usage |
| `patched_grader/checkers.py` | Juges spéciaux pour quatre problèmes de concours nommés. Très spécifique ; la *notion* (un correcteur par égalité de chaîne est faux dès qu'une tâche accepte plusieurs sorties correctes) est déjà couverte par nos invariants métamorphiques |

## 7. Verdict

**Le dépôt vaut d'être catalogué, pour une quinzaine de reprises concentrées sur ~200 lignes utiles.**

*Chiffre revu à la baisse après relecture contre `src/` : le vocabulaire d'échec de `bridge` existait déjà,
et mieux (§ 3.2).*

Ce n'est pas un dépôt dont on porte du code : c'est un dépôt dont on porte **des gardes**. Les `Copier`
survivants tiennent en quelques lignes chacun — **garde de non-progrès**, **invariant `done` sans
artefact**, **`passed_before_regrade`** — et **aucun ne corrige du code existant** : les deux premiers
s'écriront avec la boucle de `walk`, qui n'est pas encore là (§ 3.1). Ce sont des lignes que la cible de
`engine` absorbe sans justification de plafond.

Sa valeur principale est ailleurs, et elle est double :

- **Une validation externe, chiffrée et soumise à relecture, de la thèse de Pithos** — le grand livre sur
  disque plus l'appel borné battent l'appel unique, sur un modèle local de 27B, avec un effet mesuré et un
  test de permutation. Le projet dispose pour la première fois d'une mesure qu'il n'a pas produite lui-même.
- **Trois modes d'échec documentés que nous n'avions pas nommés** : le champ sérialisé dont la sémantique
  dépend du producteur, le vérificateur qui certifie une mauvaise réponse par divergence de véhicule
  d'exécution, et l'effondrement en répétition d'un appel non borné.

**Les limites, telles qu'eux-mêmes les déclarent.** Une seule famille de benchmark ; Fable 5 sans bras
manager ; le bras 128k de Qwen3.8-27B est un rejeu tronqué, pas une exécution indépendante ; les gains ne
sont pas universels — Qwen3.6-35B sans raisonnement est négatif aux deux plafonds. Le papier dit tout cela
lui-même, en section Limites, sans qu'on ait eu à le lui arracher. **Sur le critère du § Fiabilité des
extractions de [`MANIFEST.md`](MANIFEST.md) — une source auditable est celle qui quantifie ce qu'elle n'a
pas couvert — ce dépôt se range avec Langfuse, pas avec SWE-agent.**

**Une réserve de reproductibilité, constatée ici.** Le scaffold écrit un `transcript.jsonl` par problème
(`multiagent.py:62`), et l'analyse de transcripts de la Discussion s'appuie dessus. **Aucun `transcript.jsonl`
n'est présent dans `runs/`** — vérifié, zéro fichier sur les 28 997. Ce qui est publié, ce sont les grands
livres finaux et les agrégats par problème (`finish_reason`, `truncated_calls`, `n_calls`). Les affirmations
de la Discussion sur le contenu des transcripts ne sont donc **pas revérifiables depuis l'archive**. Ce
n'est pas une faute — les transcripts porteraient les énoncés sous licence tierce — mais c'est une limite
qui n'est pas déclarée dans la section Limites, et il faut la connaître avant de citer ces passages.

## 8. Prochaine action proposée

Si le dépôt est retenu, il devient la **Partie J** de [`IMPORT_REPORT.md`](IMPORT_REPORT.md), et ce fichier
est réécrit en pointeur de sortie sur le modèle de [`ouroboros.md`](ouroboros.md).
[`MANIFEST.md`](MANIFEST.md) devra alors passer de neuf à dix dépôts, avec sa ligne de licence par chemin —
il n'a pas été modifié ici.

---

## 9. Relecture contre le code livré

Les § 3.1 et § 3.2 ont été corrigés **après** coup, en relisant `src/` au lieu de raisonner sur le seul
`AGENTS.md`. Bilan de cette relecture :

| Zone | Première rédaction | Après vérification |
|---|---|---|
| `bridge` — vocabulaire d'échec | 4 × `Copier` | **0** — `Outcome` est un enum fermé qui couvre tout, § 3.2 |
| `bridge` — ladder de reprise | 2 × `Adapter` | **0** — scénarios impossibles sur une route loopback épinglée |
| `engine` — gardes de boucle | « à porter » | **prochaines actions** — `walk()` n'a pas encore de boucle, § 3.1 |
| `journal` — `passed_before_regrade` | `Copier` | **inchangé** — toujours valide, une ligne |
| `verifier` · `campaign` · `observatory` | `Inspirer` | **inchangé** |

**Aucune modification de `src/` n'est justifiée par ce dépôt.** Ce qui reste est soit à écrire plus tard
avec le code qui l'accueillera, soit une notion à verser dans `docs/EXPLANATIONS.md` (§ 4), soit un corpus
à lire (§ 3.5).

⚠️ **Une divergence à protéger, plutôt qu'une reprise à faire** : leur repli
`if not content: content = reasoning` (`orchestrator.py:205`) est exactement ce que `bridge` refuse. Un
agent qui porterait cette ligne « pour récupérer les générations coupées » introduirait le faux-vert que
leur propre § 4.3 décrit. C'est la reprise la plus tentante du dépôt, et elle est **à écarter**.
