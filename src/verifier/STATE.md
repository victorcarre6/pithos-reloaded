# STATE — `verifier`

**Statut** : en cours
**Mise à jour** : 15:09
**Lignes** : 749 code / 950 cible · 974 physiques
**Empreinte** : fcecb5f83e7d69dd2a2ea8d7c2eb2ea7bd17fd3e92dfd6142b0cca54362b5401

## Prochaine action

unit_projection est livré et le trial-25ugxn94 est vert. Prochain item : définir le binding typé outil → modèle de sortie déclaré pour schema_conform ; conserver le refus schema_binding_missing tant que ce contrat manque.

## Avancement

- [x] Projection exacte unit_projection : comparaisons sans tolérance, bornes et exemples détenus par le harness.

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

## Point de reprise — 06:09 — démarrage sur interfaces en conception

**Statut courant** : en cours. **Lignes mesurées** : 0 / ~800 L socle, ~950 L cible.

- Demande utilisateur : avancer sur verifier pendant la conception du kernel. Périmètre : `src/verifier/` et `tests/doubles/verifier.py`, aucune commande Git en écriture.
- Environnement vérifié : Python **3.12.9**, `/Users/victorcarre/.pyenv/versions/pithos`, Pydantic 2.13.4, Hypothesis 6.167.1, pytest 8.4.2 ; aucune installation.
- Sources relues : décisions 2 et 23, contrat explicite Pydantic du produit dans `docs/ARCHITECTURE.md`, Villani `validation_loop.py:282-329`, `planning.py:403-411`, `benchmark/verifier.py:15-137`, `autonomy.py:99-126`, Pi délais/process/capture. Les chemins Villani réels incluent `villani_code/`.
- `round_trip` suit la décision 2 et son exemple encode/decode : **g(f(x)) == x**. Le commentaire inverse du MODULE n'est pas utilisé.
- Hypothèse de travail : sources Python autonomes fournies en mémoire par le harness, copiées dans un répertoire d'artefacts créé par verifier ; aucun chemin du workspace ouvert. Cela permet de vérifier le moteur sans inventer les faits manquants.

### Blocages identifiés — 06:09

| Quoi | Pourquoi | Ce qui débloquerait | Résolu le |
|---|---|---|---|
| `run(criterion, facts)` complet | `kernel.Fact = FileFact` ne porte que des empreintes et une plage ; aucun contenu avant/après, aucun RepoFact. Lire `FileFact.path` violerait la frontière. | Contrat kernel pour les sources attestées avant/après et RepoFact, puis doubles des producteurs. | **Résolu le 12:09** — contrats et producteurs publiés, gate complète testée. |
| `schema_conform` | Le modèle Pydantic déclaré du produit n'a aucun champ/règle de liaison à `tool` dans l'interface actuelle. Dériver son schéma des annotations est explicitement exclu. | Définir la liaison outil → modèle de sortie déclaré dans un contrat typé. | — |
| Reçu durable | `tests/doubles/journal.py` et le Protocol du journal sont absents au démarrage. | Publication de la frontière et du double journal avec `emit` vrai/faux. | — |
| Emplacement des tests partagés | AGENTS §6 permet seulement les tests locaux et le double ; §11 exige `tests/contracts/` et `tests/boundaries/`. | Autorisation de déposer les tests propres à verifier dans ces deux dossiers. | **Résolu le 10:09** — déplacés par la passe transverse ; suite complète verte. |
| Reprises incompatibles avec les règles dures | La liste de sources inclut purge Kilo, lectures workspace et invocations Git ; elles contredisent append-only et l'autorité du module. | Aucune reprise de ces effets dans verifier ; les principes purs seuls sont applicables. | 06:09 — priorité aux interdits explicites |

**Niveau de preuve** : aucun test exécuté à ce stade.

### 06:09 — huit relations exécutées et runner borné

- `domains.py`, `relations.py`, `models.py`, `runner.py` : cinq domaines fermés ; huit relations de la décision 2 ; `schema_conform` refuse explicitement `schema_binding_missing`. `monotone` exige un domaine numérique ordonné. `raises_on` compare le type exact de l'exception déclarée.
- Admission AST sur source en mémoire : symboles présents, fonctions synchrones unaires, sans décorateur ni générateur ; aucune lecture de cible externe. Le runner crée une copie exclusive, lance `[sys.executable, '-I', '-B', script]`, conserve source/script/stdout/stderr/rapport/métadonnées et borne le retour à 24 lignes / 1 800 caractères, tête **et** queue.
- Seed fixe **0**, 100 exemples Hypothesis, shrinking actif, base d'exemples désactivée. `deepcopy` isole chaque argument de l'attendu : les fonctions mutables ne changent pas le terme de comparaison.
- Deadline locale positive finie ; fichiers de sortie directs, sans pipe hérité bloquant ; fin du groupe de processus après l'exécution. Cette isolation de processus n'est pas une sandbox de code hostile, et le worktree hermétique reste conditionné au spike 5.
- Rouge initial : collecte impossible, `ModuleNotFoundError: verifier.domains` (1 erreur). Première implémentation : **24 verts / 1 rouge**, test trop lié au libellé historique Hypothesis « Falsifying example » ; 6.167.1 écrit « Failing test case ». Assertion corrigée sur l'appel `invariant` et le contre-exemple réellement observé `x=0` ; pas de parseur de récupération ajouté.
- Vérification : `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider src/verifier/test_relations.py src/verifier/test_runner.py` → **49 passed in 9.83s**, Python 3.12.9 / venv pithos.
- Mesures ciblées : stdout de **40 009 octets** conservé intégralement, aperçu ≤1 800 caractères ; timeout 0,4 s sans statut inventé ; sorties prématurées 0/1/20/70/127/9009 classées pannes ; échec d'écriture `meta.json` retire le succès.
- **Niveau de preuve : 5** pour l'usage des contrats via le double kernel ; exécution fonctionnelle réelle de scripts Python autonomes (niveau 4). Aucune intégration workspace/journal/Ollama revendiquée.

### 06:09 — mutations et preuve de sensibilité

- Cinq opérateurs maison à un seul site : retour `None`, inversion d'une condition, échange arithmétique, inversion de comparaison, déplacement d'un nombre. Chaque mutant repart de l'AST original ; déduplication, parsing/rendu et compilation sans exécution avant émission.
- `kill_check` exige une baseline verte, archive chaque exécution et s'arrête au premier kill. Aucun code non compilable, exit 127, timeout ou autre résultat inconnu ne devient un kill. Zéro mutant ou plafond de 64 atteint sans kill → **bloqué**, pas tautologie prétendument démontrée.
- Le délai est partagé entre baseline et mutants ; les essais ne reçoivent que le temps restant.
- Rouge initial : `ModuleNotFoundError: verifier.mutation` (1 erreur de collecte), conservé ici. Après implémentation : `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider src/verifier/test_mutation.py` → **10 passed in 3.86s**.
- Observé : round-trip correct tue un mutant ; la propriété `total` d'une fonction arithmétique simple survit à tous les mutants ; les cinq opérateurs produisent des sources distinctes compilables. **481 lignes de production** à cette étape / ~800 socle.
- **Niveau de preuve : 5** sur contrats via double kernel ; subprocess et opérateurs exercés réellement sur sources de test autonomes.

### 07:09 — reprise et double gate verte

- Reprise utilisateur après changement de date ; environnement revérifié : Python 3.12.9 / pyenv pithos.
- `gates.check_sources` compose rouge-avant, vert-après et kill avec un budget partagé ; les sources identiques sont refusées avant I/O. `Verdict.verification` décrit cette seule vérification, **pas le passage d'un nœud à vert**. `run(criterion, facts)` demeure non implémentable avec les faits actuels.
- `SourceVerifier` et `MemoryVerifier` existent ; leurs tests de conformité restent à écrire. Le module réel `gates` et l'objet mémoire exposent la même signature `check_sources(..., artifact_root=..., timeout=...)`.
- Rouge initial de la gate : `ModuleNotFoundError: verifier.gates` (1 erreur de collecte). Puis **15 passed in 3.64s** sur `test_gates.py` ; suite complète après conservation séparée des notes Hypothesis et enrichissement des métadonnées : **74 passed in 16.35s**.
- Les contre-exemples Hypothesis complets restent dans `counterexample.txt` ; `ExecutionResult.counterexample` en donne un aperçu borné, distinct de stdout/stderr. `meta.json` porte désormais le critère, SHA-256 de la source, version Python et seed, plus le résultat typé. Sources/scripts/métadonnées sont écrits exclusivement et `fsync`és ; les logs du processus sont synchronisés.
- **598 lignes de production** à la reprise / ~800 socle. Aucun fichier voisin modifié.
- Blocage journal réexaminé : **résolu le 07:09 pour la dépendance d'émission**. `tests/doubles/journal.py` existe maintenant ; `Journal` est exporté par `journal/__init__.py` (et non `journal/protocol.py`, chemin recherché absent). Les tests verifier utiliseront ce double, sans lancer les tests du journal. Ses propres blocages d'intégration demeurent hors du périmètre.
- **Niveau de preuve : 5** sur double kernel ; artefacts et subprocess réellement exercés sur le corpus local.

## Point de reprise — 07:09 — tranche vérifiée, raccordements bloqués

**Statut courant : bloqué.** **Lignes mesurées : 739 / ~800 L socle, ~950 L cible.** Double : 38 L.
Les anciens en-têtes/mesures sont historiques ; ce point et « Prochaine action » décrivent l'état courant.

### Livraison vérifiée

- Huit relations, cinq domaines fermés, admission AST avant I/O, runner à argv fixe et timeout partagé,
  sources/scripts/sorties conservés, contre-exemple minimal séparé et borné.
- Cinq mutations compilables à un site ; vraie double gate rouge-avant / vert-après / kill.
- `SourceVerifier` publié par `verifier`, double mémoire déterministe conforme ; ses scénarios couvrent
  vert, rouge avec contre-exemple, rejet tautologique et reçu absent.
- `emit_receipt` utilise le double journal maintenant disponible : validation de la clé typée, relation,
  nœud, tentative et artefact avant toute écriture ; `None` lorsque `journal.emit` rend `False`.
  Le payload conserve **scope=source_verification, effect=unproven**. Ce reçu est nécessaire mais
  **insuffisant pour compter un nœud vert** : le raccordement aux faits externes n'est pas fait.
- Contrôles locaux : imports limités aux contrats kernel, interface publique journal, stdlib et dépendances
  déclarées ; aucune I/O directe hors runner, aucun `exec`, shell ni Git. Test réel instrumenté des chemins
  ouverts et de l'argv : seulement les nouveaux artefacts du runner. Ce contrôle n'est pas une sandbox
  ni une preuve d'absence d'effets pour du code candidat hostile.

### Résultats et corrections conservés

- Reçu : rouge initial de collecte `ModuleNotFoundError: verifier.receipt` (1 erreur), puis
  **8 passed in 0.86s**, avec le double officiel du journal.
- Frontières/double : **20 verts / 1 rouge en 2.98s** ; le test injecté `from kernel import codeview`
  révélait un trou dans le contrôle d'import. Résolution : vérifier les noms importés depuis le package,
  pas seulement son nom racine.
- Revue AST : **5 rouges / 7 verts / 28 deselected en 0.06s**. Cas démontrés : remplacement d'un symbole
  par une définition async ou un import (trois cas), confusion entre générateur imbriqué et fonction
  extérieure, mutation d'une définition imbriquée. Admission corrigée ; parcours du corps direct partagé
  entre admission et mutations. Puis **26 passed, 30 deselected in 0.05s**.
- Validation finale : `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider src/verifier`
  → **108 passed in 20.09s**. Python **3.12.9**, venv **pithos**, Pydantic 2.13.4, Hypothesis 6.167.1,
  pytest 8.4.2. Aucun test de module voisin lancé, aucune dépendance installée.
- Preuve autonome conservée : `/private/tmp/pithos-verifier-proof-c74qv4ng/`.
  Avant : `invariant-_9dzhvo7/invariant.py` (**exit 20**, contre-exemple `x=0`) ;
  après : `invariant-a5qihzba/invariant.py` (**exit 0**) ; mutant :
  `invariant-t3gwbghl/invariant.py` (**exit 20**, opérateur `return_none:1:10`). Chaque dossier conserve
  sa source, son script, stdout/stderr, son rapport et les métadonnées. Aucune suppression effectuée.
- **Niveau de preuve atteint : 5**, contrats sur doubles kernel/journal/verifier. Les subprocess et
  artefacts ont été réellement exercés sur des sources autonomes locales, sans mission, workspace
  de campagne ni Ollama. Aucune validation de niveau 6 revendiquée.

### Avancement — Fini quand

- [ ] Les **9** relations exécutables : **8/9**, `schema_conform` bloquée par la liaison au schéma déclaré.
- [x] Script rendu écrit et conservé, chemin porté par le reçu de vérification.
- [x] Invariant tautologique rejeté explicitement.
- [x] Invariant vert avant implémentation rejeté explicitement.
- [x] `kill_check` tue un mutant d'une implémentation correcte et zéro sur la tautologie testée.
- [x] Cinq opérateurs produisent des mutants distincts compilables ; les erreurs ne deviennent pas des kills.
- [x] Contre-exemple minimal Hypothesis conservé, aperçu borné tête et queue.
- [x] Exit 127 et sémantique `cmp > 1` classés pannes d'outillage.
- [x] `returncode=None` préservé sans coercition `or`.
- [ ] `emit_receipt` rend `None` sur refus journal **et l'appelant bloque** : première moitié testée ;
      transition de l'appelant encore à raccorder après `run` et les faits externes.
- [ ] Frontière validée dans **tests/boundaries/** : test vert localement, emplacement hors périmètre.
- [x] Test instrumenté : pas de fichier workspace ouvert, aucune commande Git lancée par verifier.
- [ ] Contrat du double dans **tests/contracts/** : `SourceVerifier` conforme et testé localement,
      emplacement hors périmètre ; l'API complète `run` reste en attente des faits.
- [x] Ratchet : **739 L**, sous la cible de socle ~800 L ; cible inchangée.

### Blocages restants et demandes précises

| Quoi | Pourquoi | Ce qui débloquerait | Résolu le |
|---|---|---|---|
| Gate complète `run(criterion, facts)` | Les seules empreintes FileFact ne permettent pas d'exécuter les états avant/après ; RepoFact absent. | Kernel doit publier des snapshots source bornés, liés aux octets/empreintes avant/après et au chemin FileFact, plus un RepoFact attestant les chemins effectivement modifiés et la complétude du diff/status. Publier les doubles correspondants. | **Résolu le 12:09** — contrats, producteurs, croisement pur et double sont publiés. |
| `schema_conform` | Aucune liaison définie entre le symbole outil et son modèle Pydantic explicitement déclaré. | Définir cette liaison dans un fait/contrat approuvé. La source du schéma doit venir du produit, jamais d'un littéral proposé par le modèle ni d'une inférence des annotations. | — |
| Appelant et reçu final de nœud | La preuve de changement effectif croisée avec RepoFact manque. | Composer les axes dans `run`, puis bloquer mécaniquement si reçu absent. Le reçu actuel annonce expressément son effet non attesté. | — |
| Placement des deux tests partagés | AGENTS §6 interdit les destinations exigées par §11. | Autorisation pour `tests/contracts/test_verifier_double.py` et `tests/boundaries/test_verifier.py`, ou décision commune sur cette contradiction. Les deux fichiers locaux sont autonomes et déplaçables. | **Résolu le 10:09** — déplacés par la passe transverse ; suite complète verte. |
| Double journal initialement absent | Dépendance publiée depuis la reprise du 07:09. | `Journal` lu dans `journal/__init__.py`, double officiel utilisé dans les tests d'émission. | 07:09 — résolu |

Déplacements préparés, **non exécutés**, suivis du seul périmètre de tests verifier :

```sh
mv src/verifier/test_double_contract.py tests/contracts/test_verifier_double.py
mv src/verifier/test_import_boundaries.py tests/boundaries/test_verifier.py
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider src/verifier tests/contracts/test_verifier_double.py tests/boundaries/test_verifier.py
```

### Reprises traitées et limites

| Source | Verdict appliqué | État | Note |
|---|---|---|---|
| Villani `benchmark/verifier.py:15-137` | Adapter le tronc conservé | fait | Interpréteur courant, sorties archivées, statut inconnu distinct ; pas de commande libre ni shell. |
| Villani `planning.py:403-411` | Copier puis corriger la borne | fait | La version source perdait la queue au cap caractères ; régression testée et queue conservée ici. |
| Villani `validation_loop.py:282-329` | Adapter | fait | Arrêt au premier échec, temps monotonic ; axes typés et notes Hypothesis remplacent la classification par mots-clés pytest. |
| Pi `bash.ts:25`, `child-process.ts:49`, `output-capture.ts:26` | Adapter | fait | Validation du timeout, groupe de processus, stdout/stderr en fichiers sans attente de pipe hérité, aperçus séparés des preuves complètes. |
| Ouroboros identité et `tools/verify.py:299-319` | Inspirer les gardes pures | fait | RecordKey du kernel, pas de repli ; aucun `or` sur code de retour ; cmp 0/1/>1 sans lancer cmp. |
| Langfuse `evalCompletion.ts:23` | Adapter | fait | Publication avant retour du reçu ; aucune attestation lorsque le journal refuse. |
| Villani comparaison au contenu antérieur + Git diff | Raccordement aux faits | bloqué | Aucune lecture workspace ni invocation Git ajoutée pour contourner les faits manquants. |
| Gate hermétique Ouroboros | Reporté au spike 5 | non porté | Aucun worktree ni plugin pytest. |
| Purges, capteurs écartés, autres reprises hors de cette tranche | Non portés | documenté | Les interdits et les propriétaires des effets priment ; aucune reprise écartée réintroduite. |

Les propositions finales sont dans `git.md` ; **aucune commande Git en écriture exécutée**. Les autres
agents ont publié journal/bridge pendant la session ; leurs fichiers et caches ont été laissés intacts.

### 07:09 — revue finale du filesystem et de l'historique

- **21 fichiers contrôlés**, dont neuf fichiers de production (**739 lignes**) et le double (38 lignes) :
  aucun diagnostic de whitespace via `git diff --no-index --check /dev/null <fichier>`. Cette commande
  contrôle aussi les fichiers qui étaient initialement non suivis ; aucune mutation Git.
- Le commit **46a18fe — arborescence modules** est apparu pendant la session. Contrôle en lecture seule :
  code, tests, double et décisions locales sont déjà identiques à HEAD ; seuls les ajouts finaux de
  `STATE.md` et `git.md` restent modifiés. Les propositions ont été actualisées en append-only : la seule
  proposition encore utile porte ces deux fichiers. L'agent n'a lancé ni add, ni commit, ni push.
- Aucun code modifié après les **108 tests verts** et la preuve autonome ; seuls les documents de reprise
  ont été enrichis. Aucune amélioration de skill proposée : les garde-fous appliqués étaient déjà couverts
  par `autonomous-work`, les enseignements restants concernent les contrats propres au projet.


### 11:09 — mesure de production et en-tête courant

Passe transverse demandée via TEMPO.md. Aucun code métier ni case de livraison modifié.
Mesure AST/tokenize : **563 lignes de code**, **739 physiques**, cible globale **950**. Sous-paquets et __init__.py inclus ; tests et doubles exclus.
L’empreinte de l’en-tête couvre les chemins et octets de toute la production.
La nouvelle métrique ne valide aucun item métier et ne relève aucune cible numérique.

**En-tête antérieur conservé** :

```text
**Statut** : en cours — code livré et vert, statut corrigé par la passe transverse du 10:09 (il portait `non commencé`)
**Mise à jour** : —
**Lignes** : 607 / ~800 L socle / ~950 L cible — **mesuré par la passe transverse du 10:09** ; l'agent du module ne l'avait pas actualisé
```

**Niveau de preuve : 2** pour la mesure documentaire ; la suite initiale complète du 11:09 a rendu 1 215 passed et 3 skipped hors sandbox. Le détail des nouvelles validations vit dans tests/STATE.md.

### 12:09 — raccordement des faits, point intermédiaire

`kernel.SourceFact`/`RepoFact` et leurs producteurs sont disponibles. Premier rouge : **12 échecs** car `run` manquait ; première implémentation : **12 passed en 1,58 s**. Elle croise cardinalité, chemins, empreintes, plage et dépôt avant exécution. La revue ajoute trois cas encore rouges : diff périmé, coordonnées fausses et diff tronqué pouvaient atteindre `check_sources`. Aucun succès de livraison annoncé ; ils doivent être corrigés avant proposition.

Le choix entre source candidate du modèle et transformations fermées reste demandé à l'utilisateur ; aucun code modèle exécuté. `schema_conform` reste bloqué sur son binding déclaré.
**Niveau de preuve : 4** intermédiaire sur fixtures de faits, double à compléter.

### 12:09 — croisement des hunks et double publiés

Les trois diff incohérents sont corrigés : **37 passed en 4,41 s** sur la première gate, le contrat et la frontière. Corpus élargi ensuite : **132 passed, 1 erreur en 21,57 s**, fixture `verifier_double` inexistante ; correction via le chargeur partagé `double("verifier")`. L'avertissement Pydantic du `model_copy` volontairement invalide est maintenant attendu explicitement par le test.

Mesure courante : **704 code / 950**, **909 physiques**. Test de substitution des faits après verdict et refus de persistance ajoutés ; nouveau contrôle global en attente.
**Niveau de preuve : 5** sur les premières signatures/doubles ; pas de campagne.

### 12:09 — gate complète vérifiée et dernière garde de budget

Après correction du chargement du double : **133 passed en 22,12 s** sur module/contrat/frontière ; suite globale **1 349 passed, 3 skipped, 7 warnings en 37,50 s**. Les trois skips concernent les scénarios propres aux doubles bridge/campaign/refinery ; warnings Starlette/httpx et fork après threads inchangés.

Une dernière régression rouge (**1 failed, 24 deselected en 0,04 s**) montre que la validation des faits redonnait tout le timeout à check_sources. `run` décompte maintenant le temps écoulé depuis l'entrée et bloque si le budget est épuisé avant l'exécution. Les coordonnées d'un hunk au-delà de la fin d'une source sont aussi refusées. Revalidation finale en cours.

**Résolution des blocages** : forme et producteurs des faits, gate complète et liaison du reçu sont résolus ; l'appelant doit encore bloquer son nœud sur `None`. La frontière et le contrat partagé sont bien dans tests/boundaries et tests/contracts. `schema_conform` demeure ouverte (8/9 relations). L'ancienne portée source_verification reste disponible via check_sources ; run autorise node_verification avec effet confirmé et faits liés.
**Niveau de preuve : 5** sur contrats et doubles, processus verifier réels sur sources de test. Aucune mission ni Ollama.

### 12:09 — preuve finale de la chaîne de faits et de la sélection

Suite complète finale dans **pithos / Python 3.12.9** : **1 367 passed, 3 skipped, 7 warnings en 37,10 s**.
Les contrôles d'en-têtes STATE et `git diff --check` passent. Aucune dépendance installée, aucun Git d'écriture, aucun bytecode suivi modifié. Les propositions sont dans les git.md ; les contrats transverses ont leur lot dans tests/git.md.
**Niveau de preuve : 5**, avec subprocess et fichiers de test effectivement exercés. Le marcheur complet et le premier vert avec modèle local restent à démontrer. La source candidate attend l'arbitrage utilisateur.

### 12:09 — admission publique avant une proposition de code

Quatre tests rouges montrent l'absence de preflight dans la façade/double. La nouvelle méthode compose
les contrôles purs existants admit/render, avec un nom d'artefact logique jamais ouvert. Elle permet à
engine de refuser un critère inexécutable avant l'appel modèle et le splice. Aucun test de propriété n'est
lancé par cette admission. Le Protocol et son contrôle de signature incluent preflight.
Le blocage « source candidate » est levé par l'accord utilisateur ; schema_conform reste non admise.
**Niveau de preuve : 2** à l'écriture ; contrôles ciblés puis globaux en cours.

### 12:09 — admission pure vérifiée

**26 passed en 2,79 s**, préflight/contrat/frontière. Aucun accès disque ni processus dans l’admission ; le symbole manquant, schema_conform et monotone sur JSON sont refusés. Suite complète à relancer avec la nano-étape engine. **Niveau de preuve : 5.**

### 13:09 — validation finale du banc audio

Suite complète dans **pithos / Python 3.12.9** : **1 402 passed, 3 skipped, 7 warnings en 40,64 s**.
La suite intermédiaire après run_attempt avait rendu **1 397 passed, 3 skipped, 7 warnings en 37,46 s**.
Les cinq tests ajoutés relisent effets disque, reçus et artefacts du banc ; aucun nouveau skip.
Skips : variantes réelles non scénarisables bridge/campaign/refinery. Warnings Starlette/httpx et
fork après threads conservés. Les onze mesures STATE passent : **4 570 code, 7 106 physiques**.
Aucune dépendance installée ni commande Git d'écriture. Aucun module déclaré fini.
**Niveau de preuve : 5** sur contrats et composition ; la sonde de critère Ollama, mesurée séparément,
atteint le niveau 6 pour ce seul appel. Le premier trial réel attend le HEAD du dépôt dédié.

### 14:09 — extension custody autorisée, intégration en cours

L'utilisateur répond « Continue en autonomie » à la demande explicite d'extension à verifier :
le raccordement de ses groupes de processus est autorisé. Réutilisation du superviseur lifecycle
et de son pipe : chaque gate a un gardien enregistré avant admission, sous le même propriétaire
que le worker. Verifier conserve commandes, artefacts et verdicts via un port contextuel.

Preuves intermédiaires : 2 erreurs de collecte avant publication des ports ; ensuite **42 passed
in 4.43s** (runner, port et frontière verifier). Custody native : **1 failed, 9 passed in 5.60s** ;
le timeout conservait la requête IPC contenant un Path dans le détail JSON de sortie. Le résultat
terminal est désormais distinct de la requête ; nouvelle vérification en cours. La CLI reste fermée
jusqu'à la preuve d'interruption d'une gate réelle et de récupération après mort du superviseur.
**Niveau de preuve** : 5 pour le port ; validation native de la composition encore incomplète.

### 14:09 — gates sous custody, contre-preuve traitée

Le port contextuel verifier couvre baseline, candidat et mutants. Le superviseur lance un gardien
par gate, écrit sa custody avant admission, puis récolte son groupe sous la plus petite deadline.
Worker et gardiens ont le même propriétaire ; sa disparition permet leur sweep par le détenteur
suivant du verrou. Le runner garde l'autorité sur le rapport, les codes 0/20 et le reçu.
Aucun nouveau protocole réseau ni dépendance ; l'IPC réutilise le pipe du worker.

Résultats intermédiaires conservés : **20 passed in 5.62s** (lifecycle/frontière), puis **2 failed,
11 passed in 34.78s**. La gate réelle était arrêtée mais le worker recevait encore un retour à la
deadline globale : il pouvait restaurer avant la coupure. Le superviseur ne répond plus après cette
borne. L'autre rouge révélait une injection de signature sur une copie différente du double ; le
contrôle reçoit désormais l'instance mutée. Relance : **1 failed, 23 passed in 42.68s** ; tous les
scénarios intégrés passent, le seul rouge est un NameError dans le nouveau test d'admission (assertions
placées dans le mauvais test, corrigées avant la reprise). Aucun résultat négatif n'est effacé.

La CLI est réouverte après les preuves de vraie gate coupée et d'orphelin récupéré ; vérification de
son entrée réelle en cours, puis suite complète. L'isolation reste celle des groupes gérés par le
harness ; elle ne confine pas un programme hostile créant lui-même une session.
**Niveau de preuve : 5 pour la mission complète** (modèle simulé), **6 pour les effets locaux** observés.

### 14:09 — custody des gates livrée et mission réouverte

L'autorisation est confirmée explicitement : « Oui, étendre à verifier ». Les critères, les entrées,
les gates et l'autorité du reçu restent inchangés. Seul le lancement passe par le port sous custody.

- Tests ciblés : **23 passed in 44.47s**. Chaque invariant produit correspond à un gardien admis
  dans la custody commune. Journal refusé : aucun programme de gate lancé.
- Deadline globale pendant la gate réelle : son programme et son descendant sont arrêtés ; le
  candidat et running sont constatés, puis le walk suivant restaure les octets sans appel modèle.
- Superviseur tué pendant une gate réelle : sweep du worker et du gardien avant admission suivante ;
  aucune custody active, aucun descendant encore exécuté et verrou libéré.
- CLI réelle sur le même --run vert : résultat passed/finalized=1, un seul reçu et un seul commit
  de finalisation. Acquittement perdu et refus restent couverts sans double commit ni reçu indu.

Suite complète, Python **3.12.9 / pithos**, sans bytecode ni cache pytest, hors sandbox : **1 556 passed, 3 skipped, 7 warnings en 100,50 s**.
Les skips sont tests/contracts/test_bridge_double.py:77, test_campaign_double.py:170 et
 test_refinery_double.py:82 : variantes réelles sans scénario à charger. Warnings existants :
Starlette/httpx et six occurrences de fork après threads. Contrôle des onze STATE et diff-check verts.
Aucun Git d'écriture sur le harness ou le dépôt opérateur ; les commits de test portent uniquement
sur les dépôts jetables. Aucun nouveau trial Ollama : trial-44kcg6ig reste refusé sur tautology.
Les suspensions de composition du 14:09 sont levées ; leurs contre-preuves restent archivées.

**Niveau de preuve : 5 pour la mission complète**, modèle simulé ; **6 pour les effets locaux**
Git/Prefect/verifier/workspace/journal/lifecycle réellement observés. Les groupes gérés par le harness
ne sont pas une sandbox de code hostile. Le dashboard demeure déclaré terminé pour le moment.

### 15:09 — refus tautology reproduit, consolidation des frontières en cours

Rejeu exact des sources et du critère archivés de trial-44kcg6ig : **rejected / tautology**, avant
rouge, après vert, trois mutants survivants. Les **44 fichiers historiques sont inchangés** par
comparaison SHA-256 avant/après. Nouvelles preuves conservées dans
/private/tmp/pithos-sensitivity-kvhdkqos/verdict.json et ses cinq répertoires d'invariants.

Le corpus réduit compare trois représentations : min/max [0,1] est rejeté ; les versions à branches
[0,1] et [0,2] passent toutes deux rouge-avant/vert-après/kill. La gate prouve seulement l'idempotence
et une sensibilité à son inventaire AST, pas les bornes exactes. Aucun opérateur opportuniste ni
assouplissement de gate n'est ajouté. `test_sensitivity.py` et mutations : **14 passed in 5.53s**.

La consolidation transverse prévue reprend ensuite les ports Walker, MissionRunner et GreenFinalizer.
La sonde de balayage sur chaque fichier, sans sa dispense flow.py, rend **1 failed, 10 passed,
14 deselected in 0.90s** : le vrai scanner accepte socket dans flow.py. Correction ciblée : seul
Prefect est permis en plus dans ce fichier ; les autres interdits persistent. Les contrats vérifient
noms, ordre, nature positionnelle/keyword-only et valeurs par défaut, avec mutations sur chaque port.
Premier passage : **2 failed, 44 passed in 3.91s**, le test oubliait le RepoFact exigé par le double
broker ; fixture corrigée avec le double kernel. Aucun code métier modifié sur ce nouveau chantier.
**Niveau de preuve : 5** pour les contrats ; scripts d'invariants réels et défaut AST reproduit.

### 15:09 — sensibilité et contrats partagés livrés

**164 passed in 22.32s** sur verifier, contrats engine et frontières injectées. Suite complète
**1 568 passed, 3 skipped, 7 warnings en 103,09 s**, Python **3.12.9 / pithos**, sans bytecode ni cache pytest, hors sandbox.
Les trois skips restent tests/contracts/test_bridge_double.py:77, test_campaign_double.py:170 et
 test_refinery_double.py:82 (variantes réelles sans scénario). Warnings existants : Starlette/httpx
et six forks après threads. Contrôle des onze STATE et diff-check verts.

La reproduction exacte conserve les 44 fichiers du trial. Le corpus autonome teste la survie des
mutants du clamp compact et l'acceptation de deux écritures à branches, dont une projection [0,2].
Aucun opérateur de mutation ajouté, aucun critère ni gate modifié ; la preuve produit n'est pas
élargie par cette livraison. `src/verifier/SENSITIVITY.md` expose les résultats et leurs limites.

Les contrats partagés couvrent désormais NanoEngine, Walker, MissionRunner et GreenFinalizer.
La dérive de chaque méthode et des paramètres keyword-only est détectée ; les doubles de walk et
mission ne font aucune I/O et rendent un arbre indépendant. Le scanner n'exempte plus flow.py :
seul Prefect y est autorisé en plus, avec une injection effective dans chaque fichier du module.
Les tests locaux engine restent en place ; aucune implémentation métier voisine n'est modifiée.

Une préférence optionnelle a été demandée sur la preuve de projection exacte. Sans changement de
périmètre décidé, le banc reste celui de PROJECT.md. Aucun essai Ollama supplémentaire, commit,
push ni suppression de données. Propositions ajoutées dans verifier/git.md et tests/git.md.
**Niveau de preuve : 5** sur contrats ; 4 pour les invariants exécutés sur copies contrôlées.

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
