# STATE — `kernel`

**Statut** : en cours
**Mise à jour** : 15:09
**Lignes** : 311 code / 380 cible · 492 physiques
**Empreinte** : 05884a1dc300bb788cecee51571247405ec8099dfca979b3f3e492ccea33e8f1

## Prochaine action

unit_projection est livré. Pour schema_conform, définir le contrat de liaison outil → modèle de sortie déclaré avec son producteur ; conserver les critères existants et ne pas inférer les annotations.

## Avancement

- [x] Relation unaire unit_projection ajoutée au catalogue fermé, sans paramètres de borne.

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
| Emplacement des tests partagés | `tests/boundaries/` et `tests/contracts/` vides, hors périmètre d'écriture § 6 ; pourtant exigés par la définition de fini | Préparer les tests sous `src/kernel/`, puis autorisation de les placer dans les deux dossiers partagés ou amendement du critère | **Résolu le 10:09** — déplacés par la passe transverse ; suite complète verte. |
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


### 11:09 — mesure de production et en-tête courant

Passe transverse demandée via TEMPO.md. Aucun code métier ni case de livraison modifié.
Mesure AST/tokenize : **282 lignes de code**, **447 physiques**, cible globale **380**. Sous-paquets et __init__.py inclus ; tests et doubles exclus.
L’empreinte de l’en-tête couvre les chemins et octets de toute la production.
La nouvelle métrique ne valide aucun item métier et ne relève aucune cible numérique.

**En-tête antérieur conservé** :

```text
**Statut** : en cours — code livré et vert, statut corrigé par la passe transverse du 10:09 (il portait `non commencé`)
**Mise à jour** : —
**Lignes** : 339 / ~380 L — **mesuré par la passe transverse du 10:09** ; l'agent du module ne l'avait pas actualisé
```

**Prochaine action antérieure, remplacée car périmée** :

La dérogation demandée ici a été **accordée et exécutée** par la passe transverse du 10:09 :
`test_double_contract.py` est devenu `tests/contracts/test_kernel_double.py` et
`test_import_boundaries.py` est devenu `tests/boundaries/test_kernel.py`. Les deux sont verts, et le
test de frontière a été prouvé mordant par injection d'un `import subprocess` dans `contracts.py`.

Ce qui reste avant `fini` : **treize cases de « Fini quand » ne sont pas cochées** dans la rubrique
Avancement ci-dessous. Les reprendre une par une et cocher ce qui est réellement vérifié — la passe
transverse n'a pas cochée à la place de l'agent du module, faute d'avoir observé chaque item. Le
compte de lignes, lui, est mesuré : 339 L pour ~380 L de cible, sous le ratchet.

**Niveau de preuve : 2** pour la mesure documentaire ; la suite initiale complète du 11:09 a rendu 1 215 passed et 3 skipped hors sandbox. Le détail des nouvelles validations vit dans tests/STATE.md.

### 12:09 — reprise autonome de la tranche de faits

L’utilisateur autorise la progression successive kernel → producteurs → verifier → engine, avec
retour à l’humain aux décisions produit. Aucun Git d’écriture autorisé. Le worktree préexistant
est conservé ; Python mesuré **3.12.9**, suite kernel + contrat + frontière **194 passed en 0,33 s**.

Plan : (1) contrats de faits bornés et double, rejets + round-trip ; (2) producteurs publiant ces
faits, observations réelles sur fichiers et Git local ; (3) gate croisant les faits avant exécution ;
(4) raccordement du marcheur si la contradiction source générée / contrainte dure n°1 est tranchée.
Question de définition envoyée, travail sur les faits indépendant. Aucune génération libre ajoutée.

Le producteur RepoFact existe dans broker/git.py, avec Change, mais ses modèles sont au mauvais
niveau pour verifier. SourceFact transporte les octets ; FileFact porte déjà leurs empreintes.
Kernel valide la forme, jamais l’accord des observations ni une autorité d’émission.
Sources relues : MODULE complet, demande verifier STATE § blocages, broker/git.py, transaction
workspace, Ouroboros code_intelligence.py:73-115 et Langfuse scores.ts:5-24. Aucun code tiers copié
pour ces nouveaux contrats ; pas d’index ni d’autorité publique d’émettre un reçu.

### 12:09 — contrats de faits publiés

Test écrit avant code : collecte rouge, RepoChange absent. Après implémentation : **222 tests verts
en 0,32 s** (kernel + contrat partagé + frontière), dont 28 nouveaux cas. Aucun module voisin importé
par les nouveaux contrats. Mesure : **307 code / 380**, **488 physiques**.

SourceFact contient les octets avant/après (2 000 000 octets maximum chacun, borne codeview existante).
Le transport JSON est hexadécimal, conservant BOM, CRLF et même les octets non UTF-8 ; verifier décide
si une source est exécutable. RepoChange refuse les chemins absolus/traversants et les incohérences
rename/origine. RepoFact reprend les champs du producteur broker avec `complete=False` par défaut.
Les reçus hétérogènes relisent FileFact/SourceFact/RepoFact sans changer les anciens champs.

**Niveau de preuve : 5** sur les constructeurs du double ; 4 sur les rejets/round-trips. L’accord
entre observations n’est pas testé ni décidé par kernel. HostFact et la liaison de schéma restent
hors de cette unité. La suite complète et les producteurs sont l’étape suivante.

### 12:09 — validation globale de l’unité kernel

Suite complète hors sandbox : **1314 passed, 3 skipped, 7 warnings en 35,05 s**.
Les trois skips et les avertissements sont ceux de la passe précédente. Prochaine étape :
producteurs workspace puis broker. Propositions ajoutées sans aucune commande Git d’écriture.

### 12:09 — preuve finale de la chaîne de faits et de la sélection

Suite complète finale dans **pithos / Python 3.12.9** : **1 367 passed, 3 skipped, 7 warnings en 37,10 s**.
Les contrôles d'en-têtes STATE et `git diff --check` passent. Aucune dépendance installée, aucun Git d'écriture, aucun bytecode suivi modifié. Les propositions sont dans les git.md ; les contrats transverses ont leur lot dans tests/git.md.
**Niveau de preuve : 5**, avec subprocess et fichiers de test effectivement exercés. Le marcheur complet et le premier vert avec modèle local restent à démontrer. La source candidate attend l'arbitrage utilisateur.

### 15:09 — projection exacte autorisée, test initial rouge

L’utilisateur demande maintenant la projection exacte sur [0, 1]. Le chantier ajoute une relation
fermée unit_projection, sans borne ni tolérance fournie par le modèle. Les nouvelles missions
l’utilisent ; les reprises conservent leur critère et les anciens reçus ne sont pas requalifiés.
Le premier test kernel échoue comme attendu : relation absente du catalogue (1 failed,
81 deselected, 0,15 s). Implémentation et vérifications en cours.
**Niveau de preuve atteint** : 1 à ce point de reprise.

### 15:09 — projection exacte vérifiée, essai local en cours

Validation ciblée : 108 tests kernel/projection en 3,88 s ; 400 tests kernel/verifier,
contrats/frontières et trial en 31,12 s ; 8 tests trial/mission en 46,27 s, dont reprise
idempotent historique, reçu unit_projection, rollback [0, 2] et custody réelle.
Suite complète : 1 600 passed, 3 skipped, 8 warnings en 114,44 s, Python 3.12.9 / pithos.
Un avertissement ajouté par le test (domain copié comme str plutôt qu'enum) a été corrigé ;
la vérification finale reste à consigner. Les trois skips sont les scénarios réservés aux
doubles bridge/campaign/refinery ; les sept avertissements antérieurs restent distincts.

Rejeu archivé : projection-replay-6k9y5dc3, avant rouge/après vert/mutant tué, 44 fichiers
historiques inchangés par SHA-256, aucun reçu et aucun appel Ollama dans ce rejeu.
Le dépôt opérateur est propre et identique au seed. La première lecture Ollama a été refusée
par la sandbox (operation not permitted) ; la lecture autorisée confirme num_ctx 16384.
Une nouvelle tentative trial --seconds 180 est lancée sous unit_projection ; ne pas en
déduire le verdict avant lecture de son result.json. Aucun Git d'écriture exécuté par l'agent.
**Niveau de preuve atteint** : 5 pour les contrats ; runtime de mission réel avec modèle simulé.

### 15:09 — premier vert réel sous unit_projection

Le nouveau trial-25ugxn94 utilise tous les composants réels, Ollama inclus : **passed** en
44,89811025001109 s pour la tentative, deux appels et 3 350 tokens rapportés (1 227 + 2 123).
Configuration num_ctx 16384 relue par ollama show ; provenance de la capacité toujours asserted.

Relecture indépendante des preuves : exactement trois résultats de gates failed/failed/passed,
un seul reçu durable lié à unit_projection avec effect confirmed, arbre passed, fichier cible
modifié et SHA-256 correspondant au rapport. Avant :
40818e8d40d125b69d8e75dff8fcaab1040dace8d87e7e06b9d8362fba577bf5 ; après :
2699717e89232fcd6ae0eee5395eb8122e67d2ffe9b3f39c9439f83c065f1b29.
La correction produite est max(0.0, min(1.0, level)). Les 44 fichiers du trial-44kcg6ig
restent inchangés, empreintes de nouveau comparées après l'essai.

Le fichier vert est conservé dans experiments/visualizer/workspace/audio_visualizer.py ;
aucun commit, push ni autre Git d'écriture exécuté par l'agent. Ce trial ne passe pas par
Prefect/GreenFinalizer : tree.finalized reste vide. Pour une future mission composée, préparer
un nouveau dépôt seed et un nouveau --run ; ne pas réinitialiser le workspace vert.
**Niveau de preuve atteint** : 6 pour cette nano-étape réelle, vérification finie du contrat
de projection ; pas de preuve universelle ni de finalisation de mission réelle.

### 15:09 — livraison finale de la projection exacte

Suite finale : **1 602 passed, 3 skipped, 7 warnings en 114,64 s**, Python **3.12.9 / pyenv pithos**,
sans bytecode ni cache pytest. Contrôle des onze STATE et revue du diff verts. Les skips
restent les variantes réelles des scénarios réservés aux doubles bridge (ligne 79), campaign
(ligne 170) et refinery (ligne 82). Les avertissements restants sont Starlette/httpx et six
forks après démarrage de threads. Aucun test supprimé ou marqué skip pour rendre la suite verte.

Les contre-preuves précédentes sont conservées : critère absent, avertissement Pydantic,
échec intermittent de reprise et reproduction native du zombie. Leurs corrections sont vérifiées.
Le trial-25ugxn94 prouve la nano-étape réelle sous unit_projection ; sa correction reste non
commitée. Les reprises idempotent gardent leur critère et leur reçu historiques.

Mesures finales : kernel 311 code / 492 physiques ; verifier 749 / 974 ; lifecycle 494 / 679.
Total des onze modules : 5 680 lignes de code / 8 514 physiques. Aucune dépendance ajoutée.
**Niveau de preuve atteint** : 5 pour les contrats partagés ; 6 pour le trial Ollama décrit
ci-dessus et les observations natives de processus, sans prétendre à une preuve universelle.
