# Graphify — évaluation

**Décision courante — 13:09 : intégration sélective autorisée et réalisée**, cataloguée dans
[IMPORT_REPORT.md](IMPORT_REPORT.md) § K. Notice d'omission budgétée et contrôle documentaire
livré/prévu ont été adaptés et testés. Les sections ci-dessous conservent l'évaluation préalable ;
les propositions « Copier » et « décision à demander » y sont historiques. Aucune dépendance
Graphify ni copie littérale. Le contrôle retenu couvre 20 interfaces livrées des 11 modules,
avec 8 tests ; les symboles prévus restent explicitement hors validation de livraison.

**Statut** : dépôt inspecté, **aucune extraction cataloguée dans `IMPORT_REPORT.md`**. Ce fichier est une
évaluation d'intérêt, pas un pointeur de sortie comme [`ouroboros.md`](ouroboros.md) ou
[`swe-agent.md`](swe-agent.md). Les verdicts ci-dessous sont **proposés**, pas actés.

**Niveau de preuve** : 2 — lecture de `ARCHITECTURE.md`, `NOTICE`, `pyproject.toml`, `CHANGELOG.md`, et des
corps ou des squelettes de 14 modules (`validate`, `security`, `paths`, `serve`, `benchmark`, `affected`,
`cache`, `symbol_resolution`, `dedup`, `reflect`, `diagnostics`, `hooks`, `prs`, `tests/test_architecture_doc`).
**Rien n'a été exécuté**, et les 28 grammaires tree-sitter n'ont pas été installées.

---

## 1. Ce que c'est

`graphify` (PyPI `graphifyy`, v0.9.55) extrait un **graphe de connaissance** d'un dépôt ou d'un corpus :
tree-sitter parse ~28 langages, un second passage résout les appels entre fichiers, NetworkX porte le
graphe, et le tout se sert ensuite par un **serveur MCP** qui répond à des questions en langue naturelle par
un **sous-graphe rendu en texte sous budget de tokens**.

```text
detect() → extract() → build() → cluster() → analyses → report.generate() → export.to_*()
```

Ce n'est pas un harness d'agent. C'est **un outil de construction de contexte**, et c'est par là qu'il
touche Pithos : là où `engine` doit décider ce qu'un nœud voit, `graphify` a une réponse travaillée et
testée.

## 2. Volumétrie et licence

| | Mesure |
|---|---:|
| Taille | **18 Mo** |
| Fichiers | **873** |
| Code Python de production | **~69 975 L** |
| Code de test | **~86 827 L**, sur **259 fichiers** de test |
| Plus gros fichier | `graphify/extract.py` — **7 645 L** |
| Version | 0.9.55, `requires-python >= 3.10` |

**Licence — mixte, et il faut la lire :**

| Fichier | Portée |
|---|---|
| `LICENSE` | **Apache 2.0** — la licence courante du dépôt |
| `LICENSE-MIT` | **MIT** — les contributions antérieures à la relicence, toujours disponibles sous ces termes |
| `NOTICE` | `Copyright 2026 Safi Shamsi and the Graphify contributors` |

`Copyright (c) 2026 Safi Shamsi`. **Apache 2.0 autorise le portage littéral**, à condition de conserver la
notice *et* de signaler les modifications dans le fichier dérivé. C'est une obligation de plus que le MIT
des dépôts B, C, D, E et H ; elle est tenable, mais elle doit être écrite dans l'en-tête de tout fichier
porté. Aucune clause AGPL, aucune zone `ee/` : rien qui ressemble aux cas F et I de
[`MANIFEST.md`](MANIFEST.md).

**Dépendances** : `networkx`, `numpy`, `rapidfuzz`, `mcp`, `starlette`, et **28 paquets tree-sitter**.
Aucune ne peut entrer dans le projet sans passer par la rubrique *Stack* d'un `MODULE.md` puis
`requirements.txt` (§ 5). En pratique, **aucune n'y entrera** : `kernel` est en `ast` stdlib, `journal` est
en stdlib pur et c'est une propriété à préserver, `workspace` est en stdlib pur. Le dépôt est donc
massivement **Inspirer** et **Adapter**, très peu **Copier**.

## 3. Reprises proposées

### 3.1 `engine` — l'assemblage de contexte sous budget

C'est la reprise la plus substantielle du dépôt, et elle vise le module le plus gros du projet.

| Source | Verdict | Notion |
|---|---|---|
| `serve.py:1028-1185` — `_subgraph_to_text` | **Adapter** | rendre un sous-graphe en texte **sous un budget de tokens explicite**, avec les graines en premier |
| `serve.py:1186-1210` — `_cut_lines_to_budget` | **Copier** | la coupe se fait **à la frontière de ligne**, et annonce ce qu'elle a coupé |
| `serve.py:1190-1205` — commentaire du correctif BUG-2 | **Copier la notion** | **la troncature est annoncée en haut *et* en bas** : « un marqueur seulement en bas se lit comme un silence, comme une absence » |
| `serve.py:702-864` — `_pick_seeds` | **Inspirer** | choisir les points d'entrée du contexte par score, avant de parcourir |
| `serve.py:970-1027` — `_bfs` / `_dfs` à profondeur bornée | **Inspirer** | le contexte est un voisinage à profondeur fixe, pas un dépôt entier |
| `serve.py:920-968` — `_complete_induced_edges` | **Inspirer** | une fois les nœuds choisis, **compléter les arêtes induites** — sinon le sous-graphe ment par omission |

**Le correctif BUG-2 mérite d'être isolé.** Un contexte tronqué qui ne dit pas qu'il est tronqué est
indiscernable, pour le modèle qui le lit, d'un contexte complet où l'information manquante n'existe pas.
C'est un **faux-vert de contexte** : le modèle répond correctement à la question qu'on lui a effectivement
posée, et la réponse est fausse pour la question qu'on croyait poser. `engine` construit le contexte de
chaque nœud sous budget ; il est exposé exactement à ça.

### 3.2 `workspace` et `journal` — l'écriture qui survit à un `SIGKILL`

⚠️ **Vérifié contre le code livré : il n'y a rien à reprendre ici.** Cette section était une erreur de la
première rédaction ; elle est conservée, corrigée, parce que le § 9 du protocole veut qu'un résultat négatif
reste écrit.

`src/workspace/transaction.py:143-162` traite **déjà** tous les cas que leur commentaire de 20 lignes
énumère, et traite deux d'entre eux **plus strictement** :

| Piège | `graphify` `paths.py:29-90` | `workspace/transaction.py` |
|---|---|---|
| Temporaire sur le même système de fichiers | `mkstemp(dir=real.parent)` | `mkstemp(dir=self.path.parent)` — identique |
| Mode du fichier préservé | `os.chmod` après écriture, *best-effort*, échec ignoré | `os.fchmod(stream.fileno(), self.mode)` sur le descripteur, avant fermeture |
| Lien symbolique | **écrit à travers le lien** (`os.path.realpath`) — choix assumé pour leurs montages | **refusé** : `os.open(..., O_NOFOLLOW)` + `S_ISREG`, `:50-53` |
| Durabilité | **aucun `fsync`** — leur docstring le déclare : *« NOT a power-loss durability guarantee »* | `stream.flush()` puis `os.fsync(stream.fileno())` avant le `replace` |
| Écriture concurrente | non traité | **CAS double** — contenu revérifié avant *et* après staging, sous `_WRITE_LOCK`, `:145` et `:157` |

Le verdict correct est donc **Écarté** pour `_atomic_replace` et ses deux enveloppes : la reprise irait
dans le mauvais sens. Leur repli `shutil.copy2` sur `PermissionError` est un contournement Windows, hors
cible. Restent deux notions mineures, sans urgence :

| Source | Verdict | Notion |
|---|---|---|
| `security.py:357-389` — `check_graph_file_size_cap` | **Inspirer** | plafond de taille **avant** lecture — `codeview.MAX_SOURCE_BYTES` le fait déjà à `transaction.py:56-59` |
| `cache.py:428-532` — `file_hash` | **Inspirer** | *un `mtime` n'est pas une preuve de fraîcheur, une empreinte de contenu l'est* — déjà la règle du projet |

`security.py:315-356` (`validate_graph_path`) est couvert par `workspace/paths.py::checked_path` et
`kernel.codeview.is_path_within`. `cache.py` est à 1 746 L et **ne doit pas être porté**.

### 3.3 `kernel` — la validation à cause fermée

`validate.py` fait **95 lignes** et c'est le fichier le mieux calibré du dépôt.

| Source | Verdict | Notion |
|---|---|---|
| `validate.py:4-7` | **Inspirer** | **quatre énumérations fermées** en tête de fichier : types de fichier, confiances, champs requis de nœud, champs requis d'arête |
| `validate.py:10-89` — `validate_extraction` | **Adapter** | renvoie **la liste des erreurs**, jamais une exception ; l'appelant décide quoi en faire |
| `validate.py:90-95` — `assert_valid` | **Copier la forme** | la version qui lève est une enveloppe de cinq lignes autour de celle qui accumule |
| `validate.py:19-24` — le `node_ids` collecté | **Inspirer** | un identifiant non hachable est **signalé comme erreur** plutôt que de faire planter le validateur sur la construction du `set` |

**Le couple accumulateur + enveloppe qui lève est exactement notre `ErrorAccumulator`.** Deux fonctions, pas
un paramètre booléen — la règle de style du projet, appliquée par quelqu'un d'autre. La forme vaut d'être
citée dans `kernel` comme confirmation externe du choix.

Le tableau des **confidences** (`EXTRACTED` / `INFERRED` / `AMBIGUOUS`) est un catalogue fermé documenté avec
sa sémantique dans `ARCHITECTURE.md`. C'est la même forme que notre catalogue de relations : le producteur
**nomme** un membre d'une énumération, il n'invente pas une valeur.

### 3.4 `verifier` — le voisinage affecté par un changement

`affected.py` (318 L) répond à : *qu'est-ce qui est touché si je modifie ce symbole ?*

| Source | Verdict | Notion |
|---|---|---|
| `affected.py:12-35` — `DEFAULT_AFFECTED_RELATIONS` | **Inspirer** | **les relations qui propagent un impact sont énumérées**, pas déduites |
| `affected.py:138-189` — `resolve_seed` | **Inspirer** | une requête humaine est **résolue en un identifiant de nœud existant**, ou échoue ; elle n'est jamais interprétée |
| `affected.py:190-257` — `affected_nodes` | **Inspirer** | propagation bornée sur les seules relations retenues |
| `serve.py:1384-1435` — `find_node_ambiguity` / `_resolve_single_node` | **Adapter** | un libellé qui résout vers plusieurs nœuds est **une ambiguïté rendue à l'appelant**, pas un choix silencieux |

`resolve_seed` et `find_node_ambiguity` sont la **contrainte dure n°1 vue depuis l'autre bout**. Le modèle
n'émet que des noms de symboles existants ; il faut donc une fonction qui, face à un nom, dit *« ce symbole
est celui-ci »*, *« ce nom est ambigu »*, ou *« ce nom n'existe pas »*.

⚠️ **Vérifié : le projet a déjà cette fonction.** `src/workspace/splice.py:77-78` refuse dès que
`len(definitions) != 1` avec `Cause.invalid_symbol` — un nom absent donne zéro définition, un nom ambigu en
donne deux, et les deux cas sont refusés par la même garde typée. `kernel.codeview.module_defs` et
`symbols()` fournissent l'inventaire en amont.

La différence de forme mérite d'être notée, sans conclure : `graphify` **rend l'ambiguïté à l'appelant avec
ses candidats**, là où `workspace` la **refuse**. Pour un splice, refuser est le bon choix — la contrainte
dure n°3 veut qu'une étape non verte ne touche rien. Le verdict passe donc de *« découpe à reprendre »* à
**confirmation externe d'un choix déjà fait**.

### 3.5 `campaign` — la forme d'un serveur MCP servi depuis un magasin

`serve.py:1579-1780` déclare une douzaine d'outils MCP au-dessus d'un seul artefact de données, avec deux
transports (stdio et HTTP), un cache de contextes borné (`_max_server_contexts`, `:95-173`) et une
compatibilité entre l'API décorateur de `mcp` 1.x et l'API par callbacks de 2.x.

**Verdict : Inspirer.** `campaign` construit une boîte à outils MCP générique et la famille `skill` de son
magasin *est* le registre d'outils. Ce que ce fichier montre, et qu'on ne trouve pas dans les neuf autres
dépôts, c'est **ce que devient un serveur MCP quand il grossit** : 2 465 L pour une douzaine d'outils, dont
l'essentiel n'est pas le protocole mais le **scoring de requête** (`_compute_idf`, `_trigram_candidates`,
`_score_query`). Le protocole est trivial ; la sélection de ce qu'on renvoie ne l'est pas.

`tools/skillgen/` génère la même compétence déclinée pour une quinzaine de plateformes d'agent, avec un
répertoire `expected/` d'attendus figés. C'est du test par instantané sur du contenu généré — **Écarté**,
sans rapport avec notre magasin.

### 3.6 `observatory` — mesurer ce que le contexte coûte

`benchmark.py` fait **152 L** et répond à une seule question : combien de tokens le sous-graphe économise-t-il
par rapport au corpus entier ?

| Source | Verdict | Notion |
|---|---|---|
| `benchmark.py:37-75` — `_query_subgraph_tokens` | **Adapter** | mesurer le contexte **réellement envoyé** pour une question donnée, pas la taille du dépôt |
| `benchmark.py:76-84` — `_SAMPLE_QUESTIONS` | **Inspirer** | un jeu de questions fixe, pour que deux mesures soient comparables |
| `benchmark.py:11` — `_CHARS_PER_TOKEN = 4` | **Adapter** | approximation **déclarée en constante nommée**, pas cachée dans une expression |
| `diagnostics.py:156-279` — `diagnose_extraction` | **Inspirer** | un rapport **en lecture seule** qui quantifie un risque de perte (ici, l'effondrement d'arêtes de mêmes extrémités) sans rien modifier |

`diagnostics.py` est le module du dépôt qui ressemble le plus à `observatory` : lecture seule assumée dès sa
docstring, aucune mutation, une sortie en deux formes — JSON et rapport texte — depuis une seule structure
(`format_diagnostic_json` / `format_diagnostic_report`, `:330` et `:348`). C'est notre séparation agrégat /
rendu.

### 3.7 `refinery` — à ne pas implémenter

`reflect.py` (882 L) agrège une « mémoire de travail » : des documents de mémoire écrits au fil des sessions
sont pondérés par une **décroissance exponentielle** (`_decay`, `:275`, demi-vie de 30 jours) et ne
deviennent une préférence qu'après **corroboration par au moins deux résultats utiles distincts**
(`_DEFAULT_MIN_CORROBORATION`, `:52`). L'agrégat est ensuite figé dans un fichier latéral
(`build_learning_overlay`, `:758`) dont chaque entrée porte une **empreinte du code cité**, et qui
s'invalide quand ce code change (`_is_stale`, `:868`).

C'est une politique d'auto-amélioration complète, avec sa garde de péremption. **Verdict : Reporté**, au sens
du § 8 du protocole. `refinery` est `enabled: false` et sa cible est de ~100 L. Le déclencheur d'une reprise
de cette forme — une campagne assez longue pour que la décroissance temporelle ait un sens — n'existe pas.
**N'implémente pas au socle.**

La notion qui survit isolément, et qui est bon marché : **une leçon apprise porte l'empreinte du code qui
l'a produite, et meurt quand ce code change.** Une leçon sans date de péremption est une source de
faux-verts à retardement.

### 3.8 Passe transverse — le test qui empêche la documentation de mentir

`tests/test_architecture_doc.py` fait **87 lignes**. Il lit le tableau des modules de `ARCHITECTURE.md`,
en extrait chaque couple `(module, symbole)`, et **importe chacun**. Trois tests supplémentaires vérifient
que le document dit toujours ce qu'il doit dire sur la signature de `extract()`.

`ARCHITECTURE.md` l'annonce en une phrase à ses lecteurs :

> Les signatures ci-dessous sont les vraies — `tests/test_architecture_doc.py` importe chaque symbole nommé
> ici, donc ce tableau ne peut pas dériver du code.

**Verdict : Adapter, pour `tests/`, sous le § 14.** C'est le problème que `tests.state_check` traite déjà par
un bout — lignes, empreinte, date, statut — attaqué par l'autre : **les symboles que la documentation
promet existent-ils ?** Onze `MODULE.md` déclarent chacun une rubrique *Interface publique* avec des
signatures. Rien ne garantit aujourd'hui qu'elles correspondent au code. Un test de cette forme, ~90 L
mutualisées dans `tests/`, rendrait cette dérive rouge au lieu de la laisser silencieuse.

C'est, de loin, **la reprise la plus immédiatement actionnable du dépôt**, et la seule qui ne dépende
d'aucune de ses 31 dépendances.

## 4. Ce qui est à écarter

| Quoi | Pourquoi |
|---|---|
| `extract.py` (7 645 L), `extractors/` (19 388 L), les 28 grammaires tree-sitter | `kernel.codeview` lit du Python avec `ast` stdlib, et le projet ne cible qu'un langage. Le rapport coût / bénéfice n'est pas discutable |
| `cache.py` (1 746 L) | Un moteur de cache portable multi-machines. `journal` est en stdlib pur et append-only ; ce problème n'est pas le nôtre |
| `dedup.py` (1 039 L) — MinHash, LSH, rapidfuzz, union-find, seuils de fusion à 92,0 | Notre redondance se détecte par `difflib.SequenceMatcher` sur des propositions, pas par similarité floue de libellés sur un graphe. **Et la décision 22 est explicite** : une identité est une clé typée, jamais une chaîne de repli |
| `security.py:20-314` — garde SSRF, blocage des réseaux de métadonnées cloud, interdiction des redirections `file://` | Sérieux, et hors périmètre : le projet ne récupère rien par HTTP hors `broker`, qui parle à `gh` en sous-processus et à Telegram |
| `hooks.py` (844 L) — hooks Git `post-commit` / `post-checkout` qui relancent une reconstruction en tâche de fond détachée | **§ 7.** Un agent ne commite pas, et le projet n'installe pas de hook qui écrit |
| `prs.py` (770 L) — tableau de bord de PR en couleurs par `gh` | Aucun usage. `broker` a son propre contrat |
| `install.py` (2 355 L), `always_on/`, `skills/` — installation de la compétence pour ~15 plateformes d'agent | Hors périmètre |
| `serve_http` + `_ApiKeyMiddleware` (`serve.py:2198-2394`) | **Contrainte dure n°5.** `observatory` est déjà un processus séparé en lecture seule et ne sert rien au-delà de la machine |

## 5. Une réserve de méthode

`graphify` est un dépôt de **~70 000 lignes de production pour ~87 000 lignes de test**, dont un seul fichier
de 7 645 L, et un `CHANGELOG` de la version en cours qui aligne une douzaine de corrections d'extraction
attribuées à des contributeurs différents. C'est un produit vivant, soigné, et **bâti sur des principes
opposés aux nôtres sur un point précis** : la couverture de cas l'emporte sur la compacité.

Le projet, lui, tient onze modules sous un ratchet shrink-only et refuse toute croissance non justifiée par
écrit. **On ne lit donc pas ce dépôt pour son architecture, on le lit pour ses corrections de bugs.** La
plus grande valeur de `graphify` est dans ses commentaires : le correctif BUG-2 sur la troncature
silencieuse, l'énumération des pièges de l'écriture atomique, la granularité de `mtime`, l'ambiguïté rendue
plutôt que tranchée. Ce sont des cas que quelqu'un a rencontrés en production et documentés sur place.

**Corollaire à tenir.** Toute reprise depuis ce dépôt doit être **relue et réécrite**, jamais collée. Un
fichier de 7 645 L ne contient pas de fonction qu'on extrait telle quelle ; le § 8 appelle ça `Adapter`, et
c'est le verdict par défaut ici.

## 6. Verdict

**Le dépôt vaut d'être catalogué, mais pour beaucoup moins que ce que la première rédaction annonçait :
une dizaine de reprises réelles, et non trente à quarante.**

La relecture contre le code livré (§ 8) a retiré la moitié des candidates : elles décrivaient des problèmes
déjà résolus dans `src/`. Ce qui reste :

1. **L'assemblage de contexte sous budget** (`serve.py:1028-1210`) — et **une seule ligne y est un vrai
   manque du code actuel**, le correctif de troncature annoncée. Voir § 8.
2. **Le test de non-dérive de la documentation** (`tests/test_architecture_doc.py`) — 87 lignes, aucune
   dépendance, et il attaque un risque réel du protocole : onze `MODULE.md` déclarent une *Interface
   publique* que rien ne confronte au code. **Avec une réserve de forme, § 8.**
3. **Le couple validateur accumulateur / enveloppe qui lève** (`validate.py:10-95`) — confirmation externe
   de la forme de `kernel.errors`, sans code à porter.

Ce qui **ne** vaut pas : l'extraction multi-langage, le cache, la déduplication floue, la sécurité réseau,
l'installation, les hooks Git, **et l'écriture atomique** (§ 3.2). Soit plus de **90 % du volume du dépôt**,
et il faut le dire ainsi pour que l'évaluation soit honnête.

**Comparé à GVS5H** — l'autre dépôt évalué dans le même geste — les deux sont complémentaires et ne se
recouvrent nulle part. GVS5H valide **la thèse** de Pithos et apporte un vocabulaire d'échec d'appel
modèle ; `graphify` apporte **des solutions d'ingénierie** à des problèmes que `engine`, `kernel` et
`workspace` vont rencontrer. GVS5H se lit en une soirée ; `graphify` se lit fichier par fichier, en ne
gardant que ce qui est nommé ci-dessus.

## 7. Prochaine action proposée

Si le dépôt est retenu, il devient la **Partie K** de [`IMPORT_REPORT.md`](IMPORT_REPORT.md), et ce fichier
est réécrit en pointeur de sortie sur le modèle de [`ouroboros.md`](ouroboros.md).
[`MANIFEST.md`](MANIFEST.md) devra alors porter onze dépôts, avec la ligne Apache 2.0 — la première du
manifeste — et sa contrainte de **signalement des modifications** dans tout fichier dérivé. Il n'a pas été
modifié ici.

Indépendamment de cette décision, la reprise n° 2 du § 6 est **actionnable seule et tout de suite** : elle
ne coûte aucune dépendance, tombe dans le périmètre de la passe transverse (§ 14), et n'exige pas que le
reste du dépôt soit catalogué.

---

## 8. Relecture contre le code livré

Cette section a été écrite **après** les sept précédentes, en relisant `src/` au lieu de raisonner sur le
seul `AGENTS.md`. Elle en corrige trois passages. C'est le mode d'échec que `TEMPO.md` § 3 documente — *un
document périmé coûte plus cher qu'un document absent, parce qu'un agent sans document va lire le code et
un agent avec un document faux le croit* — et cette évaluation était en train de le reproduire.

### 8.1 Déjà couvert, souvent mieux

| Candidate retirée | Ce que `src/` fait déjà |
|---|---|
| Écriture atomique (`paths.py:29-90`) | `workspace/transaction.py:143-162` — `fsync`, `O_NOFOLLOW`, CAS double. **Plus strict que la source**, § 3.2 |
| Confinement de chemin (`security.py:315`) | `workspace/paths.py::checked_path` + `kernel.codeview.is_path_within` |
| Plafond de taille avant lecture (`security.py:357`) | `codeview.MAX_SOURCE_BYTES`, appliqué à `transaction.py:56-59` |
| Triptyque de résolution de symbole (`affected.py:138`, `serve.py:1384`) | `workspace/splice.py:77-78` — `len(definitions) != 1` → `Cause.invalid_symbol`, § 3.4 |
| Énumérations fermées de validation (`validate.py:4-7`) | `kernel.errors.Cause`, `ContextInclusionReason`, `ContextExclusionReason`, `Outcome`… le projet en est fait |

**Aucune modification de `src/` n'est justifiée par ce dépôt sur ces cinq points.**

### 8.2 Le seul manque réel — et il appartient à l'agent `engine`

`engine/context.py::assemble` est **plus fort** que `graphify` sur l'essentiel : chaque élément évincé
reste dans le paquet avec un `excluded_reason` typé (`BUDGET_PRESSURE`, `STALE`, `DUPLICATE`,
`IRRELEVANT`), et `ContextPacket.evictions` compte les évictions. Rien n'est perdu — **pour la trace**.

Mais `ContextPacket.render()` (`context.py:78-85`) ne rend que les contenus admis :

```python
contents = [item.content for item in self.items if item.included_reason is not None]

return "\n\n".join(contents)
```

**Le paquet sait ce qu'il a évincé ; le prompt ne le dit pas.** Un nœud dont trois éléments optionnels ont
sauté sous pression de budget reçoit un texte indiscernable d'un nœud où ces éléments n'ont jamais existé.
C'est exactement le faux-vert que le correctif BUG-2 de `graphify` nomme (`serve.py:1190-1205`) :

> un marqueur de troncature seulement en bas se lit comme un silence, comme une absence

⚠️ **Ce n'est pas une modification que cette évaluation a le droit de faire** — § 6 et § 14 : le périmètre
`src/engine/` appartient à son agent, et le rôle transverse ne touche pas l'implémentation métier.

**Prochaine action proposée à l'agent `engine`**, à inscrire dans `src/engine/STATE.md` par lui seul :
*écrire d'abord le test — un `ContextPacket` portant au moins une éviction dont le `render()` ne mentionne
pas l'éviction doit être rouge — puis faire porter à la sortie une ligne d'en-tête bornée nommant le nombre
d'éléments évincés et leurs `excluded_reason`, sans jamais rendre leur contenu.* Coût estimé : ~6 lignes,
absorbables sous la cible de 1 050 L, dont `engine` est à 507.

### 8.3 Une réserve sur le test de non-dérive

La reprise n° 2 du § 6 ne se porte **pas** telle quelle. `graphify` est un produit fini : importer chaque
symbole que `ARCHITECTURE.md` nomme est vert par construction. Ici, **les onze `MODULE.md` décrivent
l'interface visée, pas l'interface livrée** — `engine` documente un `walk()` qui n'est pas écrit, et c'est
légitime au sens du § 11.

Un portage naïf serait donc **rouge pour tout module non fini, et personne ne pourrait le verdir** : un
test que sa propre conception condamne est pire que pas de test (`TEMPO.md` § 2).

L'adaptation correcte reste à trancher, et elle n'est pas évidente — deux formes tenables :

- **Un test asymétrique** : un symbole documenté et absent est toléré (travail restant) ; un symbole
  documenté dont le **nom existe avec une signature divergente** est rouge. C'est la dérive qui trompe,
  pas le manque.
- **Un rapport, pas un test** : `tests.state_check` gagne une sortie *« documenté mais absent »* par
  module, informative, non bloquante, que le `STATE.md` du module peut alors citer.

**Aucune des deux n'est implémentée ici.** La seconde tomberait dans le périmètre du § 14 ; elle demande
une décision de l'auteur avant d'être écrite, parce qu'elle ajoute une exigence au protocole.
