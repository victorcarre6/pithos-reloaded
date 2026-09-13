# STATE — `campaign`

**Statut** : en cours
**Mise à jour** : 11:09
**Lignes** : 562 code / 550 cible · 983 physiques
**Empreinte** : c2ca70a737171d391ac9256101f0513ccff82f145230326d66cacce94c5c849c

## Prochaine action

Les questions de placement et de métrique sont résolues. Arbitrer le raccordement de derive au RepoIndex existant dans engine.classify et la lecture JSON du magasin via journal, puis vérifier les items métier avant tout passage à fini. Les frontières de dépendance ne sont pas modifiées par cette passe.

## Avancement

Liste « Fini quand » du `MODULE.md` :

- [x] Le magasin **ne lève jamais** sur une entrée mal formée, corrompue, tronquée, ou d'une version
      inconnue — test par corruption systématique de chaque champ.
- [x] Une entrée ignorée est **journalisée avec sa raison**.
- [x] `dedup` rejette un doublon lexical **et** un doublon par empreinte de contrat, sans aucun appel modèle.
- [x] La récurrence est **comptée**.
- [x] `rank` est un tuple lexicographique.
- [x] `derive` ne se déclenche qu'après trois rejets consécutifs, compteurs séparés dans la trace.
- [x] `admit` rend **toutes** les violations, chacune avec son chemin de champ.
- [x] Un placeholder contenant une expression évaluable est **refusé**.
- [x] La satisfaction d'une entrée `skill` est invalidée quand l'empreinte de ses fichiers change.
- [x] `TaskLifecycle` distingue **trois formes d'échec**.
- [x] `tests/boundaries/` confirme que `campaign` n'est importé que par `refinery`.

## Journal

_Append-only. Une entrée par unité de travail terminée. **Les résultats négatifs restent** — un timeout, une
incompatibilité ou une mesure défavorable sont des preuves. Chaque entrée porte son **niveau de preuve**
(`AGENTS.md` § 10), jamais plus haut que ce qui a été observé._

### 10:09 — `store.py`, le magasin qui ne lève jamais

Porté de `prime-agent-runtime/src/rlm/harness.py:94-275,722-769`, lu avant portage. Écrit `Family`
(quatre membres, **deux vivantes** — `ALIVE`), `Source` (`model` / `derived`, le séparateur des deux
compteurs de la § 6), `Entry`, `Store`, `bind`, `normalize`, `load`, `put`, `render_compact`.

**Mesuré** : 107 cas verts dans le venv `pithos`, `python -V` = Python 3.12.9, en 0,18 s.
Le harnais de corruption est le produit cartésien **7 champs × 10 valeurs corrompues** (`None`, `0`, `-1`,
`3.5`, `True`, `""`, `[]`, `{}`, un dict imbriqué, une chaîne de 5 000 caractères) = 70 cas, plus 11 formes
de conteneur malformé et 9 formes de fichier illisible (vide, tronqué, binaire, `null`, liste, chaîne,
schéma absent, schéma inconnu). **Aucune n'a levé.**

**Mesure de morsure des tests** : la garde `except ValueError` de `_coerce` remplacée par
`except KeyboardInterrupt` → **17 échecs sur 107**. Le harnais n'est donc pas vert par vacuité.

Décidé : la coercition dégrade là où un défaut a du sens (`version`, `source`, horodatages, `reference`) et
disqualifie là où il n'en a pas (`title`/`content` non textuels) — exactement la table de la source. Le
`try/except` autour du contrat Pydantic est le **dernier filet** : il attrape ce que la coercition n'a pas
prévu, dont le refus d'une entrée `skill` sans import ni callable.

**Niveau de preuve atteint** : 4 — le test métier passe, dont un contrôle de mutation. Pas 5 : le double
`tests/doubles/campaign.py` n'existe pas encore, et rien ne vérifie encore la conformité au `Protocol`.

### 10:09 — `registry.py`, la satisfaction qui périme avec les octets

Porté de `villani_code/autonomous.py:53-60,1014-1042` et `ouroboros/tools/registry.py:1566-1571,1605-1616,1862-2005`,
lus avant portage. Écrit `TaskLifecycle` (7 états), `FAILURES` (3), `Surface`, `OmissionReason`, `Omission`,
`ToolEntry`, `fingerprint`, `diverged`, `is_satisfied`, `Projection`, `project`.

**Mesuré** : 126 cas verts (store + registry) dans le venv `pithos`, Python 3.12.9, en 0,18 s.
**Contrôle de mutation, trois mutants tués** : satisfaction toujours vraie → 5 échecs ; `retryable` compté
comme échec → 2 échecs ; empreinte insensible au contenu des fichiers → 3 échecs.

Décidé : **`campaign` ne lit jamais le filesystem.** `fingerprint` prend une table
`chemin → Digest` — exactement ce que `FileFact.sha_after` de `workspace` produit déjà — au lieu de relire
le dépôt comme le fait `_repo_fingerprint_for_task` de la source. La péremption reste mécanique et la
frontière de `workspace` reste seule autorité du filesystem.

Décidé : les **trois formes d'échec** sont `failed` (vérifié rouge), `blocked` (rien à tenter) et
`exhausted` (tentatives prises). `retryable` n'en est pas une : c'est une instruction, pas une issue.

**Niveau de preuve atteint** : 4 — tests métier verts, dont trois contrôles de mutation. Pas 5 : le double
n'existe toujours pas.

### 10:09 — `admit.py`, toutes les violations en une passe

Porté de `OpenHands-main/src/manifests/manifest-template.ts:12,21,40-43,65-80`, lu avant portage, et
lu **côte à côte** avec `pi-main/packages/coding-agent/src/core/resolve-config-value.ts:1-35` — qui
importe bien `execSync`/`spawnSync` pour exécuter une valeur de configuration. L'opposition du § 7 est
réelle et le choix est appliqué : **aucune expression n'est jamais évaluée dans un placeholder.**

Écrit `BlastRadius`, `Proposal`, `Violation`, `Ok`/`Err`, et quatre règles : nom d'outil, noms
d'arguments, module d'import, gabarit d'appel.

**Mesuré** : 184 cas verts, venv `pithos`, Python 3.12.9, en 0,20 s.
**Contrôle de mutation, cinq mutants** : seule la première violation rendue → 3 échecs ; littéral du
gabarit non contrôlé → 7 échecs ; préfixe de module non contrôlé → 2 échecs ; alphabet des arguments
ouvert → 7 échecs ; grammaire de placeholder ouverte → 1 échec.

**Résultat négatif conservé** : au premier passage, **deux mutants ont survécu**. « Grammaire de
placeholder ouverte » a survécu parce que `arguments: list[Name]` acceptait n'importe quelle chaîne :
un argument déclaré `path;id` faisait passer `{{args.path;id}}` par la seule vérification de déclaration.
Ce n'était pas un défaut de test mais **une règle manquante** — `_check_arguments` a été ajoutée, et
l'alphabet des arguments est désormais celui du nom d'outil. « Racine de placeholder non fermée » a
survécu parce qu'aucun test ne distinguait la racine : `{{env.path}}` était refusé au motif que `path`
n'était pas déclaré, pas au motif que `env` n'est pas une racine. Un test le fixe maintenant.

Décidé : l'espace **n'est pas** un métacaractère shell ici. Il l'avait été une première fois, ce qui
rejetait tout gabarit à deux arguments ; l'appel MCP se fait par exécutable + liste d'arguments exacte,
sans shell (`our/mcp_client.py:230-250`), donc le séparateur n'est pas une surface d'attaque.

Décidé : les règles tournent sur le **dict brut**, la forme Pydantic est validée **ensuite**, et les deux
listes de violations fusionnent. Un défaut de forme ne masque donc jamais un défaut de règle — c'est ce
que le § 7 achète.

**Niveau de preuve atteint** : 4 — tests métier verts, dont cinq contrôles de mutation.

### 10:09 — `propose.py`, la redondance en deux temps sans appel modèle

Porté de `kilo-memory/src/recall/topics.ts:21,26-96` et `ouroboros/improvement_backlog.py:285-374`, lus
avant portage. Écrit `terms`, `related`, `overlap`, `contract_fingerprint`, `dedup`, `remember`, `axes`,
`rank`, `Signal`, `derive`, `counters`.

**Mesuré** : 209 cas verts à ce point. **Six mutants tués** : temps 2 désactivé → 1 échec ; temps 1
désactivé → 1 ; filet ouvert sans rejet → 3 ; classement par scalaire pondéré → 4 ; tolérance aux formes
fléchies levée → 2 ; empreinte de contrat non canonicalisée → 1.

**Résultat négatif conservé** : j'avais écrit un test attendant `related("parse", "parsing") is True`. Il
est rouge, et **c'est le test qui avait tort** : la règle portée est préfixale, et `parsing` diverge de
`parse` au cinquième caractère. La limite est désormais écrite comme telle dans le paramétrage, avec
`related("render", "rendering")` pour le cas que la règle couvre réellement. La désuffixation par règles
de langue reste hors périmètre — c'est le prix, nommé, d'un moteur lexical sans dépendance.

**Niveau de preuve atteint** : 4.

### 10:09 — `stop.py` et `mcpconfig.py`

Portés de `villani_code/autonomous_stop.py:7-12,35-47` et de `villani_code/mcp.py:27-35` +
`ouroboros/mcp_client.py:230-250`, lus avant portage.

**Mesuré** : 226 cas verts à ce point. **Cinq mutants tués** : seuil de récurrence levé → 4 échecs ;
récurrences non ordonnées → 1 ; cause d'arrêt unique → 1 ; surface non projetée → 1 ; commande MCP en
chaîne shell → 3.

Décidé : `should_stop` ne produit que `no_proposal` et `all_redundant` — les trois autres causes
(`planner_churn`, `stagnation`, `budget_exhausted`) sont dans la taxonomie fermée mais se constatent
depuis `engine`, pas depuis le magasin. La taxonomie est complète ici, la décision ne l'est pas.

### 10:09 — le double, le contrat de frontière et le graphe d'imports

Écrit `tests/doubles/campaign.py` (85 L) : magasin en mémoire, `admit` pilotable par table
`{nom → verdict}`, `dedup` et `should_stop` forçables. Les politiques **pures** (`rank`, `derive`, et la
dédup non forcée) y sont importées telles quelles, comme le double du journal importe `redact` : les
réimplémenter en aurait fait une seconde politique.

`src/campaign/__init__.py` publie le `Protocol` `Campaign` ; le corpus partagé du contrat vérifie que la
politique **et** son double le satisfont et portent les **mêmes signatures**, puis rejoue sur les deux :
entrée mal formée ignorée sans lever, version montée à l'écriture, rendu compact borné et déclarant ses
omissions, doublon lexical, doublon par empreinte, proposition d'arrêt.

Le test de graphe d'imports rend **mécanique** l'interdit du § 3 : `bridge`, `httpx`, `socket`,
`subprocess`, `urllib` et `engine` sont hors du graphe de `campaign`, donc **aucune décision de politique
ne peut appeler le modèle** — ce n'est plus une discipline. Il vérifie aussi qu'aucun module hors
`refinery` n'importe `campaign`, et 20 violations injectées confirment qu'il mord.

**Mesuré, état final** : `PYTHONDONTWRITEBYTECODE=1 python -m pytest src/campaign -q -p no:cacheprovider`
→ **266 passed, 1 skipped en 0,32 s**, venv `pithos`, `python -V` = Python 3.12.9. Le `skip` est le test
de scriptabilité, qui n'a de sens que sur le double.

**Comptage des lignes, mesuré** (non blanches, hors tests) :

| Fichier | Total | Code | Docstrings | Commentaires | Cible § 8 |
|---|---:|---:|---:|---:|---:|
| `store.py` | 214 | 170 | 32 | 12 | 150 |
| `registry.py` | 79 | 53 | 19 | 7 | 120 |
| `admit.py` | 134 | 107 | 25 | 2 | 100 |
| `propose.py` | 160 | 119 | 35 | 6 | 120 |
| `stop.py` | 39 | 22 | 11 | 6 | 40 |
| `mcpconfig.py` | 21 | 11 | 10 | 0 | 20 |
| **Total** | **647** | **482** | **132** | **33** | **550** |

**Niveau de preuve atteint** : **5 — validé sur double.** Le contrat de frontière tient dans les deux
sens. Pas 6 : rien ici n'a touché Ollama, un dépôt de campagne réel, ni un serveur MCP vivant.

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
| La cible de ~550 L est dépassée de 97 L | 647 L mesurées pour les six fichiers du § 8. **Mesuré** : 482 L de code exécutable — donc **sous la cible** — 132 L de docstrings et 33 L de commentaires. L'écart n'est pas fait de fonctionnalités en trop mais du style imposé au § 6 (une intention par ligne, un en-tête de bloc commenté, une docstring de contrat par fonction publique). | Un arbitrage de l'auteur : soit la cible du `MODULE.md` monte avec cette justification mesurée, soit une passe `/readability` allège les docstrings. **Ne pas trancher seul** : le ratchet est shrink-only. | Résolu le 11:09 — unité code dans AGENTS § 4, total global 562 / 550 ; plafond motivé ci-dessous, cible inchangée. |
| Les deux tests transverses sont hors de leur place | `AGENTS.md` § 11 les veut dans `tests/contracts/` et `tests/boundaries/` ; le § 6 m'interdit d'écrire hors de `src/campaign/`. Ils sont donc dans `src/campaign/`, prêts et verts. | La même dérogation que celle demandée par `kernel` et `journal`. Après accord : `test_double_contract.py` → `tests/contracts/test_campaign_double.py`, `test_import_boundaries.py` → `tests/boundaries/test_campaign.py`. | **Résolu le 10:09** — déplacés par la passe transverse ; suite complète verte. |
| Aucune fonction de **lecture** JSON dans l'interface de `journal` | `campaign` écrit son magasin par `journal.update_json_locked` (verrou + écriture atomique) mais doit le relire lui-même : `journal._read_json` **lève** sur un fichier corrompu, ce qui est exactement le comportement interdit ici. La lecture se fait donc en direct par `Path.read_text`, et le double journal ne peut pas rejouer un aller-retour `put` → `load` sur disque. | Une `read_json(path) -> dict` tolérante dans l'interface de `journal`, ou l'acceptation explicite que `campaign` possède seul la lecture de son fichier. En attendant, l'aller-retour se teste par `_parse(json_files[path])` sur le double, ce qui couvre le même code. | — |
| `derive` prend un `Signal` local au lieu de `RepoIndex` | **Corrigé le 10:09 par la passe transverse** : `RepoIndex` **existe**, publié par `engine/classify.py:66`, et `campaign` (niveau 4) a le droit de l'importer. La formulation initiale de ce blocage — « `engine` n'a aucun code » — était fausse : elle datait d'une lecture de `src/engine/STATE.md`, qui portait `non commencé` alors que le module avait 507 L vertes. | Un arbitrage : adopter `derive(index: RepoIndex)` **exige de retirer `engine` de l'ensemble interdit** de `tests/boundaries/test_campaign.py`, où la passe l'avait mis pour garantir qu'aucune décision de politique n'atteigne le modèle. Les deux objectifs ne sont pas incompatibles — `engine.classify` est déterministe et sans appel modèle — mais le choix doit être écrit, pas glissé. | — |

## Décisions locales

- **`bind(path, *, trace)` s'ajoute à l'interface du `MODULE.md`.** Les trois signatures publiées
  (`load`, `put`, `render_compact`) ne portent pas le magasin : elles supposent un propriétaire unique et
  implicite. C'est le précédent de `journal`, qui se lie de la même façon. Les trois signatures publiées
  sont respectées à la lettre.
- **Aucun état en mémoire n'est conservé entre deux appels.** `load()` relit à chaque fois et `put` fusionne
  **dans** le verrou de `journal`. La reprise `_sync_from_disk` (garde par `st_mtime_ns`, verdict *Copier*)
  devient **sans objet** : elle protège un état long-vivant que nous n'avons pas. Ne pas la réintroduire
  sans réintroduire d'abord un cache.
- **`_record` n'est jamais appelée sous le verrou de `journal`.** `journal.emit` prend le même verrou
  global `flock`, qui n'est pas réentrant : journaliser depuis le callback de `update_json_locked` ferait
  expirer le verrou. C'est pourquoi `_with_entry` est muette et purement mécanique.
- **`put` laisse remonter l'erreur de `journal` sur un fichier de magasin illisible.** Écraser un fichier
  qu'on ne sait pas relire détruirait une donnée brute (contrainte dure n°6). La relecture, elle, tolère —
  c'est le chemin exposé au modèle.
- **Le fichier fait autorité sur `version` et `created_at`**, jamais l'appelant : `put` incrémente à partir
  de ce qu'il relit sous le verrou.
- **`render_compact` réserve d'avance la place du marqueur `+N more`**, donc la borne `budget` tient
  strictement, au prix de quelques caractères perdus quand rien n'est omis.
- **Écart de cible** : `store.py` fait 214 L non blanches pour les ~150 L annoncées au § 8. L'écart tient
  à la mise en forme du projet (une intention par ligne, blocs commentés, appels Pydantic verticaux) et aux
  docstrings de contrat. Le budget du module (~550 L) n'est pas menacé : `registry` + `admit` + `propose` +
  `stop` + `mcpconfig` visent ~400 L, et le ratchet reste **shrink-only** au niveau du module.

- **`TaskLifecycle` reprend le vocabulaire de `kernel.NodeStatus` sans le réimporter.** Le `MODULE.md` § 8
  demande l'enum ici ; `kernel` publie déjà les mêmes sept valeurs plus `budget_limited`. Un test
  (`test_the_lifecycle_stays_inside_the_kernel_vocabulary`) vérifie **mécaniquement** l'inclusion, pour que
  la duplication ne dérive pas en silence. Ne pas la « nettoyer » sans trancher qui possède ce vocabulaire.
- **`project` est une fonction pure à trois entrées** — entrées du registre, empreintes courantes, modules
  en échec d'import. `campaign` ne découvre rien : elle reçoit les faits et rend la surface plus les
  raisons typées de chaque absence.

- **`Ok[T]` / `Err[T]` sont redéfinis ici.** `bridge` publie déjà les siens, mais liés à un
  `schema_sha256` qui n'a aucun sens pour une admission, et `kernel` n'en publie pas. Deux modules
  définissent donc maintenant le même patron. **C'est à `kernel` de le posséder** — voir Blocages.
- **L'alphabet fermé, et non une liste noire, est ce qui exclut les métacaractères shell.** `_check_name`
  et `_check_arguments` valident par regex positive ; `FORBIDDEN` ne sert qu'au **texte littéral** du
  gabarit, où une liste positive n'a pas de sens.

- **`should_stop` respecte la signature publiée à la lettre** : elle ne lit que le magasin. La récurrence
  y est lisible parce que le **compte est la version** de l'entrée `memory`, que `put` incrémente. Aucun
  compteur parallèle n'a été inventé.
- **`derive` prend `list[Signal]` et non `RepoIndex`.** ⚠️ **Le motif écrit ici le 10:09 était faux** :
  `RepoIndex` **est** publié, par `engine/classify.py:66`. Je ne l'avais pas trouvé parce que
  `src/engine/STATE.md` portait `non commencé` — et je l'ai cru plutôt que de regarder le code. La leçon
  vaut au-delà de ce champ : **un `STATE.md` périmé est une source de vérité qui ment.** `Signal` reste le
  contrat minimal que le filet lit vraiment ; le remplacer par `RepoIndex` est un choix ouvert, pas un
  blocage — voir la ligne correspondante dans Blocages.
- **Le double importe `rank`, `derive` et `dedup` de la politique réelle.** Ce sont des fonctions pures :
  les réimplémenter aurait créé une seconde politique, donc une divergence possible entre deux vérités.
  C'est le précédent du double de `journal` avec `redact`.
- **`DiskBackedTrace`, dans le corpus de contrat, est un adaptateur de test au-dessus du double du
  journal** — pas l'implémentation du voisin. Il referme exactement l'écart nommé au premier blocage.

## Reprises traitées

| Source | Verdict | Fait ? | Note |
|---|---|---|---|
| `rt/harness.py` — `HarnessEntry` en dataclass | Copier | oui | passé en Pydantic v2, structure conservée |
| `rt/harness.py` — `load()` défensif champ par champ | Copier | oui | cœur du spike n°6 ; Pydantic ne lève plus, il est encapsulé |
| `rt/harness.py` — entrée `skill` portant import + callable | Copier | oui | `Entry.callable_skill` ; une capacité non appelable n'entre pas |
| `rt/harness.py` — `_strip_scope_prefix` | Copier | oui | `normalize` : `skill:tool` accepté verbatim |
| `rt/harness.py` — `overview()` compact borné | Copier | oui | `render_compact`, `ref=` tronqué, `+N more` |
| `rt/harness.py` — `_sync_from_disk` par `st_mtime_ns` | Copier | non | **sans objet** : aucun état long-vivant — voir Décisions locales |
| `rt/harness.py` — mode `in_memory` en repli sûr | Copier | oui | `_path is None` rend un magasin vide sans jamais résoudre de chemin |
| `our/semantic_dedup.py:52-62` — bornage à marqueur visible | Copier | oui | `_clip` termine par `…` ; l'artefact durable n'est jamais touché |
| `rt/harness.py` — scopes, rollback, label mobile | Écarté | non | ils servent à éditer des `prompt` ; rien n'édite de `prompt` au socle |
| `autonomous.py:53-60` — `TaskLifecycle`, 7 états / 3 échecs | Copier | oui | valeurs alignées sur `kernel.NodeStatus`, inclusion testée |
| `autonomous.py:1029-1042` — satisfaction invalidée par l'empreinte | Copier | oui | `is_satisfied` + `diverged` |
| `autonomous.py:1014-1027` — empreinte restreinte à la tâche | Copier | adapté | restreinte aux fichiers **attestés de l'entrée**, sans relire le dépôt |
| `our/evolution_fingerprint.py:1-42` — une seule primitive d'empreinte | Copier | oui | `fingerprint`, lue par `is_satisfied` et par `project` |
| `our/tools/registry.py:1862-2005` — `capability_omissions` | Copier | oui | `Projection.omissions`, raison typée + sujet exact |
| `our/tools/registry.py:1566-1571,1605-1616` — un module qui échoue omet tous ses outils | Copier | oui | testé sur deux outils d'un même module |
| `our/skill_loader.py:28-33` — fichiers de contrôle exemptés du hash | Copier | **non** | **Reporté** : au socle, `campaign` n'écrit aucun marqueur dans l'arbre d'un outil, l'exemption serait vide. À réintroduire le jour où elle y écrit. |
| `autonomous_helpers.py:61-64` — `retry_limit_for_contract` | Copier | **non** | la source donne 2 tentatives aux contrats de *validation*, parce qu'ils sont instables. Nos invariants sont déterministes (Hypothesis, graine fixée) : aucune relation n'a de raison mesurée d'avoir deux tentatives. À implémenter dès qu'un non-déterminisme est **constaté**, pas avant. |
| `our/tools/registry.py:2006-2030` — `policy_hidden_reason` | Écarté | non | aucune politique ne cache d'outil ici |
| `autonomous_helpers.py:29-41` — `effective_priority` | Écarté | non | scalaire pondéré, interdit § 3 |
| `manifest-template.ts:12,40-43` — grammaire de placeholder fermée | Adapter | oui | `PLACEHOLDER_PATTERN`, chemin pointé d'identifiants, rien d'autre |
| `manifest-template.ts:21,76` — interpolation sans évaluation d'expression | Adapter | oui | racine fermée `args.<nom>`, argument devant être déclaré |
| `automation-setup.ts:403` — carte d'erreurs par champ | Adapter | oui | `Violation.field_path`, y compris `template.<i>` et `arguments.<i>` |
| `opencode/src/config/parse.ts:8-72` — erreurs portant scope et chemin | Traduire | oui | même chemin de champ, cause fermée de `kernel` |
| `pi/resolve-config-value.ts:10` — commande shell dans une valeur de config | Écarté | non | **lu et confirmé** : la source importe `execSync`. C'est l'inverse de notre règle |
| `topics.ts:26-96` — moteur lexical sans dépendance | Traduire | oui | `terms` + `related` ; la désuffixation par langue reste hors périmètre |
| `improvement_backlog.py:285-374` — la récurrence n'est jamais jetée | Copier | oui | le compte est la version de l'entrée `memory` |
| `harness-table.ts:66,105` — canonicalisation avant comparaison, empreinte de contrat | Adapter | oui | `contract_fingerprint`, JSON trié puis sha256 |
| `autonomy.py:390-400` — `Opportunity`, `evidence` obligatoire | Copier | oui | `Proposal.evidence`, `min_length=1` |
| `autonomy.py:523-631` — découverte déterministe du backlog | Adapter | partiel | `derive` a sa porte et son déterminisme ; les heuristiques de découverte appartiennent à qui produira les `Signal` |
| `autonomous_stop.py:7-12` — `StopDecision`, dont `planner_churn` et `stagnation` | Copier | oui | taxonomie complète ; `campaign` n'en décide que deux |
| `autonomous_stop.py:35-47` — la raison énumère ce qui a été examiné | Copier | oui | `StopProposal.examined` + `detail` |
| `mcp.py:27-35` — couche `managed` écrite par le runtime | Copier | oui | `mcpconfig.managed_layer`, décision 7 |
| `our/mcp_client.py:230-250` — stdio = exécutable + arguments exacts | Copier | oui | ni shell, ni env, ni cwd ; testé |
| `our/semantic_dedup.py:1-140` — dédup sémantique par appel modèle | Adapter | **non** | **Écarté par le § 3** : une décision de politique n'est pas prise par un modèle. Le graphe d'imports le rend mécanique |
| `mcp.py:11-24` — `_expand_env` avec `${VAR:-default}` | Copier | **non** | **Reporté** : la couche `managed` que nous écrivons ne contient aucune variable ; l'expansion appartient au lecteur de la config, pas à son auteur |
| `autonomous_helpers.py:9-26` — `build_wave_candidates` | Copier | partiel | la déduplication par clé en gardant le meilleur rang est dans `rank` ; le filtre par `min_confidence` vient de `TakeoverConfig`, **écarté** |


### 11:09 — mesure de production et en-tête courant

Passe transverse demandée via TEMPO.md. Aucun code métier ni case de livraison modifié.
Mesure AST/tokenize : **562 lignes de code**, **983 physiques**, cible globale **550**. Sous-paquets et __init__.py inclus ; tests et doubles exclus.
L’empreinte de l’en-tête couvre les chemins et octets de toute la production.
La nouvelle métrique ne valide aucun item métier et ne relève aucune cible numérique.

**En-tête antérieur conservé** :

```text
**Statut** : en cours — socle complet et vert, deux items de `AGENTS.md` § 11 hors périmètre
**Mise à jour** : 10:09
**Lignes** : 647 / ~550 L pour les six fichiers du § 8, plus 41 L de `__init__.py` non budgétées.
**Le corps exécutable fait 482 L, sous la cible** ; l'écart est entièrement fait des 132 L de
docstrings et des 33 L de commentaires que le style impose. Mesure par fichier dans le journal du
10:09, et arbitrage demandé dans Blocages.
```

**Prochaine action antérieure, remplacée car périmée** :

Aucun code n'est en attente : les onze items de « Fini quand » passent, 266 cas verts. Faire trancher
par l'auteur les **deux blocages de périmètre** ci-dessous, dans cet ordre :

1. **L'écart de cible** (647 L pour ~550, corps exécutable à 482 L) — soit la cible du `MODULE.md` monte
   avec la justification mesurée, soit une passe `/readability` allège les docstrings. Ne pas trancher
   seul : le ratchet est shrink-only.
2. **L'emplacement des deux tests transverses** — `src/campaign/test_double_contract.py` doit aller dans
   `tests/contracts/test_campaign_double.py` et `src/campaign/test_import_boundaries.py` dans
   `tests/boundaries/test_campaign.py`. Les deux sont prêts et verts ; `AGENTS.md` § 6 m'interdit d'écrire
   hors de `src/campaign/`. C'est la **même dérogation** que celle déjà demandée par `kernel` et `journal`.

Après accord : déplacer les deux fichiers, relancer `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q
-p no:cacheprovider` sur `src/campaign`, `tests/contracts` et `tests/boundaries` dans le venv `pithos`,
consigner le résultat ici, passer le statut à `fini` et pointer la prochaine action sur `src/engine/STATE.md`.

**Plafond justifié** : 562 code
**Justification** : Le total de 562 lignes inclut la façade __init__.py, les modèles typés et les six fichiers du magasin, de sélection et de politique. Le comptage précédent de 482 omettait une partie de ce périmètre ; les 12 lignes au-delà de 550 restent bornées et documentées.

Les anciens comptes « corps exécutable sous la cible » sont des mesures historiques partielles ; ils ne décrivent pas le périmètre global désormais contrôlé.

**Niveau de preuve : 2** pour la mesure documentaire ; la suite initiale complète du 11:09 a rendu 1 215 passed et 3 skipped hors sandbox. Le détail des nouvelles validations vit dans tests/STATE.md.
