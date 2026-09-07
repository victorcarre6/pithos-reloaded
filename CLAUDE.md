# AGENTS.md — protocole de développement

Ce dépôt se construit **module par module, par des agents successifs**. Chaque agent travaille sur **un
seul module**, en lisant deux fichiers et en n'écrivant que dans son répertoire.

Ce fichier est le point d'entrée. Lis-le en entier avant toute action.

---

## 1. Le projet en cinq phrases

Pithos Reloaded est une **expérience d'autonomie logicielle sur modèle local souverain** : un modèle de 8
milliards de paramètres (`pithos/ling-3.0-tiny:8b-16k` sur Ollama, Mac mini M2 16 Go) piloté par un harness
qui ne le laisse jamais planifier plus d'une étape vérifiable à l'avance.

L'unité de travail est la **nano-étape vérifiable** : un nœud de travail ne s'exécute que s'il porte un
critère exécutable, sinon il se scinde ou il est bloqué. La validation passe exclusivement par des
**invariants métamorphiques** exécutés par le harness — le modèle n'émet jamais une valeur attendue, il
nomme une relation dans un catalogue fermé et le harness génère les entrées.

La campagne construit une **boîte à outils MCP générique** dans un dépôt Git séparé. Le livrable a une
valeur d'usage propre ; **la trajectoire est l'objet d'étude.**

---

## 2. Les six contraintes dures

Elles priment sur tout le reste, y compris sur ce que dit un `MODULE.md`. Si un `MODULE.md` semble les
contredire, **arrête-toi et signale-le** dans `STATE.md` plutôt que de trancher.

1. **Aucun littéral produit par le modèle n'atteint l'exécution.** Le modèle n'émet que des noms de symboles
   existants et des choix dans des énumérations fermées.
2. **Un nœud non vérifiable ne s'exécute jamais.** Il se scinde, ou il est marqué `blocked`.
3. **Une nano-étape non verte restaure son fichier cible à l'octet près.**
4. **Une mission a un temps mural dur.** À l'expiration elle finalise ce qui est vert et reste reprenable ;
   elle n'échoue pas globalement.
5. **Souveraineté totale.** Aucune donnée ne quitte la machine, hors Git et Telegram — tous deux passant par
   le module `broker`, et par lui seul.
6. **Les données brutes sont append-only et ne sont jamais supprimées**, échecs compris.

---

## 3. Les trois règles d'import

Elles sont **testées** dans `tests/boundaries/`, pas laissées à la discipline.

```text
verifier   n'importe jamais bridge, ni le modèle,
           et n'a d'I/O que sur ce qu'il a lui-même produit
bridge     n'importe jamais engine
broker     est le seul module par lequel une donnée quitte la machine
```

La première est l'inversion qui fonde l'architecture : **la couche qui décide de la vérité est en dessous de
celle qui parle au modèle.** La troisième rend la contrainte dure n°5 mécaniquement vérifiable.

---

## 4. La carte des modules

| # | Module | Autorité | Dépend de | Cible |
|---|---|---|---|---:|
| 1 | `kernel` | vocabulaire, AST, contrats, faits | — | ~380 L |
| 2 | `journal` | durabilité : JSONL append-only, `live.log`, lecture | 1 | ~400 L |
| 3 | `verifier` | **la vérité**, et l'autorité d'émettre le reçu | 1-2 | ~950 L |
| 4 | `bridge` | **la frontière modèle** | 1-2 | ~250 L |
| 5 | `workspace` | **le filesystem** | 1-2 | ~200 L |
| 6 | `engine` | l'arbre, le contexte, le budget | 1-5 | ~1 050 L |
| 7 | `campaign` | le magasin, propositions, redondance, arrêt | 1-6 | ~550 L |
| 8 | `lifecycle` | verrou, launchd, custody, garde disque | 1-2 | ~250 L |
| 9 | `broker` | **la seule sortie de données** : Git + Telegram | 1-2 | ~550 L |
| 10 | `observatory` | lecture seule, processus séparé, agrégats | 1-2 | ~550 L + 700 L web |
| 11 | `refinery` | politique d'auto-amélioration, **`enabled: false`** | 1-7 | ~100 L |

**Niveaux de dépendance :**

```text
niveau 0   kernel
niveau 1   journal
niveau 2   verifier · bridge · workspace · lifecycle · broker · observatory
niveau 3   engine
niveau 4   campaign
niveau 5   refinery
```

**Ordre de construction — tranche verticale d'abord.** `kernel` minimal → `journal` → `verifier` (une
relation, une gate) → `workspace` → `engine` (`walk` sans Prefect) → `bridge`, jusqu'au jalon **« premier
vert »** : une nano-étape, un invariant, un mutation-check, un reçu, un fichier réellement modifié, de bout
en bout. Puis chaque module s'élargit à sa cible.

---

## 5. Protocole de travail

### Au démarrage — trois lectures, dans cet ordre

1. **`AGENTS.md`** — ce fichier.
2. **`src/<module>/STATE.md`** — où en est le module. **La rubrique « Prochaine action » est ton point
   d'entrée exact.** Si le statut est `bloqué`, lis le blocage avant tout.
3. **`src/<module>/MODULE.md`** — ton contrat complet : autorité, interface, interdits, cible, reprises,
   critères, double, définition de « fini », et les sources en fin de fichier.

Tu n'as **pas besoin** de lire `docs/` pour travailler. Le `MODULE.md` est autosuffisant. Consulte `docs/`
seulement si le `MODULE.md` t'y renvoie explicitement, ou si tu dois vérifier une décision.

### L'environnement — avant la première commande

Le harness tourne dans le virtualenv **pyenv `pithos`**, en **Python 3.12.9**. Le fichier `.python-version`
à la racine le sélectionne à l'entrée du répertoire ; si ton shell ne l'applique pas, active-le à la main.

```sh
pyenv activate pithos                    # ou : source ~/.pyenv/versions/pithos/bin/activate
python -V                                # doit afficher exactement : Python 3.12.9
pip install -r requirements.txt
```

⚠️ **Un test lancé hors de ce venv ne prouve rien** !
→ Les versions y sont bornées par `requirements.txt`. Un vert obtenu sur le Python système ne dit rien de
plus qu'un niveau 1 — *le processus a rendu 0* (§ 10). Vérifie `python -V` avant de conclure.

**N'ajoute jamais une dépendance en l'installant.** Une dépendance se déclare d'abord dans la rubrique
**Stack** de ton `MODULE.md`, puis dans `requirements.txt`. Un `pip install` non déclaré rend ton module
irreproductible et te fera rejeter (§ 6).

### Pendant — la boucle

```text
1. lire STATE.md → prendre « Prochaine action »
2. écrire le test d'abord, quand la nature de l'étape le permet
3. implémenter le minimum qui le fait passer
4. lancer les tests du module dans le venv `pithos` (jamais ceux des autres)
5. mettre à jour STATE.md — toujours, même si l'étape a échoué
6. proposer le commit dans git.md quand une unité cohérente est terminée — SANS l'exécuter (§ 7)
7. recommencer
```

**Mets à jour `STATE.md` à chaque unité de travail terminée**, pas seulement à la fin de la session.

⚠️ **`STATE.md` est le seul mécanisme de reprise** !
→ Une session peut être coupée à tout moment, sans préavis. Ce qui n'y est pas écrit est perdu.

### À la fin — ou à l'interruption

`STATE.md` doit toujours laisser le module dans un état repris­able par un autre agent qui n'a **aucun**
contexte de ta session. Une « Prochaine action » vague — *« continuer l'implémentation »* — est un défaut.
Écris *« implémenter `relations.round_trip` : rendre le script, vérifier qu'il échoue avant patch »*.

---

## 6. Règles d'écriture du code

### Périmètre

- **N'écris que dans `src/<ton module>/` et `tests/doubles/<ton module>.py`.** Rien d'autre.
- Si ton travail exige un changement dans un autre module, **ne le fais pas** : consigne-le dans `STATE.md`
  § *Blocages* avec ce qui débloquerait.
- Ne modifie jamais `docs/`, `resources/`, ni le `MODULE.md` d'un autre module. Tu peux enrichir **ton**
  `MODULE.md` § *Décisions locales* si tu prends un choix d'implémentation qu'un successeur doit connaître.

### Isolation

Chaque module publie une **interface** (`typing.Protocol` + modèles Pydantic) et un **double conforme** dans
`tests/doubles/<module>.py`. Tu testes ton module **contre les doubles de tes dépendances, jamais contre
leur implémentation**.

⚠️ **Le double est un test de l'architecture, pas seulement du code** !
→ Si le double d'un voisin doit simuler un état interne pour que ton module passe, **ta frontière est
fausse**. Consigne-le dans `STATE.md` § *Blocages* plutôt que de contourner.

### Style — non négociable

Ces règles viennent de l'auteur du projet. Elles priment sur tes habitudes.

- **Une intention par ligne.** Si une ligne filtre *et* trie, scinde-la et nomme l'étape intermédiaire.
  Préfère `running = [...]` puis `targets = sorted(running, key=...)` à une compréhension imbriquée.
- **Ne réécris jamais la même sous-expression deux fois** — itère sur les valeurs, ou passe par une variable.
- **N'extrais un helper que pour du code réellement partagé** (≥ 2 appelants), et extrais **le tronc commun
  seul**, pas la fonction publique avec ses effets de bord.
- **Pas de paramètre booléen qui pilote le comportement.** `do_x(..., only_y=True)` → deux fonctions.
- **Aucune abstraction pour du code à usage unique.** Aucune « flexibilité » non demandée. Aucune gestion
  d'erreur pour un scénario impossible.
- **Découpage visuel** : une ligne vide après la docstring ; le corps en blocs séparés par une ligne vide,
  chaque bloc introduit par un **commentaire court en minuscules** (`# cible + capacité disponible`) ; une
  ligne vide avant le `return`. **Ne commente pas les one-liners triviaux.**
- **Sorties et logs construits en deux temps** : d'abord la chaîne dans une variable, puis l'appel. Pour du
  multi-ligne, groupe les littéraux entre parenthèses — jamais de `+` ni de backslash.
- **Dict à plusieurs clés en vertical**, une clé par ligne. Les petits dicts (2-3 clés) restent en ligne.
- **Docstrings** : une phrase suffit ; décris **ce que fait** la fonction et son contrat, pas comment elle
  est implémentée.
- Note les questions ouvertes avec un `# TODO:` explicite plutôt que de les résoudre en silence.

**Version Python** : **3.12.9**, dans le virtualenv pyenv `pithos` — voir § 5, *L'environnement*. Elle est
figée par `requires-python` dans `pyproject.toml`. **N'utilise aucune syntaxe 3.13+.** À l'inverse, les
guillemets identiques imbriqués dans une f-string (`f"{d["k"]}"`) sont **légaux** ici : PEP 701 les autorise
depuis 3.12, la restriction héritée de 3.9 ne s'applique pas à ce dépôt.

### Ce qui te fera rejeter

- Une dépendance non déclarée dans la stack du `MODULE.md`.
- Un import qui viole une des trois règles.
- Du code qui dépasse la cible du module sans justification écrite dans `STATE.md`.
- Une reprise marquée **`Écarté`** réintroduite. Elles portent leur raison ; si tu penses qu'elle est
  fausse, **écris-le dans `STATE.md`, n'implémente pas.**
- **Toute commande Git qui écrit** — voir § 7. C'est le rejet le plus simple à éviter et le plus grave.

---

## 7. Git — tu ne commites jamais

**Aucun agent ne commite, ne pousse, ne merge, ne rebase, ne stash, ni ne change de branche.** Sans
exception, et quel que soit ce que la tâche semble demander.

### Interdit — toute commande Git qui écrit

```text
git add · git commit · git push · git merge · git rebase · git reset · git revert
git checkout / switch · git stash · git cherry-pick · git tag · git clean
et leurs alias : ga · gaa · gc · gcmsg · gp · gcm · gco · gst -u ...
```

### Autorisé — les commandes de lecture

`git status`, `git diff`, `git log`, `git show`, `git ls-files`. Tu en as besoin : **savoir exactement ce que
tu as changé est ce qui te permet de proposer un commit précis.**

### Pourquoi

Un commit est un **acte peu réversible et orienté vers l'extérieur**.

⚠️ **Onze agents qui commitent chacun à leur idée produisent un historique que personne n'a choisi** !
→ Et qu'on ne peut plus relire pour comprendre ce qui a été décidé.

**L'humain est portier de l'historique, exactement comme il est portier de la fin de campagne.** Toi, tu
prépares le travail et tu le rends immédiatement exécutable.

### À la place — `src/<module>/git.md`

Tu maintiens un fichier `git.md` à la racine de ton module. Il **propose** ; un humain **exécute**.

Le fichier est **append-only**, comme `STATE.md` : on ajoute une proposition, on ne réécrit pas les
précédentes. Une proposition déjà exécutée est marquée, pas supprimée.

````markdown
## Proposé le JJ:MM — <titre court>

**Intention** : une phrase — ce que ce commit fait, et rien d'autre.

```sh
ga src/kernel/contracts.py \
   src/kernel/errors.py \
   tests/doubles/kernel.py
gcmsg "kernel: contrats du socle et hiérarchie d'erreur à cause fermée"
```

**Contient** : les cinq modèles du socle, l'enum `Cause`, `ErrorAccumulator`, et le double correspondant.
**Ne contient pas** : `codeview`, encore en cours — fera l'objet d'un commit séparé.
**Tests verts** : `tests/kernel/test_contracts.py`, `tests/contracts/test_kernel_double.py`.
**Exécuté** : —
````

### Six règles pour une proposition utile

1. **Un commit, une intention.** Si tu écris « et » dans l'intention, coupe en deux propositions.
2. **Chemins explicites, un par ligne.** `ga` avec la liste exacte des fichiers.
   **N'utilise jamais `gaa`** : il stage tout, y compris le travail en cours d'un autre module et les
   fichiers que tu n'as pas relus. C'est l'inverse d'un commit précis.
3. **Message au format `<module>: <ce que ça fait>`**, en minuscules, sans point final. Le module en préfixe
   rend l'historique lisible quand onze agents ont contribué.
4. **Ne propose que du travail dont les tests passent.** Si un test est rouge, la proposition attend — dis-le
   dans `STATE.md`, pas dans `git.md`.
5. **Liste les tests verts** au moment de la proposition. C'est ce qui permet à l'humain de commiter sans
   revérifier.
6. **Ne propose jamais de fichier hors de ton périmètre** — `src/<ton module>/` et
   `tests/doubles/<ton module>.py`. Si tu crois qu'un fichier ailleurs doit changer, c'est un blocage
   (`STATE.md` § *Blocages*), pas un commit.

### Quand proposer

**Quand une unité cohérente est terminée et verte** — pas à chaque fichier, pas une seule fois à la fin. Un
bon rythme est une proposition par item coché de la liste « Fini quand ».

Si ta session est coupée avant que tu aies proposé, ce n'est pas grave : `STATE.md` porte l'état, et le
prochain agent proposera. **`git.md` n'est pas un mécanisme de reprise — c'est `STATE.md` qui l'est.**

---

## 8. Le vocabulaire des reprises

Une part majoritaire de ce projet est **portée** depuis neuf dépôts de référence montés sous `resources/`.
Chaque ligne du `MODULE.md` § *Reprises* porte un verdict :

| Verdict | Ce que tu dois faire |
|---|---|
| **Copier** | source Python, porter quasi tel quel, **conserver la notice de licence** dans le fichier dérivé |
| **Traduire** | source TypeScript → Python, ligne à ligne, structure préservée, en-tête `PORTED_FROM: <dépôt>/<fichier>:<lignes>` |
| **Adapter** | l'idée est juste, l'implémentation suppose leur objet de session — relis, réécris, ne copie pas |
| **Inspirer** | la structure de données vaut mieux que le code |
| **Écarté** | **n'implémente pas.** La raison est écrite ; le pointeur reste pour un éventuel retournement |
| **Reporté** | la reprise est juste, son déclencheur n'existe pas encore. **N'implémente pas au socle.** |

**Lis la source avant de porter.** Un pointeur `fichier:lignes` se lit dans `resources/<dépôt>/`. Une reprise
collée sans être relue est un défaut.

---

## 9. `STATE.md` — le fichier de reprise

Un par module, à la racine du répertoire du module. **Tu le maintiens. Il n'est jamais supprimé.**

```markdown
# STATE — <module>

**Statut** : non commencé | en cours | bloqué | fini
**Mise à jour** : JJ:MM
**Lignes** : <n> / <cible du MODULE.md>

## Prochaine action
Une phrase, immédiatement exécutable par un agent sans contexte.

## Avancement
Reprend la liste « Fini quand » du MODULE.md, cochée.
- [x] …
- [ ] …

## Journal
### JJ:MM — <titre court>
Ce qui a été fait, ce qui a été **mesuré**, ce qui a été décidé.
**Niveau de preuve atteint** : 1 à 6 (§ 10) — jamais plus haut que ce qui a été observé.

## Blocages
| Quoi | Pourquoi | Ce qui débloquerait |
|---|---|---|

## Décisions locales
Choix d'implémentation pris ici, qu'un successeur doit connaître et ne doit pas défaire sans raison.

## Reprises traitées
| Source | Verdict | Fait ? | Note |
|---|---|---|---|
```

**Trois règles sur ce fichier.**

1. **Le journal est append-only.** On ajoute une entrée, on ne réécrit pas les précédentes. Même règle que
   les traces du produit — et pour la même raison.
   **Les résultats négatifs y restent** : un timeout, une incompatibilité, une mesure défavorable sont des
   preuves, pas des brouillons à effacer.
2. **Un blocage n'est jamais supprimé, il est résolu** : on ajoute la résolution dans la ligne.
3. **« Prochaine action » est réécrite à chaque mise à jour.** C'est le seul champ mutable en place.

---

## 10. Discipline de preuve

**Ne déclare jamais un niveau de validation supérieur à celui que tu as réellement observé.** C'est la même
exigence que la décision 13 impose au produit, appliquée à ton propre travail.

| Niveau | Ce que ça prouve | Ce que ça ne prouve pas |
|---|---|---|
| 1 — le processus a rendu 0 | la commande s'est terminée | qu'elle a fait quelque chose |
| 2 — le format est conforme | la sortie parse | qu'elle est juste |
| 3 — l'effet réel est constaté | un fichier a changé, mesuré | que le changement est celui voulu |
| 4 — la fonction est correcte | le test métier passe | qu'elle tient hors du double |
| 5 — validé **sur double** | le contrat de frontière tient | que l'implémentation voisine s'y conforme |
| 6 — validé **en réel** | runtime, réseau, matériel compris | — |

⚠️ **Une sortie qui imprime un `tool_call` ne prouve pas son exécution** !
→ Un mock Git ne prouve pas qu'une PR distante existe ; un schéma valide ne prouve pas que la route l'applique.
Écris dans `STATE.md` le niveau que tu as atteint, pas celui que tu espérais.

**Conserve les résultats négatifs.** Un timeout, une incompatibilité, une mesure défavorable **sont des
preuves**. Ne les masque pas, ne les estime pas, ne les transforme pas en succès de protocole — consigne-les
dans `STATE.md` § *Journal*. La valeur durable de v1 tient à ses traces, pas à son code ; la tienne aussi.

**La plupart de ton travail s'arrête au niveau 5**, et c'est normal : tu testes contre des doubles. Dis-le.
Le niveau 6 demande Ollama, un dépôt de campagne réel et une machine — il appartient aux spikes et au jalon
« premier vert », pas à un module isolé.

---

## 11. Définition de « fini », pour un module

Un module est fini quand **tous** ces points sont vrais, et pas avant :

- [ ] Tous les items de la rubrique *Fini quand* du `MODULE.md` passent.
- [ ] Le double dans `tests/doubles/<module>.py` existe et satisfait le même `Protocol` que
      l'implémentation, vérifié par un test dans `tests/contracts/`.
- [ ] Le test de graphe d'imports de `tests/boundaries/` passe pour ce module.
- [ ] Le nombre de lignes est **au niveau ou en dessous** de la cible, ou l'écart est justifié par écrit
      dans `STATE.md` (le ratchet est **shrink-only** : une cible ne remonte jamais sans justification).
- [ ] `STATE.md` est à jour, statut `fini`, avec « Prochaine action » indiquant le module suivant.

---

## 12. Quand tu es bloqué

Dans l'ordre :

1. **Relis la source de la reprise** dans `resources/`. La plupart des blocages viennent d'un pointeur lu
   trop vite.
2. **Vérifie que ce n'est pas une frontière fausse.** Si tu as besoin d'un état interne d'un voisin, la
   découpe est en cause, pas ton implémentation.
3. **Consigne le blocage dans `STATE.md`** avec ce qui le débloquerait, et **passe à l'item suivant** de la
   liste « Fini quand » s'il en reste un qui n'en dépend pas.
4. Si tout dépend du blocage : statut `bloqué`, « Prochaine action » = la question exacte à trancher, et
   arrête-toi. **Ne devine pas.**

**Ce qui n'est jamais une solution** : contourner une garde, élargir ton périmètre à un autre module,
réintroduire une reprise `Écarté`, ou marquer `fini` un module dont un item de « Fini quand » ne passe pas.

---

## 13. Où trouver le reste

| Question | Document |
|---|---|
| **Où en est le projet, et par quoi commencer** | **`docs/QUICK_CATCH.md`** |
| Périmètre, contraintes, 27 critères de socle | `docs/PROJECT.md` |
| Pourquoi une décision a été prise, et par quoi elle a été amendée | `docs/EXPLANATIONS.md` § Partie I (33 décisions) |
| Ce qui s'est passé et quand | `docs/EXPLANATIONS.md` § Partie II (journal) |
| Découpe en modules, stack, méthode | `docs/ARCHITECTURE.md` |
| Ordre des phases, spikes | `docs/ROADMAP.md` |
| Les ~800 reprises retenues, avec source et verdict | `resources/IMPORT_REPORT.md` |
| Les neuf dépôts : taille, licence, fiabilité d'extraction | `resources/MANIFEST.md` |
| Les commits que tu proposes, et ceux déjà exécutés | `src/<module>/git.md` (§ 7) |
