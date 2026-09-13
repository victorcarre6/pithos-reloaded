# STATE — `refinery`

**Statut** : en cours
**Mise à jour** : 11:09
**Lignes** : 112 code / 100 cible · 223 physiques
**Empreinte** : 2c2baa0497de1332f6c5b23704461924d9d5f5f9d3969f13817dbdc92dcfc56d

## Prochaine action

Conserver ENABLED=False. Faire publier Baseline/NodeEvidence par kernel, puis émettre la baseline par engine ; l’admission de la famille prompt par campaign reste aussi un prérequis. Placement des tests et métrique résolus le 11:09 ; ne pas confondre ces résolutions avec l’autorisation d’activer la gate.

## Avancement

Liste « Fini quand » du `MODULE.md` :

- [x] `plan_refinement` est **déterministe** ; aucun appel modèle — test qui échoue si un client de
      modèle est instancié, doublé par le graphe d'imports.
- [x] Un edit visant l'entrée de base est **refusé mécaniquement**.
- [x] La gate laisse en `shadow` un edit dont l'effet est dans le bruit.
- [x] La gate promeut sur effet mesurable, et **seulement** en déplaçant le label `active` — testé par
      l'absence de tout champ de contenu dans `Decision`.
- [x] Un edit invalide est **enregistré et non fatal**.
- [x] Le module reste **`enabled: false`** : aucun module du socle ne l'importe, vérifié mécaniquement.
- [x] L'`evidence` est un identifiant de nœud + un verdict d'invariant — une rationale est **refusée par
      le contrat**, pas seulement découragée.
- [x] Le test de graphe d'imports confirme que `refinery` n'est importé par aucun autre module.

## Journal

_Append-only. Une entrée par unité de travail terminée. **Les résultats négatifs restent** — un timeout, une
incompatibilité ou une mesure défavorable sont des preuves. Chaque entrée porte son **niveau de preuve**
(`AGENTS.md` § 10), jamais plus haut que ce qui a été observé._

### 10:09 — vérification préalable : `engine` n'écrit pas la baseline

La « Prochaine action » précédente demandait de **vérifier d'abord que `engine` écrit le triplet de
baseline à chaque fin de mission**. Vérifié : `grep -rn "baseline" src/engine/*.py` rend **zéro
occurrence**, et `src/engine/STATE.md` porte le statut `non commencé`.

**Résultat négatif conservé** : la première condition d'allumage du § 8 — « dix missions ont tourné et
leur triplet de baseline est écrit » — ne peut pas commencer à se satisfaire. Consigné en blocage ; le
travail se poursuit sur le reste, qui n'en dépend pas.

**Niveau de preuve** : 3 — l'absence est constatée sur les fichiers, pas déduite.

### 10:09 — `gate.py`, l'apport propre du projet

Porté de `packages/coding-agent/src/core/refinement/refinement.ts:673-682,716-750`, lu avant portage —
dont le point qui compte : `validateEdit` **rend une raison** et l'appelant l'enregistre avec
`applied: false`, il ne lève pas. C'est littéralement « un edit invalide est enregistré et non fatal ».

Écrit `Label`, `Effect`, `NodeEvidence`, `Baseline`, `Edit`, `Decision`, `refuse`, `z_score`, `gate`.

**Mesuré** : 20 cas verts. **Cinq mutants tués** : seuil de bruit annulé → 6 échecs ; label toujours
actif → 2 ; entrée de base éditable → 2 ; écart non normalisé par la taille d'échantillon → 2 ; refus
levé en exception au lieu d'être enregistré → 3.

Décidé : **le seuil est le bruit lui-même, pas un nombre rond.** La gate calcule un test z à deux
proportions (`math` seul, aucune dépendance) et promeut à partir de `Z_PROMOTE = 1.96`, soit ~95 %. La
conséquence est mesurée et testée : 6/10 → 7/10 reste en `shadow`, alors que 600/1000 → 700/1000 promeut
sur **le même écart de taux**. C'est exactement ce que « variation dans le bruit » veut dire, et cela
évite d'inventer une constante magique.

Décidé : `Decision` ne porte **aucun champ de contenu**. Un test vérifie que le contenu de l'edit
n'apparaît pas dans sa sérialisation JSON : le seul acte de la gate est le déplacement du label.

### 10:09 — `propose.py`, le plan déterministe

Porté de `prime-agent-runtime/src/rlm/harness.py:705-720`, lu avant portage : plan en trois étapes,
zéro appel modèle. Les deux premières — diagnostiquer, modifier la plus petite entrée utile — sont ici ;
la troisième (rejouer et enregistrer) appartient à `engine`.

**Mesuré** : 32 cas verts à ce point. **Cinq mutants tués** : un harness qui tient est réécrit → 1
échec ; plus petite entrée utile non choisie → 2 ; plancher de récurrence supprimé → 1 ; preuve élargie
aux nœuds verts → 3 ; version non incrémentée → 1.

Décidé : la **table de routage** de la source se réduit à une ligne au socle — un fait récurrent va en
`memory`. Les deux autres destinations (procédure ⇒ `skill`, délégation ⇒ `subagent`) n'ont pas de
consommateur tant que le mode agentic est différé ; les écrire aurait été du code mort.

### 10:09 — le double, le contrat de frontière et le graphe d'imports

Écrit `tests/doubles/refinery.py` (30 L) — trivial, comme le § 9 l'annonce. Deux scénarios scriptables
(`plan`, `decision`) ; **sans script, le double ne propose rien et ne promeut rien**, parce qu'un double
qui promeut par défaut ferait passer une gate que personne n'a mesurée. `refuse` y est importée telle
quelle : fonction pure, et la réimplémenter aurait créé un second jeu de règles d'immuabilité.

Le test de graphe d'imports rend **mécanique** le `enabled: false` : `reaches_refinery` balaie tous les
modules de `src/` et vérifie qu'aucun n'atteint `refinery`, par import absolu comme par sous-module.
Cinq chemins d'atteinte injectés et trois non-atteintes confirment qu'il mord dans les deux sens. Le même
fichier vérifie que `bridge`, `httpx`, `socket`, `subprocess`, `urllib` et `engine` sont hors du graphe.

**Mesuré, état final** : `PYTHONDONTWRITEBYTECODE=1 python -m pytest src/refinery -q -p no:cacheprovider`
→ **72 passed, 1 skipped en 0,25 s**, venv `pithos`, `python -V` = Python 3.12.9. Le `skip` est le test de
scriptabilité, qui n'a de sens que sur le double.

**Comptage des lignes, mesuré** (non blanches, hors tests) :

| Fichier | Total | Code | Docstrings | Commentaires | Cible § 7 |
|---|---:|---:|---:|---:|---:|
| `gate.py` | 98 | 70 | 23 | 5 | 50 |
| `propose.py` | 31 | 13 | 15 | 3 | 50 |
| **Total** | **129** | **83** | **38** | **8** | **100** |

**Niveau de preuve atteint** : **5 — validé sur double.** Le contrat de frontière tient dans les deux
sens. Pas 6, et il ne peut pas l'être : le niveau 6 demanderait dix missions réelles, or la baseline
n'est pas écrite. **La gate n'a jamais vu une seule donnée réelle** — c'est la troisième condition
d'allumage du § 8, et elle est ouverte.

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
| `engine` n'écrit pas le triplet de baseline | Vérifié : zéro occurrence de `baseline` dans `src/engine/*.py`, et `src/engine/STATE.md` porte `non commencé`. La première condition d'allumage du § 8 ne peut pas commencer à se satisfaire, et la gate ne peut être testée que contre des baselines fabriquées. | Les ~5 L de `engine` qui écrivent nœuds verts / nœuds tentés, temps mural et cause de sortie en fin de mission, **dès la mission 1**. | — |
| `Baseline` n'est publié par personne | Il est défini dans `refinery/gate.py`, ce qui est légal pour un **consommateur**. Mais `engine` doit le **construire**, et il lui est interdit d'importer `refinery`. Le contrat est donc chez le mauvais propriétaire. | Remonter `Baseline` et `NodeEvidence` dans `kernel.contracts`, puis les réimporter ici. Aucun autre changement : la gate ne lit que `green`, `attempted`, `exit_cause` et `wall_seconds`. | — |
| `campaign` refuse d'écrire la famille `prompt` | Mesuré : `campaign/store.py:38` fixe `ALIVE = (skill, memory)` et `put` lève sur toute autre famille (`store.py:240`). Un edit `prompt` produit par ce module **ne pourrait donc pas être écrit** aujourd'hui, même si la gate le promouvait. | Une **sixième condition d'allumage**, à ajouter au § 8 : `campaign` doit admettre la famille `prompt` avant que `refinery` soit allumé. C'est cohérent — les deux interdits disent la même chose, chacun de son côté — mais personne ne l'avait écrit. | — |
| Les deux tests transverses sont hors de leur place | `AGENTS.md` § 11 les veut dans `tests/contracts/` et `tests/boundaries/` ; le § 6 m'interdit d'écrire hors de `src/refinery/`. Ils sont donc dans `src/refinery/`, prêts et verts. | La même dérogation que celle demandée par `kernel`, `journal` et `campaign`. | **Résolu le 10:09** — déplacés par la passe transverse ; suite complète verte. |
| La cible de ~100 L est dépassée de 29 L | 129 L mesurées pour les deux fichiers du § 7. **Mesuré** : 83 L de code exécutable — donc **sous la cible** — 38 L de docstrings et 8 L de commentaires. Le § 7 budgétait deux fichiers de logique ; les six contrats que personne d'autre ne publie ont atterri ici (voir le blocage `Baseline`). | Soit `Baseline` et `NodeEvidence` remontent dans `kernel` — ce qui rend ~20 L —, soit la cible monte avec cette justification mesurée. **Ne pas trancher seul** : le ratchet est shrink-only. | Résolu le 11:09 — unité code dans AGENTS § 4, total global 112 / 100 ; plafond motivé ci-dessous, cible inchangée. |

## Décisions locales

- **Le seuil de promotion est un test z à deux proportions, pas un delta en points.** `Z_PROMOTE = 1.96`
  a un sens statistique (~95 %) au lieu d'être une constante magique, et il fait dépendre la décision de
  la **taille d'échantillon** : le même écart de taux est du bruit sur dix nœuds et un effet sur mille.
  C'est ce que le § 4 demande quand il parle d'« effet mesurable ». `math` de la stdlib suffit.
- **`Baseline` dérive `green` et `attempted` de sa liste de nœuds au lieu de les stocker.** Deux nombres
  stockés à côté de la liste qui les produit peuvent diverger ; un seul les rend cohérents par
  construction. Le § 5 parle d'un triplet écrit par `engine` — il l'est, sous une forme dont le triplet
  se déduit.
- **`Effect` et `Label` sont deux enums, pas une.** `held` et `reverted` mènent tous deux au label
  `shadow`, mais ne disent pas la même chose au lecteur d'une trace : l'un dit « on ne sait pas
  encore », l'autre « on sait que c'est pire ».
- **`refuse` rend une raison, jamais une exception.** C'est le contrat de `validateEdit` dans la source,
  et c'est ce qui rend « un edit invalide est enregistré et non fatal » vrai par construction.
- **Les six contrats vivent dans `gate.py`.** Le § 7 ne prévoit que deux fichiers ; en ajouter un
  troisième pour les modèles aurait été une abstraction pour du code à usage unique. `propose.py` les
  importe de `gate.py` — aucun cycle.
- **Le double importe `refuse` de la politique réelle**, comme le double de `journal` importe `redact` :
  une fonction pure réimplémentée aurait créé une seconde règle d'immuabilité, donc une divergence
  possible sur l'invariant le plus important du module.

## Reprises traitées

| Source | Verdict | Fait ? | Note |
|---|---|---|---|
| `ca/core/refinement/refinement.ts:680-682` — immuabilité du prompt de base | Traduire | oui | `refuse` + `BASE_KEY` ; le préfixe affiché `prompt:` est accepté verbatim via `campaign.store.normalize` |
| `refinement.ts:716-750` — edit invalide enregistré et non fatal | Adapter | oui | `Effect.refused` porte la raison ; aucune exception |
| `refinery/propose` — `plan_refinement` déterministe en trois étapes | Copier | oui | les deux premières étapes ; la troisième appartient à `engine` |
| `refinery` — table de routage vers la plus petite famille pertinente | Traduire | partiel | réduite à « fait récurrent ⇒ `memory` » ; `skill` et `subagent` n'ont pas de consommateur au socle |
| `LF056` — label mobile séparé d'une version immuable | Adapter | oui | `Label.shadow`/`Label.active` ; `Decision` ne porte aucun contenu, testé |
| `refinement.ts:716-750` — conflit détecté par état de base capturé avant l'appel | Adapter | **non** | **Reporté** : il protège contre une écriture concurrente **pendant** l'appel modèle, or `plan_refinement` n'en fait aucun et le module est éteint. À réintroduire le jour où un appel modèle de dernier recours existe. |
| `refinery` — rollback par reconstruction inverse | Adapter | **non** | **Reporté** : c'est une opération **du magasin**, donc de `campaign` (§ 3). Rien à écrire ici. |
| `refinery/store` — les huit lignes du magasin (`load` défensif, `_sync_from_disk`, `overview`, …) | Copier | oui, **ailleurs** | déjà portées dans `campaign/store.py` le 10:09 : le magasin appartient à `campaign`, un fichier un propriétaire |
| `ca/core/goals.ts:75-94,125-181` — budget visible, objectif borné | Traduire | **non** | **Reporté** : le budget est montré au modèle par `engine`/`bridge`, pas par la politique d'auto-amélioration |
| `serializeConversation(...).slice(-80_000)` | — | **non** | inapplicable, § 11 : nous n'avons pas de trajectoire, et 80 Ko ne rentrent pas dans 16 k |


### 11:09 — mesure de production et en-tête courant

Passe transverse demandée via TEMPO.md. Aucun code métier ni case de livraison modifié.
Mesure AST/tokenize : **112 lignes de code**, **223 physiques**, cible globale **100**. Sous-paquets et __init__.py inclus ; tests et doubles exclus.
L’empreinte de l’en-tête couvre les chemins et octets de toute la production.
La nouvelle métrique ne valide aucun item métier et ne relève aucune cible numérique.

**En-tête antérieur conservé** :

```text
**Statut** : en cours — écrit, vert, et **laissé éteint** ; deux items de `AGENTS.md` § 11 hors périmètre
**Mise à jour** : 10:09
**Lignes** : 129 / ~100 L pour les deux fichiers du § 7, plus 24 L de `__init__.py` non budgétées.
**Le corps exécutable fait 83 L, sous la cible** ; l'écart est fait des 38 L de docstrings et 8 L de
commentaires que le style impose. Mesure par fichier dans le journal du 10:09.
```

**Prochaine action antérieure, remplacée car périmée** :

⚠️ **Ne rien activer.** `ENABLED` reste `False`, et aucune des cinq conditions du § 8 n'est remplie —
la première ne peut même pas commencer à l'être (premier blocage).

Le code des huit items de « Fini quand » est écrit et vert. Ce qui reste est **hors de mon périmètre** et
demande un arbitrage, dans cet ordre :

1. **Faire écrire le triplet de baseline par `engine`** — c'est ~5 L dans une trace qui existe déjà, et
   c'est la condition qui rend ce module utile un jour. Tant qu'il n'est pas écrit, activer la gate au
   bout de dix missions reviendrait à comparer un chiffre à rien.
2. **Faire remonter `Baseline` dans `kernel`** — il est défini ici faute de propriétaire, or `engine`
   doit le construire et ne peut pas importer `refinery`.
3. **Déplacer les deux tests transverses** — `test_double_contract.py` →
   `tests/contracts/test_refinery_double.py`, `test_import_boundaries.py` →
   `tests/boundaries/test_refinery.py`. Même dérogation que celle déjà demandée par `kernel`, `journal`
   et `campaign`.

Après arbitrage : relancer `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider` sur
`src/refinery` dans le venv `pithos`, consigner ici, et **laisser le statut sur `en cours` tant que
`ENABLED` est `False`** — ce module n'est pas « fini », il est *en attente de sa mesure*.

**Plafond justifié** : 112 code
**Justification** : La façade publique et les modèles des deux fichiers portent le total à 112 lignes de code, au lieu du compte partiel de 83. Le surplus de 12 lignes reste borné ; la gate demeure désactivée et aucune fonctionnalité d’allumage n’est ajoutée.

Les anciens comptes « corps exécutable sous la cible » sont des mesures historiques partielles ; ils ne décrivent pas le périmètre global désormais contrôlé.

**Niveau de preuve : 2** pour la mesure documentaire ; la suite initiale complète du 11:09 a rendu 1 215 passed et 3 skipped hors sandbox. Le détail des nouvelles validations vit dans tests/STATE.md.
