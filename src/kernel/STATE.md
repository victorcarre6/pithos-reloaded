# STATE — `kernel`

**Statut** : non commencé
**Mise à jour** : —
**Lignes** : 0 / ~380 L

## Prochaine action

Obtenir la dérogation à AGENTS.md § 6 pour déplacer `src/kernel/test_double_contract.py` vers `tests/contracts/test_kernel_double.py` et `src/kernel/test_import_boundaries.py` vers `tests/boundaries/test_kernel.py`. Les deux fichiers sont prêts et verts. Après accord : déplacer, lancer uniquement ces deux tests et `src/kernel/` avec `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider`, ajouter le résultat ici et actualiser les propositions sans commande Git d'écriture ; puis statut fini et prochaine action = lire `src/journal/STATE.md`.

## Avancement

_Recopie ici la liste « Fini quand » de `MODULE.md` et coche au fur et à mesure._

## Journal

_Append-only. Une entrée par unité de travail terminée. **Les résultats négatifs restent** — un timeout, une
incompatibilité ou une mesure défavorable sont des preuves. Chaque entrée porte son **niveau de preuve**
(`AGENTS.md` § 10), jamais plus haut que ce qui a été observé._

<!--
### JJ:MM — <titre court>
Ce qui a été fait, ce qui a été mesuré, ce qui a été décidé.
**Niveau de preuve** : 5 — validé sur double.
-->

## Blocages

| Quoi | Pourquoi | Ce qui débloquerait | Résolu le |
|---|---|---|---|

## Décisions locales

_Choix d'implémentation pris ici, qu'un successeur doit connaître et ne doit pas défaire sans raison._

## Reprises traitées

| Source | Verdict | Fait ? | Note |
|---|---|---|---|

## Point de reprise — 06:09 — contrats du socle

**Statut** : en cours. **Mise à jour** : 06:09. L'en-tête initial ci-dessus est conservé ; le dernier point de reprise porte l'état courant.

### Journal — 06:09

- Environnement observé : Python 3.12.9, préfixe `/Users/victorcarre/.pyenv/versions/pithos`, Pydantic 2.13.4, pytest 8.4.2. Aucune installation nécessaire au kernel.
- État initial : aucun code Python dans kernel ni aucun test partagé. `README.md` modifié ; configuration et `src/` déjà non suivis. Aucun changement utilisateur repris ni commande Git d'écriture exécutée.
- Test `Node.target` écrit avant les modèles : collecte rouge (`ModuleNotFoundError`). Première implémentation : 74 tests verts, 3 rouges ; `JsonValue` laissait passer NaN/Infinity via `model_validate_json` malgré `allow_inf_nan=False`. Union JSON récursive avec `FiniteFloat` : **77 tests verts**.
- `FileFact` et `Receipt` résident dans `facts.py`, conformément au tableau de contenu. Aucun reçu n'est émis, aucune autorité n'est assignée.
- **Niveau de preuve atteint : 4**, tests métier locaux ; aucun runtime de campagne essayé.

### Avancement

- [x] Les cinq modèles valident/rejettent les contraintes couvertes, dont liste refusée pour `Node.target`.
- [ ] Signature AST : arité, défauts, kwonly, annotations, incident `smooth_levels`.
- [ ] Classification des cinq classes avec table complète de cas.
- [ ] Snippet borné en octets et lignes sur une ligne de 10 Mo.
- [ ] Binaire : extension, BOM UTF-16/32, NUL, seuil strict de 30 %.
- [ ] Accumulateur : trois défauts, chemins exacts (tests écrits, à exécuter).
- [ ] Identité réflexive, symétrique, transitive.
- [ ] Contrôles dans `tests/boundaries/`.
- [ ] Double et conformité au `Protocol`, dont contrôle dans `tests/contracts/`.

### Blocages

| Quoi | Pourquoi | Ce qui débloquerait | Résolu le |
|---|---|---|---|
| Emplacement des tests partagés | `tests/boundaries/` et `tests/contracts/` vides, hors périmètre d'écriture § 6 ; pourtant exigés par la définition de fini | Préparer les tests sous `src/kernel/`, puis autorisation de les placer dans les deux dossiers partagés ou amendement du critère | — |
| Classification | La source Villani a six retours, dont `unknown`, le contrat exige cinq classes ; secrets et fichiers cachés ne doivent pas devenir authoritative par défaut | Question envoyée à l'utilisateur ; refus explicite des cas sans classe sûre proposé | — |

### Décisions locales

- Les contrats décrivent les données. La présence effective d'un symbole appartient aux consommateurs de `codeview` ; aucune I/O dans `contracts`.
- Les neuf relations suivent la décision 2. Les cinq domaines concrets sont repris ; `lists_of<T>` reste reporté jusqu'au catalogue concret de verifier (pas de type libre fourni par le modèle).
- `NodeStatus` reprend les sept états de la décision 5, avec `budget_limited` demandé par le MODULE. Un nœud `running`/`passed` doit porter un critère, `blocked` doit porter sa cause exclusivement. Parenté locale cohérente ; existence/unicité des parents laissées à engine.
- `EventType` initial : `status`, `validation`, `tool_activity` (source Villani) ; extensions uniquement à l'arrivée de leurs producteurs. Version Event fixée à 1, entiers/booléens stricts, champs inconnus refusés.
- Modèles gelés ; reconstruire un modèle validé pour une transition. Le gel Pydantic n'est pas une immutabilité profonde : le payload est détaché de son entrée, la publication durable appartient à journal.
- `spliced_range` : lignes 1-based, bornes inclusives ; `n_replacements=0` reste un fait représentable, jamais transformé en succès. `returncode=None` demeure inconnu.
- Les limites de snippets seront fixes. La reprise Villani lit tout avant de tronquer : il faut borner la lecture elle-même. La signature Ouroboros omet défauts/kwonly/annotations : lecture directe de l'AST nécessaire.

### Reprises traitées

| Source relue | Verdict | Fait ? | Note |
|---|---|---|---|
| Villani `villani_code/mission_state.py:12-95`, `autonomous.py:53-60` | Inspirer / Copier | oui | Modèles Pydantic et états ; source réelle sous `villani_code/`, licence absente, copie libre accordée dans MANIFEST |
| Pi `packages/chord/src/json.ts:4`, `session/jsonl/types.ts:4` | Adapter | oui | JSON fini, version explicite ; aucune persistance kernel |
| Pi `packages/agent/src/harness/result.ts:1` ; Kilo `packages/core/src/util/error.ts:3-72` | Adapter / Traduire | partiel | Cause fermée et accumulateur ; pas de fabrique de classes d'erreur, conformément au contrat local |
| Villani `villani_code/repo_rules.py:54-68` | Copier | en attente | Six classes réelles, divergence conservée ci-dessus |
| Villani `villani_code/indexing.py:146-150` ; Ouroboros `ouroboros/code_intelligence.py:261-270` | Copier | non | Sources relues ; insuffisances mesurables à corriger pour satisfaire le contrat |

## Point de reprise — 06:09 — lecture structurelle et identité

**Statut** : en cours. **Mise à jour** : 06:09.

### Journal — 06:09

- Accumulateur validé : **80 tests verts** avec les contrats, trois causes et chemins conservés dans une seule exception. Première proposition de commit ajoutée, non exécutée.
- `codeview` : collecte rouge avant création du module, puis **20 tests verts** sur AST, snippet, binaire et confinement. Fichier réel de 10 000 000 octets : instrumentation de `Path.open` attestant **un seul `read(8000)`**, sortie 8 000 octets. Source jamais exécutée malgré un `raise` au niveau module.
- Incident `smooth_levels(0.0, 0.0, 0.0)` : arité 3 identique, annotations réelles `tuple, tuple, float` différentes des types de l'appel ; kernel fournit le fait, verifier devra faire la gate de compatibilité.
- Identité : collecte rouge avant `RecordKey`, puis **78 tests verts** pour identité et codeview (31 cas de classification acceptée, 16 cas de refus, 11 tests d'identité inclus).
- **Niveau de preuve atteint : 4** ; lectures filesystem réelles observées, aucune validation de campagne ni des modules voisins.

### Avancement

- [x] Cinq modèles et liste interdite pour `Node.target`.
- [x] Signature AST, défauts, kwonly, posonly, annotations ; incident d'arité rejoué.
- [x] Cinq classes avec table des règles et précédences ; refus explicite des autres chemins.
- [x] Snippet borné en octets et lignes, fichier d'une ligne de 10 Mo.
- [x] Binaire : extension, quatre BOM UTF-16/32, NUL et seuil strictement supérieur à 30 %.
- [x] Accumulateur : toutes les violations avec chemin exact.
- [x] Identité réflexive/symétrique/transitive sur les clés présentes ; absence jamais égale à une absence.
- [ ] Contrôles dans `tests/boundaries/`.
- [ ] Double et `Protocol`, dont contrôle dans `tests/contracts/`.

### Décisions locales

- Classification : choix conservateur annoncé en attente de réponse utilisateur. Cinq classes, et `PithosError(invalid_path)` pour les adresses absolues, `..`, chemins cachés non classés et secrets. `.env.example` est refusé aussi. Les environnements ignorés par Villani (`.venv`, `venv`, `.villani_code`) sont `runtime_artifact`. La fonction est lexicale : `is_path_within(child, parent)` reste nécessaire au consommateur pour les symlinks.
- Snippet : lignes 1-based inclusives, **dans le préfixe de 8 000 octets** ; au plus 40 lignes. Une plage située après ce préfixe rend `""`. Pas de balayage non borné pour atteindre une ligne lointaine. L'UTF-8 de sortie reste borné même après remplacement d'octets invalides.
- Symboles : fonctions synchrones/asynchrones de premier niveau uniquement. `arity` = nombre total de positions déclarées, y compris positions avec défaut ; `posonly`, `kwonly`, `defaults`, `annotations`, `vararg`, `kwarg` complètent le contrat. `module_defs` inclut aussi les classes ; aucune arité de constructeur n'est inventée.
- Pas de regex Python, ni import/exécution de la source. Fichier Python supérieur à 2 000 000 octets : refus `oversized`. Autre langage : `structural_unavailable` explicite.
- `RecordKey(kind="verification", value=(mission_id, node_id, attempt, relation))` : seul kind produit au socle, décision 30. Aucun fallback, aucune normalisation de noms, aucun kind de campagne/broker anticipé. `Fact = FileFact` jusqu'à l'arrivée d'un autre producteur de faits.

### Reprises traitées

| Source relue | Verdict | Fait ? | Note |
|---|---|---|---|
| Villani `villani_code/utils.py:22-27` | Copier | oui | `relative_to` et résolution ; ordre public child/parent respecté |
| Villani `villani_code/repo_rules.py:54-68` | Copier | adapté | Précédence conservée ; sixth `unknown` remplacé par refus explicite, environnements non authoritative |
| Villani `villani_code/indexing.py:146-150` | Copier | adapté | Lecture bornée AVANT décodage, contrairement à la source ; preuve instrumentée |
| Ouroboros `ouroboros/code_intelligence.py:261-270`, `:485-582` | Copier | adapté | AST direct enrichi ; pas de copie de l'index ni du `FileFact` structurel homonyme ; limites et secrets relus |
| Kilo `packages/opencode/src/tool/read.ts:146-195`, `:394-435` | Traduire | adapté | Détection par extension/contrôles portée avec notice MIT ; BOM traité binaire pour le lecteur UTF-8, là où la source récente sait lire UTF-16/32 |
| Décisions 22 et 30, sources locales de vérité | Adapter | oui | Clé de vérification typée ; tests de toutes les composantes et de l'équivalence |

**Blocage classification précédent** : mitigé par refus explicite, implémentation vérifiée. La politique annoncée reste soumise à la réponse utilisateur, sans empêcher le travail indépendant.

## Point de reprise — 06:09 — livraison vérifiée, clôture bloquée par le périmètre

**Statut courant : bloqué. Mise à jour : 06:09. Lignes : 440 / ~380 L.**

### Journal — 06:09

- Double : **13 erreurs de setup** avant création de `tests/doubles/kernel.py` (fichier absent), puis **13 tests verts**. Le contrôle supplémentaire de fichiers absents porte désormais ce groupe à **14 tests**. Constructeurs valides, même Protocol et mêmes paramètres publics, corpus AST commun ; accès disque interdits par monkeypatch pour le double. Aucun état interne d'un voisin simulé.
- Contrôle AST d'imports/I/O préparé : autorisations stdlib/Pydantic et imports relatifs kernel seulement ; lecture dans `codeview` seulement, aucune écriture ni exécution de source. **14 tests**, dont 12 cas interdits injectés pour vérifier le détecteur. Le contrôle porte sur les imports et appels directs observables, pas sur un sandbox de code Python hostile.
- Revue adversariale du payload : **3 nouveaux tests rouges** (tuple, set, Decimal coercés par l'union récursive), 91 verts dans le run contrats/frontières. Correction par `TypeAdapter` JSON strict et fini en mode Python avant la validation externe, y compris à la lecture JSON. Ce chemin remplace l'union récursive précédente, conservée comme tentative historique dans le journal. Test de cycle ajouté, rejet explicite.
- Identité : les valeurs brutes égales ne réconcilient plus rien ; trois tests supplémentaires pour chaîne, dict et tuple non typés.
- Validation finale : `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider src/kernel` → **193 passed in 0.32s**, après les dernières corrections de lisibilité. `python -V` : **Python 3.12.9** ; `sys.prefix` : **`/Users/victorcarre/.pyenv/versions/pithos`**.
- Décompte physique production : `codeview.py` 210, `contracts.py` 121, `errors.py` 45, `facts.py` 48, `protocol.py` 16 = **440 lignes** (blancs, docstrings, notice inclus). Le double a **175 lignes** ; les tests ne sont pas comptés comme production.
- **Justification de l'écart de 60 lignes** : notice MIT obligatoire conservée en entier ; projection de signature avec défauts/kwonly/posonly/annotations/variadiques ; refus explicites des chemins indéterminés ; Protocol de 16 lignes et clé typée réellement testée. La cible reste **~380**, non remontée. Pas d'index, d'I/O d'écriture ni de fonctionnalités de campagne pour justifier artificiellement ce dépassement.
- Travail concurrent observé : `src/journal/redact.py` est apparu après l'inventaire initial. Il n'a été ni lu pour les tests kernel, ni modifié, ni proposé au commit. Les autres fichiers préexistants restent hors livraison.
- **Niveau de preuve atteint : 5 — contrat du double validé.** Les tests métier sont de niveau 4, certaines lectures sur fichiers réels sont observées ; aucune campagne, aucun Ollama et aucun module voisin réel n'ont été testés. Niveau 6 non revendiqué.

### Avancement final du module

- [x] Les cinq modèles valident/rejettent leurs contraintes avec cas de rejet explicites.
- [x] `Node.target` refuse une liste.
- [x] `codeview.symbols` décrit tuple, défauts, kwonly et posonly ; incident `smooth_levels` couvert.
- [x] `classify_repo_path` : cinq classes, table de précédence et refus conservateurs.
- [x] Snippet borné en octets et lignes, lecture instrumentée sur une seule ligne de 10 Mo.
- [x] Binaire : extension, quatre BOM UTF-16/32, NUL, seuil > 30 %.
- [x] Accumulateur : trois défauts rendus ensemble avec leurs chemins exacts.
- [x] Identité : réflexive, symétrique, transitive sur les clés ; absence et données non typées ne réconcilient jamais.
- [x] Double présent dans `tests/doubles/kernel.py`, même `CodeView` Protocol, test contractuel vert localement.
- [x] Contrôle du graphe d'imports et des I/O vert localement.
- [x] Écart de lignes justifié sans remonter la cible ; documentation de reprise et propositions disponibles.
- [ ] Contrôle d'import **situé dans `tests/boundaries/`**, exigence littérale du MODULE.
- [ ] Contrôle du double **situé dans `tests/contracts/`**, exigence littérale d'AGENTS.md § 11.
- [ ] Statut `fini`, après résolution des deux points de placement seulement.

### Blocages — résolution ou suite exacte

| Quoi | Pourquoi | Ce qui débloquerait | Résolu le |
|---|---|---|---|
| Emplacement des tests partagés, ouvert au premier point de reprise | Tous les tests sont prêts et verts mais AGENTS.md § 6 interdit encore l'écriture dans leurs dossiers obligatoires | Autoriser uniquement les deux déplacements nommés dans « Prochaine action » ; aucun changement d'un autre module requis | — |
| Classification, ouvert au premier point de reprise | La source comportait `unknown` en sixième classe | Implémentation conservatrice annoncée : cinq classes + erreur pour les chemins indéterminés ; table verte, choix encore modifiable sur réponse explicite utilisateur | 06:09, choix conservateur |

### Commandes de reprise

```sh
# déjà exécuté avec succès, uniquement le kernel
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider src/kernel

# après autorisation des deux déplacements uniquement
mv src/kernel/test_double_contract.py tests/contracts/test_kernel_double.py
mv src/kernel/test_import_boundaries.py tests/boundaries/test_kernel.py
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider src/kernel tests/contracts/test_kernel_double.py tests/boundaries/test_kernel.py
```

Les chemins racine des deux tests sont calculés par `parents[2]` et restent corrects à leur destination. Les commandes `mv` ci-dessus sont préparées, **non exécutées**. Le prochain module est **journal**, sans intervention sur son travail dans cette session.

### Revue de livraison — 06:09

Les 15 fichiers de cette livraison (documents kernel, code, tests, double) ont été contrôlés individuellement
avec `git diff --no-index --check /dev/null <fichier>` : **aucun diagnostic d'espace ou de conflit**. Leur
statut non suivi impose ce contrôle explicite ; le `git diff --check` ordinaire ne les inspecte pas. Le
retour 1 de `--no-index` correspond à la différence avec `/dev/null`. Les seules modifications postérieures
aux 193 tests verts concernent la documentation. Les propositions finales visibles de `git.md` remplacent
les propositions antérieures conservées ; aucune écriture Git exécutée.
