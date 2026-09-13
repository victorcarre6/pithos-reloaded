# Explications techniques

Document de référence des choix d'architecture et de leur raisonnement, **et journal de laboratoire du
projet**. Les deux documents ont fusionné le 06:09 (décision 33) : une décision et la séance qui l'a
produite se lisaient mal séparées.

- **Partie I — Décisions.** Le référentiel. Trente-trois décisions numérotées, stables, **amendées en
  place** quand une source les corrige. C'est ce qu'un lecteur futur lit.
- **Partie II — Journal.** La chronologie, une entrée par séance, horodatée `JJ:MM`. C'est ce qui explique
  *quand* et *pourquoi* une décision a bougé.

Chaque décision majeure est rattachée à une observation chiffrée de Pithos v1 quand elle en découle.

---

# Partie I — Décisions

---

## Ce que v1 a réellement mesuré

Le socle v1 a produit 67 runs projetés : **10 `completed`, 53 `failed`, 4 `interrupted`**. En détaillant les
dix succès, seuls **trois runs** contiennent une inference ayant produit un effet réel ; les autres sont des
preflights verts sans appel au modèle ou des runs terminaux déterministes. Environ **500 lignes de produit**
pour **~25 000 lignes de harness**, avec **30 % de tool calls en échec**.

Six modes d'échec sont documentés run par run dans l'ELN de v1. Trois structurent v2 :

1. **L'arithmétique du modèle n'est pas fiable.** L'oracle auto-généré produisait des contrats rouges
   confirmés mais faux. Le double-vote inter-générations filtre le bruit aléatoire, jamais une
   incompréhension systématique. Cause d'échec dominante, sur six micro-rushes.
2. **Le contexte périmé bloque le modèle sans le faire échouer.** Un brief décrivant une fonction déjà
   mergée a produit 12 419 `thinking_delta` consécutifs et zéro tool call.
3. **Une écriture destructrice peut être syntaxiquement valide.** Un appel d'outil mal formé, écrit comme
   contenu de fichier, était du Python littéral valide : boucle de six heures sur un fichier vidé.

---

## Décision 1 — La nano-étape, et son critère d'arrêt

v1 disposait déjà d'une décomposition (`plan_todo`) : greffée en option sur une machine à états figée,
plafonnée à quatre étapes, non récursive, et son plan n'était jamais validé sémantiquement.

v2 fait de la décomposition la **primitive centrale**. L'unité est le **nœud de travail** :

```text
node := { id, parent, intention, cibles, critère | null, statut, profondeur }
```

- `critère == null` → le nœud doit être scindé (`decompose`).
- `critère != null` → le nœud s'exécute (`implement` → `verify`).

**Le critère d'arrêt de la récursion est la vérifiabilité, pas une profondeur.** C'est le point central :
découper à l'infini sans critère exécutable ne fait que multiplier des étapes invérifiables. C'est exactement
ce qui s'est passé sur `level-clamping` en v1 — le plan était correct, l'oracle était faux.

Une profondeur maximale de **3** existe comme filet de sécurité, jamais comme borne nominale.

---

## Décision 2 — Le contrat est un invariant, jamais une valeur

C'est la décision structurante de v2. Le modèle **n'émet plus aucun littéral**.

En v1, « une chaîne et des littéraux numériques » traversaient la frontière modèle → exécution. En v2, seuls
traversent : un **choix dans une énumération fermée** et des **noms de symboles vérifiés présents** dans les
fichiers approuvés.

### Catalogue fermé des relations

| Relation | Propriété exécutée | Symboles requis |
|---|---|---|
| `round_trip` | `g(f(x)) == x` | `f`, `g` |
| `idempotent` | `f(f(x)) == f(x)` | `f` |
| `commutes_with` | `f(g(x)) == g(f(x))` | `f`, `g` |
| `preserves` | `p(f(x)) == p(x)` | `f`, `p` |
| `invariant_under` | `f(t(x)) == f(x)` | `f`, `t` |
| `monotone` | `x ⊑ y ⟹ f(x) ⊑ f(y)` | `f` |
| `total` | `f(x)` ne lève jamais sur le domaine | `f` |
| `raises_on` | `f(x)` lève exactement `E` | `f`, `E` |
| `schema_conform` | la sortie valide le JSON Schema de l'outil | `tool` |

La sortie structurée attendue du modèle est donc :

```json
{ "relation": "round_trip", "symbols": ["encode", "decode"], "domain": "json_values" }
```

**Le harness génère les entrées.** Les domaines sont un second catalogue fermé, déterministe et seedé
(`small_ints`, `floats_finite`, `text_unicode`, `json_values`, `lists_of<T>`, `paths`). Le seed est
journalisé : un échec est rejouable à l'identique.

Ce que ça achète : la faiblesse mesurée de Ling — calculer juste — n'entre plus jamais dans la boucle. Nommer
une relation entre deux fonctions est une tâche de reconnaissance de forme, pas de calcul.

Ce que ça coûte : les propriétés sont plus faibles qu'un contrat exact. `total` seul ne prouve presque rien.
D'où la décision suivante.

---

## Décision 3 — Double gate : rouge-avant et mutation-check

v1 exigeait déjà qu'un oracle **échoue sur le code courant** avant d'être accepté. Nécessaire, insuffisant :
un oracle peut échouer pour une mauvaise raison. v1 a corrigé cela tardivement en exigeant que l'échec soit
bien une `AssertionError` et pas un `TypeError` d'arité.

v2 ajoute la gate que v1 n'a jamais eue : le **mutation-check**.

Avant d'accepter un invariant, le harness applique un jeu de mutations déterministes à l'AST de la fonction
cible — inverser un opérateur de comparaison, remplacer un `return` par une constante, supprimer une
instruction — et exige que l'invariant **échoue sur au moins une mutation**. Un invariant qui survit à toutes
les mutations est tautologique et rejeté.

Séquence complète d'acceptation d'un critère :

1. Les symboles nommés existent réellement dans les fichiers approuvés (vérification AST, pas regex).
2. L'arité et la nature des symboles sont compatibles avec la relation choisie.
3. L'invariant est **rouge** sur le code actuel, et rouge par assertion.
4. L'invariant est **tué par au moins une mutation** de la cible.
5. Après implémentation, l'invariant est **vert**, et la suite de régression accumulée reste verte.

Un critère qui échoue à l'une de ces gates est rejeté et le nœud est retenté puis bloqué — jamais exécuté
sur la foi du modèle.

---

## Décision 4 — Coquille MCP fine, cœur pur

Les invariants métamorphiques opèrent sur des fonctions pures. Un outil MCP a des effets de bord. La
conséquence est une contrainte de structure imposée au produit :

```text
core/<outil>.py     fonction pure, sans I/O          → porte les invariants
tools/<outil>.py    coquille MCP : schéma, I/O       → porte schema_conform
```

Un nœud d'exécution ne modifie **qu'un seul fichier**. Cette règle est vérifiée par le harness, pas demandée
au modèle : tout changement hors cible est refusé à la projection.

C'est aussi la réponse à la question « comment valider un outil à effet de bord sans humain » : on ne le
valide pas directement, on rend sa partie non triviale pure et on valide celle-là.

---

## Décision 5 — Le registre d'outils est l'état de la campagne

`registry.json` porte, pour chaque outil : nom, schémas d'entrée/sortie, statut
(`proposed` / `implemented` / `verified`), invariants tenus, mission d'origine.

Il sert simultanément de :

- **garde anti-redondance** — une proposition doit nommer un outil absent du registre ;
- **métrique de progression** — outils vérifiés / proposés ;
- **entrée de la proposition d'arrêt** — plus de proposition non redondante possible ;
- **source d'auto-extension** — voir décision 7.

### Le risque assumé du backlog ouvert

Le `seed` ouvert avec backlog auto-alimenté est le mécanisme qui a produit les boucles stériles de v1 :
`frame-pipeline-v2` redemandait mot pour mot une fonction déjà mergée, cinq missions consécutives à vide.
v1 ne validait que la sécurité des chemins, jamais la pertinence, et n'a plafonné les retries que tardivement.

v2 rend le rejet **mécanique et antérieur à toute inference**. Une proposition est refusée si :

- le nom existe déjà dans le registre ;
- le couple (schéma d'entrée, schéma de sortie) est structurellement identique à un outil existant ;
- la description dépasse un seuil de recouvrement lexical normalisé avec une entrée existante ;
- l'outil cible une fonction déjà bloquée à répétition.

Trois propositions rejetées d'affilée déclenchent la **proposition d'arrêt**, pas une quatrième tentative.

### Amendement — la récurrence se compte, elle ne se jette pas

Rejeter une proposition redondante est correct ; **la jeter ne l'est pas**. Ouroboros
(`improvement_backlog.py:285-374`) ne détruit jamais un doublon : il incrémente `count`/`last_seen`,
**rouvre** un item clos, et **élève le rang** de l'item récurrent.

Notre formulation initiale détruisait cette information **au moment exact où elle devenait un signal
d'arrêt informé**. Un outil que le système reproposera trois fois n'est pas du bruit : c'est ce que le
système croit devoir faire, et c'est précisément ce que la proposition d'arrêt doit rapporter à l'opérateur.
Le registre porte donc, par entrée rejetée, un compteur de récurrence et sa dernière occurrence.

Deux mécanismes qui vont avec, repris tels quels : le vivier de candidats est **déterministe, classé et
plafonné à vingt avant tout appel modèle** (`:199-220`) — le modèle ne voit jamais le backlog brut — et la
**fermeture d'un item se fait sur commit, par le code** (`:423-455`), jamais sur la déclaration du modèle.

### Amendement — la satisfaction se périme

Un outil `verified` ne doit pas rester verrouillé pour toujours. v1 a échoué là-dessus : son marqueur
`~/logs/pithos/runtime/*-completed.json` figeait un rush comme terminé et **ne savait pas se périmer quand le
code changeait**, transformant tous les réveils suivants en no-op jusqu'à intervention humaine.

Villani résout ça proprement (`autonomy` — `autonomous.py:1014-1042`) : une tâche satisfaite mémorise une
**empreinte du repo restreinte à ce qui la concerne**. Tant que l'empreinte est identique, la tâche reste
satisfaite ; dès qu'elle bouge, la satisfaction est invalidée et la tâche redevient éligible.

Le registre porte donc, par outil, l'empreinte des fichiers qui le composent au moment de sa vérification.
Un outil dont le `core/` a changé repasse automatiquement par la gate d'invariants. C'est aussi ce qui rend
sûre l'auto-extension de la décision 7 : un outil réutilisé par une étape ultérieure est toujours un outil
dont l'empreinte est encore valide.

La granularité des états vient de la même source (`autonomous.py:53-60`) : `pending` / `running` / `passed` /
`failed` / `blocked` / `retryable` / `exhausted`. **Trois formes d'échec distinctes** — « échoué » ne dit pas
s'il faut réessayer, et c'est précisément ce que le harness doit savoir au réveil suivant.

Le nombre de retries dépend enfin du type de contrat (`autonomous_helpers.py:61-64`) : une étape de
validation en obtient deux, une étape effectueuse une seule.

### Amendement — la redondance se mesure en deux temps, sans jamais appeler le modèle

*(06:09 — ferme la seule question laissée explicitement ouverte du rapport d'import, § D5 n°3.)*

Le rejet lexical par `SequenceMatcher` laisse passer la reformulation : « normaliser un chemin » et
« canoniser un path » sont deux propositions distinctes pour le même outil. Ouroboros résout ça par **un**
appel light-model à énumération fermée, validé exactement, fail-open — et cet appel respecte la contrainte
dure n°1 à la lettre, puisqu'il ne produit qu'un choix dans une énumération.

**Il est écarté quand même.** La décision 24 refuse qu'une décision de politique soit prise par un modèle,
et la redondance *est* une décision de politique. À la place, deux temps :

| Temps | Quand | Sur quoi | Décide |
|---|---|---|---|
| **1 — lexical** | à la proposition | titre et description normalisés | rejet immédiat d'un quasi-doublon |
| **2 — empreinte de contrat** | dès que les critères existent | `{relation, symbols, domain}` canonicalisé (décision 19) | rejet, même si les mots diffèrent |

**Deux propositions formulées différemment qui produisent le même contrat sont le même outil.** L'empreinte
tranche là où le lexical est aveugle, et elle ne coûte aucun appel.

Le prix est nommé : **le doublon du temps 2 se découvre tard**, après décomposition, parfois après une
première nano-étape verte. C'est un rejet tardif, pas un outil livré en double — et la récurrence est
comptée, jamais jetée (amendement précédent).

---

## Décision 6 — Nano-étape en mode direct, sans session agentique

**Décision la plus impactante sur le coût, et celle qui s'écarte le plus de v1.**

v1 ouvrait une session Pi complète par phase cognitive. Coût de démarrage mesuré : « quelques minutes selon
la charge de la machine ». Avec une décomposition récursive, ce coût domine tout le reste.

Or les deux seuls rushes v1 réellement réussis par inference ont consommé **1 et 6 tool calls**. Une
nano-étape qui modifie une fonction dans un fichier déjà projeté n'a pas besoin d'une boucle d'agent : elle
a besoin d'une génération bornée et d'un patch appliqué par le harness.

Deux modes de nœud feuille, `direct` par défaut :

- **`direct`** — un appel Ollama borné, sortie structurée, le harness applique le changement. Ni Pi, ni
  tools, ni boucle. C'est le mode nominal.
- **`agentic`** — une session Pi outillée, réservée aux nœuds qui doivent réellement explorer (lire
  plusieurs fichiers, exécuter une commande). Non implémenté au socle, ouvert si le mode direct plafonne.

Conséquence : **Pi devient optionnel**. Le harness parle directement à Ollama pour le chemin nominal. Cela
retire de la surface les extensions Pi, la configuration Pi host/Docker et les sockets brokerisés côté
modèle — trois sources de complexité de v1 dont aucune n'est requise par le mode direct.

### Le contre-modèle, nommé

Prime Agent prend l'option inverse **jusqu'au bout** : un seul outil `ipython`, et le modèle écrit du Python
qui lit, édite, exécute et délègue dans un REPL persistant. C'est le contre-modèle le plus complet de cette
décision, et il vaut d'être nommé plutôt qu'ignoré.

Ce qu'on abandonne en refusant cette voie : la composition, la délégation native, l'état qui survit entre les
tours. Ce qu'on gagne : **aucune surface d'exécution ouverte, aucun REPL à sécuriser, et un modèle 8B qui n'a
jamais à écrire de code de contrôle.** Le rapport de force penche clairement vers le REPL sur un modèle
frontière ; il penche dans l'autre sens sur un 8B dont les modes d'échec documentés incluent « omet un champ
requis » et « abrège les noms de paramètres ».

---

## Décision 7 — L'auto-extension passe par le registre, pas par un mécanisme dédié

v1 disposait d'un sous-système d'auto-mutation (snapshots, manifests SHA-256, promotion contrôlée,
rechargement de ressources Pi) pour répondre à la question « l'agent crée-t-il une capacité et la
réutilise-t-il ? ». Réponse obtenue : oui, une fois, sur un run de preuve dédié.

En v2, la campagne **construit littéralement des outils**. Un outil qui passe au statut `verified` est
enregistré par le harness dans la configuration MCP de la campagne, et devient appelable par les nœuds
suivants. L'auto-extension devient la boucle produit elle-même.

Garde-fous : seul le harness écrit la configuration MCP ; un outil n'est exposé qu'après vérification ; la
suite d'invariants accumulée s'exécute en gate de régression au démarrage de chaque mission, de sorte qu'un
outil devenu faux est détecté avant d'être réutilisé.

### Amendement — `reload` rend l'outil appelable dans la mission en cours

La formulation initiale disait qu'un outil vérifié « devient appelable par les nœuds suivants », sans dire
**quand**. Implicitement : au prochain réveil, puisque la configuration MCP est lue au démarrage.

`rt/mcp.py:397-416,483-491` ferme ce chaînon : **fermeture et réouverture d'un serveur MCP sans redémarrer le
processus**, sous verrou par nom, génération courante remplacée atomiquement. Un outil promu `verified`
devient appelable **dans la mission qui vient de le construire**.

Ce n'est pas un confort. **C'est ce qui rend la question expérimentale 4 mesurable dans une seule mission**
— « crée-t-il un outil utile, puis le réutilise-t-il ? » — au lieu d'exiger deux réveils et un intervalle de
trois heures pour observer un seul cycle création-réutilisation.

Deux compléments du même module : les outils sont **découverts au runtime et filtrés** par listes
d'activation, donc un outil retiré du registre cesse d'être appelable sans redéploiement ; et l'installation
se fait **par hash de `pyproject.toml`, en ordre topologique des dépendances**, avec un fichier de version
dans le venv qui porte l'identité du runtime et la liste des outils installés.

---

## Décision 8 — Borne murale, et échec partiel non fatal

La borne dure d'une mission est le **temps mural**. Les autres bornes (sessions, profondeur, tokens) existent
comme filets, pas comme contrat.

Justification : la latence de Ling varie fortement avec la charge machine, et le mode d'échec le plus coûteux
de v1 était précisément une session qui tourne longtemps sans rien produire — 300 à 390 secondes par phase à
zéro tool call et zéro token. Une borne en tokens ou en sessions ne protège pas de ce cas ; une borne murale
si.

À l'expiration : la mission **finalise ses nœuds verts**, sérialise l'arbre et sort. Elle n'échoue pas
globalement. Un nœud échoué est `skipped`, ses frères continuent ; la mission n'échoue que si aucun nœud n'est
vert. C'est la philosophie best-effort déjà retenue en v1 : un incident partiel ne doit jamais jeter un
travail déjà validé.

Valeur de départ proposée : **20 minutes par mission**, réveil toutes les **3 heures**. À réviser après les
dix premières missions.

### Amendement — deux réserves, pas une

Une borne murale unique confond deux décisions différentes, et Ouroboros a mesuré le coût : **confondre la
fenêtre d'émission et la réserve de démarrage a amputé 54 minutes d'une tâche de six heures**
(`task_pacing.py:199-224`).

Les deux réserves :

- **« ne plus démarrer »** — une gate coûteuse ne se lance que si elle tient au-dessus de la réserve, avec
  une raison typée quand elle est sautée. La réserve est calibrée par **EWMA des durées observées**
  (`max(plancher, 1,5 × EWMA)`, `alpha = 0.5`), depuis les événements de timing déjà écrits — auto-calibration
  au lieu d'une constante devinée.
- **« finaliser »** — la fenêtre réservée à la finalisation des nœuds verts, qui ne doit jamais être entamée
  par un démarrage optimiste.

Un détail qui décide de la correction de l'ensemble : **le latch de l'ancre de départ**
(`task_pacing.py:233-245`). Sans lui, chaque snapshot ré-ancre le total sur « maintenant » et la réserve se
dégrade silencieusement vers son plancher — une mission longue perd sa marge sans qu'aucune trace ne le dise.

Deux règles de forme : `has_deadline=False` **désactive l'axe temps entièrement** plutôt que de simuler un
infini, et quand un chiffre faisant autorité est indisponible, la substitution est **divulguée**, jamais
silencieuse.

**Et une règle de propagation, qui manquait.** Les deux réserves disent *quand* s'arrêter ; elles ne disaient
pas comment le budget atteint un `subprocess` de vérification ou une requête au modèle. La réponse est **un
seul deadline monotonique de mission, propagé à toutes les sous-opérations**
(`unsloth/dataprep/synthetic.py:162,172`), et non des timeouts indépendants qui s'additionnent. Sans cela, une
mission bornée à 20 minutes se termine à 35 : chaque sous-opération respecte le sien, et la somme dépasse.

Corollaire : **la terminaison est récursive sur l'arbre de processus, avec son propre timeout de nettoyage**
(`:52`). Quatre sources le disent — Pi, Kilo, Prime Agent, Unsloth : on arrête le groupe, jamais le seul
parent.

### Amendement — une seule réserve au socle, la calibration après mesure

*(06:09, passe de simplification.)*

Les deux réserves distinctes et leur calibration par EWMA sont conservées comme cible, **et reportées**. Au
socle : un deadline monotone unique, propagé à toutes les sous-opérations, et une **réserve de finalisation
en constante** au-delà de laquelle on n'ouvre plus de nœud mais on finalise les verts. ~30 L.

La raison est arithmétique, pas doctrinale : **une EWMA se calibre sur des durées observées, et il n'y en a
aucune.** `PROJECT.md` prévoit déjà de fixer la valeur de la borne après les dix premières missions ; le
latch d'ancre et le `CostCeiling` à quatre états arrivent au même moment. Le seam transport/logique, lui,
reste au socle : un timeout HTTP n'est pas un jalon logique.

---

## Décision 9 — Transactionnalité et garde d'écriture

Repris de v1 sans modification, parce que ces deux mécanismes y sont nés d'incidents réels :

- **Snapshot / restauration** des seuls fichiers cibles, avant la boucle et à toute sortie non verte. Un
  fichier cible créé est supprimé au rollback ; aucun fichier hors allowlist n'est touché.
- **Garde syntaxique** : un changement `.py` est refusé avant écriture s'il ne compile pas, ou si le fichier
  portait des `def` au niveau module et n'en porte plus aucune. C'est la signature exacte de la destruction
  observée en v1.

### Amendement — seuils nommés et snapshot sur disque

Deux renforts repris de Villani.

**Seuils de mutation** (`state_tooling.py:21-122`). La garde syntaxique attrape la destruction totale ; elle
laisse passer la réécriture massive qui compile encore. `MutationGuardThresholds` la nomme :
`max_touched_lines = 120`, `max_touched_ratio = 0.35`, `min_lines_for_ratio_guard = 40`. L'analyse passe par
`difflib.SequenceMatcher` sur les lignes et compte insertions, suppressions et remplacements pour produire un
verdict `probable_rewrite`. Des seuils nommés, versionnés et testables valent mieux qu'un jugement implicite.

Notre décision « le modèle renvoie une fonction, pas un fichier » ferme la faille en amont — le splice AST
rend la réécriture globale structurellement impossible. Ces seuils restent la **seconde ligne**, appliquée au
diff effectif après splice.

**Snapshot sur disque plutôt qu'en mémoire** (`checkpoints.py:18-60`). Un snapshot conservé en mémoire ne
survit pas à un crash du processus : la restauration transactionnelle serait perdue au moment où elle compte
le plus. Villani écrit le snapshot dans un répertoire horodaté avec son `metadata.json`, et `rewind()` recopie.
Nous adoptons ce mécanisme pour les `target_files` d'un nœud, sous `~/logs/pithos2/missions/<id>/snapshot/`.

### Amendement — le snapshot est un dépôt Git fantôme, et l'écriture est un compare-and-swap

Le snapshot par copie de fichiers dans un répertoire horodaté est la forme la plus faible du mécanisme. Kilo
en donne une strictement supérieure (`snapshot/index.ts:107-111,406-408,465-501`) : `git init` dans un
`--git-dir` **hors projet**, `write-tree` pour capturer, `read-tree` + `checkout-index` pour restaurer.

Trois propriétés qu'une copie n'a pas : **adressage par contenu** (deux snapshots identiques ne coûtent
rien), **atomicité** (tous les hashes sont validés avant qu'un seul fichier soit touché, et un échec est
fatal plutôt que partiel), et **invisibilité** (le dépôt fantôme vit hors du workspace, donc n'apparaît ni
dans le `git status` du produit ni dans les diffs de la campagne).

**Second renfort : `writeIfUnchanged`** (`core/src/file-mutation.ts:144-158`), un compare-and-swap sur le
contenu, sous verrou par chemin canonique et section `uninterruptible` (`:79-83`). La contrainte dure n°3
couvre la restauration ; elle ne couvre pas la **détection d'un changement concurrent au moment d'écrire**.
Un CAS transforme « on a écrasé quelque chose sans le savoir » en `StaleContentError` typé. Ni Villani ni v1
ne l'avaient.

### Amendement — une mutation rend son bilan chiffré

La garde vérifie *qu'une écriture n'a pas détruit le fichier* ; elle ne dit rien de **combien** elle a
changé. SWE-agent fait retourner à toute opération de remplacement un objet portant `first_replaced_line`,
`n_search_lines`, `n_replace_lines` et **`n_replacements`** (`windowed_file.py:36-52`).

Ce compteur débloque trois choses : comparer les remplacements effectués au **nombre attendu** — la règle de
Kilo qui annule le lot entier en cas d'écart, mais rendue vérifiable ; alimenter la métrique d'**inflation de
patch** d'Ouroboros sans instrumentation séparée ; et **détecter un splice qui a touché zéro ligne sans
relire le fichier**.

S'y ajoute un `undo_edit` **au niveau du fichier** (`:276`), distinct du rollback transactionnel de mission —
utile entre deux tentatives d'un même nœud, là où restaurer le snapshot complet serait disproportionné.

**Une reprise volontairement écartée** : le repli *fuzzy* d'application de patch (`patch_apply.py:231-323`),
qui tolère un déplacement de six lignes et normalise les blancs. Il est soigné — candidat unique exigé, sinon
rejet — mais un patch approximatif appliqué avec succès est exactement le risque que le splice AST supprime.
En revanche, le principe « valider tous les patchs, **puis** appliquer » (`patch_apply.py:95-106`) est repris :
aucun fichier n'est touché tant qu'un seul changement du lot peut encore échouer.

### Amendement — le snapshot est une copie d'octets, et le CAS devient gratuit

*(06:09, passe de simplification. Renverse au socle l'amendement « le snapshot est un dépôt Git fantôme ».)*

La contrainte dure n°3 dit **« son fichier cible »**, au singulier. La transaction d'une nano-étape est donc
`before = path.read_bytes()` avant, `path.write_bytes(before)` si le nœud n'est pas vert : **~10 L au lieu
des ~150 L du dépôt Git fantôme** (`git init --git-dir` hors projet, `write-tree`, `read-tree`,
`checkout-index`, capture incrémentale, comparaison de snapshots, nettoyage borné).

Et le singulier cesse d'être une convention : **`Node.target` est un `Path`, pas une liste.** Une nano-étape
qui voudrait toucher deux fichiers ne peut pas se construire.

**Conséquence en cascade :** le compare-and-swap de cette décision devient *gratuit*. On détient déjà
`before` ; comparer le contenu courant à `before` juste avant d'écrire fait trois lignes et rend le
`StaleContentError` typé. Le dépôt fantôme revient le jour où une étape devra toucher plusieurs fichiers, et
la raison de son report est écrite.

---

## Décision 10 — Traces JSONL sans projection SQLite

v1 maintenait un event store SQLite reconstructible depuis les JSONL : **612 Mo de base pour 444 551
événements**, plus un collecteur permanent, des curseurs, des migrations et une quarantaine.

Les JSONL restaient la source de vérité, et tous les diagnostics post-mortem de v1 ont été faits en lisant
les JSONL et les streams bruts — jamais la base. La projection payait un coût permanent pour un service que
le dashboard peut rendre en lisant directement les fichiers.

v2 conserve donc : JSONL append-only par mission, `live.log` suivable en `tail -F`, et `tree.json` comme état
sérialisé de l'arbre. Le frontend React de v1 est réutilisé quasiment tel quel ; la couche FastAPI est
réécrite pour lire les JSONL au lieu de SQLite — c'est le seul travail d'adaptation réel du réemploi.

### Amendement — le flag `durable`, et l'agrégat déjà écrit

**Tous les événements ne sont pas des preuves.** v1 ne faisait pas la distinction, et le collecteur a produit
un stdout de 1,3 Go en réécrivant l'inventaire des sources toutes les cinq secondes. Villani porte la
séparation dans le type lui-même (`runtime_events.py:28-34`) : chaque `RuntimeEvent` a un flag **`durable`**.
Un spinner, une progression, un « model_request_started » sont éphémères ; un tool call, une validation, une
transition de nœud sont durables. Deux enums fermées cadrent le reste — le canal (qui écoute) et le type
(quoi).

La ligne JSONL suit le même modèle (`event_recorder.py:20-33`) : `ts` + `type` + `phase` + `durable` +
`summary` + **payload brut complet**. Le résumé est à côté du brut, jamais à sa place.

Deux détails qui coûtent cher quand ils manquent : les identifiants d'événement doivent reprendre après
redémarrage en relisant le fichier (`trace_summary.py:16-51`), et les compteurs de tokens doivent pouvoir
rester `None` (`trace_summary.py:104-133`) — **un token absent n'est jamais un zéro**, sinon le dashboard
affiche des débits faux.

**Un journal tronqué se diagnostique, il ne se répare pas.** Pi détecte correctement une ligne finale
incomplète (`jsonl/storage.ts:87`) puis **réécrit le fichier** pour la supprimer (`open`, l. 210). C'est un
contre-exemple direct de la contrainte dure n°6. Nous reprenons la détection, jamais la réparation : les
octets bruts sont conservés, le fragment est diagnostiqué, et la mission reprend dans un **nouveau segment
lié au précédent**. Deux corollaires du même module : **publier sur disque avant de modifier la projection
mémoire** (`storage.ts:253`), et **scinder les JSONL sur LF uniquement** (`rpc/jsonl.ts:21`) — `U+2028` et
`U+2029` peuvent appartenir à une chaîne JSON, ce qui interdit `str.splitlines()` pour ce protocole.

**Enfin, l'agrégateur que ce choix impose existe déjà.** `aggregate_summary_from_events`
(`trace_summary.py:439-757`) reconstruit l'intégralité de l'agrégat d'un run — métriques, tool calls,
commandes, durées, statut — à partir des seuls JSONL, sans base. C'est littéralement ce que notre API doit
exécuter au démarrage pour construire son index mémoire. Il est accompagné de `validate_summary`
(`trace_summary.py:777-820`) : **l'agrégat est validé contre un contrat avant d'être servi**, parce qu'une
projection non validée est une projection fausse.

### Amendement — écrire n'échoue jamais, compter vert exige le reçu

*(06:09, passe de simplification.)*

Deux règles semblaient s'opposer : *« une panne du recorder ne casse jamais la mission »* (Villani, marquée
règle absolue) et *« publier la preuve avant la transition terminale »* (décision 13 amendée par Langfuse,
dont le contre-exemple est un `catch` qui journalise l'échec d'écriture et continue).

Elles portent sur **deux moments distincts**, et la résolution est celle-ci :

```text
écrire        →  n'échoue jamais, toute écriture d'observabilité est encapsulée
compter vert  →  exige le reçu effectivement écrit
```

C'est `_receipt_custody_failure` d'Ouroboros, déjà repris dans `verifier` : **un reçu non écrit retire
l'attestation.** L'écriture ne lève jamais ; c'est **l'absence du reçu, constatée après coup**, qui empêche
le nœud d'être vert — cause `receipt_not_written`. Une mission survit à un disque plein sans en sortir un
seul faux vert.

Le flag `durable` conserve son rôle de qualification de la preuve dans la trace ; il n'est plus le
discriminant d'un comportement d'écriture.

---

## Décision 11 — Prefect enveloppe le moteur, sans jamais le pénétrer

L'orchestration n'a jamais été le problème de v1 : 232 lignes de contrôleur, aucun des six modes d'échec
documentés n'en provient. Le premier réflexe était donc de tout garder en Python nu.

**Correction d'une objection erronée** portée initialement contre les moteurs de workflow : Prefect 3 est
impératif, pas un DAG statique. Une récursion pilotée par la donnée — décomposer un nœud puis relancer le
flow sur chaque enfant — s'y écrit directement, et les subflows imbriqués donnent même une représentation
d'arbre exploitable. L'argument « le framework impose son modèle de flow » ne tient pas ici.

Prefect est donc retenu pour ce qu'il apporte réellement : cycle de vie des tâches, retries
d'infrastructure, annulation en filet de sécurité, et une UI pour déboguer le harness lui-même.

Les coûts assumés sont nommés : poids de dépendances pour une expérience mono-machine, un second état
(la base Prefect à côté de `tree.json`), une seconde observabilité (l'UI à côté du dashboard), et une couche
de plus entre un incident et sa cause — alors que la totalité des diagnostics de v1 est venue du JSONL brut.

La règle qui rend l'arbitrage sain est une frontière stricte : **Prefect enveloppe, ne pénètre jamais.**
L'état du domaine reste `tree.json`, la preuve reste le JSONL, la sémantique de retry et le budget mural
restent dans `engine`, la frontière transactionnelle reste dans `workspace`. En particulier le budget ne
passe pas par `timeout_seconds` : la décision 8 exige une finalisation des nœuds verts à l'expiration, qu'une
annulation ne garantit pas. Le marcheur d'arbre reste du Python pur, testable sans Prefect, sous un
adaptateur mince.

Le mode `agentic` différé, lui, recevra LangGraph et `langchain-mcp-adapters` le jour où il sera activé :
c'est une vraie boucle agent↔tools, et il pourra binder les outils MCP que la campagne vient de construire —
ce qui est directement la question expérimentale 4. Il entre alors comme **exécuteur de feuille**, jamais
comme orchestrateur de mission.

Le détail de la stack est dans [`ARCHITECTURE.md`](ARCHITECTURE.md).

## Décision 12 — Le prédicat `authoritative`

Un seul prédicat détermine ce qui est **proposable, modifiable et comptable comme changement**.

`classify_repo_path` (`repo_rules.py:54-68`) range tout chemin dans cinq classes : `vcs_internal`,
`editor_artifact`, `runtime_artifact`, `generated`, `authoritative`. Rien de non-`authoritative` n'entre dans
une proposition, ne peut être écrit par un nœud, ni ne compte comme un changement produit.

Trois conséquences directes, toutes tirées d'incidents mesurés :

- **Un `.pyc` ou un `.DS_Store` touché n'est pas un changement.** `summarize_changes`
  (`state_execution.py:17-30`) sépare `intentional` et `incidental` sur ce seul critère. Sans cette
  séparation, un rapport de mission attribue au système des changements qu'il n'a pas voulus.
- **Les chemins d'artefacts runtime ne sont jamais montrés au modèle** (`context_projection.py:9-20`).
  Un modèle qui voit `~/logs/pithos2/` finit par y écrire.
- **Une proposition touchant un chemin non-`authoritative` est éliminée avant sélection**
  (`autonomy.py:716-722`), donc avant toute inference.

Le point de méthode compte autant que la règle : **un seul prédicat, partagé**. v1 avait cette logique
dupliquée dans quatre modules — `next_rush.py`, `oracle.py`, `pi_phase.py`, `campaign.py` — avec des
définitions divergentes qui ont produit des incohérences de comptage. Ici c'est une fonction de `kernel/codeview`,
importée partout, testée une fois.

### Amendement — la garde des répertoires système

Le prédicat `authoritative` décide de ce qui est proposable et modifiable **dans le workspace**. Il ne dit
rien des chemins **hors workspace**.

Or le `verifier` exécute du code écrit par le modèle en `subprocess`, et ce code n'a aucune raison légitime
de toucher `~/.prefect`, `~/Library/LaunchAgents`, la configuration Git globale ou `~/logs/pithos2/`. Une
seconde ligne est nécessaire : **une liste nommée de répertoires système et de chemins de configuration
protégés contre toute écriture**, indépendante du prédicat de workspace
(`unsloth_cli/_system_dir_guard.py:1`).

C'est la version applicative de ce que la décision 21 obtient au niveau OS. Les deux se couvrent : le sandbox
échoue en fermé si `sandbox-exec` est indisponible, la garde applicative échoue en fermé si un chemin sort de
la liste blanche.

---

## Décision 13 — Aucun succès sans preuve d'effet

**C'est la correction du mode d'échec dominant de v1** : sur dix runs `completed`, sept n'avaient produit
aucun effet. Des preflights verts sans appel au modèle et des runs terminaux déterministes étaient comptés
comme des succès, gonflant artificiellement le seul indicateur qui comptait.

Deux mécanismes indépendants, repris de Villani, ferment cette porte.

**Preuve d'effet sur le filesystem** (`autonomy.py:99-126`). Le nœud transporte ses `before_contents` — le
contenu exact des fichiers cibles avant exécution. Après, le vérificateur compare au contenu courant **et**
croise avec `git diff --name-only`. Si la cible attendue existe toujours et n'a pas changé, un finding
`FAILED_ASSUMPTION` « no effective change detected for intended target » est levé. Un nœud sans effet ne peut
plus se déclarer vert.

**Preuve d'exécution réelle** (`autonomous_helpers.py:110-120`). Un artefact de validation n'est accepté que
s'il contient littéralement `(exit=0)` avec une commande non vide. Une validation dont on n'a pas la trace
d'exécution n'a pas eu lieu. Villani va plus loin avec `meets_contract` (`autonomous_helpers.py:88-108`) : le
**type de preuve exigé dépend du type de tâche** — une tâche effectueuse doit produire un changement, une
tâche de validation doit produire un artefact d'exécution, une tâche d'inspection une conclusion.

**Et un ordre, qui manquait.** La preuve durable **précède** la transition terminale : écrire le reçu,
publier, *puis* marquer le nœud comme terminé (`evalCompletion.ts:23`). Une interruption entre les deux est
rattrapée par la réconciliation au démarrage ; l'ordre inverse produit un nœud vert sans preuve.

Le contre-exemple est dans le même dépôt et vaut d'être nommé (`codeEvalExecution.ts:363`) : un `catch` qui
**journalise l'échec d'écriture de trace et continue**. C'est acceptable pour une télémétrie secondaire, et
**inacceptable pour la preuve primaire** — si la trace de l'exécution n'a pas pu être écrite, le verdict n'est
pas attesté. Même règle que le `_receipt_custody_failure` d'Ouroboros, vue depuis sa violation.

Un troisième mécanisme mérite d'être repris pour lui-même : `_reconcile_findings`
(`autonomy.py:261-302`). **Un finding contredit par une preuve directe est retiré, et le retrait est
journalisé.** Le vérificateur peut se tromper ; la preuve filesystem gagne, mais jamais en silence.

Enfin, la détection de boucle stérile par empreinte de diagnostic (`autonomy.py:203-210`) : si le
vérificateur produit exactement le même ensemble de findings deux fois de suite, l'état est marqué
`repeated_verification_state`. **C'est le signal qui manquait aux six heures de boucle de v1** — le harness y
rejouait indéfiniment le même échec sans jamais remarquer qu'il était identique.

### Amendement — le reçu attesté par l'hôte, et trois capteurs de faux-vert

Villani donne le mécanisme brut ; Ouroboros a passé plusieurs itérations de revue adversariale **sur ce
mécanisme lui-même** et en a sorti trois choses de plus.

**Le succès et sa preuve cessent d'être deux actes séparés.** `verify_and_record`
(`our/tools/verify.py:553-850`) : le modèle *déclare* un contrat de vérification, l'hôte *exécute* la
commande **et** écrit le reçu durable, dans le même appel. Coût marginal nul, et la classe entière « le check
a tourné mais rien ne l'atteste » disparaît. Corollaire dur (`:59-66`) : **un reçu non écrit retire
l'attestation**, pas seulement l'écriture — *« ne traite pas cette vérification comme attestée »*.

**Trois capteurs de faux-vert, dont aucun ne change le verdict.** Tous écrivent un drapeau que le relecteur
lit.

1. **Masquage du code de sortie** (`:116-155`) — un tube terminal vers un filtre (`| tail`, `| grep`), un
   `|| true`, une redirection `>/dev/null` blanchissent le vrai exit. Notre suite de régression accumulée est
   faite de **commandes persistées comme donnée** : une commande avec `| tail` serait verte pour toujours.
2. **Cycle de vie des artefacts** (`:368-433`) — après le check, l'hôte re-sonde les chemins déclarés :
   attrape le check qui **construit puis supprime** le livrable qu'il vient d'attester.
3. **Provenance du critère** (`:632-641`) — `criterion_source ∈ {task_stated, agent_defined}`, **défaut
   `agent_defined`**. Chez nous un critère est toujours proposé par le modèle, mais le `seed` et les
   invariants de régression accumulés sont `task_stated` : **la distinction porte directement la question
   expérimentale n°4**.

Un quatrième détail vaut d'être nommé : deux bornes distinctes (`:44-49`), l'une pour la **preuve durable**,
l'autre pour le **transport vers le modèle**. La preuve n'est jamais bornée par le budget de contexte.

**Un point où nous divergeons volontairement.** Ouroboros fait de l'absence de reçu un drapeau *advisory* qui
garde le résultat `solved` — *« never a downgrade — anti-oscillation »*. Nous faisons l'inverse, et les deux
positions sont défendables pour des raisons différentes : Ouroboros tourne sur des modèles frontières et
craint l'oscillation acceptation/révision ; nous tournons sur un 8B dont le mode d'échec **mesuré** est le
succès fantôme. Notre gate dure reste la bonne, mais il faut accepter le coût qu'Ouroboros nomme — des nœuds
qui refont un travail déjà fait parce que la preuve n'a pas été captée — et reprendre son remède : **le
drapeau est binaire et ne s'accumule pas.**

### Amendement — `verifier` possède le reçu, et n'a d'I/O que sur ce qu'il a produit

*(06:09 — arbitrage de frontière : trois modules touchaient le reçu, aucun ne le possédait.)*

Le reçu était produit par `verifier`, attesté par l'hôte, écrit par la couche de trace, publié par `engine`.
Quatre modules, aucun propriétaire — la configuration exacte qui produit une divergence de définition,
comme le prédicat `authoritative` éparpillé dans quatre modules de v1 (décision 12). La règle retenue :

> **`verifier` n'a d'I/O que sur ce qu'il a lui-même produit** — le script d'invariant qu'il vient
> d'écrire, le process qu'il vient de lancer.
> **L'état du monde lui arrive toujours comme fait typé.**

| Fait | Fourni par | Forme |
|---|---|---|
| contenu avant / après de la cible | `workspace` | chemin, empreintes, plage splicée, bilan chiffré du remplacement |
| `git diff` et `git status` | `broker` | fichiers touchés, lignes ajoutées et retirées |
| attestation d'hôte, horloge monotone, ancre de démarrage | `lifecycle` | identité de machine, PID + heure de démarrage |
| artefact d'exécution de l'invariant | **`verifier` lui-même** | script rendu, code de retour, sortie bornée tête + queue |

`verifier` ne lit donc jamais un fichier du workspace et n'appelle jamais git. Deux conséquences, toutes
deux voulues : le module le plus critique du projet **se teste intégralement avec des faits en dur**, et il
reste structurellement au-dessous de tout ce qui a des effets — c'est l'inversion qui fonde l'architecture,
poussée jusqu'à son I/O.

Le **type** du reçu vit dans `kernel`, qui est le vocabulaire. **L'autorité de l'émettre appartient à
`verifier` seul** : aucun autre module n'écrit un reçu.

### Amendement — les trois capteurs de faux-vert sont écartés comme inapplicables

*(06:09, passe de simplification.)*

Les trois capteurs supposent un agent qui **compose ses propres commandes shell** et **écrit ses propres
assertions**. La contrainte dure n°1 et la décision 6 ont supprimé les deux.

| Capteur | Ce qu'il attrape | Pourquoi il n'a pas de sujet |
|---|---|---|
| **1 — masquage d'exit** | `\|\| true`, `>/dev/null`, tube terminal vers un filtre | le script d'invariant est **rendu par le harness**, jamais par le modèle |
| **2 — cycle de vie d'artefact** | build-puis-delete | subsumé par la preuve d'effet contenu avant/après croisée avec `git diff` |
| **3 — `criterion_source`** | qui a écrit le critère | structurellement constant : relation d'un catalogue fermé, entrées générées par le harness |

**~250 L évitées**, réactivables si le mode `agentic` s'ouvre — c'est là que la menace redevient réelle.
La garde est portée seule par l'amendement précédent : un reçu non écrit retire l'attestation.

Deux reprises du même fichier sont **gardées**, parce qu'elles ne dépendent d'aucun modèle de menace :
**aucune coercition `or` sur un code de retour** — `None or 0` lisait un résultat inconnu comme un succès —
et `cmp` où **`>1` signifie panne d'outillage**, pas différence.

---

## Décision 14 — Le contexte est un objet inspectable, pas une chaîne

v1 assemblait le contexte par concaténation sous budget et n'en gardait aucune trace. Quand un brief périmé a
produit **12 419 `thinking_delta` consécutifs et zéro tool call**, rien dans les traces ne permettait de voir
que le contexte était contradictoire : il a fallu lire le stream Pi brut.

v2 reprend la gouvernance de contexte de Villani (`context_governance.py`), qui traite le contexte comme un
inventaire typé plutôt que comme un texte.

- **Chaque élément porte la raison de sa présence ou de son absence** — `ContextInclusionReason`
  (`task_relevance`, `plan_target`, `memory_signal`, `validation_signal`, `repair_signal`,
  `checkpoint_handoff`) et `ContextExclusionReason` (`irrelevant`, `budget_pressure`, `duplicate`, `stale`).
  Deux enums fermées, l. 11-31.
- **La pression est mesurée et graduée** (l. 252-266) : `total / limite`, quatre paliers — `low` sous 0,45,
  `moderate` sous 0,75, `high` sous 1,0, `overflow_risk` au-delà. Avec Ling plafonné à 16k, ce cadran est
  vital, et chaque élément porte sa `pressure_share`.
- **Chaque éviction est enregistrée et comptée** (l. 200-208, `pruning_events`).
- **La dérive est détectée activement** (l. 210-220) : `detect_stale_context` lève des signaux nommés —
  mode docs avec fichiers de code, **réparations répétées avec contexte gonflé**, contexte multi-sources.
  C'est le capteur qui aurait attrapé l'incident de v1 avant qu'il ne coûte 26 minutes de sessions à vide.
- **Le compactage préserve le signal** (l. 83-122) : un compacteur par type de source, chacun avec ses
  tokens de signal, jamais une troncature aveugle. Et côté messages, un `tool_use` et son `tool_result` sont
  inséparables (`context_budget.py:82-93`) tandis qu'un contenu portant `@@` ou `diff --git` n'est jamais
  compacté (`context_budget.py:204-205`) — **un diff résumé est un diff faux**.

Le paquet de contexte est construit **structuré** puis rendu en texte séparément
(`context_projection.py:23-70`). Le paquet est traçable et sert le dashboard ; le rendu est jetable.

### Amendement — la séparation est la forme du contrat, pas un traitement

Six sources nous ont dit de séparer le *thinking* du contenu exploitable. SWE-agent va un cran plus loin :
son `StepOutput` (`types.py:15-31`) sépare `query`, `thought`, `action`, `output`, `observation`,
`execution_time`, `exit_status`, `state` et `thinking_blocks` en **champs typés distincts**, jamais
concaténés — et son `HistoryItem` impose un `message_type` en littéral fermé
`{"thought", "action", "observation"}`.

**Un `StepOutput` mal formé est alors rejeté par le type, pas par une heuristique de parsing.** C'est la
différence entre « on extrait le contenu utile de la réponse » et « la réponse a une forme, et elle la
respecte ou elle est rejetée ».

Détail de rendu qui compte : `to_template_format_dict` (`:33-41`) **exclut explicitement** `tool_calls`,
`tool_call_ids` et `state` du dictionnaire de formatage tout en aplatissant `state` à la racine. **Ce qui
sert au template et ce qui sert à la machine ne sont pas le même objet** — les confondre est ce qui fait
qu'un identifiant de tool call finit dans un prompt.

### Amendement — le dump de contexte remplace la compaction

*(06:09, passe de simplification.)*

`PROJECT.md` dit *« contexte borné, **session neuve**, vérification hors modèle »*. Chaque nœud reçoit donc
un contexte assemblé de zéro : **il n'y a aucune conversation à compacter.** Et il y a une raison plus forte
que l'inapplicabilité — **un résumé est du texte produit par le modèle qui entre dans le prompt suivant**,
soit exactement la dérive de contexte qui a produit les 12 419 `thinking_delta` de v1. Le contrat de
résumeur haché d'Ouroboros existe précisément parce qu'un résumé n'est pas fiable.

**Dans la session : évincer, jamais résumer.** Sous pression on évince avec raison enregistrée ; si le
contenu irréductible dépasse le budget, le nœud est `blocked` avec cause mécanique. Un nœud bloqué est un
signal exploitable ; un résumé approximatif est une dette invisible.

**À la fin de la session : un artefact de passation.**

```text
~/logs/pithos2/missions/<mission_id>/CONTEXT.md
```

Un fichier par mission, **une section ajoutée à chaque fin de session** — nœud, critère, inclusions et
exclusions avec leur raison, palier de pression, évictions, verdict, et **l'empreinte des fichiers décrits au
moment de l'écriture**. **Écrit par le harness, pas par le modèle** : l'inventaire typé existe déjà, le
rendre en markdown est déterministe et coûte ~30 L.

**L'empreinte n'est pas décorative.** Le mode d'échec n°2 mesuré de v1 était un brief décrivant une fonction
déjà mergée. **Un fichier de suivi réinjecté a exactement cette forme.** Il est donc traité comme n'importe
quel élément de contexte — sélectionné sous budget, avec une raison d'inclusion, soumis à
`detect_stale_context` — et une section dont l'empreinte a bougé est **exclue avec sa raison**, jamais
injectée en silence.

Écartés : compacteur par type de source, contrat de résumeur haché, unités `tool_use`/`tool_result`
inséparables. **~150 L.**

---

## Décision 15 — Ce que Villani prouve, et ce qu'on n'en reprend pas

`resources/villani-code-main/` est un runtime d'agent codant local-first de 21 512 lignes. Il défend
littéralement notre thèse — *« small models do not just need better weights. They need a better runtime »*
(`README.md:9`) — et il la chiffre :

| Résultat | Source |
|---|---|
| Terminal-Bench 2.0 : **44,0 %** avec Qwen3.6 27B, contre 40,1 % pour Claude Code + Sonnet 4.5 | `README.md:13-31` |
| À modèle identique (Qwen3.5 9B) : **63,3 %** contre 43,3 % — 6 tâches gagnées, 0 perdue | `README.md:53-73` |

C'est la meilleure preuve externe disponible que l'hypothèse retenue au cadrage est mesurable, et elle rend
l'entreprise nettement moins spéculative qu'elle ne l'était après l'audit de v1.

**Ce que Villani n'a pas, et qui reste notre apport propre :** aucun invariant métamorphique, aucun
mutation-check, aucune sortie contrainte par JSON Schema, aucun catalogue de relations fermé. Sa validation
est « exécuter les commandes du repo et lire le code de retour ». Les décisions 2 et 3 — le cœur du projet —
sont sans équivalent chez lui. Ce qu'il apporte, c'est **tout ce qui entoure ce cœur** : quoi valider,
comment exécuter, comment rendre un échec lisible à un 8B, et comment ne jamais confondre une absence
d'effet avec un succès.

**Ce qu'on n'en reprend délibérément pas :**

- Les trois monolithes `state.py` (2 073 L), `state_runtime.py` (1 427 L) et `autonomous.py` (1 307 L),
  construits autour d'un objet `Runner` que tout traverse — `state_runtime.py` prend `runner: Any` en premier
  argument dans une trentaine de fonctions. C'est le paradigme boucle-d'agent que la décision 6 supprime.
  **Piocher les notions, jamais l'ossature.**
- L'extraction de symboles Python **par regex** (`indexing.py:57-66`) : l'erreur exacte de v1, celle qui a
  coûté l'incident d'arité `smooth_levels(0.0, 0.0, 0.0)`. Notre `codeview` utilise l'AST.
- Le repli fuzzy d'application de patch, la TUI Textual, le harnais de benchmark multi-agents, le client
  Anthropic et l'UX de session interactive.

Le registre complet de l'héritage — catalogue des ~90 reprises, ce que chacune a changé dans la
documentation, ce qui est écarté et pourquoi — est dans [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md).

Une convergence mérite d'être notée : `pyproject.toml:11-19` liste `typer`, `httpx`, `pydantic`, `pyyaml` —
trois de nos quatre choix transverses, arrêtés indépendamment avant lecture du dépôt. Et son client
OpenAI-compatible (`openai_client.py`) est directement réutilisable pour notre `bridge` : il ne lui manque que
`response_format`, à insérer en `openai_client.py:75-86`. **C'est exactement le point du spike n°2.**

Le projet est personnel et la copie est libre : l'absence de fichier `LICENSE` dans l'archive n'est pas un
obstacle et ne conditionne aucune reprise.

---

## Décision 16 — Persister l'intention avant l'effet externe

**La décision qui rend la reprise possible.** Avant tout appel modèle et toute modification de fichier, le
harness écrit son intention : tentative, identifiant, cible, digest attendu, état visé.

Sans cela, une trace *a posteriori* ne sépare pas trois situations pourtant incompatibles :

| État | Signification | Action à la reprise |
|---|---|---|
| non commencé | l'intention est écrite, aucun effet | rejouer |
| **effet inconnu** | l'intention est écrite, l'effet a pu avoir lieu | **interroger, jamais rejouer aveuglément** |
| résultat enregistré | l'effet et son verdict sont persistés | continuer |

Le corollaire opérationnel est plus dur qu'il n'y paraît : **un appel interrompu ne prouve pas que son effet
n'a pas eu lieu.** Une lecture est rejouable sans risque ; une écriture est à réconcilier contre le digest ;
une publication Git doit être **interrogée par identifiant** avant toute nouvelle tentative — sinon deux
réveils peuvent produire deux PR pour un seul travail. L'autorisation de rejouer appartient au harness,
jamais au modèle.

**La face amont du même contrat : le claim idempotent.** Interroger avant de rejouer traite le cas où
l'effet a déjà eu lieu ; le claim traite celui où la demande arrive deux fois. Une demande d'effet à identité
connue — lancement d'un nœud enfant, promotion d'un outil au statut `verified`, création d'une PR — est
**réclamée avant d'être exécutée**, et une seconde réclamation du même identifiant est un no-op
(`child-conversation-launch.ts:205`). Les deux mécanismes se complètent : le claim empêche le doublon en
entrée, l'interrogation le rattrape en sortie.

**Le fencing complète le claim.** Langfuse (`runLifecycle.ts`) durcit trois points que ni le claim
idempotent ni l'interrogation ne couvrent :

- **le heartbeat retourne une perte de propriété explicite** (`:64`), pas un booléen ambigu — après perte, on
  arrête les écritures et on propage l'annulation. Savoir qu'on a perdu la main est aussi important que
  savoir annuler ;
- **la classification de péremption est pure et à quatre causes** (`:702`) — délai de queue, durée maximale,
  heartbeat perdu, approbation expirée — et **la durée maximale l'emporte sur le heartbeat** : un nœud qui bat
  encore mais dure trop est périmé quand même ;
- **la réconciliation ne réapplique une transition que si l'état observé n'a pas changé** depuis la lecture
  (`:673`). **Une lecture de nœud périmé ne donne pas le droit de tuer une nouvelle incarnation** — c'est
  exactement le risque des deux réveils launchd rapprochés que la décision 27 nomme.

Réserve reprise telle quelle : **un CAS de statut n'est pas à lui seul un jeton de propriété.** Il faut la
génération.

La réconciliation vit sur un **chemin distinct du chemin nominal**, et l'état est vérifié avant tout effet :
ids, parenté, statut, références aux snapshots et verdicts. Un état contradictoire est **bloqué avec cause**
— il n'est pas corrigé en relançant le modèle. C'est la contrepartie de la contrainte dure n°4 : une mission
bornée qui sort en cours de route doit pouvoir reprendre sans jamais dupliquer un effet.

Sources et détail : [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § B2.2.

---

## Décision 17 — La frontière du modèle a quatre pièges nommés

La décision 2 pose que le modèle n'émet que des énumérations et des noms de symboles. Quatre mécanismes
concrets font tenir cette frontière — leur absence la ferait retomber en silence.

**La contrainte de décodage est requise, jamais préférée.** Un mode `prefer` désactive la contrainte quand le
provider ne la supporte pas ; un mode `require` échoue. Pour `Criterion` et `Proposal`, seul le refus
explicite est acceptable : un repli silencieux ferait passer une sortie libre pour une sortie contrainte,
sans qu'aucune trace ne le signale. **C'est exactement ce que le spike n°2 doit mesurer sur `/v1`.**

**Le thinking n'est pas du contenu.** Les champs `reasoning_content`, `reasoning` et `reasoning_text` sont
distincts du contenu final. `Criterion` et `new_source` ne s'extraient **que du contenu désigné**, jamais
d'un bloc de raisonnement ni d'une concaténation de toutes les chaînes de la réponse. Sur un modèle capable
de produire 12 419 `thinking_delta` d'affilée quand il est bloqué, ce n'est pas une précaution théorique.

**Une terminaison doit être explicite.** Un socket fermé avec du JSON syntaxiquement plausible n'est pas une
réussite. `length`, `error` et toute sortie tronquée sont des échecs ; la cause brute est conservée, et un
`finish_reason` inconnu reste un échec explicite plutôt qu'un succès par défaut.

**Le budget réserve la place de la sortie avant l'appel.** Budget = entrée + schéma + instructions + sortie +
marge. **Si le contrat obligatoire ne tient pas dans la fenêtre, l'appel est refusé** — il n'est pas tenté
avec l'espoir que ça passe. Sur Ling 16k, la marge se mesure au spike, et le thinking doit être borné pour
ne pas consommer la réponse.

**`response_format` est une intention, pas une garantie — et c'est le point le plus important de cette
décision.** Ouroboros le documente noir sur blanc (`our/llm.py:2241-2250`) : sur les routes
OpenAI-compatibles, `response_format` est une *intention de requête* ; certaines routes **l'ignorent**, et un
rejet du fournisseur **le retire** via la ladder de retry — il figure littéralement dans
`_OPTIONAL_DROPPABLE_PARAMS` (`:183-186`).

**La contrainte dure n°1 ne peut donc pas reposer sur le décodage contraint côté serveur.** Elle repose sur
une **revalidation locale contre le schéma exact envoyé**, obligatoire quoi qu'il arrive
(`request_wire_custom_validation.py:107-170`), avec un reçu liant quatre digests — requête, catalogue, schéma,
arguments — et cinq codes d'erreur fermés plutôt qu'un booléen.

La règle qui l'accompagne mérite d'être citée : *« validation failure may prove wire acceptance but cannot
authorize tool execution »*. **L'acceptation par le transport n'est pas une autorisation d'exécution.**

Un détail d'une ligne ferme une classe entière : `json.loads` accepte `NaN`, `Infinity` et `-Infinity` par
défaut (`:85-87`). Un modèle qui émet `NaN` dans un domaine de génération franchirait un parse naïf et
atteindrait Hypothesis.

**Le backend est vérifié avant la mission, pas pendant.** Le `bridge` suppose Ollama joignable et
compatible ; rien ne disait ce qui se passe si le serveur est plus ancien que ce que le contrat exige.
OpenHands écrit la règle (`agent-server-compatibility.ts:19,81`) : une **version minimale compatible**, des
codes d'erreur fermés, et un **refus avant toute mission**. Trois points de forme : une **version inconnue est
un état distinct, jamais la version courante** (`:95`) — même famille que « un token absent n'est jamais un
zéro » ; la comparaison est **sémantique**, jamais lexicographique (`:252`) ; et une erreur typée distingue
**backend absent, backend indisponible et détail de connexion** (`:50`), au lieu d'un « Ollama ne répond
pas » qui recouvre un serveur éteint, un port occupé et un modèle non chargé.

**Le schéma doit être normalisé avant d'être contraint.** Pydantic v2 émet des `$defs` et des `$ref` pour
toute enum et tout modèle imbriqué — donc pour `Criterion.relation`, `Criterion.domain` et toute structure de
`Proposal`. Les backends de décodage contraint s'en accommodent mal, et un `integer` sans bornes fait échouer
certaines grammaires. **`Criterion.model_json_schema()` ne peut donc pas être envoyé tel quel.** La
normalisation (`opencode/src/tool/json-schema.ts:28-88`) doit être écrite et testée **avant** de mesurer
`response_format` avec Ling : c'est un prérequis du spike n°2, pas une optimisation.

S'y ajoute un raccordement direct à la décision 11 : **les retries implicites du client sont désactivés.**
`engine` décide du retry et de son budget. Sans cela on empile SDK × bridge × Prefect — trois couches qui
retentent sans se connaître, et un `503` transitoire devient huit requêtes.

Sources et détail : [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § B2.3.

### Amendement — pas de streaming, et aucune abstraction de fournisseur

*(06:09, passe de simplification.)*

En mode `direct`, `bridge` fait **un** appel borné et attend **un** objet JSON. Pi énonce lui-même la règle
qui rend le flux inutile ici : *« ne jamais exécuter un JSON partiel ou réparé »*. Et **l'incident de
contexte le plus grave de v1 était un incident de streaming** — 12 419 `thinking_delta` consécutifs, zéro
tool call.

Un `POST` bloquant, timeout 300 s, réponse complète revalidée localement. **~10 reprises écartées** :
parsing SSE, terminaison explicite de stream, deltas linéaires, séparation thinking/contenu *au niveau du
flux*, erreur de stream en exception structurée. Le cinquième piège de la décision 17 — thinking ≠ contenu —
**reste obligatoire**, mais s'applique à la réponse complète : trois lignes au lieu d'un parseur
d'événements. Le signal de vivacité vient de la borne murale et d'une ligne d'attente dans `live.log`.

**Et rien n'abstrait un fournisseur unique.** Écartés : transformations par fournisseur derrière une
frontière, sélection de prompt par famille de modèle, et `convert_openai_response_to_anthropic` — **du legacy
v1, puisque aucun chemin Anthropic n'existe**. Écartés aussi, pour une raison plus simple encore, tous les
mécanismes de credential — headers d'auth, `route_fingerprint` excluant les secrets, résolution de clé par
priorité : **Ollama local n'a aucune authentification.**

La sonde d'avant-campagne tombe de ~200 à ~40 L : lire `n_ctx_train` sur `/v1/models`, envoyer **un** schéma
`Criterion` réel et vérifier qu'il revalide, refuser de démarrer sinon. La fenêtre porte sa provenance en
enum à trois valeurs, `unprobeable` étant fail-closed. Écarté : `test_tool_calling`, qui sonde une capacité
que le mode `direct` n'utilise pas.

---

## Décision 18 — Annuler une attente ne tue pas l'opération

Une course entre une opération et un timeout **rend la main sans prouver l'arrêt de l'I/O**. Il faut fermer
explicitement le stream ou le client, puis vérifier la fin. Cette distinction conditionne la borne murale
réelle de la décision 8 : une mission qui « sort » à 20 minutes alors que trois requêtes sont encore en vol
n'a pas la propriété qu'on lui prête.

Le même piège existe côté filesystem, et il est plus grave. Libérer le verrou d'écriture à l'annulation
alors que l'écriture peut encore se terminer permet une **écriture tardive qui atterrit après le rollback**.
Notre décision 9 promet une restauration à l'octet près ; elle est fausse tant qu'on n'attend pas la fin
réelle de l'effet avant de restaurer. Le cas se teste explicitement, par intercalation — pas par relecture
du code.

Corollaire côté `engine` : **fermer l'admission de nouveaux effets avant de propager l'annulation.** À
l'expiration de la borne, on cesse d'admettre, puis on finalise ce qui est vert, dans cet ordre.

Sources et détail : [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § B2.4.

---

## Décision 19 — Le registre est indexé par empreinte de contrat

Un outil est identifié par **le hash de son contrat canonicalisé**, pas par le nom que le modèle a proposé.

Cela ferme une classe de redondances que le rejet lexical de la décision 5 laisse passer : deux propositions
portant des noms différents pour le même couple (schéma d'entrée, schéma de sortie) collisionnent
mécaniquement, sans dépendre d'un seuil de similarité ni d'une table d'alias. La canonicalisation JSON
préalable est la brique qui rend cette comparaison fiable — c'est elle qui manquait au critère « schémas
structurellement identiques » posé en décision 5.

Trois compléments pour l'auto-extension de la décision 7 : **provenance explicite de chaque ressource**,
**collisions nommées avec gagnant et ressource ignorée** — un écrasement silencieux est un bug, pas une
politique — et **vérification d'intégrité avant d'activer une nouvelle génération**. Un outil n'entre dans la
couche `managed` de la configuration MCP qu'après contrôle.

Une dernière reprise mérite d'être signalée pour ce qu'elle valide : `extensions.eval.ts:110` prouve
**création, chargement et appel effectif** d'une capacité produite par l'agent. C'est littéralement notre
question expérimentale 4, avec son patron de test déjà écrit.

Sources et détail : [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § B2.5.

### Amendement — l'empreinte sert aussi à la proposition, pas seulement à l'outil livré

*(06:09)*

L'empreinte de contrat indexait le registre des outils **vérifiés**. Elle devient le second temps de la
détection de redondance d'une **proposition** (décision 5 amendée) : même canonicalisation, même clé,
appliquée plus tôt dans le cycle. Une seule fonction d'empreinte, deux points d'appel — et c'est
précisément parce qu'elle est unique qu'elle reste une relation d'équivalence (décision 22).

---

## Décision 20 — Le prompt et les paramètres de Ling sont des données mesurées

Kilo Code maintient une famille `ling` de bout en bout : détection de famille, prompt système dédié de
129 lignes, et trois paramètres d'échantillonnage. **Notre modèle de campagne est exactement de cette
famille, et notre architecture ne fixait aucun paramètre.**

| Paramètre | Valeur | Source |
|---|---:|---|
| `temperature` | **0.3** | `opencode/src/provider/transform.ts:605` |
| `top_p` | **0.95** | `opencode/src/provider/transform.ts:617` |
| `top_k` | **20** | `opencode/src/provider/transform.ts:629` |

Retenues telles quelles jusqu'à contre-mesure. Le point de méthode compte autant que les valeurs : **elles
sont versionnées comme une donnée du projet**, pas dispersées dans le code, et toute modification exige une
contre-mesure.

`prompt/ling.txt` est mieux qu'un prompt : c'est un **catalogue daté de modes d'échec observés sur Ling**,
chacun avec sa contre-mesure. Sept nous concernent, y compris en mode `direct` où le modèle n'a pas de tools.
Deux touchent le chemin nominal et doivent être traités avant la première ligne du `bridge` :

- **Ling recopie les préfixes `N: ` de numérotation de lignes dans son payload** (`ling.txt:109-115`). Notre
  `codeview` rend des lignes numérotées — le splice AST doit **strip ces préfixes de `new_source` avant
  parse**, sinon chaque nœud échoue silencieusement pour une raison qui n'a rien à voir avec la tâche.
- **Ling tronque le code qu'il génère** (`ling.txt:23`). Confirme la distinction `length`/`stop` de la
  décision 17 et impose une garde de complétude : un `def` tronqué peut rester syntaxiquement valide.

Un troisième est structurant : **sur « No changes to apply », Ling retente ou cherche autre chose à
changer** (`ling.txt:84`). C'est le générateur de la boucle stérile de v1, documenté indépendamment sur le
même modèle. Notre garde est déjà posée — décision 13, un patch sans effet est un nœud rouge immédiat — et
cette observation la rend non négociable.

Deux notions de rédaction transposables : la **politique de longueur conditionnelle à la tâche**
(`ling.txt:22-25`) — une consigne « sois concis » unique est précisément ce qui fait tronquer un petit
modèle — et le « planning before coding » (`ling.txt:49-59`), qui est notre phase `decompose` formulée en
prompt.

Détail des sept modes : [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § C1.2.

---

## Décision 21 — Confinement d'exécution sans conteneur

Le `verifier` exécute du code écrit par le modèle en `subprocess`. `PROJECT.md` a écarté le **runtime
conteneurisé** — mesuré inexploitable sur ce matériel en v1 — mais cette exclusion ne portait pas sur le
confinement natif, et la distinction n'avait pas été faite explicitement.

`kilo-sandbox/` fournit `sandbox-exec` macOS : natif, zéro installation, et **le profil de base — la partie
coûteuse à dériver — est fourni** (`seatbelt-base.ts:1-4`). Il est doublé d'une garde in-process sur chaque
opération d'écriture, avec refus des descripteurs de fichier inscriptibles (`filesystem.ts:107-158`) : le
sandbox OS et la garde applicative se couvrent mutuellement.

**Placé en P7**, parce qu'il conditionne l'exécution autonome non supervisée et non le socle. Il remonte en
P2 si le premier réveil supervisé montre que le `verifier` exécute du code produit touchant des chemins
inattendus — auquel cas ce n'est plus une précaution mais une correction.

### Amendement — le confinement a une dimension réseau

Le profil seatbelt porte aussi une politique réseau, et nous ne l'avions pas nommée. **Le code produit
exécuté par le `verifier` n'a aucune raison légitime d'ouvrir une socket** : la politique est donc *refus par
défaut*.

La seule exception envisageable — un outil MCP dont le cœur ferait un appel réseau — est précisément ce que
la décision 4 interdit : le cœur est pur, la coquille porte l'I/O, et **la coquille n'est pas ce qui tourne
sous invariant**. Un invariant qui aurait besoin du réseau pour passer n'est pas un invariant.

### Amendement — le confinement reste, la permission part

*(06:09, passe de simplification.)*

Deux sous-domaines voisins, deux sorts opposés, et la phrase qui les sépare :

> **Le modèle n'émet aucune commande — donc il n'y a rien à autoriser.**
> **Mais son code *est* exécuté — donc le confinement reste nécessaire.**

En mode `direct`, le modèle émet `{function_name, new_source}` et `{relation, symbols, domain}`. Le seul
subprocess du projet est le script d'invariant que le harness a rendu lui-même.

**Écartés** : `PermissionEngine.evaluate_with_reason` (deny → ask → allow), `classify_bash_command` par
préfixe de tokens, `bash_matches` conscient des opérateurs, **l'arité des commandes shell — 161 L chez
Kilo**, le découpage d'une ligne shell, les permissions de sous-agent. **~200 L**, raison écrite,
réactivables avec le mode `agentic`.

**Gardé** : tout le confinement `sandbox-exec` et sa phase P7bis — `new_source` finit dans un `subprocess`,
et c'est une menace réelle, pas hypothétique.

---

## Décision 22 — Une identité est une clé typée, jamais une chaîne de repli

Un reçu rouge doit pouvoir être réconcilié par un vert ultérieur **de la même vérification**. Une proposition
rejetée doit pouvoir être reconnue comme identique à une proposition antérieure. Les deux problèmes ont la
même forme, et Ouroboros a mesuré ce qui arrive quand on la traite par une chaîne de repli — matcher sur un
identifiant, sinon sur un texte, sinon sur un ensemble de chemins :

> *A chain is not an equivalence relation. It was not transitive — `{c1, check}` matched `{check}`,
> `{check}` matched `{c2, check}`, while `c1` and `c2` are explicitly different criteria — so one check-only
> green reconciled two distinct reds, and the outstanding set came out order-dependent. **No care at the call
> sites can repair a relation that is not an equivalence.***

La forme retenue est **une seule clé typée `(kind, value)`**. Le `kind` est la chose la plus spécifique que
l'enregistrement porte réellement ; une fois le `kind` choisi, aucun second composant n'est consulté. Deux
enregistrements nomment la même chose quand `kind` **et** `value` coïncident, jamais entre kinds. La relation
devient le noyau d'une fonction — réflexive, symétrique, transitive par construction — et elle échoue dans la
**direction sûre** : strictement moins de réconciliations, donc un rouge que la chaîne effaçait peut rester
ouvert.

**Cette décision remplace la formulation par seuil des décisions 5 et 19.** Notre rejet de redondance avait
exactement la forme d'une chaîne — nom, puis schémas, puis recouvrement lexical — avec exactement le même
risque de non-transitivité.

Trois raffinements, chacun né d'un incident réel :

- **Le rendu d'un texte fait partie de son identité.** Passer de `" ".join(argv)` à `shlex.join` corrige la
  non-injectivité (`["echo","a b"]` et `["echo","a","b"]` rendaient la même chaîne) mais **rouvre le trou
  dans l'autre sens** : un ancien enregistrement et un nouveau, écrits par deux rendus différents, se lisent
  pareil. La solution est un **tampon de version du rendu** stocké à côté du texte, toute valeur inconnue
  étant son propre espace de noms — un futur rendu devient automatiquement incomparable, sans modification de
  code.
- **La normalisation ne jette jamais un octet dont l'identité dépend.** Dédupliquer et trier, *et rien
  d'autre* : un espace de fin est un octet légal de nom de fichier, et le rogner a laissé une observation de
  `"a.md"` fermer une observation de `"a.md "`. L'ordre est **canonicaliser → rendre → borner**, jamais rendre
  → dédupliquer, parce que le rendu est lossy : dédupliquer après lui jette des valeurs distinctes pendant que
  le compteur d'omissions annonce zéro.
- **Ce qui décide doit être ce qui est rapporté.** Décideur et rapporteur appellent la même fonction de
  projection. Une preuve attestée par l'hôte qui **ment sur sa propre base** est précisément la classe de
  défaut que cette surface existe pour éliminer.

Et une règle de table : le catalogue des kinds est **total**, y compris pour le kind « aucune identité ». Un
kind ajouté sans sa ligne lève une erreur au lieu de retomber sur un défaut — la gate qui fonctionne. Enfin,
deux enregistrements **sans clé** ne sont jamais égaux, **même entre eux** : indiscernables n'est pas
connu-égal.

Sources : [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § D2.3.

---

## Décision 23 — Le résultat n'est pas un statut, c'est un produit d'axes

Notre `Node.statut` est une énumération plate. Ouroboros (`our/outcomes.py:83-244`) sépare le résultat d'une
tâche en **six axes** — `lifecycle`, `execution`, `objective`, `review`, `artifacts`, `verification` — plus
l'absorption des enfants.

L'intérêt n'est pas la granularité pour elle-même, il est dans les **vocabulaires de non-échec**
(`:284-295`) : un blocage de politique, une sortie cosmétique, un outil qui répond honnêtement `{"ok": false}`
— un diagnostic qui rapporte ce qu'on lui a demandé de trouver — **ne sont pas des échecs**. Chacun de ces cas
a été mesuré en train de se faire passer pour une panne d'outil.

Notre métrique de campagne est « outils vérifiés livrés / cycles consommés ». Sans cette séparation, trois
cycles très différents comptent identiquement comme échec :

| Cycle | Ce que c'est réellement |
|---|---|
| Ollama injoignable | une panne d'infrastructure |
| proposition rejetée comme redondante | **un succès du garde-fou** |
| critère tautologique rejeté par le mutation-check | **un succès du garde-fou** |

Compter les deux derniers comme des échecs rend l'indicateur central du projet illisible, et pousse
mécaniquement à affaiblir les gates pour « améliorer le taux ». La séparation en axes est donc une condition
de validité de la mesure, pas un raffinement.

Sources : [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § D2.4.

---

## Décision 24 — Le filtre de pression interne

`BIBLE.md:412-429` — le test qu'aucun critique persistant ne peut contourner :

> *Does the proposed change make a class of failure structurally impossible, or does it weaken the immune
> system to remove friction? If the latter — decline or redesign before acting.*

Et la règle qui l'accompagne : **auto-initié ne veut pas dire auto-exempté.** Une idée que le système génère
lui-même passe par les mêmes filtres qu'une demande externe.

Notre campagne propose ses propres outils et sa propre fin. La décision 5 rejette une proposition
**redondante** ; rien ne rejette une proposition qui **retire une gate**. C'est le prédicat manquant, et il
est d'autant plus nécessaire que la pression est structurelle : un système jugé sur « outils vérifiés livrés »
a un gradient permanent vers l'assouplissement de ce qui définit « vérifié ».

Concrètement, une proposition est rejetée si elle touche un chemin du harness plutôt que du produit, si elle
propose de retirer ou d'assouplir un invariant de la suite de régression accumulée, ou si elle réduit la
surface d'une gate existante. Le rejet est mécanique et antérieur à toute inference, comme les autres.

Une contrepartie honnête, reprise du même corpus : **certaines opérations doivent être exemptes de gate**
(`BIBLE.md:707-726`). Un rollback mécanique restaure un état déjà vert ; le soumettre aux gates piégerait le
harness avec du code cassé qu'il ne peut pas annuler.

---

## Décision 25 — Discipline de dépôt : le ratchet de taille

`ARCHITECTURE.md` visait « ~3 000 lignes de harness » — la cible est passée à ~5 900 le 06:09 puis à ~5 230
après la passe de simplification, voir l'amendement en fin de section — et ajoutait honnêtement *« ordres de grandeur cibles, pas des mesures »*.
**Rien ne l'applique.** C'est exactement la forme d'engagement que v1 a tenu jusqu'à 8 000
lignes sans qu'aucun signal ne se déclenche.

Le ratchet (`our/review.py:292-830`) rend la cible mécanique : un manifeste **généré** de la dette de taille,
avec transition **shrink-only** vérifiée par une gate de test. Module cible ~1 000 lignes, gate dure au-delà,
bande intermédiaire à **justification obligatoire et immuable** dont l'abandon « blanchit la justification »,
comptes d'octets qui ne peuvent que décroître, et **correspondance exacte avec l'inventaire vivant** — une
entrée périmée est une erreur au même titre qu'une entrée manquante.

La règle de comportement vaut autant que la gate :

> *Treat a size gate as pressure to reduce total complexity, not as a design reason for a helper or sibling
> module. Relocating the same complexity, or stripping contract-bearing comments, diagnostics, or tests to
> buy bytes, is not paydown. If neither a safe simplification nor a natural boundary exists, **report the
> ratchet conflict instead of gaming or silently raising the cap**.*

À lire les yeux ouverts : le manifeste d'Ouroboros compte 49 chemins géants, dont un module de 6 379 lignes.
**Le ratchet n'a pas empêché la dette — il l'a rendue visible, bornée et décroissante.** C'est déjà beaucoup
plus que ce que nous avons.

Deux invariants documentaires complètent le dispositif (`BIBLE.md:564-622`). **DRY/SSOT étendu aux
documents** : chaque fait vit dans exactement un emplacement canonique nommé, tout le reste pointe — *« a
self-describing system that says two different things about itself cannot see its own contradiction »*. Nos
six documents `docs/` en sont un test permanent, et `IMPORT_REPORT.md` applique déjà la règle. Et le **seuil de
relisibilité** : *« if code, prompts, or docs grow toward the point where strong whole-repo review no longer
fits inside the reviewer's context, simplify the system »*. **Pour un relecteur à 16 k, c'est la contrainte
la plus dure de tout le projet** — et elle s'applique à ce document autant qu'au code.

Une dernière règle, tirée de quatre incidents en série (`od/DEVELOPMENT.md:127-180`) : **ne jamais dériver
l'identité d'un enregistrement créé par l'hôte de son contenu.** L'identité est capturée à la création et
passée par valeur ; un hash de contenu ne sert que de contrôle d'intégrité sur une identité déjà connue, ou
quand le contenu *est* l'identité. Cela s'applique directement à nos missions, nœuds et propositions.

Sources : [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § D2.8 et D3.9.

### Amendement — la cible passe à ~6 000 lignes, et le ratchet devient la seule discipline restante

*(06:09 — arbitrage, après comptage.)*

Le chiffre de ~3 000 lignes datait du cadrage, **avant** l'absorption de neuf sources. Comptage des seize
fichiers Python marqués « entier » dans les ordres de portage :

```text
villani   repo_rules, context_governance, context_projection,
          autonomous_stop, autonomous_progress                   625 L
ouroboros verify, shell_parse, write_shape, argv_budget,
          runtime_mode_policy, deadline_utils,
          evolution_fingerprint, size_ratchet_manifest,
          request_wire_custom_validation                       2 819 L
swe       tools/parsing.py                                       621 L
prime     rt/harness.py                                          820 L
                                                            ────────────
                                                               4 885 L
```

**+48 % au-dessus de la cible pour tout le harness**, avant les reprises par plage (Ouroboros seul en
estime ~1 650 de plus), avant les cinq sources TypeScript, et avant une seule ligne de `relations`,
`domains` ou `mutation` — l'apport propre du projet. `refinery` visait 250 L pour porter un fichier de 820 L.

**La cible passe à ~6 000 lignes**, allouée par module d'après les portages mesurés (voir
[`ARCHITECTURE.md`](ARCHITECTURE.md) § *Carte*). Le coût est nommé, pas dissimulé : **un plafond relevé ne
mord plus par lui-même.** La discipline de taille repose désormais entièrement sur le ratchet
**shrink-only** de cette décision, qui passe de confort à nécessité — et sa cible cesse d'être un chiffre
global pour devenir **la valeur inscrite dans le `MODULE.md` de chaque module**, qui ne peut que descendre.

---

## Décision 26 — Le continual harness, et la gate d'effet qui le ferme

**C'est la réponse à « l'agent peut-il s'améliorer au fil de son cycle de vie ? ».** Prime Agent est le seul
des cinq dépôts montés sous `resources/` à l'implémenter de bout en bout — et le seul dont le mécanisme soit
isolé, testé et lisible en une journée.

### Le magasin

Un état durable **éditable, versionné, scopé et injecté dans le contexte à chaque construction**, avec quatre
familles d'entrées : `prompt`, `memory`, `skill`, `subagent`. Trois d'entre elles ont un analogue direct chez
nous, et `skill` **est déjà notre `registry.json`**.

Chaque entrée porte `id`, `kind`, `title`, `content`, `scope`, `reference`, `arguments`, `source`,
`created_at`, `updated_at` et **`version`**. Un update incrémente la version et conserve la date de création :
l'entrée a une histoire, pas seulement un état.

**La règle qui rend le mécanisme sûr tient en trois lignes** : un edit visant l'entrée de base est refusé
mécaniquement. Le prompt de base n'est jamais réécrit, seule la couche supplémentaire l'est. **C'est ce qui
sépare « harness qui s'améliore » de « harness qui se détruit ».**

Le reste du dispositif est repris tel quel : deux scopes superposés avec préfixage seulement en cas de
collision, écriture atomique préservant le mode du fichier, historique JSONL append-only **hors du fichier
d'état**, détection de conflit par état de base capturé **avant** l'appel modèle, détection d'écriture
concurrente par `mtime`, et **rollback par reconstruction inverse** depuis les `before`/`after` de chaque
edit. C'est ce dernier point qui autorise à laisser un modèle faible écrire dans l'état du harness.

### Ce qui manque à Prime Agent, et que nous avons

**Son auto-amélioration est une boucle ouverte.** `expectedOutcome` est une phrase générée, jamais évaluée.
Rien ne vérifie qu'un raffinement améliore quoi que ce soit — c'est précisément le mode d'échec que v1 a payé
sous une autre forme.

Notre `verifier` est le seul moyen de la fermer, et la fermeture prend trois formes :

- **Un edit `memory` ou `prompt` est candidat, pas appliqué.** Il reste en `shadow` et n'entre au contexte
  qu'après N missions où le taux de nœuds verts ne s'est pas dégradé. **La gate rouge-avant a un analogue
  exact ici : l'entrée doit avoir un effet mesurable, sinon elle est rejetée comme tautologique.** C'est le
  mutation-check transposé du code vers le prompt.
- **Un edit `skill` est notre entrée de registre**, qui gagne en retour `version`, les horodatages, `source`
  et l'historique de raffinement. Réciproquement, **notre empreinte de vérification (décision 5 amendée)
  donne à Prime Agent la péremption qui lui manque** : une entrée dont les octets ont changé perd son verdict.
- **L'`evidence` d'un raffinement n'est jamais la rationale générée**, mais l'identifiant du nœud et le
  verdict d'invariant qui l'ont produite. C'est la règle `Opportunity.evidence` obligatoire de Villani,
  appliquée à l'auto-amélioration.

### Le module

Neuvième module, sous `campaign` dans l'ordre d'autorité, **~250 lignes**.

```text
refinery/store.py      HarnessEntry + HarnessState, portés de rt/harness.py
refinery/propose.py    proposition d'edits — déterministe d'abord, modèle en dernier recours
refinery/gate.py       accepter un edit seulement s'il est mesurablement bon
```

Ordre de construction, cohérent avec l'inversion de la roadmap : **la gate avant le magasin, le magasin avant
l'appel modèle.**

### Le label mobile, et le versionnement des dépendances

Langfuse donne à `refinery` la forme exacte de sa paire `shadow` / `active`
(`updatePromptLabels.ts:3`) : **le contenu est versionné et immuable, et seul le déplacement du label
`active` est un acte**. Une version n'est jamais modifiée ; on en crée une nouvelle et on décide séparément
si le label bouge. **C'est ce déplacement, et lui seul, que la gate d'effet contrôle.**

Trois compléments du même module : une version est **créée avec ses dépendances, publiées ensemble**
(`createPrompt.ts:93`) ; le graphe de dépendances est **borné en cycles et en profondeur**, et il faut
**tracer les versions réellement résolues** de toutes les dépendances, pas seulement le nom de la racine
(`PromptService/index.ts:242`) ; et la clé de cache **distingue label et version** (`:204`) — sans quoi la
version numérique `2` et le label `"2"` collisionnent. C'est la décision 22 appliquée au cache.

### Trois réglages inversés par rapport à Prime Agent

- **`enabled: false` au socle.** Prime Agent active l'auto-refine par défaut, tous les 25 tours. Il tourne sur
  des modèles frontières ; nous avons un 8B dont les modes d'échec documentés incluent « omet un champ
  requis ». Activation manuelle après mesure sur les dix premières missions.
- **La cooldown se compte en nœuds terminés, pas en minutes.** Sur une mission bornée en temps mural, une
  cooldown de 20 minutes est mal calibrée par construction.
- **Le raffinement tourne en fin de mission**, après finalisation et avant le rapport. Pas de
  disconnect/reconnect à gérer, et le substrat de preuve est complet à ce moment-là.

### Une frontière à énoncer, pas à invoquer

Prime Agent laisse le modèle écrire **du texte libre** dans l'état durable. Il serait tentant d'y voir une
violation de la contrainte dure n°1 — c'en est pas une : **une entrée de harness atteint le contexte, pas
l'exécution.** La contrainte n°1 porte sur ce qui traverse la frontière modèle → exécution, et un texte
injecté dans un prompt ne la traverse pas.

Ce qu'il faut dire à la place, et qui est le vrai risque : une entrée de `memory` fausse ne casse rien, elle
**dégrade silencieusement** tous les nœuds suivants. D'où la gate d'effet, qui est le seul garde-fou
approprié — la contrainte n°1 ne l'était pas.

Sources et détail : [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § E1 et E2.1.

### Amendement — `campaign` possède le magasin, `refinery` n'est plus qu'une politique

*(06:09 — arbitrage de frontière.)*

Cette décision annonçait que la famille `skill` du magasin **est** le `registry.json` de `campaign`, que
« les deux objets fusionnent ». Deux modules revendiquaient donc le même fichier, et l'un dépendait de
l'autre — un module `enabled: false` propriétaire d'un objet du socle.

**`campaign` possède le magasin** : les quatre familles, le versionnement, les scopes, la relecture
défensive, le rendu compact pour le prompt. `refinery` perd `store` et se réduit à ce qui reste — `propose`
(le plan de raffinement déterministe) et `gate` (l'acceptation sur effet mesuré). **~150 lignes au lieu de
250**, et la dépendance `refinery → campaign` reste descendante.

Conséquence de portage : `prime/rt/harness.py` — 820 L — atterrit dans `campaign/store.py`, pas dans
`refinery`. Le **spike n°6** (la relecture défensive survit-elle à Pydantic v2 sans lever ?) change de
module, pas de contenu.

### Amendement — deux familles vivantes au socle, pas quatre

*(06:09, passe de simplification.)*

Sur les quatre familles du magasin, **deux seulement ont un consommateur au socle** : `skill` — qui *est* le
registre d'outils — et `memory` (décision 31). `prompt` n'est consommée que par `refinery`, qui est
`enabled: false`, et `subagent` est vide tant que le mode `agentic` est différé.

Or **tout ce qui est lourd dans `rt/harness.py` existe pour éditer des `prompt`** : les deux scopes, le
rollback par reconstruction inverse, le label mobile séparé de la version immuable, la clé de cache typée.
Reportés avec P9. Chaque entrée garde `version` entier, horodatages et `source` — ~5 L.

**~150 L au lieu d'un portage de 820 L.** Gardée intégralement parce qu'elle est le cœur du spike n°6 : **la
relecture défensive champ par champ qui ne lève jamais.** Un magasin écrit par un modèle doit se relire sans
exception.

Et ce qui reste de `refinery` : `plan_refinement` — plan déterministe, zéro appel modèle — et la **gate
d'effet**, ~100 L. Il **reste un module séparé**, pour une raison précise : son `MODULE.md` porte par écrit
pourquoi il est éteint et ce qui conditionne son allumage. Une politique invisible dans `campaign`
s'allumerait un jour sans que personne ne relise sa condition.

---

## Décision 27 — La politique d'exposition réseau

`PROJECT.md` diffère l'ouverture LAN du dashboard. v1 la différait aussi — **sans jamais écrire de
politique**. « Différé » n'est pas une règle : c'est l'absence de règle, et elle se transforme en ouverture
accidentelle au premier `--host 0.0.0.0` tapé pour déboguer depuis un autre poste.

Unsloth est le seul des six dépôts à traiter la question frontalement, et sa politique tient en quatre
pièces.

**Un prédicat unique, partagé par trois consommateurs.** `is_public_address`
(`studio/backend/lan_access.py:213`) est appelé par le bind, par l'affichage et par la politique d'outils.
Trois définitions séparées finissent toujours par diverger, et c'est celle qui autorise qui gagne.

**La détection couvre la résolution DNS et l'IP littérale** (`unsloth_cli/_tool_policy.py:19`), et **les
binds wildcard sont normalisés avant évaluation** (`:108`). Un `0.0.0.0` qui se lit « local » parce que
personne ne l'a normalisé est la faille type.

**L'exposition des outils dépend de l'adresse de bind** (`_tool_policy.py:165`). Une surface d'outils
accessible en loopback ne l'est pas automatiquement en LAN. Chez nous le dashboard est en lecture seule — mais
**le serveur MCP construit par la campagne, lui, expose des outils**, et c'est le livrable.

**L'énumération des adresses n'inclut jamais aveuglément loopback ni les interfaces hôte-only**
(`lan_access.py:72`).

### Le cycle de vie d'un service local

La même source donne les règles qui valent pour tout service que le harness démarre — dashboard, serveur MCP
de la campagne, ou serveur d'inférence.

- **Ne jamais considérer le spawn comme un succès** (`cloudflare_tunnel.py:507`). Une readiness observable
  est attendue sous deadline, et une URL n'est annoncée qu'après probe (`:354`).
- **Sur échec de bind, fermer tous les sockets partiellement ouverts et conserver la cause**
  (`lan_access.py:370`). Un bind partiel laisse un port occupé que le réveil suivant ne pourra pas prendre.
- **L'état de confiance réseau suit l'état réel du listener**, jamais le seul flag de configuration (`:350`).
- **L'arrêt porte un jeton d'admission/génération** (`cloudflare_tunnel.py:930`) pour qu'une ancienne
  instance ne tue pas la nouvelle. Directement applicable à deux réveils launchd rapprochés dont le premier
  est lent à mourir — un cas que v1 a rencontré sans le nommer.
- **Ne pas tuer un serveur encore utilisé par une session active** (`unsloth_cli/commands/start.py:1191`) :
  le propriétaire est explicite.
- **Un registre de hooks d'arrêt exécutés à toute sortie** (`dev-process-utils.mjs:131`). Notre mission a
  quatre effets à défaire — verrou, subprocess de vérification, serveur MCP de la campagne, watch du
  dashboard — et chacun se libère aujourd'hui à un endroit différent.
- **Les leases périmées sont libérées au démarrage, pas à l'arrêt** (`dev-safe.mjs:1177`). Un crash ne laisse
  jamais un verrou orphelin bloquer le réveil suivant — c'est le complément du `RunLock` v1, qui savait
  détecter un PID mort mais pas nettoyer proactivement.
- **Un port libre se trouve par bind explicite sur loopback** (`:218,266`), et plusieurs ports sont vérifiés
  avant de démarrer le stack. Pas de « probablement libre ».
- **`Host` et `Origin` sont validés avant traitement** (`mcp/server/security.ts:70`), sans l'échappatoire
  `allowedHosts=["*"]`, et **l'absence d'en-tête `Origin` n'est pas une preuve de confiance**.
- **Un verrou a trois états, pas deux** (`RedisLock.ts:4`) : acquis, détenu par autrui, **indisponible**. Le
  défaut de Langfuse — *procéder* quand l'état est indisponible — est explicitement inadapté à nos écritures
  critiques : **indisponible bloque.** Un verrou dont on ne sait pas l'état n'autorise rien.

Sources et détail : [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § F2.1.

### Amendement — l'interdiction est dans le type, pas dans la configuration

*(06:09, passe de simplification.)*

Cette décision mêlait deux objets de statuts opposés : **le cycle de vie d'un service local**, qui a un sujet
réel — `observatory` est un service FastAPI, et « aucun service local n'est déclaré prêt sur la base de son
spawn » est un critère de socle — et **la politique d'exposition**, qui n'en a aucun, puisque rien n'est
exposé et que l'ouverture au LAN reste une décision différée.

**L'adresse d'écoute d'`observatory` devient une constante, pas un réglage** : aucun chemin de code ne peut
binder ailleurs que `127.0.0.1`. Une ligne — et `is_public_address`, la résolution DNS, la détection d'IP
littérale, la normalisation des binds wildcard et la validation `Host`/`Origin` deviennent **sans objet**.
**~120 L évitées.**

La décision est tenue dans sa lettre, et mieux qu'avant : *« LAN différé »* cesse d'être l'absence de règle,
parce que **l'interdiction est dans le type et non dans la configuration**. Ouvrir au LAN redeviendra un
changement de code, donc une décision, avec la politique à écrire à ce moment-là.

**Gardé** : readiness observable sous deadline, arrêt idempotent, état de sortie confirmé, fermeture des
sockets partiellement ouverts sur échec de bind. Et le verrou, réduit à ~40 L **sans thread** : verrou-répertoire
atomique, paire `(pid, heure de démarrage)` contre le PID recyclé, péremption par durée maximale, et l'état
`indisponible` qui **bloque** au lieu de procéder. Le heartbeat ne détecte qu'un processus vivant mais
bloqué — cas déjà couvert par la borne murale et le kill de dernier recours de Prefect.

---

## Décision 28 — L'admission déclarative, et l'accumulateur d'erreurs

Notre `Proposal` et notre `registry.json` sont des **données déclaratives produites par un modèle faible et
consommées par le harness**. Les décisions 5, 19 et 22 disent comment décider qu'une proposition est
*redondante* ; aucune ne disait comment une proposition est admise **en tant que donnée bien formée**.

C'était un trou : entre « le schéma Pydantic a validé » et « la proposition est acceptable », il y a tout ce
qu'un schéma de types ne capture pas — un identifiant qui ne respecte pas la forme du registre, un chemin qui
sort du workspace, une commande qui contient un pipe, un texte de 40 000 caractères destiné au contexte.

### Six règles d'admission

- **Les identifiants sont validés par regex avant insertion au registre.**
- **Le markup est interdit** dans tout texte produit par le modèle et destiné à être rendu — contexte de
  nœud, dashboard, Telegram.
- **Les commandes déclaratives sont restreintes à un alphabet sans métacaractères shell**, et toute syntaxe
  shell est refusée. C'est le complément amont du capteur de masquage d'exit de la décision 13 : **l'un
  refuse `| tail` à l'admission, l'autre le détecte à l'exécution.** Notre suite de régression accumulée est
  faite de commandes persistées ; les deux gates sont nécessaires.
- **Les chemins sont restreints à des préfixes autorisés**, vérifiés relatifs et sans échappement possible.
- **Les modes et types sont des énumérations fermées**, et tout message rendu au contexte porte une **borne
  dure de longueur**.
- **Une fonction publique unique de validation** renvoyant `{valid, errors}`, et une **gate locale rapide
  avant tout appel réseau ou création d'effet**.

### La règle qui change notre comportement de rejet

Nos rejets s'arrêtent à la première règle qui échoue. **Sur un modèle à 16 k, chaque cycle de re-génération
coûte une session complète** : renvoyer une seule violation à la fois transforme une proposition à trois
défauts en trois cycles.

L'**accumulateur d'erreurs avec chemin de champ** (`manifest-validation.ts:93`) les renvoie **toutes en une
fois**, chacune avec le chemin exact du champ fautif. Langfuse confirme la règle et en donne le
contre-exemple dans le même fichier : sa validation compilée retourne bien `path`/`message`/`keyword`
(`jsonSchemaValidation.ts:58`), mais sa configuration voisine **ne renvoie que la première erreur et désactive
la validation des formats** (`:25`) — écartée explicitement comme incompatible avec une admission exhaustive. C'est gratuit à implémenter et cela divise mécaniquement
le coût des propositions mal formées. S'y ajoute une carte d'erreurs par champ permettant de **corriger une
proposition sans rejouer tout le cycle**.

### Les placeholders sont fermés, et rien n'est évalué

Corollaire de la contrainte dure n°1, appliqué aux données déclaratives plutôt qu'à l'exécution. Deux espaces
de noms fermés, et deux règles d'interpolation : quand un placeholder **occupe tout le champ**, la valeur est
substituée **en conservant son type** — pas de conversion silencieuse en chaîne ; et l'interpolation
textuelle **n'évalue aucune expression**, la lecture d'une valeur imbriquée se faisant par **chemin fermé**.

Le contre-exemple est déjà dans notre registre. Pi **exécute les commandes contenues dans une valeur de
configuration** (`resolve-config-value.ts:10`), et nous l'avions écarté à ce titre. OpenHands prend la
position inverse et l'implémente. **Deux sources, deux réponses opposées à la même question** — la nôtre est
la seconde, et elle est maintenant écrite plutôt que déduite.

Sources et détail : [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § G2.1 et G2.2.

---

## Décision 29 — Une projection dit toujours ce qu'elle cache

Notre `codeview` projette les fichiers cibles dans le contexte d'un nœud. Il les projette **entiers ou
tronqués**, et dans le second cas **rien ne dit au modèle ce qui manque**. C'est un trou silencieux : le
modèle raisonne sur un fichier qu'il croit avoir vu en entier.

SWE-agent donne la forme correcte (`windowed_file.py:150-175`). Une fenêtre rendue au modèle porte trois
éléments en plus du texte :

```text
[File: src/core/parse.py (312 lines total)]     ← ligne de statut
(48 more lines above)                            ← ce qui précède
  49:def parse(text: str) -> dict:               ← la fenêtre, numérotée
  ...
(184 more lines below)                           ← ce qui suit
```

Trois lignes de rendu, et la classe entière des raisonnements fondés sur « le fichier fait ce que j'ai lu »
disparaît. Sur Ling, dont un mode d'échec documenté est **de partir chercher un fichier de spécification
externe quand le contexte semble incomplet** (décision 20, `ling.txt:69`), rendre l'incomplétude *explicite*
plutôt que *devinable* est directement utile.

**Deux compléments obligatoires.**

- **La fusion d'intervalles avant projection** (`patch_formatter.py:28-49`). Quand plusieurs hunks touchent
  des lignes proches, projeter chacun avec son contexte produit **trois fois le même bloc**. `_merge_intervals`
  fusionne les plages chevauchantes avant rendu. Notre projection autour d'un diff en a besoin dès qu'un nœud
  touche deux fonctions voisines — c'est-à-dire souvent.
- **Un `context_length` et un `linenos` explicites** (`patch_formatter.py:147`), jamais un découpage
  implicite.

Cette décision est le pendant de la décision 14 côté *fichier* : le contexte de nœud est un inventaire typé
qui dit pourquoi chaque élément est là ; la projection d'un fichier dit ce qu'elle omet. Les deux répondent
à la même question — **qu'est-ce que le modèle ne sait pas qu'il ne sait pas ?**

Une note sur la provenance : **les quatre reprises les plus utiles de cette source, dont celle-ci, venaient de
la zone qu'une extraction automatique avait omise.** Voir [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § H1.

---

## Décision 30 — L'identité logique n'est pas l'identité de transport

**La décision qui manquait entre la 16 et la 22.**

La décision 22 pose qu'une identité est une clé typée. La décision 16 pose qu'une demande d'effet est
réclamée avant exécution, et qu'un effet à résultat inconnu s'interroge avant d'être rejoué. Aucune ne dit
ce qui se passe quand **un résultat déjà calculé échoue à être publié et doit être republié**.

Langfuse sépare deux identités (`evalScoreIds.ts:6` · `evalScoreEvent.ts:21`) :

| Identité | Nature | Au retry |
|---|---|---|
| **résultat** | déterministe — hash sur `(exécution, nom, occurrence)` | **stable** |
| **transport** | renouvelée à chaque tentative d'émission | **change** |

**Conséquence : on republie autant qu'il le faut sans jamais compter deux résultats.** L'identité de résultat
est ce qui déduplique ; l'identité de transport est ce qui permet de distinguer deux tentatives dans les
traces sans les confondre avec deux verdicts.

Chez nous, l'identité de résultat est la clé typée `(mission, nœud, tentative, relation)` de la décision 22.
Ce qu'il faut ajouter est l'identité de transport, renouvelée, et surtout la règle : **elle ne participe
jamais à la comparaison.**

### Deux corollaires sur la provenance

**Les métadonnées de l'hôte s'écrivent après la charge utile** (`evalScoreEvent.ts:54`), dans un **espace de
champs réservé**. Un champ de provenance ne peut pas être écrasé par ce que le modèle a produit — la
protection est dans l'ordre d'écriture, pas dans une vérification.

**L'autorité interne n'est pas attribuable par l'API publique** (`scores.ts:18`). L'énumération des sources
acceptées en création publique **exclut la valeur réservée aux évaluateurs**. C'est strictement plus fort que
le `criterion_source` à défaut sûr d'Ouroboros : là-bas une provenance non déclarée retombait sur
« agent » ; ici la valeur d'autorité est **inatteignable par construction du schéma d'admission**.

C'est la forme à retenir pour le champ de provenance de nos verdicts : `task_stated` ne doit pas être une
valeur qu'une proposition peut demander, mais une valeur que **seul le harness peut écrire**.

### Le manifest comme point de commit

Même famille de règle, appliquée aux artefacts (`handleBlobStorageIntegrationProjectJob.ts:1433`) : **le
manifest est écrit après tous les fichiers, et le curseur n'avance qu'ensuite**. Un export sans manifest est
un export incomplet, par construction et sans ambiguïté.

Transposé : le marqueur de complétude d'une mission — celui que le réveil suivant lit — s'écrit **en
dernier**, après le journal, l'arbre et les artefacts, et par `rename` atomique.

Sources et détail : [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § I3.1 et I3.7.

## Décision 31 — La mémoire s'écrit au socle ; s'en servir pour se réécrire vient après

*(06:09)*

Entre deux missions, v2 ne transmettait que **l'arbre** et **le registre d'outils**. Rien ne retenait ce qui
avait été tenté et raté. Un système censé tenir sur le très long terme avec un modèle de 8 milliards de
paramètres ne peut pas redécouvrir chaque impasse à chaque réveil.

Ouroboros a la réponse maximale — `consolidator`, mémoire biographique, identité persistante — et elle reste
**écartée** : c'est sa thèse, pas la nôtre, et une mémoire narrative n'est pas mécaniquement traçable.

**La famille `memory` du magasin de `campaign` est alimentée dès le socle**, par trois écrivains et sur une
seule clé :

| Ce qui est écrit | Par | Indexé par |
|---|---|---|
| nœud `blocked`, avec sa cause mécanique | `engine` | empreinte de contrat du nœud |
| invariant rejeté comme tautologique par le mutation-check | `verifier` | empreinte de contrat du critère |
| proposition récurrente, avec son compteur | `campaign` | empreinte de contrat de la proposition |

Ces entrées sont **projetées dans le contexte de nœud** (décision 14), donc elles atteignent le *prompt*.
C'est la frontière déjà énoncée face à Prime Agent : **une entrée de magasin atteint le prompt, jamais
l'exécution.** La contrainte dure n°1 porte sur les littéraux exécutés, pas sur ce que le modèle lit.

**Et voici la distinction qui fait la décision.** Écrire la mémoire et s'en servir pour réécrire le harness
sont deux actes séparés. `refinery` reste `enabled: false` (décision 26) ; **la mémoire ne l'attend pas.**
Accumuler un historique d'échecs ne coûte que le magasin, qui existe déjà. S'autoriser à le rejouer contre
son propre prompt exige la gate d'effet.

---

## Décision 32 — Un module se développe contre un double, jamais contre son voisin

*(06:09)*

Onze modules, ~5 230 lignes, un seul développeur. L'ordre ascendant strict — n'écrire un module que
lorsque toutes ses dépendances sont vertes — repousse **toute erreur de découpe à l'intégration**, c'est-à-dire
là où elle coûte le plus cher à corriger.

Chaque module publie donc deux choses et un fichier :

1. une **interface** — `typing.Protocol` pour le comportement, modèles Pydantic pour les données ;
2. un **double conforme**, livré avec le module dans `tests/doubles/<module>.py` ;
3. un **`MODULE.md`**, colocalisé dans le répertoire du module.

Un module se teste **toujours** contre les doubles de ses dépendances, jamais contre leur implémentation.
Un test de conformité vérifie que le double et l'implémentation satisfont le même protocole — sans quoi le
double dérive et les tests deviennent décoratifs.

Ce que ça achète, au-delà du parallélisme : **une frontière fausse se détecte à l'écriture du double.** Si
le double de `workspace` doit simuler un état interne pour que `verifier` passe, c'est que `verifier` lit le
monde au lieu de recevoir des faits — et la décision 13 amendée est violée **avant** la première ligne
d'implémentation. Le double est un test de l'architecture, pas seulement du code.

Le `MODULE.md` porte huit rubriques fixes : autorité, interface, interdits d'import, cible de lignes,
reprises filtrées depuis le rapport d'import avec leur verdict, critères de socle concernés, ce que le
double doit simuler, et **« fini quand »** — la liste exacte des tests qui doivent passer. Une session de
développement sur un module n'ouvre alors rien d'autre que ce fichier et le code voisin.

---

## Décision 33 — Un document vit à côté de ce qu'il décrit

*(06:09)*

Six documents dans `docs/` pour un projet sans une ligne de code — `PROJECT`, `EXPLANATIONS`,
`ARCHITECTURE`, `ROADMAP`, `ELN`, `SUCCUBUS` — soit 6 772 lignes. Deux problèmes concrets, pas esthétiques.

**`ELN` et `EXPLANATIONS` disaient la même chose deux fois.** Une décision et la séance qui l'a produite se
lisent mal séparées : l'amendement vivait dans l'une, son pourquoi dans l'autre, et la cohérence des deux
tenait à la seule discipline. Ils fusionnent en un document à deux parties — le référentiel, puis la
chronologie.

**`SUCCUBUS` décrivait des sources qui ne sont pas dans `docs/`.** Ses 3 400 lignes sont un registre de
pointeurs `fichier:ligne` vers neuf dépôts montés sous `resources/` ; vérifier un pointeur imposait un
aller-retour entre deux répertoires. Il devient **`resources/IMPORT_REPORT.md`** : le registre vit avec ce
qu'il indexe.

La règle générale, qui s'applique au code comme aux `MODULE.md` de la décision 32 :

> **Un document se place là où se trouve ce qu'il décrit**, pas là où vivent les autres documents.

Il reste quatre documents dans `docs/` : le périmètre, les décisions et le journal, l'architecture, la
roadmap.

---

## Ce qui est instrumenté dès le premier jour

La valeur durable de v1 tient à ses traces, pas à son code. v2 instrumente avant de construire :

- **par nœud** — profondeur, décomposé / exécuté / bloqué, durée, tokens, mode ;
- **par critère** — relation choisie, domaine, seed, rouge-avant, mutations tuées, accepté ou rejeté et
  pourquoi ;
- **par mission** — temps mural consommé, nœuds verts sur total, outil livré ou non, cause de sortie ;
- **par proposition** — acceptée ou rejetée, avec la règle mécanique qui a tranché.

Ces quatre familles répondent directement aux indicateurs du `PROJECT.md`. Rien n'est ajouté au-delà.

---

# Partie II — Journal de laboratoire

Une entrée par séance, horodatée `JJ:MM`, dans l'ordre chronologique. La partie I dit **ce qui est
décidé** ; celle-ci dit **quand et pourquoi ça a bougé**. Les deux se corrigent l'une l'autre : une
décision amendée porte la date de la séance qui l'a amendée.

## 05:09 — Cadrage initial, aucune ligne de code

- Reprise décidée dans un dépôt neuf après audit complet de Pithos v1. Constat chiffré retenu comme point de
  départ : **67 runs, 10 `completed` dont 3 seulement avec un effet réel produit par inference**, ~500 lignes
  de produit pour ~25 000 lignes de harness, 30 % de tool calls en échec.
- **L'objectif reste celui de v1.** Ce qui change est l'unité de travail et l'autorité de validation.
- Cadrage conduit par questionnaire en trois tours. Décisions actées : hypothèse d'extraction par harness
  avec décomposition récursive dynamique ; livrable = serveur MCP d'outils génériques pour agents ;
  validation par invariants métamorphiques ; récursion arrêtée par la vérifiabilité ; humain portier de la
  fin de campagne uniquement ; Ling 8B / 16k assumé sans re-benchmark ; borne dure en temps mural ; réemploi
  de quatre composants v1 (dashboard, broker Git, traces JSONL, launchd + Telegram).
- **Arbitrage central posé :** en v1, « une chaîne et des littéraux numériques » traversaient la frontière
  modèle → exécution, et c'est là qu'était la cause d'échec dominante. En v2, seuls un choix dans une
  énumération fermée et des noms de symboles vérifiés la traversent. Le harness génère les entrées.
- **Écart le plus important par rapport à v1, à confirmer en pratique :** le mode `direct` retire la session
  Pi du chemin nominal. Motivé par le coût de démarrage mesuré en v1 (« quelques minutes ») rapporté aux
  1 et 6 tool calls réellement consommés par les deux seuls rushes réussis. Pi reste disponible pour un mode
  `agentic` non implémenté au socle.
- **Risque assumé et documenté :** le backlog ouvert auto-alimenté est le mécanisme qui a produit les boucles
  stériles de v1. Retenu sur décision explicite, avec rejet mécanique des propositions redondantes **avant**
  toute inference, et proposition d'arrêt après trois rejets consécutifs.
- **Inversion d'ordre par rapport à v1 :** l'autorité de validation (P1) est construite avant la boucle
  d'exécution (P2) et avant tout appel au modèle. En v1 elle est arrivée en dernier et a été rapiécée pendant
  tout le projet.
- Prochaine étape : rédiger le `seed` et la liste du noyau d'outils, puis attaquer P0.

## 05:09 — Découpe en modules et choix de stack

- Décomposition en **huit modules** ordonnés par autorité, dépendances strictement descendantes. Les deux
  règles structurantes : `verifier` n'importe jamais le modèle, `bridge` n'importe jamais la boucle. C'est
  l'inversion de v1, où l'oracle appelait le modèle qui appelait le contrôleur qui rappelait l'oracle.
- Cible ~3 000 lignes de harness Python contre 8 000 en v1, dans **une seule distribution** — v1 publiait
  douze packages installables pour une seule chose déployée.
- Stack arrêtée par questionnaire, détail dans [`ARCHITECTURE.md`](ARCHITECTURE.md). Retenus : Pydantic v2,
  Hypothesis, script rendu + subprocess, `ast.NodeTransformer` maison, client OpenAI-compatible sur `/v1`,
  Prefect 3 en enveloppe, Typer, FastAPI et React portés de v1, FastMCP + schémas Pydantic explicites,
  Telegram bidirectionnel porté, venv + pip + hatchling, LangGraph réservé au mode `agentic` différé.
- **DuckDB écarté** sur décision de l'opérateur : l'API du dashboard indexe les JSONL en mémoire au
  démarrage. Aucune projection persistante, aucun collecteur permanent.
- **Correction actée :** l'objection portée contre les moteurs de workflow — « impose son modèle de flow à
  une récursion pilotée par la donnée » — était fausse pour Prefect 3, qui est impératif. La décision 11 a
  été réécrite en conséquence, avec la frontière stricte qui la rend saine.
- **Arbitrage nommé :** la complexité propre baisse fortement, la surface de dépendances augmente nettement.
  Complexité empruntée contre complexité possédée, assumée et documentée. Sans lock de dépendances (choix
  `pip`), figer `pip freeze` après chaque changement d'environnement est le minimum pour rejouer une campagne.
- **Deux spikes conditionnent l'architecture** et précèdent P0 : Prefect sous launchd en mode éphémère, et
  la stricte application du JSON Schema sur la route `/v1` d'Ollama — dont dépend toute la contrainte n°1.

## 05:09 — Extraction de Villani Code

- Inspection complète de `resources/villani-code-main/` (**21 512 L** de runtime, 13 661 L de tests).
  Résultat consigné dans [`../resources/villani.md`](../resources/villani.md) : **~90 notions mappées**
  `module -> fichier:ligne -> notion`, avec verdict Copier / Adapter / Inspirer / Écarter.
- **Preuve externe de notre hypothèse.** Villani défend la même thèse — le runtime déplace la frontière, pas
  seulement les poids — et la chiffre : Terminal-Bench 2.0 à **44,0 % avec Qwen3.6 27B** contre 40,1 % pour
  Claude Code + Sonnet 4.5, et **63,3 % contre 43,3 % à modèle identique** (Qwen3.5 9B).
- **Ce que Villani n'a pas** : aucun invariant métamorphique, aucun mutation-check, aucune sortie contrainte
  par JSON Schema. Sa validation est « exécuter les commandes du repo et lire le code de retour ».
  `verifier/relations`, `verifier/domains` et `verifier/mutation` restent l'apport propre du projet.
- **Convergence de stack non concertée** : `pyproject.toml` liste `typer`, `httpx`, `pydantic`, `pyyaml` —
  trois de nos quatre choix transverses. Le client OpenAI-compatible de `openai_client.py` est directement
  réutilisable ; il ne lui manque que `response_format`, exactement le point du spike n°2.
- **Cinq extractions prioritaires**, chacune fermant un mode d'échec mesuré en v1 : le prédicat
  `authoritative` unique, la satisfaction de tâche invalidée par empreinte de repo, la preuve d'effet réel
  (`before_contents` + `(exit=0)` littéral), `detect_stale_context`, et les seuils de garde de mutation.
- **Écarté explicitement** : les trois monolithes construits autour d'un objet `Runner` (4 807 L), la
  détection de symboles Python par regex — l'erreur exacte de v1 —, le repli fuzzy d'application de patch,
  la TUI Textual et le harnais de benchmark.
- **Point ouvert** : aucun fichier `LICENSE` dans l'archive, aucune mention de licence dans `pyproject.toml`
  ni dans le `README`. À trancher avant tout portage littéral (verdicts « Copier »).

## 05:09 — Reprises Villani intégrées à la documentation

- Décision de l'opérateur : **projet personnel, copie libre**, l'absence de `LICENSE` dans l'archive ne
  conditionne aucune reprise. Le point ouvert de l'entrée précédente est clos.
- Les ~90 notions extraites sont **absorbées dans `docs/`** plutôt que maintenues à part, pour ne pas
  recréer la duplication documentaire qui parasitait v1. `resources/villani.md` est réduit à une carte de
  destination.
- **`ARCHITECTURE.md`** — un tableau *Reprises de Villani* par module (`cible -> fichier:ligne -> notion`,
  verdict Copier / Adapter / Inspirer), une section *Sources de reprise*, et une section
  *Ce qu'il ne faut pas reprendre* qui nomme les quatre pièges. 225 → 453 lignes.
- **`EXPLANATIONS.md`** — trois décisions amendées et quatre ajoutées. 290 → 490 lignes.
  - **Décision 5 amendée** : la satisfaction d'un outil se périme par empreinte de repo. Corrige le défaut
    du marqueur `*-completed.json` de v1, incapable de se périmer quand le code changeait.
  - **Décision 9 amendée** : seuils de mutation nommés (`120` lignes / `0.35` de ratio) en seconde ligne
    derrière le splice AST, et snapshot **sur disque** pour survivre à un crash du processus.
  - **Décision 10 amendée** : flag `durable` sur chaque événement — la séparation qui manquait au collecteur
    v1 à 1,3 Go — et reprise de l'agrégateur JSONL déjà écrit, validé contre contrat avant d'être servi.
  - **Décision 12** — le prédicat `authoritative` unique, partagé, qui décide de ce qui est proposable,
    modifiable et comptable comme changement.
  - **Décision 13** — aucun succès sans preuve d'effet : `before_contents` croisé avec `git diff`, artefact
    `(exit=0)` littéral, réconciliation des findings, détection de boucle par empreinte de diagnostic.
    **C'est la correction du mode d'échec dominant de v1** — 7 des 10 `completed` sans effet réel.
  - **Décision 14** — le contexte devient un inventaire typé avec raisons, pression graduée et détection de
    dérive. Le capteur qui aurait attrapé les 12 419 `thinking_delta`.
  - **Décision 15** — ce que Villani prouve (les chiffres Terminal-Bench), ce qu'il n'a pas (notre cœur
    décisions 2-3), et ce qu'on écarte délibérément.
- **`ROADMAP.md`** — chaque item porte sa source `villani/<fichier>:<lignes>`. Les items du cœur `verifier`
  sont explicitement marqués *(neuf)* : relations, domaines, mutations, gate rouge-avant s'écrivent de zéro.
  Section *Différé — mode `agentic`* ajoutée. 70 → 182 lignes.
- **`PROJECT.md`** — quatre critères de socle ajoutés (effet réel, prédicat `authoritative`, péremption de
  satisfaction, contexte inspectable). **Périmètre inchangé**, seuls les critères se resserrent.
- Correction de cohérence : le mode agentique différé est un exécuteur de feuille LangGraph, plus une
  session Pi outillée.

## 05:09 — `IMPORT_REPORT.md`, registre de l'héritage Villani

- Les reprises étaient dispersées dans quatre documents après l'intégration précédente. Elles sont désormais
  **consignées dans un registre unique**, [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) — 379 lignes, sept sections : pourquoi
  ce dépôt et ses chiffres, ce que Villani n'a pas, ce que la reprise a changé dans la doc, le catalogue
  complet des ~90 reprises par module, ce qui est écarté, les cinq reprises qui changent la trajectoire, et
  l'ordre d'exploitation par phase.
- **Duplication assumée et arbitrée** : le catalogue existe à deux endroits, organisé par nature du
  changement dans `IMPORT_REPORT.md` et par module dans `ARCHITECTURE.md`. Les deux axes servent des moments
  différents — savoir ce qu'on doit à Villani, contre implémenter un module. La règle est écrite dans les
  deux en-têtes : **toute correction se fait dans `IMPORT_REPORT.md` en premier.**
- `resources/villani.md` est réduit à un pointeur ; `README.md`, `ARCHITECTURE.md`, `EXPLANATIONS.md` et
  `ROADMAP.md` renvoient au registre.

## 05:09 — Extraction de Prime Agent

- Inspection complète de `resources/prime-agent-main/` (**173 298 L** de TypeScript runtime hors tests et
  modèles générés, 180 514 L de tests, **4 581 L de Python** dans `prime-agent-runtime/src/rlm/`). Résultat
  consigné dans [`../resources/prime-agent.md`](../resources/prime-agent.md) : **~160 notions mappées**
  `module -> fichier:ligne -> notion`, verdicts Porter / Transposer / Inspirer / Écarter.
- **Réponse à la question posée** — « l'agent peut-il s'améliorer au fil de son cycle de vie ». Prime Agent
  est le seul des quatre dépôts montés sous `resources/` qui l'implémente : le **continual harness**, un
  magasin d'état éditable à quatre familles (`prompt` / `memory` / `skill` / `subagent`), scopé local/global,
  versionné, rollbackable, réinjecté au system prompt à chaque construction.
- **Le garde-fou central tient en trois lignes** (`refinement.ts:680-682`) : un edit visant le prompt de base
  est refusé mécaniquement. Seule la couche supplémentaire est éditable. C'est ce qui sépare « harness qui
  s'améliore » de « harness qui se détruit ».
- **Licence MIT explicite** (Mario Zechner 2025 / Prime Intellect 2026). Contrairement à Villani, aucun point
  ouvert : portage littéral licite, attribution à conserver dans les fichiers dérivés.
- **Nouveau verdict « Transposer »** : c'est du TypeScript. Presque rien ne se copie, tout se réécrit. La
  seule exception, mais majeure, est `rt/harness.py` (820 L) — l'implémentation Python de référence du
  magasin, avec relecture défensive champ par champ et resynchronisation par `mtime`.
- **Ce que Prime Agent n'a pas, et qui reste notre apport propre** : son auto-amélioration est une **boucle
  ouverte**. `expectedOutcome` est une phrase générée, jamais évaluée. C'est le mode d'échec exact du backlog
  de v1. La gate d'effet proposée (§ 0.5 du rapport) — une entrée reste en `shadow` tant qu'elle n'a pas
  démontré un effet mesurable sur le taux de nœuds verts — est neuve et n'existe dans aucune des sources.
- **Six reprises prioritaires**, chacune fermant un mode d'échec mesuré : le continual harness complet ;
  **ne pas relancer une gate sur un arbre de travail inchangé** (`autonomous.ts:294-311`, le détecteur de
  boucle stérile le plus direct des quatre dépôts, à coût nul) ; le verrou par `pid` **+ heure de démarrage
  du processus** (le PID recyclé que le `RunLock` v1 ne distinguait pas) ; la **réclamation de tick avant
  délivrance** avec coalescence des ticks manqués ; le buffer de sortie borné tête + queue ; et
  `mcp.reload(server)`, **le chaînon manquant de la décision 7** — un outil vérifié devient appelable dans la
  mission en cours, pas la suivante.
- **Huit conflits frontaux avec les décisions actées** listés et arbitrés dans le rapport plutôt qu'absorbés
  en silence. Le principal : Prime Agent est le contre-modèle complet du mode `direct` — tout y est
  programmatique via un REPL Python persistant, ce qui suppose un modèle capable d'écrire du Python correct.
  **Décision 6 conservée**, à réévaluer seulement si le mode `direct` plafonne.
- **Écarté** : le monolithe `agent-session.ts` (12 136 L, même verdict que les trois monolithes de Villani),
  le superviseur daemon multi-processus, la couche multi-fournisseurs de `packages/ai/`, l'upload de traces
  distant et la télémétrie (contraires à la souveraineté), et le protocole IPC du kernel — la décision 6
  supprime le REPL persistant.
- **Deux spikes ajoutés** : portage du magasin en Pydantic v2 sans reproduire un `ValidationError` là où
  l'original dégrade ; et chronométrage de l'empreinte d'arbre de travail sur le dépôt de campagne.
- Rien n'est encore absorbé dans `docs/`. Le rapport est la source à arbitrer avant intégration — décision
  distincte de celle prise pour Villani, où l'absorption a été immédiate.

## 05:09 — Extraction de Kilo Code

- Inspection de `resources/kilocode-main/` — monorepo **TypeScript de ~1 M lignes**, 34 paquets, fork
  d'OpenCode bâti sur Effect-TS. Résultat consigné dans [`../resources/kilocode.md`](../resources/kilocode.md) :
  **~150 notions mappées** `module -> fichier:ligne -> notion`, avec verdict Copier / Adapter / Inspirer / Écarter.
- **Licence MIT** (`LICENSE:1-4`, `package.json:128`). Aucune question de portage à trancher, contrairement
  à Villani.
- **Découverte la plus directement exploitable : Kilo maintient une famille `ling` de bout en bout.** Un
  prompt système dédié (`session/prompt/ling.txt`, 129 L), une détection de famille avec liste d'exclusions
  (`kilocode/model-match.ts:1-6`), et surtout **des paramètres d'échantillonnage chiffrés** —
  `temperature 0.3`, `top_p 0.95`, `top_k 20` (`provider/transform.ts:605,617,629`). Notre `ARCHITECTURE.md`
  n'en fixait aucun.
- `ling.txt` est moins un prompt qu'un **catalogue de modes d'échec observés sur notre modèle exact**. Deux
  touchent le chemin nominal : Ling **recopie les préfixes `N: ` de numérotation de lignes** dans son
  payload d'édition (`ling.txt:109-115`) — notre `codeview` rend des lignes numérotées, le splice AST devra
  les retirer de `new_source` ; et Ling **tronque le code qu'il génère** (`ling.txt:23`), ce qui confirme
  l'importance du `finish_reason: length` distingué de `stop`. Cinq autres sont listés dans le rapport.
- **Ce que Kilo apporte que Villani n'avait pas**, trois mécanismes : le snapshot comme **dépôt Git fantôme**
  (`--git-dir` hors projet, `write-tree` / `read-tree` + `checkout-index`) — strictement supérieur au
  `CheckpointManager` par copie ; le **compare-and-swap sur contenu de fichier** (`writeIfUnchanged` →
  `StaleContentError`), qui manquait à notre contrainte n°3 côté écriture ; et la **normalisation de
  JSON Schema pour le décodage contraint** (`tool/json-schema.ts:28-88`), qui est l'outillage manquant du
  spike n°2 — Pydantic v2 émet des `$defs`/`$ref` que les grammaires digèrent mal.
- **Confinement d'exécution sans conteneur.** `sandbox-exec` macOS, natif, zéro installation, avec le profil
  de base éprouvé fourni (`kilo-sandbox/src/seatbelt-base.ts`) et une garde in-process doublant chaque
  écriture, descripteurs inscriptibles refusés. Notre `PROJECT.md` avait écarté le *runtime conteneurisé*,
  pas ceci. Placé en P7 dans le rapport, remontable en P2 si le `verifier` déborde en pratique.
- **Convergence avec l'extraction Prime Agent sur le verrou.** Prime Agent proposait `pid` + heure de
  démarrage pour distinguer un PID recyclé ; Kilo va plus loin (`core/src/util/flock.ts:148-240`) avec un
  **heartbeat** — une section critique longue n'est plus évincée à tort — et un **verrou « breaker »** qui
  garantit qu'un seul prétendant nettoie un verrou périmé. Les deux sources pointent le même défaut du
  `RunLock` v1 ; retenir la version Kilo, plus complète.
- **Ce que Kilo n'a pas non plus** : aucun invariant métamorphique, aucun mutation-check, aucun catalogue de
  relations fermé. Sa validation est « lancer format / lint / typecheck / tests du repo et lire le code de
  retour », plus les diagnostics LSP renvoyés après chaque édition. Troisième source consécutive à le
  confirmer : `verifier/relations`, `verifier/domains` et `verifier/mutation` restent l'apport propre.
- **Écarté** : Effect-TS dans son ensemble — le graphe d'injection structure chaque fichier et n'a aucun
  équivalent Python souhaitable pour ~3 000 lignes ; les neuf stratégies de remplacement flou de `edit.ts`
  (mêmes raisons que le repli fuzzy de Villani) ; `kilo-indexing` (embeddings + magasins vectoriels
  distants, contraire à la souveraineté) ; la passerelle 500+ modèles ; l'interpréteur JavaScript de
  `codemode` (3 465 L) ; les 265 k lignes d'extension VS Code. Un piège nommé : `patch/index.ts:486-511`
  s'appelle `generateUnifiedDiff` mais fait une comparaison **positionnelle** ligne à ligne — faux dès
  qu'une ligne est insérée, et le commentaire l'avoue.
- Rapport rédigé, **rien n'est encore absorbé dans `docs/`** — même statut que Prime Agent, à arbitrer avec
  lui avant intégration. Les deux rapports se recoupent sur le verrou et sur la détection de boucle stérile.

## 05:09 — Extraction de Pi intégrée

- `resources/pi.md` — étude documentaire de `pi-main` (**1 673 fichiers, 397 645 lignes**, TypeScript, MIT),
  **185 mappages** déjà au format du projet — est absorbée dans [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md), qui devient le
  registre des **deux** héritages : partie A pour Villani, partie B pour Pi. 379 → 816 lignes.
- **Complémentarité constatée, pas redondance.** Villani apporte les garde-fous d'un agent codant sur petit
  modèle — quoi valider, comment rendre un échec lisible, comment ne pas confondre absence d'effet et succès.
  Pi apporte les contrats de durabilité et de reprise d'un runtime de production. *Villani dit quoi mesurer,
  Pi dit comment ne pas perdre la mesure.*
- **Décision 10 amendée** : Pi détecte une fin de journal tronquée puis **réécrit le fichier** pour la
  supprimer — contre-exemple direct de la contrainte dure n°6. On reprend la détection, jamais la réparation :
  octets bruts conservés, fragment diagnostiqué, reprise dans un nouveau segment lié.
- **Décision 16 — persister l'intention avant l'effet externe.** Sans elle, une reprise ne distingue pas
  *non commencé* d'*effet inconnu*, et rejouer devient un pari. Corollaire dur : un appel interrompu ne prouve
  pas que son effet n'a pas eu lieu — une publication Git doit être **interrogée par identifiant** avant toute
  nouvelle tentative, sinon deux réveils produisent deux PR pour un seul travail.
- **Décision 17 — quatre pièges nommés à la frontière du modèle** : contrainte de décodage `require` et non
  `prefer` ; le thinking n'est pas du contenu ; terminaison de stream explicite ; le budget réserve la place
  de la sortie et refuse l'appel si le contrat obligatoire ne tient pas. Plus la désactivation des retries SDK,
  qui raccorde à la frontière Prefect de la décision 11.
- **Décision 18 — annuler une attente ne tue pas l'opération.** Notre promesse de restauration à l'octet près
  est fausse tant qu'on n'attend pas la fin réelle de l'écriture avant de restaurer : un verrou libéré à
  l'annulation autorise une écriture tardive **après** le rollback.
- **Décision 19 — le registre est indexé par empreinte de contrat canonicalisé**, pas par l'identifiant que le
  modèle propose. Ferme une classe de redondances que le rejet lexical de la décision 5 laisse passer.
- **Trois critères de socle ajoutés** à `PROJECT.md` : aucune ligne JSONL jamais réécrite ; une reprise
  distingue les trois états d'effet ; **les frontières d'import sont testées comme contrats d'architecture** —
  nos deux règles structurantes cessent d'être de la discipline et deviennent un test.
- **Trouvaille inattendue** : douze utilitaires purs de Pi sont des candidats crédibles au noyau de la
  campagne, dont cinq (`json_canonical`, `jsonl_split`, `text_newlines`, `frontmatter`, `html_entities`) avec
  un invariant `round_trip` évident. De quoi amorcer le registre sans inventer.
- `resources/pi.md` réduit à un pointeur, comme `villani.md`.

## 05:09 — Extraction de Kilo Code intégrée

- `resources/kilocode.md` — monorepo Effect-TS d'environ **1 M lignes**, 34 paquets, fork d'OpenCode, MIT,
  **173 mappages** — absorbé dans [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § Partie C. 816 → 1 205 lignes.
- **Découverte principale, et la plus directement exploitable des trois sources : Kilo maintient une famille
  `ling` de bout en bout.** Détection de famille, prompt système dédié de 129 lignes, et trois paramètres
  d'échantillonnage — `temperature 0.3`, `top_p 0.95`, `top_k 20` — mesurés par un tiers sur **notre modèle
  exact**. Notre architecture n'en fixait aucun. Actés en décision 20 et dans `PROJECT.md`.
- **`ling.txt` est un catalogue daté de sept modes d'échec de Ling avec leurs contre-mesures.** Deux touchent
  le chemin nominal et doivent être traités avant la première ligne du `bridge` : **Ling recopie les préfixes
  `N: ` de numérotation dans son payload** — sans strip, chaque splice AST échoue silencieusement — et **Ling
  tronque le code qu'il génère**. Un troisième confirme indépendamment la boucle stérile de v1 : sur
  « No changes to apply », Ling retente ou cherche autre chose à changer.
- **Décision 9 amendée** : le snapshot devient un **dépôt Git fantôme** (`git init` dans un `--git-dir` hors
  projet, `write-tree` / `read-tree`, tous les hashes validés avant de toucher un fichier). Strictement
  supérieur au snapshot par copie de Villani : adressé par contenu, dédupliqué, atomique, invisible du
  `git status` produit. Plus **`writeIfUnchanged`**, un compare-and-swap qui transforme « on a écrasé sans le
  savoir » en `StaleContentError` typé — ni Villani ni v1 ne l'avaient.
- **Décision 17 amendée, et c'est un blocage découvert** : Pydantic v2 émet des `$defs`/`$ref` pour toute
  enum et tout modèle imbriqué, donc pour `Criterion`. Les backends de décodage contraint s'en accommodent
  mal. **`Criterion.model_json_schema()` ne peut pas être envoyé tel quel** : la normalisation est un
  **prérequis du spike n°2**, pas une optimisation. L'outillage existe (`tool/json-schema.ts:28-88`).
- **Décision 21 — confinement d'exécution sans conteneur.** Notre `verifier` exécute du code écrit par le
  modèle en `subprocess`. `PROJECT.md` avait écarté le runtime *conteneurisé*, pas le sandbox natif — la
  distinction n'avait jamais été faite explicitement. `sandbox-exec` macOS, profil de base fourni, doublé
  d'une garde in-process. Nouvelle phase **P7bis**, qui remonte en P2 si le premier réveil supervisé montre
  des chemins inattendus.
- **Verrou à heartbeat et breaker** (`flock.ts:148-240`) : notre `RunLock` v1 décide de la péremption par
  liveness de PID, donc deux prétendants peuvent casser le verrou simultanément et une section longue être
  évincée à tort. Régime nominal = réveil launchd toutes les trois heures sans humain devant la machine.
- **Convergence à trois** : les trois dépôts implémentent un remplacement flou de texte, et les trois sont
  écartés au même endroit — il contredit « le modèle renvoie une fonction, pas un diff ».
- **Ce que Kilo n'a pas non plus**, comme Villani et Pi : aucun invariant métamorphique, aucun mutation-check,
  aucun catalogue de relations fermé. Trois sources, trois fois le même constat : `verifier/relations`,
  `verifier/domains` et `verifier/mutation` sont l'apport propre du projet.
- MIT sans ambiguïté. Attribution à conserver sur les trois reprises les plus littérales : le profil sandbox,
  le verrou, la normalisation de schéma. `resources/kilocode.md` réduit à un pointeur.

## 06:09 — Extraction d'Ouroboros intégrée

- `resources/ouroboros.md` — agent auto-modifiant à identité persistante, **222 035 lignes de Python**, MIT,
  papier arXiv, Terminal-Bench 2.1 à **86,74 %**, **~200 mappages** — absorbé dans [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md)
  § Partie D. 1 205 → 1 746 lignes. **Premier des quatre dépôts écrit dans notre langage** : le portage est
  littéral, le point de friction est la taille, pas la transposition.
- **C'est le seul des quatre à avoir construit la machinerie complète de la preuve d'effet** — notre décision
  13, poussée deux crans plus loin que Villani. Là où Villani compare `before_contents` au contenu courant,
  Ouroboros a un reçu attesté par l'hôte, une relation de réconciliation **prouvée transitive**, et trois
  capteurs de faux-vert dont aucun ne change le verdict.
- **Découverte la plus lourde de conséquences : `response_format` est une *intention*, pas une garantie.**
  Certaines routes l'ignorent, et la ladder de retry a le droit de le **retirer** pour faire passer l'appel —
  il figure dans `_OPTIONAL_DROPPABLE_PARAMS`. **La contrainte dure n°1 ne peut donc pas reposer sur le
  décodage contraint côté serveur.** Elle repose sur une revalidation locale contre le schéma exact envoyé,
  obligatoire quoi qu'il arrive. *« Validation failure may prove wire acceptance but cannot authorize tool
  execution. »* Le spike n°2 est reformulé : la question n'est plus binaire, c'est le **taux de rejet** de la
  revalidation locale, par code d'erreur.
- **Décision 22 — une identité est une clé typée, jamais une chaîne de repli.** Citée telle quelle :
  *« A chain is not an equivalence relation. […] No care at the call sites can repair a relation that is not
  an equivalence. »* Notre clé anti-redondance (décisions 5 et 19) avait **exactement la forme fautive** —
  nom, puis schémas, puis recouvrement lexical — avec le même risque de non-transitivité. Trois raffinements
  repris, chacun né d'un incident : tampon de version du rendu, canonicalisation qui ne jette aucun octet
  d'identité, décideur et rapporteur sur la même projection.
- **Décision 13 amendée** : le reçu attesté par l'hôte (exécuter **et** attester dans le même acte ; un reçu
  non écrit **retire l'attestation**) et les trois capteurs de faux-vert. Le capteur de **masquage d'exit**
  nous concerne directement : notre suite de régression accumulée est faite de commandes persistées, et une
  commande avec `| tail` serait verte pour toujours.
- **Décision 23 — le résultat n'est pas un statut, c'est un produit d'axes.** Sans vocabulaires de non-échec,
  trois cycles très différents comptent identiquement : Ollama injoignable, proposition rejetée comme
  redondante, critère tautologique rejeté. **Les deux derniers sont des succès du garde-fou.** Les compter
  comme échecs rend l'indicateur central illisible et pousse mécaniquement à affaiblir les gates.
- **Décision 24 — le filtre de pression interne.** *« Self-started does not mean self-exempt. »* La décision 5
  rejette une proposition redondante ; rien ne rejetait une proposition qui **retire une gate**. C'est le
  prédicat manquant, d'autant plus nécessaire qu'un système jugé sur « outils vérifiés livrés » a un gradient
  permanent vers l'assouplissement de ce qui définit « vérifié ».
- **Décision 25 — discipline de dépôt.** Le ratchet de taille rend mécanique la cible « ~3 000 lignes »,
  aujourd'hui purement déclarative — exactement la forme d'engagement que v1 a tenu jusqu'à 8 000 lignes sans
  qu'aucun signal ne se déclenche. Nouvelle phase **P8**. Le seuil de relisibilité — *« if docs grow beyond
  what fits in the reviewer's context, simplify the system »* — s'applique à ce document autant qu'au code.
- **Décision 5 amendée** : la récurrence se compte, elle ne se jette pas. Une proposition répétée est de
  l'information sur ce que le système croit devoir faire, détruite au moment exact où elle deviendrait un
  signal d'arrêt informé.
- **Décision 8 amendée** : deux réserves murales, pas une. Les confondre a coûté 54 minutes sur une tâche de
  six heures chez Ouroboros, et le **latch de l'ancre de départ** évite que la réserve se dégrade
  silencieusement vers son plancher.
- **Deux spikes ajoutés.** N°4 : lire `n_ctx_train` sur `/v1/models` et mesurer la densité de tokens réelle —
  **si elle dépasse 1,2, le cadran de pression de la décision 14 est faux d'un palier entier**. N°5 : mesurer
  le coût d'un worktree jetable ; si c'est de l'ordre de la seconde, la classe entière « régression verte
  parce que le worktree était sale » disparaît.
- **Neuf conflits frontaux relevés et arbitrés** (§ D5). Deux tranchés en gardant notre position : la gate
  dure de la décision 13 (leur drapeau advisory vise l'oscillation, notre mode d'échec mesuré est le succès
  fantôme) et l'interdiction de tronquer un JSONL (ils quarantinent **puis tronquent**). Un laissé ouvert :
  leur dédup sémantique par appel à choix fermé respecte notre contrainte n°1 à la lettre — à trancher après
  mesure du taux de faux négatifs du lexical.
- **Convergence à quatre sources**, désormais : les quatre implémentent un remplacement flou de texte et les
  quatre sont écartés au même endroit ; et **aucun des quatre n'a d'invariant métamorphique, de mutation-check
  ni de catalogue fermé de relations**. Quatre runtimes matures, quatre fois le même constat.
- Total estimé du portage Ouroboros : **~1 650 lignes** sur une cible de 3 000. `resources/ouroboros.md`
  réduit à un pointeur.

## 06:09 — Extraction de Prime Agent intégrée

- `resources/prime-agent.md` — *« A Self-Improving RLM Harness »* de Prime Intellect, TypeScript avec un cœur
  Python de 4 581 lignes, MIT, papier arXiv, **~110 mappages** — absorbé dans [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md)
  § Partie E. 1 746 → 2 129 lignes.
- **C'est la réponse à « l'agent peut-il s'améliorer au fil de son cycle de vie ? »** — seul des cinq dépôts à
  l'implémenter de bout en bout. Magasin d'état durable **éditable, versionné, scopé et injecté au contexte**,
  quatre familles d'entrées dont `skill` qui **est déjà notre `registry.json`**, rollback par reconstruction
  inverse, détection de conflit par état de base, et **l'immuabilité du prompt de base en trois lignes** —
  ce qui sépare « harness qui s'améliore » de « harness qui se détruit ».
- **Son défaut est exactement notre force : c'est une boucle ouverte.** `expectedOutcome` est une phrase
  générée, jamais évaluée. Rien ne vérifie qu'un raffinement améliore quoi que ce soit.
- **Décision 26 — le continual harness et la gate d'effet.** Neuvième module `refinery` (~250 L), et la
  fermeture de boucle en trois formes : un edit `memory`/`prompt` reste en **`shadow`** tant qu'il n'a pas
  démontré un effet mesurable sur le taux de nœuds verts — **le mutation-check transposé du code vers le
  contexte** ; un edit `skill` fusionne avec le registre et lui apporte `version` et historique, tandis que
  notre empreinte lui apporte la péremption qui lui manque ; et l'`evidence` d'un raffinement est
  l'identifiant de nœud + le verdict d'invariant, jamais la rationale générée.
- **Une frontière à énoncer plutôt qu'à invoquer.** Prime Agent laisse le modèle écrire du texte libre dans
  l'état durable. Ce n'est **pas** une violation de la contrainte n°1 : une entrée de harness atteint le
  contexte, pas l'exécution. Le vrai risque est autre — une `memory` fausse ne casse rien, elle **dégrade
  silencieusement** tous les nœuds suivants. La gate d'effet est le garde-fou approprié ; la contrainte n°1 ne
  l'était pas.
- **Trois réglages inversés** : `enabled: false` au socle (Prime Agent l'active par défaut, mais il tourne sur
  des modèles frontières) ; cooldown comptée **en nœuds terminés, pas en minutes** ; raffinement **en fin de
  mission**, après finalisation, avant le rapport.
- **Décision 7 amendée — `mcp.reload` ferme le chaînon manquant.** Notre formulation disait qu'un outil
  vérifié « devient appelable par les nœuds suivants » sans dire **quand**. Avec `reload`, il l'est **dans la
  mission en cours** : la question expérimentale 4 devient mesurable en une seule mission au lieu d'exiger
  deux réveils à trois heures d'intervalle.
- **Décision 6 — le contre-modèle nommé.** Prime Agent prend l'option inverse jusqu'au bout : un seul outil
  `ipython`, le modèle écrit du Python dans un REPL persistant. On garde la décision 6, mais on écrit ce
  qu'on abandonne (composition, délégation native, état entre les tours) et ce qu'on gagne (aucune surface
  d'exécution ouverte, un 8B qui n'écrit jamais de code de contrôle). **Le rapport de force s'inverse selon la
  taille du modèle.**
- **Deux reprises à coût nul qui ferment des modes d'échec de v1** : *ne pas relancer une gate sur un arbre de
  travail inchangé* (les six heures de boucle stérile) et *buffer de sortie borné tête + queue* (le collecteur
  à 1,3 Go). Plus le **verrou par `pid` + heure de démarrage** qui ferme le PID recyclé, et la **réclamation
  de tick avant délivrance** qui empêche un réveil launchd de rejouer ou d'empiler après une suspension.
- **Spikes 6 et 7 ajoutés.** Le 6 est subtil : porter `harness.py` en Pydantic v2 **change le comportement
  d'erreur** — Pydantic lève là où l'original dégrade, et c'est exactement ce qu'il ne faut pas reproduire
  pour un magasin écrit par un modèle.
- **Trois convergences à cinq sources**, désormais : les cinq implémentent un remplacement flou de texte et
  les cinq sont écartés ; les cinq portent un **monolithe de session de 6 000 à 12 000 lignes** et les cinq
  sont écartés pour la même raison ; et **aucun des cinq n'a d'invariant métamorphique, de mutation-check ni
  de catalogue fermé de relations** — dont deux avec un papier et un à 86,74 % sur Terminal-Bench.
- Nouvelle phase **P9 — Auto-amélioration**, après P6. `resources/prime-agent.md` réduit à un pointeur.

## 06:09 — Extraction d'Unsloth intégrée

- `resources/unsloth.md` — bibliothèque de fine-tuning, **~2,1 M lignes**, **~110 mappages** — absorbée dans
  [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § Partie F. 2 129 → 2 427 lignes. **Sixième et dernière source.**
- **Source d'une autre nature.** Unsloth n'est pas un runtime d'orchestration : kernels CUDA, entraînement RL
  et optimisation MoE sont hors périmètre par construction. **Sa valeur est dans `unsloth_cli/` et
  `studio/backend/`** — le seul des six dépôts à traiter frontalement « à quelles conditions un service local
  a-t-il le droit d'être joignable ».
- **Point de licence, le seul ouvert des six sources.** Le dépôt **mélange une licence AGPL pour `studio/`**
  avec d'autres notices, et ce sont précisément les fichiers `studio/` qui portent les reprises les plus
  utiles. Les obligations AGPL se déclenchent à la distribution ou à la mise à disposition réseau — un
  harness personnel local ne les déclenche pas — mais **décision retenue par prudence : reprendre les
  notions, réécrire le code, aucune copie littérale depuis `studio/`.**
- **Décision 27 — la politique d'exposition réseau.** `PROJECT.md` différait l'ouverture LAN **sans jamais
  écrire de politique** ; « différé » n'est pas une règle, c'est l'absence de règle, et elle se transforme en
  ouverture accidentelle au premier `--host 0.0.0.0` tapé pour déboguer. Quatre pièces : un prédicat
  `is_public_address` **unique et partagé** par le bind, l'affichage et la politique d'outils ; détection
  couvrant **résolution DNS et IP littérale** ; **binds wildcard normalisés avant évaluation** ; exposition
  des outils dépendant de l'adresse de bind. Ce dernier point nous vise directement : le dashboard est en
  lecture seule, mais **le serveur MCP construit par la campagne expose des outils**, et c'est le livrable.
- **Le cycle de vie d'un service local**, qui vaut pour tout ce que le harness démarre : **ne jamais
  considérer le spawn comme un succès**, readiness observable sous deadline ; sur échec de bind, **fermer tous
  les sockets partiellement ouverts en conservant la cause** ; et **jeton d'admission/génération à l'arrêt**
  pour qu'une ancienne instance ne tue pas la nouvelle — cas que v1 a rencontré sans le nommer, avec deux
  réveils launchd rapprochés.
- **Décision 8 amendée** : les deux réserves disaient *quand* s'arrêter, pas comment le budget atteint un
  `subprocess`. **Un seul deadline monotonique propagé à toutes les sous-opérations** — sans quoi une mission
  bornée à 20 minutes se termine à 35, chaque sous-opération respectant le sien.
- **Décision 12 amendée** : le prédicat `authoritative` ne dit rien des chemins **hors workspace**. Le code
  produit exécuté en `subprocess` n'a aucune raison de toucher `~/.prefect` ou `~/Library/LaunchAgents` — une
  garde des répertoires système est la seconde ligne, version applicative de ce que la décision 21 obtient au
  niveau OS.
- **Décision 21 amendée** : le confinement a une **dimension réseau**, non nommée jusqu'ici. Refus par défaut
  pour le code produit sous invariant — et **un invariant qui aurait besoin du réseau pour passer n'est pas un
  invariant**.
- **Sixième confirmation** de « séparer texte visible et thinking », et **quatrième** de « arrêter le groupe
  de processus, jamais le seul parent ».
- **Bilan des six sources.** Trois convergences : les six implémentent une forme de patch textuel approximatif
  et les six sont écartés ; les cinq runtimes portent un monolithe de session de 6 000 à 12 000 lignes et les
  cinq sont écartés ; et **aucun des six n'a d'invariant métamorphique, de mutation-check ni de catalogue fermé
  de relations**. Six dépôts matures, dont deux avec un papier et un à 86,74 % sur Terminal-Bench.
  `verifier/relations`, `verifier/domains` et `verifier/mutation` restent intégralement l'apport propre du
  projet.
- `resources/unsloth.md` réduit à un pointeur. **Les six extractions sont absorbées ; `resources/` ne contient
  plus que les dépôts sources et six pointeurs.**

## 06:09 — Extraction d'OpenHands intégrée

- `resources/openhands.md` — frontend Agent Canvas, **~373 367 lignes** TypeScript/React/Electron,
  **~110 mappages** — absorbé dans [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § Partie G. 2 427 → 2 734 lignes.
  **Septième source**, deuxième non-runtime après Unsloth.
- **Décision 28 — l'admission déclarative.** C'était un trou identifié en l'écrivant : entre « le schéma
  Pydantic a validé » et « la proposition est acceptable », il y a tout ce qu'un schéma de types ne capture
  pas — un identifiant hors forme du registre, un chemin qui sort du workspace, une commande contenant un
  pipe, un texte de 40 000 caractères destiné au contexte. Les décisions 5, 19 et 22 disaient comment décider
  qu'une proposition est *redondante* ; aucune ne disait comment elle est admise **en tant que donnée bien
  formée**.
- **La reprise qui change le plus le comportement, et elle est gratuite : l'accumulateur d'erreurs avec chemin
  de champ.** Nos rejets s'arrêtaient à la première règle qui échoue. Sur un modèle à 16 k, chaque cycle de
  re-génération coûte une session complète : **une proposition à trois défauts coûtait trois sessions au lieu
  d'une.** Toutes les violations sont désormais renvoyées ensemble, avec le chemin exact de chaque champ.
- **Complémentarité amont/aval avec la décision 13.** La restriction des commandes déclaratives à un alphabet
  sans métacaractères shell refuse `| tail` **à l'admission** ; le capteur de masquage d'exit d'Ouroboros le
  détecte **à l'exécution**. Notre suite de régression accumulée est faite de commandes persistées : les deux
  gates sont nécessaires, aucune ne remplace l'autre.
- **Une opposition frontale entre deux sources, tranchée.** Pi **exécute** les commandes contenues dans une
  valeur de configuration (`resolve-config-value.ts:10`, écarté en partie B) ; OpenHands **interdit toute
  expression évaluable** dans un placeholder (`manifest-template.ts:76`, repris). Même question, deux
  réponses opposées — la nôtre est la seconde, et elle est maintenant écrite plutôt que déduite.
- **Décision 17 amendée** : le backend est vérifié **avant** la mission. Version minimale compatible, refus
  avant tout démarrage, **version inconnue traitée comme un état distinct** — même famille que « un token
  absent n'est jamais un zéro ». Et une erreur typée distinguant backend absent, indisponible et détail de
  connexion, au lieu d'un « Ollama ne répond pas » qui recouvre trois causes et trois remédiations.
- **Décision 16 amendée — le claim idempotent**, face amont de « interroger avant de rejouer ». Le claim
  empêche le doublon **en entrée**, l'interrogation le rattrape **en sortie**. Trois applications chez nous :
  lancement d'un nœud enfant, promotion d'un outil au statut `verified`, création d'une PR.
- **Décision 27 amendée** : registre de hooks d'arrêt exécutés à toute sortie — notre mission a quatre effets
  à défaire et chacun se libérait à un endroit différent — et **leases périmées libérées au démarrage, pas à
  l'arrêt**, pour qu'un crash ne bloque jamais le réveil suivant.
- **Cinquième confirmation** de « signaler l'arbre de processus, pas le parent », et **troisième** de
  « registre construit à partir d'entrées validées, sans découverte implicite ».
- **Bilan à sept sources.** Trois convergences : les sept implémentent une forme de patch ou d'interpolation
  textuelle approximative et les sept sont écartés ; les cinq runtimes portent un monolithe de session de
  6 000 à 12 000 lignes et les cinq sont écartés ; et **aucun des sept n'a d'invariant métamorphique, de
  mutation-check ni de catalogue fermé de relations**.
- `resources/openhands.md` réduit à un pointeur. **`SWE-agent-main/` est monté mais sans extraction** —
  huitième source possible, non traitée.

## 06:09 — Extraction de SWE-agent : audit, complétion, intégration

- **Extraction vérifiée avant absorption**, à la demande de l'opérateur — elle avait été produite par un
  petit modèle. Verdict : **utilisable, mais incomplète et imprécise.**
- **Ce qui tient** : les 22 ancres testées pointent toutes vers un fichier et une ligne existants. Zéro
  chemin mort. Volumétrie en fichiers correcte (414), licence MIT correctement identifiée, structure par
  module conforme à `ARCHITECTURE.md`.
- **Ce qui ne tient pas** : dans `tools/parsing.py`, **3 ancres sur 8 nomment la classe voisine** — `:72`
  est `ActionParser` mais annoncé « action-only » (qui est en `:97`), `:543` est `BashCodeBlockParser` mais
  annoncé « bloc unique » (qui est en `:574`). Plusieurs ancres pointent au milieu d'un corps de fonction
  plutôt que sur une définition. Volumétrie en lignes surestimée d'environ 15 %.
- **Ce qui manquait, et c'est le vrai défaut : trois zones entières, ~3 000 lignes.** `tools/` (~900 L, dont
  `windowed_file.py` à 315 L), `tests/` (~1 700 L, 14 fichiers), et `sweagent/types.py` — **le vocabulaire de
  contrats du dépôt**. Le document affirmait pourtant en clôture que « les tools et trajectoires ont été
  parcourus ».
- **Les quatre reprises les plus utiles venaient de la zone omise.** C'est le point qui compte : la
  vérification a coûté vingt minutes et a récupéré ce qui avait le plus de valeur.
- **Décision 29 — une projection dit toujours ce qu'elle cache.** Notre `codeview` projetait les fichiers
  cibles entiers ou tronqués sans jamais dire ce qui manque. Trois lignes de rendu — ligne de statut,
  `(N more lines above)`, `(N more lines below)` — suppriment la classe entière des raisonnements fondés sur
  « le fichier fait ce que j'ai lu ». Sur Ling, dont un mode d'échec documenté est **de partir chercher un
  fichier de spécification externe quand le contexte semble incomplet** (décision 20), rendre l'incomplétude
  explicite plutôt que devinable est directement utile.
- **Complément obligatoire : la fusion d'intervalles avant projection.** Quand deux hunks touchent des lignes
  proches, projeter chacun avec son contexte produit **trois fois le même bloc**. Notre projection autour d'un
  diff en a besoin dès qu'un nœud touche deux fonctions voisines — c'est-à-dire souvent.
- **Décision 9 amendée** : une mutation rend son **bilan chiffré** (`n_replacements`, lignes ajoutées). Ce
  compteur rend vérifiable la règle de Kilo « nombre d'occurrences attendu », alimente la métrique
  d'inflation de patch d'Ouroboros sans instrumentation séparée, et **détecte un splice qui a touché zéro
  ligne sans relire le fichier**. Plus un `undo_edit` au niveau du fichier, distinct du rollback de mission.
- **Décision 14 amendée** : six sources disaient de séparer le thinking du contenu. SWE-agent va plus loin —
  `StepOutput` sépare `thought`, `action`, `output`, `observation` en **champs typés distincts**, et
  `HistoryItem` impose un `message_type` en littéral fermé. **La séparation est la forme du contrat, pas un
  traitement appliqué à une chaîne** : un `StepOutput` mal formé est rejeté par le type, pas par une
  heuristique de parsing.
- **Bilan à huit sources.** Les huit implémentent une forme de patch ou d'interpolation textuelle
  approximative et les huit sont écartés ; les six runtimes portent un monolithe d'agent de 1 300 à 12 000
  lignes et les six sont écartés ; et **aucun des huit n'a d'invariant métamorphique, de mutation-check ni de
  catalogue fermé de relations**.
- **Leçon de méthode, consignée** : une extraction par petit modèle produit des **ancres fiables** et des
  **descriptions approximatives**, et **couvre le répertoire principal en ignorant la périphérie**. C'est le
  profil d'erreur exact que la décision 13 anticipe — un travail qui *paraît* complet parce qu'il en a la
  forme, la volumétrie et la structure.

## 06:09 — Extraction de Langfuse livrée

- [`resources/langfuse.md`](../resources/langfuse.md) : **105 mappages stricts**, **67 fichiers cités**,
  répartis entre les neuf modules, dont `refinery`. Version déclarée du snapshot : **4.30.0**.
- Inventaire de **5 704 fichiers réguliers**, dont **5 684 textes / 1 209 171 lignes logiques** ;
  neuf liens symboliques exclus des comptes. Inventaire exhaustif et lecture sémantique ciblée sont
  explicitement distingués, avec une carte des familles couvertes et des éléments non retenus.
- Apports : provenance des scores, publication avant état terminal, claims et réconciliation,
  versions de prompts/datasets, cohortes déterministes, manifests d'export et projections bornées.
  La décision 29 issue de SWE-agent a été prise en compte pendant la finalisation.
- Limites documentées dans les mappages : `insecure-local`, preuve de trace best effort, checkpoint de
  replay concurrent, troncature du brut, normalisation IO expérimentale et frontières MIT/Enterprise.
- Contrôle effectué des modules, chemins, lignes, ancres, tableaux, liens et empreintes du snapshot.
  Les tests source sont des scénarios lus, **non exécutés**. Aucune dépendance installée, aucun runtime
  lancé. Les suggestions restent à arbitrer avant absorption dans `IMPORT_REPORT.md` ; aucun port implémenté.

## 06:09 — Extraction de Langfuse intégrée

- `resources/langfuse.md` — plateforme d'observabilité LLM, **1 209 171 lignes**, version 4.30.0, MIT hors
  `ee/`, **105 mappages sur 67 fichiers cités** — absorbée dans [`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § Partie I.
  2 734 → 3 425 lignes. **Neuvième source.**
- **Extraction vérifiée, verdict opposé à celui de SWE-agent.** 5 704 fichiers, 9 liens symboliques et
  version 4.30.0 : **exacts au fichier près**. **15 ancres vérifiées, 15 exactes**, pointant toutes sur la
  définition canonique avec la notion correspondante. L'empreinte SHA-256 de l'inventaire n'a pas été
  reproduite faute de spécification du format de chemin et de l'ordre de tri — défaut de documentation, pas
  d'inventaire divergent.
- **Ce qui distingue cette extraction : elle déclare ses limites et quantifie sa couverture.** Carte par
  famille avec le nombre de fichiers cités, section « traitement des autres familles », et la phrase
  *« l'inventaire est exhaustif ; l'analyse sémantique est ciblée »*. **La leçon des deux audits n'est pas
  « les petits modèles extraient mal » — c'est que la seule extraction auditable est celle qui quantifie ce
  qu'elle n'a pas couvert.** C'est la décision 13 appliquée au travail documentaire.
- **Décision 30 — l'identité logique n'est pas l'identité de transport.** La décision qui manquait entre la
  16 et la 22 : la 22 dit qu'une identité est une clé typée, la 16 dit qu'une demande est réclamée avant
  exécution, **aucune ne disait ce qui se passe quand un résultat déjà calculé échoue à être publié**.
  Identité de résultat déterministe et stable au retry, identité de transport renouvelée et **exclue de toute
  comparaison** : on republie autant qu'il le faut sans jamais compter deux résultats.
- **Deux corollaires sur la provenance.** Les métadonnées de l'hôte s'écrivent **après** la charge utile,
  dans un espace de champs réservé — la protection est dans l'ordre d'écriture. Et l'autorité interne est
  **inatteignable par le schéma d'admission public** : strictement plus fort que le défaut sûr d'Ouroboros.
  `task_stated` ne doit pas être une valeur qu'une proposition peut demander, mais une valeur que **seul le
  harness peut écrire**.
- **Décision 16 amendée — le fencing.** Trois durcissements : heartbeat à **perte de propriété explicite**
  (pas un booléen) ; classification de péremption à quatre causes où **la durée maximale l'emporte sur le
  heartbeat** ; et **réconciliation qui ne réapplique une transition que si l'état observé n'a pas changé** —
  *une lecture de nœud périmé ne donne pas le droit de tuer une nouvelle incarnation*, exactement le risque
  des deux réveils launchd rapprochés. Réserve reprise telle quelle : **un CAS de statut n'est pas à lui seul
  un jeton de propriété.**
- **Décision 13 amendée — l'ordre.** La preuve durable **précède** la transition terminale. Avec son
  contre-exemple dans le même dépôt : un `catch` qui journalise l'échec d'écriture de trace et continue —
  acceptable en télémétrie, **inacceptable pour la preuve primaire**.
- **Décision 27 amendée** — verrou à **trois états** dont `indisponible`, qui **bloque** (le défaut Langfuse
  « procéder » est explicitement inadapté) ; validation de `Host` et `Origin` sans échappatoire wildcard, et
  **l'absence d'`Origin` n'est pas une preuve de confiance**.
- **Décision 28 confirmée par son contre-exemple** : la configuration de validation voisine **ne renvoie que
  la première erreur** et est écartée comme incompatible avec une admission exhaustive. Deux sources
  indépendantes disent désormais la même chose.
- **Décision 26 amendée — le label mobile.** Langfuse donne à `refinery` la forme exacte de sa paire
  `shadow`/`active` : le contenu est versionné et **jamais modifié**, on crée une nouvelle version, et **seul
  le déplacement du label `active` est l'acte que la gate d'effet contrôle**. Plus la clé de cache typée qui
  évite que la version `2` collisionne avec le label `"2"`.
- **Pour l'observatory** : arbre **résistant aux IDs dupliqués** (sinon graphe multiparent explosif), **durée
  de nœud distincte de l'enveloppe du sous-arbre** — ne jamais sommer des durées concurrentes —, lecture
  coûteuse **subordonnée à un périmètre**, et **budget de rendu en nœuds distinct du budget en caractères**.
  Plus un X important : **ne jamais corriger silencieusement une durée négative**, c'est une anomalie à
  conserver et à montrer.
- **Bilan à neuf sources.** Les neuf implémentent une forme de patch ou d'interpolation textuelle
  approximative — écartés. Les six runtimes portent un monolithe de 1 300 à 12 000 lignes — écartés. Et
  **aucune des neuf n'a d'invariant métamorphique, de mutation-check ni de catalogue fermé de relations**.

## 06:09 — Douze arbitrages de frontières, avant toute ligne de code

Fin de la phase d'absorption : neuf sources, 30 décisions, ~1 100 reprises. Trois salves de QCM pour
transformer ce catalogue en **frontières de modules développables séparément**. Rien de nouveau n'est
appris ici — tout est arbitré.

### Le constat qui a ouvert la session

Comptage des seize fichiers Python marqués **« entier »** dans les ordres de portage : **4 885 lignes**,
contre une cible de 3 300 L pour tout le harness — **+48 %**, avant les reprises par plage, avant les cinq
sources TypeScript, et avant une seule ligne de `relations`/`domains`/`mutation`. `refinery` visait 250 L
pour porter un fichier de 820 L. Le chiffre global n'avait jamais été recalculé après neuf absorptions.

### Salve 1 — les frontières

- **Cible relevée à ~6 000 L**, allouée par module d'après les portages mesurés. Coût assumé : le plafond ne
  mord plus par lui-même, et la discipline de taille repose désormais **entièrement sur le ratchet
  shrink-only de la décision 25**, qui passe de confort à nécessité.
- **`hostside` éclaté en deux** — `lifecycle` (verrou, launchd, custody, garde disque) et `broker`
  (Git + Telegram, 550 L). **Dix modules au lieu de neuf.** Le regroupement de Git et de Telegram sous un
  seul nom est délibéré : `broker` est **le seul module par lequel une donnée quitte la machine**, ce qui
  fait de la contrainte dure n°5 un test de graphe d'imports au lieu d'une discipline de relecture. Le terme
  vient de `PROJECT.md`, qui parlait déjà de « Git et Telegram déjà brokerisés ».
- **`verifier` possède le reçu d'effet (décision 13).** Formulation exacte à graver, plus précise que celle
  posée en séance : *`verifier` n'a d'I/O que sur ce qu'il a lui-même produit* — le script qu'il vient
  d'écrire, le process qu'il vient de lancer. **L'état du monde lui arrive toujours comme fait typé** :
  contenu avant/après par `workspace`, `git diff` par `broker`, attestation d'hôte par `lifecycle`. C'est cette
  règle qui rend le module le plus critique intégralement testable avec des faits en dur.
- **`campaign` possède le magasin à quatre familles**, la famille `skill` **est** le registre d'outils.
  `refinery` perd `store` et se réduit à une politique — `propose` + `gate`, ~150 L. La fusion annoncée dans
  `ARCHITECTURE.md` cesse d'être une phrase et devient un propriétaire de fichier.

### Salve 2 — ce qui est adapté

- **Quatrième verdict : `Traduire`.** `Copier` ne veut rien dire pour cinq sources sur neuf. Désormais
  **Copier** (Python, quasi tel quel, notice MIT), **Traduire** (TS → Python ligne à ligne, en-tête
  `PORTED_FROM`), **Adapter**, **Inspirer**. Le travail devient comptable par module.
- **Dédup en deux temps — D5 #3 se ferme.** Lexical sur la proposition, puis **empreinte de contrat
  canonicalisée** dès que les critères `{relation, symbols, domain}` existent. Deux propositions formulées
  différemment qui produisent le même contrat sont le même outil. **Aucun appel modèle** : l'option
  d'Ouroboros (light-model à choix fermé, fail-open) est écartée, la décision 24 vaut aussi ici. Dernière
  question explicitement ouverte du document.
- **La famille `memory` est alimentée au socle** : nœuds `blocked` avec cause mécanique, invariants rejetés
  comme tautologiques, propositions récurrentes — indexés par empreinte, injectés dans le contexte de nœud.
  **Écrire la mémoire et s'en servir pour se réécrire sont deux choses distinctes** : `refinery` reste
  `enabled: false` sans que la mémoire attende. C'est la réponse minimale à l'endurance longue, sans la
  mémoire narrative d'Ouroboros.
- **Les critères de socle sont tous conservés — 26, et non 16.** Le décompte de 16 portait sur les critères
  *ajoutés* par les neuf sources, pas sur le total ; la décision 31 en ajoute un, ce qui fait **27**. Ils
  sont précédés d'un **jalon « premier vert »** : une nano-étape, un invariant, un mutation-check, un reçu,
  un fichier réellement modifié — de bout en bout — avant tout durcissement. Prouve l'emboîtement des dix
  frontières pendant qu'une erreur de découpe coûte encore peu.

### Salve 3 — la méthode

- **Protocole typé + double conforme à chaque frontière.** Chaque module publie une interface
  (`typing.Protocol` + modèles Pydantic) et un double livré avec lui ; tout module se teste contre les
  doubles de ses dépendances, jamais contre leur implémentation. Une frontière fausse se détecte à
  l'écriture du double, pas à l'intégration.
- **`MODULE.md` colocalisé** dans `src/<module>/` — **modules à la racine de `src/`, sans package
  intermédiaire `pithos/`**. **Conséquence d'ordre :** l'arborescence de code
  doit exister avant toute spécification — le premier acte physique du projet est un scaffold de répertoires
  vides portant dix `MODULE.md`, écrits avant la moindre ligne de Python.
- **Distribution unique, `resources/` hors dépôt.** `~/code/pithos_reloaded` n'est pas encore un dépôt Git
  et `resources/` pèse **475 Mo**. Un `resources/MANIFEST.md` versionné fige nom, version et empreinte de
  chaque source ; les pointeurs `fichier:ligne` restent traçables sans versionner du code tiers.
- **Tranche verticale d'abord**, puis élargissement dans l'ordre P0→P9.

### Consolidation documentaire, dans la même séance

Trois ajustements demandés après la restitution des douze arbitrages, et appliqués immédiatement :

- **Modules à la racine de `src/`**, sans package intermédiaire `pithos/`. Supprime un niveau et le risque
  de nommage qu'un module `git` aurait posé sous `pithos.git`.
- **`git/` et `notify/` regroupés en `broker/`** — voir la salve 1 ci-dessus, corrigée en conséquence.
- **Documentation ramenée de six fichiers à quatre** : `ELN.md` fusionné dans `EXPLANATIONS.md` (deux
  parties — décisions, puis journal), `docs/SUCCUBUS.md` déplacé en `resources/IMPORT_REPORT.md`.
  Formalisé en **décision 33** : *un document vit à côté de ce qu'il décrit*.

### Ce que la propagation a produit

- **323 lignes de verdict reclassées** dans le rapport d'import : `Copier` → `Traduire` pour les 90 reprises
  Kilo, `Porter` → `Copier` pour les 136 reprises Ouroboros, et les 59 reprises Prime Agent réparties par
  extension de fichier source — `.py` en `Copier`, `.ts` en `Traduire`. Les 38 `Transposer` deviennent
  `Adapter`. Vocabulaire final : **250 Copier, 126 Traduire, 101 Adapter, 40 Inspirer**.
- **Cinq parties sans colonne `Verdict`** — B, F, G, H, I, environ 600 lignes écrites avant que le
  vocabulaire soit fixé — reçoivent un **défaut déclaré au niveau de la partie** plutôt qu'une
  requalification à l'aveugle. Toutes à `Adapter`, sauf les quatre reprises prioritaires de SWE-agent
  (Python MIT) en `Copier`.
- **Trois décisions ajoutées** : 31 (la mémoire s'écrit au socle, s'en servir pour se réécrire vient après),
  32 (un module se développe contre un double), 33 (un document vit à côté de ce qu'il décrit). Et cinq
  amendements — décisions 5, 13, 19, 25, 26.
- **Une phase de roadmap neuve, `M`**, entre les spikes et P0 : `git init`, arborescence `src/`, dix
  `MODULE.md`, dix protocoles et dix doubles, test de graphe des trois règles, puis le jalon « premier
  vert ». Le magasin quitte P9 pour P0, et la « fusion `skill`/`registry` » cesse d'être un item : c'est un
  objet unique dès P0.
- **`resources/MANIFEST.md` créé** : 475 Mo, 28 648 fichiers, licence et fiabilité d'extraction par dépôt.
  C'est ce qui rend légitime de ne pas versionner les neuf sources tout en gardant leurs pointeurs
  vérifiables.
- **Une correction de décompte.** J'ai annoncé « 16 critères de socle » pendant les QCM ; le chiffre 16
  était celui des critères **ajoutés** par les neuf sources, pas le total. Le socle en compte **26**, et
  **27** avec la décision 31. La décision — les garder tous, précédés d'un jalon — ne change pas.

## 06:09 — Passe de simplification, module par module

Objectif : pour chaque module, mesurer la complexité réelle — nombre de reprises, de fichiers sources à
lire, de fonctions et d'objets — puis couper. Méthode assumée : **partir simple, ajouter ensuite.**

### La mesure qui ouvre la passe

| Module | Reprises | Fichiers sources | Cible | Reprises / 100 L |
|---|---:|---:|---:|---:|
| `verifier` | 157 | 62 | 1 400 L | 11 |
| `campaign` | 153 | 91 | 700 L | 22 |
| `kernel` | 141 | 71 | 600 L | 24 |
| `workspace` | 141 | 76 | 500 L | 28 |
| `engine` | 140 | 70 | 900 L | 16 |
| `observatory` | 117 | 77 | 400 L | 29 |
| `lifecycle` | 109 | 60 | 400 L | 27 |
| `bridge` | 104 | 50 | 300 L | **35** |
| `broker` | 90 | 53 | 550 L | 16 |
| `refinery` | 45 | 18 | 150 L | 30 |

**La densité de reprise est le vrai signal, pas la taille.** `verifier`, le plus gros module, est le **moins**
saturé — une grande part y est du code neuf. `bridge` à 300 L doit absorber 104 reprises : arithmétiquement
impossible sans couper.

### `kernel` — quatre ajustements

Diagnostic : **`kernel` n'était pas un vocabulaire mais quatre modules empilés**, dont un seul est du
vocabulaire. `trace` portait à lui seul ~55 reprises — rotation, quarantaine base64, séquence dense,
validation incrémentale de reprise — soit plus que la cible du module entier.

- **`trace` sort de `kernel` et devient le module `journal`.** Onzième module. `kernel` redevient purement
  déclaratif. Le coût est nommé : on rouvre un nombre de modules fixé le matin même, et `journal` est
  importé par les dix autres. Le bénéfice : la couche de durabilité a enfin une cible et des tests propres,
  et `kernel` cesse d'être le fourre-tout par défaut.
- **La rédaction de secrets tombe à une fonction** : `redact(structure) -> (valeur, chemins_rédigés)`,
  alimentée par une liste de motifs nommée, ~25 L. Les quatre couches de reconnaissance de clé d'Ouroboros
  sont réduites à cette liste. **Et le `SecretRedactingLogFilter` est retiré du catalogue** — la décision 10
  exclut `logging`, il n'y a rien à filtrer. Première reprise écartée pour inapplicabilité, pas pour coût.
- **`codeview` est scindé par nature et réduit au socle.** *Lire et parser* reste dans `kernel` — AST,
  arité, `def` de module, snippet borné, `classify_repo_path`. *Sélectionner et scorer* — `relevant_files`,
  `impact_files`, fermeture d'imports — part dans `engine/context`, où ça appartient : c'est du contexte,
  pas du vocabulaire. Au socle, ni index persistant ni reconstruction incrémentale : ils arrivent quand
  relire le dépôt de campagne coûtera quelque chose. **~180 L au socle au lieu de ~350.**
- **Cinq modèles au socle, une seule classe d'erreur.** `Node`, `Criterion`, `Event`, `FileFact`, `Receipt` —
  ceux que la tranche verticale traverse. `Proposal` et `ToolEntry` arrivent avec `campaign`, `RepoFact` avec
  `broker`, `HostFact` avec `lifecycle` : **un contrat s'écrit quand son producteur existe.** Une classe de
  base plus un **enum de cause fermé** remplacent la taxonomie d'erreurs par cas de Kilo — l'enum se compose
  directement avec l'accumulateur à chemin de champ de la décision 28.

### Ce que la sortie de `trace` fait aux niveaux de dépendance

```text
niveau 0   kernel                                        aucun import interne
niveau 1   journal                                       kernel
niveau 2   verifier · bridge · workspace · lifecycle     kernel, journal
           broker · observatory
niveau 3   engine                                        niveaux 0-2
niveau 4   campaign                                      niveaux 0-3
niveau 5   refinery                                      niveaux 0-4
```

`journal` possède **le format**, donc les deux sens : `observatory` lit par lui plutôt que de reparser le
JSONL de son côté.

### `journal` — quatre ajustements

**~51 reprises** viennent de la couche durable, dont 39 explicitement ciblées `trace`. **Zéro dépendance
externe** — `os`, `json`, `fcntl`, `hashlib`, `base64`, `pathlib` : c'est le seul module du projet dans ce
cas, et c'est une propriété à préserver.

- **Un verrou global unique pour tout `journal`**, ~15 L, plutôt qu'un verrou sidecar par fichier nommé par
  SHA-256 (~40 L). Cohérent avec « une mission à la fois, sous `RunLock` ». Le coût est nommé : il sérialise
  des écritures qui n'entrent jamais en conflit.
  **Et la conséquence à ne pas oublier** : un verrou d'écrivain ne protège pas le lecteur, puisque
  `observatory` n'en prend aucun. Ce qui protège le lecteur d'une ligne déchirée reste **une seule syscall
  `write()` par ligne** plus **un lecteur qui tolère une queue déchirée**. Les deux exigences sont
  indépendantes ; le verrou n'en dispense pas.
- **Une écriture, deux sorties.** `emit(event)` écrit la ligne JSONL complète puis sa projection d'une ligne
  dans `live.log`. Un seul chemin d'écriture, donc **impossible qu'un événement soit dans l'un et pas
  l'autre** ; et `live.log` devient explicitement dérivable, donc jetable et reconstructible. La décision 29
  s'applique : la projection déclare qu'elle omet le payload.
- **Champ `v` par ligne + signature de génération de fichier.** Le champ de version coûte une ligne et rend
  toute migration future possible. La signature d'Ouroboros — hash de la première ligne plus taille — permet
  à lecteur et écrivain de savoir qu'ils parlent du même fichier. **Le tableau `MIGRATIONS` de Kilo est
  écarté** (~80 L) : le JSONL étant append-only et jamais réécrit, une migration est un lecteur qui tolère
  deux versions, pas un script qui transforme le passé — ce que la contrainte dure n°6 interdit.
- **`journal` parse, `observatory` agrège.** `journal` expose l'itération, la lecture bornée et la détection
  de queue déchirée : **un format, un parseur.** L'index mémoire et les agrégats sont à `observatory`. Même
  coupe que sur `codeview` — parser d'un côté, choisir de l'autre.

### Une découverte de mesure, corrigée au passage

En relisant les dix sections `kernel` du rapport d'import, **~15 lignes sur 141 ne sont pas du vocabulaire** :
`F3.1` en entier (résolution de backend, espace disque, temporaires, parallélisme) appartient à `lifecycle` ;
`G3.1` en entier (normalisation d'URL, headers d'auth, compatibilité de version) et deux lignes de `H4.1`
(config de retry, contrat de modèle) appartiennent à `bridge`. Les sections `kernel` des parties tardives ont
servi de fourre-tout. Charge réelle de `kernel` : **~126 reprises, pas 141** — et `bridge`, déjà le plus
saturé du projet, en gagne huit.

### `verifier` — quatre ajustements, et la plus grosse coupe de la passe

**157 reprises, 62 fichiers sources, cible 1 400 L.** Densité la plus faible du projet (11 / 100 L), mais
c'est trompeur : le module portait **cinq autorités** — invariant (0 reprise, l'apport propre), reçu (~30),
gate (~40), admission (17), parsing (15).

**Le constat qui structure les quatre coupes :** plusieurs reprises défendent contre un modèle qui **compose
ses propres commandes shell** et **écrit ses propres assertions**. La contrainte dure n°1 et la décision 6
ont supprimé les deux. Une garde contre une surface fermée n'est pas de la prudence, c'est du poids mort.

- **Les trois capteurs de faux-vert sont écartés comme inapplicables**, avec leur raison écrite. Capteur 1
  (masquage d'exit par `|| true`, `>/dev/null`, tube vers un filtre) : le script d'invariant est **rendu par
  le harness**. Capteur 2 (build-puis-delete) : subsumé par la preuve d'effet contenu avant/après croisée
  avec `git diff`, qui est un critère de socle. Capteur 3 (`criterion_source`) : structurellement constant,
  puisque la relation vient d'un catalogue fermé et les entrées du harness. **~250 L évitées.**
  Deux reprises du même fichier sont gardées, parce qu'elles ne dépendent d'aucun modèle de menace :
  **aucune coercition `or` sur un code de retour** (`None or 0` lisait un résultat inconnu comme un succès)
  et `cmp` où **`>1` signifie panne d'outillage**, pas différence.
- **Le catalogue de douze parsers est écarté** : il existe chez SWE-agent pour des backends sans sortie
  structurée native ; nous avons un seul chemin, `response_format` json_schema revalidé localement contre le
  schéma exact envoyé. **Une sortie non conforme est rejetée, jamais récupérée** — récupérer une sortie mal
  formée par extraction, c'est laisser passer un littéral du modèle par une autre porte. Deux notions
  seulement survivent, et elles vont dans `bridge` : rejeter un appel de fonction inconnu, et **localiser**
  l'erreur JSON (ligne et position) au lieu de rendre le stdout brut. **~200 L évitées.**
- **La planification de gate par coût croissant est écartée.** `validation_loop.py` ordonne
  `format → lint → typecheck → test` avec inférence de portée, inférence de cibles et politique d'escalade —
  or **la stack actée n'a ni linter ni typechecker** : notre échelle a une seule marche, il n'y a rien à
  ordonner. **~150 L évitées.** Quatre primitives sont gardées parce qu'elles servent à chaque exécution :
  `compact_failure_output` (tête + queue bornée), `summarize_validation_failure` (classe d'échec et lignes
  d'erreur pertinentes), `_is_launch_failure` (**exit 127 = la commande n'existe pas, ce n'est pas un test
  rouge**), et la normalisation de commande en `[sys.executable, "-m", …]`.
- **L'admission déclarative quitte `verifier`.** Le **mécanisme** — accumulateur d'erreurs à chemin de champ,
  toutes les violations d'un coup — descend dans `kernel` avec l'enum de cause déjà décidé ; il servira aussi
  à la revalidation de schéma de `bridge`. Les **règles** — regex, alphabet sans métacaractères shell,
  préfixes autorisés, bornes de longueur, placeholders fermés sans expression évaluable — montent dans
  `campaign`, qui possède les propositions. `verifier` passe de cinq autorités à trois.

**Bilan : cible 1 400 → ~800 L au socle, ~950 L avec la gate hermétique** (conditionnée au spike n°5). Et
**la seule ligne à zéro reprise du tableau reste le cœur du projet** : `relations`, `domains`, `mutation`.

### `bridge` — quatre ajustements sur le module le plus saturé

**~107 reprises pour 300 L, soit 36 / 100 L** — le plus saturé du projet, après deux corrections : `G3.1` et
`H4.3` mal ciblés en `kernel` lui en ajoutent 10, et `F3.3` lui en retire 7 qui appartiennent au **produit
MCP**, dépôt séparé (décision 4). Quatre natures y cohabitaient : la frontière modèle (~30), le transport
HTTP (~50), la sonde de capacité (~12), le prompt et l'échantillonnage (~5). **Une seule est le point
d'application de la contrainte dure n°1.**

- **Pas de streaming.** Un `POST` bloquant, timeout 300 s, une réponse JSON complète revalidée localement.
  Pi énonce lui-même la règle qui rend le flux inutile ici — *« ne jamais exécuter un JSON partiel ou
  réparé »* — et **l'incident de contexte le plus grave de v1 était un incident de streaming** : 12 419
  `thinking_delta` consécutifs, zéro tool call. **~10 reprises écartées.** La séparation thinking/contenu
  reste obligatoire (décision 17), mais sur la réponse complète : trois lignes au lieu d'un parseur
  d'événements. Le signal de vivacité vient de la borne murale et d'une ligne d'attente dans `live.log`.
- **Un client de ~30 lignes, aucune abstraction de fournisseur.** Celui de Villani, 23 L, plus
  `response_format` au point d'insertion déjà repéré. **Écartés** : transformations par fournisseur derrière
  une frontière, sélection de prompt par famille, et surtout `convert_openai_response_to_anthropic` — **du
  legacy v1 : aucun chemin Anthropic n'existe, la contrainte dure n°5 l'exclut.** Écartés aussi, pour une
  raison plus simple encore, **tous les mécanismes de credential** — headers d'auth, `route_fingerprint`
  excluant les secrets, résolution de clé par priorité : **Ollama local n'a aucune authentification.**
  **Gardés** : `finish_reason` avec `length` distingué de `stop` (une génération tronquée n'est pas une
  réponse), retries SDK désactivés, corps d'erreur borné avec le complet dans l'artefact, annulation qui ne
  tue pas l'opération. **~40 L évitées.**
- **La sonde tombe de ~200 à ~40 L.** Trois contrôles : lire `n_ctx_train` sur `/v1/models`, envoyer **un**
  schéma `Criterion` réel et vérifier que la réponse revalide, refuser de démarrer sinon. Plus cinq lignes
  qui valent leur coût : la fenêtre porte sa **provenance** en enum à trois valeurs — `confirmed` /
  `asserted` / `unprobeable` — et `unprobeable` est **fail-closed**. Écarté : `test_tool_calling`, qui sonde
  une capacité que le mode `direct` n'utilise pas.
- **Le prompt système est un fichier de données, démarré à ~20 lignes.** `src/bridge/prompt/ling.md`, hors
  du décompte de lignes du module, au même titre que les paramètres d'échantillonnage (décision 20 : ce sont
  des données mesurées). Et **court, pas 129 lignes** : aucun des sept modes d'échec de Ling documentés par
  Kilo n'a été mesuré sur *nos* prompts, et un prompt de 129 lignes consomme une part notable des 16 k à
  chaque appel. **Chaque ajout ultérieur doit citer la mission où le mode d'échec a été observé** — le
  prompt devient un journal de contre-mesures, pas un pavé hérité.

**Bilan : ~107 reprises → ~50, et 300 L de cible qui deviennent réalistes à ~250 L.**

### `workspace` — quatre ajustements, et un amendement de la décision 9 renversé

**141 reprises, 76 fichiers sources, cible 500 L**, réparties sur six sous-domaines dont deux avaient des
sorts opposés malgré leur apparente proximité.

**La distinction qui décide de tout ici :** en mode `direct`, le modèle émet `{function_name, new_source}` et
`{relation, symbols, domain}`. **Il n'émet aucune commande shell — donc il n'y a rien à autoriser. Mais son
code *est* exécuté — donc le confinement reste nécessaire.**

- **`permission` est écarté, `sandbox` est gardé.** Écartés : `PermissionEngine.evaluate_with_reason`
  (deny → ask → allow), `classify_bash_command` par préfixe de tokens, `bash_matches` conscient des
  opérateurs, **l'arité des commandes shell — 161 L chez Kilo**, le découpage d'une ligne shell, les
  permissions de sous-agent. **~200 L évitées**, raison écrite, réactivables si le mode `agentic` s'ouvre.
  `sandbox` garde sa phase P7bis : `new_source` finit dans un `subprocess`.
- **La transaction est une copie d'octets, et la cible unique devient un type.** `before = read_bytes()`
  avant, `write_bytes(before)` si non vert : **~10 L au lieu de ~150.** Et la contrainte dure n°3 cesse
  d'être une convention — `Node.target` est un `Path`, **pas une liste** : une nano-étape qui voudrait
  toucher deux fichiers ne peut pas se construire.
  **Cela renverse l'amendement de la décision 9** (« le snapshot est un dépôt Git fantôme »), au socle
  seulement : le dépôt fantôme revient le jour où une étape devra toucher plusieurs fichiers, et la raison de
  son report est écrite. **Bénéfice en cascade** : le compare-and-swap de la décision 9 devient *gratuit*,
  puisqu'on détient déjà `before` — comparer le contenu courant à `before` avant d'écrire fait trois lignes.
- **La machinerie de patch est écartée, une notion est gardée et généralisée.** *Valider tout, puis
  appliquer* : chez Villani c'est `# apply atomically after validation` sur un lot de patchs ; chez nous
  c'est **parser, vérifier le `def` unique, contrôler l'arité et compiler avant la moindre écriture.** Plus
  `_detect_newline_style`, trois lignes qui préservent CRLF et BOM.
- **Six gardes devant une écriture**, dans cet ordre : chemin assaini **et** `authoritative` → parse en `def`
  unique au bon nom → arité compatible → `py_compile` du fichier splicé → refus d'une écriture sans effet →
  compare-and-swap contre `before`. **Écartés : `MutationGuardThresholds` et `_analyze_text_rewrite`** — le
  splice par plage AST borne le rayon d'action par construction. Une réécriture massive n'est pas un cas à
  détecter, c'est un cas que le mécanisme ne peut pas produire. C'était la seconde ligne de défense de v1
  derrière un chemin d'écriture qui n'existe plus.

**Bilan : 141 reprises → ~40, et 500 L → ~200 L au socle**, plus ~150 L de `sandbox` en P7bis.

### `engine` — quatre ajustements, dont deux qui s'écartent de la recommandation

**~150 reprises** (140 catalogués plus la sélection de fichiers récupérée de `codeview`), **70 fichiers
sources**, cible 900 L.

- **Le classifieur d'instruction est porté**, contre la recommandation de l'écarter. `analyze_instruction`
  et ses cinq enums fermées (`PlanRiskLevel`, `ActionClass` à 13 valeurs, `EstimatedScope`, `ChangeImpact`,
  `TaskMode`) dérivent du repo les cibles candidates, la classe d'action, la portée et l'impact — **zéro
  appel modèle**. ~200 L.
  **Condition pour que ce ne soit pas du code mort** : sa place chez nous n'est pas d'évaluer un risque mais
  de **dériver les enfants d'un nœud sans appeler le modèle**. Une décomposition déterministe est
  strictement plus alignée sur la contrainte dure n°1 que de demander au modèle de scinder. Les enums
  apparaissent aussi dans la trace, pour qu'une campagne s'analyse a posteriori.
- **`ExecutionBudget` et `VILLANI_TASK_BUDGET` sont écartés**, sur un fait distinct : 20 tours, 40 tool
  calls, 8 outils, `max_no_edit_turns`, `max_reconsecutive_recon_turns` sont des bornes **de tours**, et le
  mode `direct` fait un appel par nœud. Remplacés par le deadline mural plus **un entier de tentatives par
  nœud**. Gardés : `InterruptController` (premier signal interrompt, second quitte — 18 L) et `RepairContext`
  comme payload borné en champs typés, sans la boucle de réparation qui l'entoure.
- **Le dump de contexte remplace la compaction.** La compaction en session est écartée — chaque nœud reçoit
  une **session neuve**, il n'y a aucune conversation à compacter, et un résumé serait du texte de modèle
  entrant dans le prompt suivant. À la place, un **artefact de passation** :
  `~/logs/pithos2/missions/<mission_id>/CONTEXT.md`, un fichier par mission, **une section ajoutée à chaque
  fin de session** — nœud, critère, inclusions et exclusions avec leur raison, palier de pression,
  évictions, verdict, et **l'empreinte des fichiers décrits au moment de l'écriture**.
  **Écrit par le harness, pas par le modèle** : l'inventaire typé de la décision 14 existe déjà, le rendre en
  markdown est déterministe et coûte ~30 L, sans appel supplémentaire ni contrat de résumeur.
  **Et l'empreinte n'est pas décorative.** Le mode d'échec n°2 mesuré de v1 était un brief décrivant une
  fonction déjà mergée — 12 419 `thinking_delta`, zéro tool call. **Un fichier de suivi réinjecté a
  exactement cette forme.** Il est donc traité comme n'importe quel élément de contexte : sélectionné sous
  budget, avec une raison d'inclusion, et soumis à `detect_stale_context` — une section dont l'empreinte a
  bougé est **exclue avec sa raison**, jamais injectée en silence.
  Écartés : compacteur par type de source, contrat de résumeur haché, unités `tool_use`/`tool_result`
  inséparables (~150 L). L'éviction sous pression reste la règle **dans** la session.
- **Frontière avec la famille `memory` (décision 31)**, pour que les deux objets ne se recouvrent pas :
  `CONTEXT.md` est une projection lisible et narrative, de portée **une mission**, ordonnée
  chronologiquement. La famille `memory` est un magasin machine, de portée **toute la campagne**, indexé par
  empreinte de contrat. Deux durées de vie, deux consommateurs.
- **Un deadline monotone et une réserve fixe.** `time.monotonic()`, une borne souple, et une réserve de
  finalisation en constante au-delà de laquelle on n'ouvre plus de nœud mais on finalise les verts. ~30 L.
  Le seam transport/logique est conservé — un timeout HTTP n'est pas un jalon logique. **EWMA, latch d'ancre
  et `CostCeiling` arrivent après les dix premières missions**, exactement quand `PROJECT.md` prévoit de
  fixer la valeur de la borne : calibrer par EWMA avant la première mesure, c'est calibrer sur rien.
- **`tree.json` reste l'état du domaine**, plus deux notions du ledger d'Ouroboros.
  `child_result_disposition` — un parent enregistre **par enfant** ce qu'il a fait de son résultat
  (`integrated`, `rejected`, …), ce qui rend une décomposition auditable. Et `cap_children`, **la borne de
  largeur qui manquait au projet** : le plafond dur de 3 porte sur la profondeur, rien n'empêchait un nœud de
  se scinder en cinquante enfants. Écartés : ledger append-only parallèle à `tree.json`, curseurs,
  pagination à hash de snapshot, bornes de 2 Mo, `halt_fanout` et les autres directives de délégation.

### `campaign` — quatre ajustements sur le module qui lit le plus de sources

**~168 reprises** (153 catalogués plus ~15 règles d'admission venues de `verifier`), **91 fichiers
sources — le plus de tous les modules**, cible 700 L. Le chiffre qui décide : **le magasin portait un
portage de 820 L pour une cible de module de 700 L.**

- **Deux familles au socle, pas quatre.** `skill` — qui **est** le registre d'outils — et `memory`
  (décision 31) ont un consommateur ; `prompt` n'en a qu'un, `refinery`, qui est `enabled: false`, et
  `subagent` est vide. Or tout ce qui est lourd dans `rt/harness.py` — deux scopes, rollback par
  reconstruction inverse, label mobile séparé de la version immuable, clé de cache typée — **existe pour
  éditer des `prompt`**. Chaque entrée garde `version` entier, horodatages et `source` (~5 L).
  **~150 L au lieu d'un portage de 820 L.** Gardée intégralement parce qu'elle est le cœur du spike n°6 :
  **la relecture défensive champ par champ qui ne lève jamais** — un magasin écrit par un modèle doit se
  relire sans exception.
- **Le modèle propose, la dérivation est un filet.** Le backlog ouvert reste le sujet d'étude ; la
  dérivation déterministe (`discover_opportunities` plus le classifieur porté dans `engine`) ne se déclenche
  **qu'après trois rejets consécutifs** pour redondance ou malformation, afin qu'une mission ne soit pas
  stérile. **Les deux compteurs sont séparés dans la trace** : l'indicateur de la question expérimentale
  reste mesurable, et le filet devient lui-même une mesure — *à quelle fréquence le modèle n'arrive-t-il pas
  à proposer ?*
- **Le classement est un tuple lexicographique d'axes nommés**, par exemple
  `(a_une_preuve, est_authoritative, récurrence, -profondeur)`. Aucune constante magique, chaque départage
  inspectable, et l'ordre des axes est une décision écrite plutôt qu'un poids. **Écartés** :
  `effective_priority = priority*0.7 + confidence*0.3` et `_RANK_ORDER` en dur par titre. Cohérent avec la
  décision 23 et avec le refus du score de confiance déjà acté dans `verifier`.
- **Trois notions de registre gardées, trois écartées.** Gardées : `capability_omissions` — la surface
  projetée porte la **raison typée** de ce qui manque, soit la décision 29 appliquée au registre ; **un
  module d'outils qui échoue à l'import omet *tous* ses outils**, mode d'échec réel et silencieux du produit
  MCP ; et `TaskLifecycle` à sept états dont **trois formes d'échec distinctes** — « échec » n'est pas un
  état. Écartés : `policy_hidden_reason` (aucune politique ne cache d'outil), `alias_for` (aucun renommage
  avant plusieurs outils), `mutates_worktree` (notre snapshot est inconditionnel et fait 10 L), et
  `TakeoverConfig` avec ses vagues — nous avons des missions et une borne murale.

### `lifecycle` et `broker` — quatre ajustements, dont deux qui refusent la coupe

Les sections du rapport d'import traitent les deux ensemble : elles étaient un seul module jusqu'au matin
même. **~205 reprises** (109 + 90, plus les 6 de `F3.1` récupérées de `kernel`), cibles 400 + 550 L.

- **`observatory` binde `127.0.0.1` en dur, non configurable.** L'adresse d'écoute est une **constante**, pas
  un réglage : aucun chemin de code ne peut binder ailleurs. Une ligne, et toute la politique d'exposition
  devient sans objet — `is_public_address`, résolution DNS, détection d'IP littérale, normalisation des binds
  wildcard, validation `Host`/`Origin`. **~120 L évitées.** La décision 27 est tenue dans sa lettre : « LAN
  différé » cesse d'être l'absence de règle, parce que **l'interdiction est dans le type, pas dans la
  configuration**. Gardé, parce que c'est un critère de socle et que `observatory` est un vrai service :
  readiness observable sous deadline, arrêt idempotent, état de sortie confirmé, fermeture des sockets
  partiellement ouverts sur échec de bind.
- **Le verrou : répertoire + `(pid, heure de démarrage)` + péremption par durée.** ~40 L, **aucun thread**.
  Le `RunLock` de v1 porté tel quel, la paire de Prime contre le PID recyclé, une péremption par durée
  maximale qui domine tout le reste, et l'état `indisponible` de Langfuse qui **bloque** au lieu de procéder.
  Le heartbeat est écarté au socle : il ne détecte qu'un processus **vivant mais bloqué**, cas déjà couvert
  par la borne murale de `engine` et le `timeout_seconds` de Prefect en kill de dernier recours. Il arrive si
  un incident de verrou coincé se produit réellement.
- **Telegram bidirectionnel intégral dès le socle**, contre la recommandation de n'en garder que le sortant.
  Les cinq commandes de v1 — `/status`, `/latest`, `/pause`, `/stop`, `/answer` — avec offsets persistants,
  idempotence de requête et allowlist utilisateur. ~200 L de code éprouvé.
  **Deux conséquences à tenir** : la boucle de polling est un **processus à cycle de vie propre**, donc géré
  par `lifecycle` comme tout autre processus, avec sa custody et son arrêt confirmé ; et `/pause` et `/stop`
  doivent atteindre le marcheur, ce qui donne à `engine` un **chemin d'interruption** — c'est exactement
  l'`InterruptController` déjà gardé (premier signal interrompt, second quitte).
- **Le broker Git de v1 est porté complet**, contre la recommandation du Git local seul : `subprocess` +
  `gh`, politique de branche et de PR, auto-merge après gate verte. 225 lignes qui ont produit dix PR réelles
  et dont la valeur est de *restreindre* les opérations.
  **Conséquence à tenir** : la surface de sortie de données reste double — Git distant **et** Telegram. La
  règle d'import « `broker` est le seul module par lequel une donnée quitte la machine » cesse d'être une
  formalité et devient le seul test qui garde la contrainte dure n°5. Gardés en plus : validation des
  arguments Git avant passage à la CLI, préflight dépôt sale, **ne jamais assimiler un checkpoint Git à un
  commit**, ne publier que des fichiers explicitement désignés.

**Bilan : `lifecycle` de 400 → ~250 L. `broker` reste à ~550 L, assumé comme du réemploi.**

### `observatory` et `refinery` — quatre ajustements, dont un qui rouvre un critère

**117 et 45 reprises**, cibles 400 L + 700 L web et 150 L. Le web est déjà écrit : ~700 L React 19 + Vite
portés de v1, six tests jsdom verts, design fait — restent la vue d'arbre et le rebranchement de la source.

- **Les agrégats d'analyse deviennent des routes de l'API**, contre la recommandation de les différer. Les
  cinq scripts de Pi — statistiques journalières, stats par outil, inflation de patch, occupation du contexte
  par appel — sont implémentés comme routes FastAPI consommées par le web. ~150 L de plus dans
  `observatory`, et **les cinq indicateurs des questions expérimentales deviennent visibles sans terminal**.
  Conséquence à tenir : l'analyse expérimentale dépend désormais du dashboard tournant.
- **Toute écriture d'observabilité est encapsulée** — la règle absolue de Villani, appliquée sans exception,
  contre la recommandation de discriminer par le flag `durable`.
  **Et voici la forme qui la rend compatible avec la décision 13**, parce que les deux exigences portent sur
  deux moments distincts : **écrire n'échoue jamais ; compter vert exige le reçu écrit.** C'est exactement
  `_receipt_custody_failure` d'Ouroboros, déjà gardée dans `verifier` — *un reçu non écrit retire
  l'attestation*. L'écriture est encapsulée et ne lève jamais ; c'est **l'absence du reçu, constatée après
  coup**, qui empêche le nœud d'être vert, avec la cause `receipt_not_written`. La mission survit à un disque
  plein et n'en sort aucun faux vert.
- **Zéro ligne de `refinery` au socle, mais la baseline est mesurée dès la mission 1.** `engine` écrit à
  chaque fin de mission le triplet qui la constitue : nœuds verts / nœuds tentés, temps mural consommé, cause
  de sortie. ~5 L dans une trace qui existe déjà. Sans eux, activer la gate d'effet au bout de dix missions
  reviendrait à comparer un chiffre à rien — or **vérifier que le raffinement améliore quelque chose est la
  seule chose que `refinery` apporte de neuf par rapport à Prime Agent.**
- **`refinery` garde deux fonctions et reste un module.** `plan_refinement` — plan déterministe, zéro appel
  modèle, l'appel n'étant qu'un dernier recours en mode non-raisonnant — et la **gate d'effet**. ~100 L.
  Sont partis avec le magasin, parce que ce sont des opérations *du magasin* : rollback par reconstruction
  inverse, application par cas fermés, injection bornée par famille, label mobile. **Rester un module a une
  valeur précise** : son `MODULE.md` porte par écrit pourquoi il est éteint et ce qui conditionne son
  allumage — une politique invisible dans `campaign` s'allumerait un jour sans que personne ne relise sa
  condition.

### Résultat de la passe

| Module | Reprises avant → après | Cible avant → après |
|---|---|---|
| `kernel` | 141 → ~50 | 600 → **380** |
| `journal` *(neuf)* | — → ~51 | — → **400** *(~150 au socle)* |
| `verifier` | 157 → ~75 | 1 400 → **950** |
| `bridge` | ~107 → ~50 | 300 → **250** |
| `workspace` | 141 → ~40 | 500 → **200** *(+150 en P7bis)* |
| `engine` | 140 → ~120 | 900 → **1 050** |
| `campaign` | ~168 → ~140 | 700 → **550** |
| `lifecycle` | 109 → ~70 | 400 → **250** |
| `broker` | 90 → ~80 | 550 → **550** |
| `observatory` | 117 → ~110 | 400 → **550** + 700 web |
| `refinery` | 45 → ~15 | 150 → **100** |
| **Total** | **~1 180 → ~800** | **5 900 → ~5 230 L** |

**~380 reprises écartées, ~670 lignes de cible en moins**, malgré un module ajouté, le classifieur porté et
les agrégats montés dans l'API.

**Deux renversements de hiérarchie.** `engine` devient le plus gros module du projet — le classifieur porté
et la sélection de fichiers y ont atterri. Et `verifier` cesse d'être dominant : il perd 600 L de gardes.

**Le fil rouge, en une phrase :** presque tout ce qui a été écarté défendait contre un **agent libre** —
commandes shell à autoriser, assertions écrites par le modèle, conversation accumulée à compacter, couche
multi-fournisseurs. La contrainte dure n°1 et la décision 6 avaient déjà fermé ces surfaces ; les catalogues
les rouvraient par habitude, parce que leurs auteurs construisaient tous un agent libre.

### Décisions amendées par cette passe

| Décision | Ce qui change |
|---|---|
| **8** | Une réserve fixe au socle ; EWMA, latch d'ancre et `CostCeiling` après dix missions |
| **9** | Le snapshot est une **copie d'octets** au socle, pas un dépôt Git fantôme ; le CAS devient gratuit |
| **10** | Le flag `durable` reste, mais **toute** écriture d'observabilité est encapsulée |
| **13** | Les trois capteurs de faux-vert sont écartés ; **un reçu non écrit retire l'attestation** porte seul la garde |
| **14** | La compaction est remplacée par un **dump de contexte** en fin de session, écrit par le harness |
| **17** | Pas de streaming : une requête, une réponse complète, revalidée |
| **21** | `sandbox` gardé, `permission` écarté — le modèle n'émet aucune commande mais son code est exécuté |
| **26** | Magasin à **deux familles** vivantes au socle ; scopes, rollback et label mobile avec P9 |
| **27** | Bind `127.0.0.1` **en dur** ; l'interdiction est dans le type, pas dans la configuration |

---

## 06:09 — L'environnement d'exécution, fixé avant la première ligne de Python

Un audit de l'état du dépôt, juste avant de lancer le développement, a trouvé un trou entre la
documentation et le travail réel : **le dépôt n'était pas exécutable.** Pas de `pyproject.toml`, pas de
venv, pas de pytest — alors que `src/kernel/STATE.md` envoyait le premier agent écrire un test, et que
l'étape 4 de la boucle d'`AGENTS.md` § 5 dit *« lancer les tests du module »*.

La phase M posait `git init`, l'arborescence, puis les `Protocol` et les doubles. **Aucune de ses puces ne
rendait le dépôt exécutable.** C'est l'étape manquante, et elle passe avant toutes les autres — elle est
désormais la deuxième puce de § M.

### La version : 3.12.9, et c'est un choix

`AGENTS.md` disait jusqu'ici : *lis la version dans `pyproject.toml`, et s'il n'existe pas, écris du code
compatible 3.11*. Une consigne de repli qui aurait fait écrire du 3.11 sur une machine en 3.14.7, sans que
personne le décide.

**Virtualenv pyenv `pithos`, Python 3.12.9**, sélectionné par `.python-version`, borné par
`requires-python = ">=3.12,<3.13"`. Deux conséquences directes sur le style :

- **PEP 701** rend légaux les guillemets identiques imbriqués dans une f-string. La restriction héritée de
  3.9 — `f"{d['k']}"` obligatoire — **ne s'applique pas à ce dépôt**, et `AGENTS.md` le dit explicitement
  plutôt que de laisser un agent l'appliquer par réflexe.
- **PEP 695** ouvre la syntaxe de paramètres de type. Aucune syntaxe 3.13+ n'est admise.

### `requirements.txt` : huit lignes, chacune adossée à un `MODULE.md`

Le fichier déclare des bornes majeures, il ne fige pas — le choix `pip` étant sans lock, `pip freeze >
requirements.lock` reste ce qui rend une campagne rejouable. Chaque ligne se justifie par la rubrique
**Stack** d'un module, ce qui rend vérifiable la règle d'`AGENTS.md` § 6 : *une dépendance non déclarée dans
la stack du `MODULE.md` fait rejeter le code*.

| Quand | Dépendances |
|---|---|
| socle, dès `kernel` | `pydantic` · `httpx` · `hypothesis` |
| tests | `pytest` |
| P2/P4 | `prefect` · `typer` |
| P5 | `fastapi` · `uvicorn` |

Le fichier porte aussi, en clair, **ce qui n'a pas le droit d'y entrer** et pourquoi : `fastmcp` appartient
au produit et jamais au harness, `langgraph` au mode `agentic` différé, `GitPython` à une couche que
`broker` remplace par `subprocess` + la CLI `gh`, et `ruff`/`mypy` à une discipline que ce projet a refusée.
Sans cette liste, chaque agent qui bute sur une frontière réintroduira la dépendance que la frontière
existait pour éviter.

### Le piège que `prefect` pose au fichier

`engine/MODULE.md` exige que `walk` passe **sans Prefect installé** — c'est la garantie que le marcheur reste
pur et testable au pytest nu. Mais `prefect` est dans `requirements.txt`, donc installé.

L'invariant ne se teste donc **pas** en désinstallant Prefect : il se teste **par graphe d'imports**, comme
les trois règles d'import d'`AGENTS.md` § 3. La note est écrite dans `requirements.txt`, à côté de la ligne,
pour qu'un agent ne perde pas une heure à démonter son environnement.

### Ce que l'audit a trouvé d'autre, et qui reste ouvert

- **`.gitignore` ignore `docs/` et `resources/` en bloc.** Les cinq documents canoniques,
  `IMPORT_REPORT.md`, `MANIFEST.md` et les neuf fiches de dépôt — ~8 400 lignes — ne sont pas versionnés, et
  le dépôt compte un seul commit. L'intention de § M était d'exclure les 475 Mo de code tiers, pas le
  markdown. Forme vérifiée : `resources/*` + `!resources/*.md` — le `/` final de `resources/` bloque toute
  négation. **Laissé en l'état sur décision de l'auteur.**
- **`CLAUDE.md` à la racine est une copie octet pour octet d'`AGENTS.md`.** Deux copies d'un protocole
  amendé pendant des mois divergent. Conservé tel quel ; **toute modification d'`AGENTS.md` doit être
  recopiée dans `CLAUDE.md` dans le même geste.**
- **Sept dossiers vides ne survivront pas au clone** — `journals/`, `src/bridge/prompt/`,
  `src/observatory/{api,web}/`, `tests/{boundaries,contracts,doubles}/`. Git ne suit pas les répertoires
  vides.
- **Ollama ne tourne pas** (`could not connect to ollama server`). Les spikes n°2 et n°4 en dépendent, et
  n°4 peut rendre le cadran de pression de la décision 14 faux d'un palier entier.


## 11:09 — reprise autonome de TEMPO : preuve des tests et mémoire mesurée

La demande utilisateur a ouvert un chantier transverse. Le défaut de collecte avait déjà été corrigé
par la passe précédente ; cette reprise l’inscrit dans le protocole. Les implémentations métier
présentes ne sont pas réattribuées à cette passe et aucun MODULE.md n’est modifié ici.

### Contrôler le balayage, pas seulement le prédicat

Un scanner partagé énumère la production récursivement, refuse un périmètre vide et conserve le
chemin relatif complet. Les onze politiques gardent leurs interdits propres. Les tests appellent
leurs vrais points d’entrée sur copies, puis injectent une violation dans chaque fichier, y compris
un nouveau sous-paquet. Trois reproductions rouges supplémentaires ont montré que des exemptions
par basename pouvaient fuiter vers un sous-paquet homonyme ; elles sont maintenant limitées au
chemin exact. Neuf sondes de signature appellent le contrôle effectivement utilisé par leur corpus.
Le chargeur de doubles est unique et rend un module neuf à chaque appel, sans cache d’état partagé.

### Mesurer les en-têtes sans inventer l’état métier

Les lignes portant du code excluent blancs, commentaires et docstrings AST ; les littéraux de données
restent comptés. Les fichiers de façade et sous-paquets comptent ; les tests, conftest et doubles non.
Le nombre physique est affiché à côté, et les cibles globales numériques restent inchangées.
Six modules dépassent encore ces cibles : plafonds précis et justifications ajoutés aux STATE.
La mesure globale réfute l’idée que tous les écarts de campaign/refinery étaient de la documentation.
Leurs anciens chiffres restent comme observations historiques, pas comme compteur courant.

L’empreinte couvre chemins et octets de production : un changement sans nouvelle ligne doit aussi
être reporté. La date JJ:MM ne porte pas d’année ; seul son format calendaire est contrôlable.
Le statut est un choix fermé, incompatible avec « non commencé » dès qu’il y a du code. Ni un hash
ni une suite verte ne peuvent décider « fini » : les agents de module gardent cette responsabilité.
Les champs courants deviennent explicitement mutables, avec conservation du journal historique.

### Protocole, documentation et index

AGENTS § 14 définit les écritures transverses, leur foyer et leurs limites. CLAUDE.md reçoit le même
texte conformément à la règle du journal précédent. Les cinq documents de docs et les onze Markdown
à la racine de resources sont désormais visibles par Git ; les dépôts tiers restent ignorés.
Aucune donnée brute supprimée, aucune commande Git d’écriture : le retrait des 27 caches suivis et
l’ajout des documents sont préparés, avec chemins explicites, dans `tests/git.md`.
La précédente décision de laisser les exclusions telles quelles est amendée par la demande actuelle.
ELN reste dans la Partie II de ce document ; PROJECT conserve son cadrage produit.

### Résultats et limites

Dans la sandbox : **2 failed, 1173 passed, 3 skipped, 40 errors**. Bind loopback et observations de
processus macOS bloqués ; résultat conservé avant relance autorisée. Hors sandbox, avant changements :
**1215 passed, 3 skipped en 33,90 s**. Validation finale : **1 286 passed, 3 skipped, 7 warnings en 34,59 s**, Python **3.12.9**.
Les trois skips n’excluent que les variantes réelles de scénarios scriptables propres aux doubles.
Les sept avertissements Starlette/httpx et fork après threads subsistent sans modifier la stack.
Les contrats sont prouvés au **niveau 5**. Des effets locaux réels sont observés, mais aucun jalon
Ollama/campagne n’est démontré. Les blocages métier et le premier vert restent ouverts.

### 12:09 — reprise autonome : faits canoniques, gate et sélection

Autorisation de poursuivre module par module depuis les STATE. Les quatre premières unités publient
SourceFact/RepoFact, les producteurs workspace/broker, puis Verifier.run. L'état du monde traverse une
frontière de données typées ; verifier ne lit toujours aucun chemin du workspace et n'appelle pas Git.
Le fait source conserve ses octets via JSON hex, y compris BOM/CRLF. La complétude Git est fausse sans HEAD
ou avec non-suivis, dont le contenu ne figure pas dans diff HEAD. Le double broker reçoit une racine
explicite pour relativiser les FileFact absolus sans I/O.

La revue a reproduit trois diffs faux qui pouvaient atteindre la gate (contenu périmé, coordonnées fausses,
troncature) : ils sont désormais croisés avec les deux copies. Un autre test rouge a imposé de décompter
la validation des faits dans le budget transmis à check_sources. Le reçu revalide les faits et leur liaison
aux sources testées ; un succès de propriété n'est pas un acquittement de persistance.

En attendant la définition de la source candidate, engine/select.py a été livré : index d'imports injecté,
parcours en largeur dans les deux sens, cycles dédupliqués, distances et raisons, cible conservée.
La source Ouroboros a été relue et la notice MIT conservée ; sa résolution dynamique n'a pas été inventée.

Validation finale : **1 367 passed, 3 skipped, 7 warnings en 37,10 s**, pithos Python 3.12.9.
Une commande ciblant tout broker a échoué sur les sockets interdites de la sandbox : **93 passed,
21 erreurs en 1,88 s** ; relance autorisée **114 passed en 1,99 s**. Les erreurs restent dans STATE.
Contrôles d'en-têtes et de whitespace verts, aucune commande Git d'écriture ni installation.
**Niveau de preuve : 5** ; pas de campagne réelle, d'appel à Ollama ni de premier vert revendiqué.

La décision produit reste à prendre explicitement : autoriser du code candidat du modèle avec critères
et entrées de validation contrôlés par le harness, ou maintenir l'interdiction littérale et définir un
catalogue fermé de transformations. Aucun des deux choix n'a été appliqué en silence. PROJECT reste figé.
Les prochaines actions précises et propositions de commits sont dans les STATE/git.md de chaque module.

### 12:09 — amendement approuvé : code candidat et expérience audio

L'utilisateur répond « Tout à fait » à l'autorisation de proposer du code candidat en laissant critères
et entrées de validation au harness. La contrainte n°1 de PROJECT et AGENTS (miroir CLAUDE) est amendée :
l'interdiction porte sur l'attendu, les entrées de validation et les commandes d'exécution, pas sur le
corps Python candidat soumis au splice et au verifier. Les décisions historiques à formulation plus large
se lisent désormais avec cet amendement ; aucun test produit ne devient une assertion écrite par le modèle.

Le projet d'essai s'inspire uniquement de la vision et des micro-rushes du PROJECT de l'ancien visualiseur.
Pas de copie de son application, ses résultats acquis ou son rapport `.pithos/report.md`. Le nouveau contrat
vit dans `experiments/visualizer/PROJECT.md`. La souveraineté, le catalogue fermé, la durabilité et le rollback
restent inchangés. Le passage à une campagne Git réelle demeure distinct des essais du harness.

### 13:09 — du cadrage audio à la nano-étape vérifiée

La fonction scalaire clamp_level permet d'exercer le catalogue actuel sans inventer un domaine de tableaux.
Le code candidat est fixé sur un nom existant ; critères et entrées restent fournis par le harness.
Verifier publie une admission pure avant toute proposition. Engine compose une tentative complète :
intention/CAS, snapshot, candidat, splice, faits, double gate, reçu et publication. Même un échec de CAS
après reçu provoque la restauration ; un running n'est jamais rejoué implicitement.

Le banc experiments/visualizer a observé un vert avec modification et reçu, un invariant rouge et un
refus du reçu avec restauration exacte. Engine, workspace, verifier et journal sont réels ; bridge et
Git sont explicitement simulés. L'idempotence ne démontre pas à elle seule les bornes exactes du produit.

Ollama est joignable et le modèle prévu est présent. /v1/models ne publie pas sa fenêtre ; ollama show
rend num_ctx=16384, transmis comme asserted. Le premier appel a tronqué ses 128 tokens dans le thinking.
La consigne explicite et une réserve de 1 024 ont donné un critère conforme en 358 tokens de completion
(223 de prompt), stop. Ces mesures et les échecs restent sous experiments/visualizer/runs ; ni taux de
fiabilité ni génération de fonction réelle ne sont déduits de cette sonde.

Validation : **1 402 passed, 3 skipped, 7 warnings en 40,64 s**, Python 3.12.9/pithos ; mesures des onze
STATE conformes. Le seed du dépôt dédié est préparé. Son initialisation Git appartient à l'humain selon
AGENTS § 7 ; trois commandes exactes figurent dans le README du banc. La suite immédiate est ce trial,
puis le marcheur complet avec reprise, finalisation et baseline. Aucun Git d'écriture exécuté.


### 13:09 — entrée unique et suivi terminal

La demande d'entrée unique est réalisée par `src/main.py`, avec le parseur/exécuteur commun du banc.
`src/tui.py` relit les preuves sur un thread d'affichage ; l'exécution reste dans le thread principal
pour conserver le déroulement des context managers sur `KeyboardInterrupt`. Les panneaux fixes sont
rendus en ANSI avec la bibliothèque standard. La référence `resources/gguf-tester/ggufscan/tui.py`
a été relue : sa présentation compacte sans dépendance est retenue, sans copie de code tiers.

L'usage de bridge fait autorité pour les tokens ; la copie du candidat dans engine ne s'y additionne
pas. La sonde est comprise dans les appels, les tours candidats sont comptés séparément, les opérations
workspace sont distinguées des `tool_calls` modèle absents de ce banc. Les mesures inconnues restent
inconnues. Aucun comportement métier de validation ni transport modèle n'est changé.

Validation ciblée : **22 passed en 6,08 s** dans Python 3.12.9/pithos. Un vrai SIGINT est envoyé après
splice dans un pseudo-terminal : le seed est retrouvé à l'octet près, result.json conserve l'interruption,
le code est 130 et le curseur est restauré. Cela valide le terminal et le filesystem locaux ; le bridge
de cet essai reste scénarisé. Les vérifications complètes sont consignées dans le STATE du banc.


Clôture de l'entrée TUI : **23 tests ciblés** et **1 444 tests de suite complète** passent
(3 skips connus, 7 warnings), en 44,62 s pour la suite finale. Les onze STATE et le diff passent.
Le dernier état est prélevé à la fermeture des panneaux ; un résumé interactif garde les tokens
visibles même si la réponse arrive entre deux frames. Les preuves négatives et la proposition Git
restent dans [STATE](../experiments/visualizer/STATE.md) et [git.md](../experiments/visualizer/git.md).

### 13:09 — observatoire des essais et adaptations J/K

L'observatoire lisait uniquement logs/missions et reconstruisait l'arbre depuis les événements.
Le banc publie une collection runs/, un tree.json et un result.json : son refus réel apparaissait
donc sans nœud ni cause. Une entrée de collection directe est désormais explicite. Le snapshot
publié fait autorité sur les intentions, le résultat complète le diagnostic, les JSONL restent lus
par journal. Aucun événement ni reçu n'est fabriqué pour compléter l'histoire.

Le dashboard React/Vite de l'ancien harness est adapté au nouveau contrat : catalogue paginé,
arbre, gates, historique de vérification, métriques, événements et aperçus d'artefacts. Les chemins
restent sous le run, sans traversée ni lien symbolique ; au-delà de 2 Mo, l'aperçu est refusé.
API et web écoutent sur la loopback seule, sans collecteur, base de données ni service extérieur.

GVS5H apporte l'idée d'un historique de vérification durable et de mesures sourcées. Chaque
verdict de verifier est désormais consigné avant décision ; un refus d'écriture restaure la cible.
Le rapport ne se substitue jamais au reçu. Les appels réels sont distingués des refus de préflight,
les états publiés des intentions, les tokens rapportés des estimations. Bridge conserve capacité,
provenance et durée ; les données absentes restent inconnues. Le sidecar de regrading du dépôt
source est réécrivable : il ne constitue pas à lui seul un modèle append-only à reprendre.

Graphify inspire une notice d'omission dans le contexte, dont le coût estimé est compris dans le
budget, et un contrôle des signatures livrées dans ARCHITECTURE. Le contrôle compare les noms,
l'ordre, le passage positionnel/nommé et l'obligation des paramètres de 20 interfaces ; il ne valide
ni types ni valeurs par défaut. Deux interfaces encore prévues sont distinguées explicitement.
Les sources et licences ont été relues ; les adaptations réécrivent les idées, sans importer
les stacks graphiques ou la boucle manager. Les choix J/K sont catalogués dans IMPORT_REPORT.
La garde de non-progrès fondée sur les faits et le branchement de ContextPacket attendent walk.

Le trial-44kcg6ig reste une preuve négative : cinq gates, dont avant rouge, candidat vert et trois
variantes vertes ; refus tautology, zéro reçu, restauration exacte. L'idempotence ne prouve pas
les bornes du produit et cet échec n'est pas une preuve contre le code candidat. L'ancien journal
reste intact ; les nouveaux rapports enrichissent uniquement les exécutions suivantes.

Validation sur le dépôt commun avec l'entrée TUI : **1 444 passed, 3 skipped, 7 warnings en 43,83 s**
dans Python 3.12.9/pithos ; huit tests jsdom, typage et build web verts sous Node 26.7.0.
Les onze STATE passent. La lecture réelle par le proxy web confirme les cinq gates, sept événements,
2 461 tokens et le SHA restauré ; un nouveau selftest expose son rapport durable.
**Niveau 5** sur contrats, **4** pour jsdom, **6 limité à la lecture HTTP et aux fichiers locaux**.
Le contrôle visuel reste ouvert : l'outil CUA ne fournit aucun navigateur dans cette session.
