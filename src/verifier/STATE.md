# STATE — `verifier`

**Statut** : non commencé
**Mise à jour** : —
**Lignes** : 0 / ~800 L socle / ~950 L cible

## Prochaine action

Lire `src/kernel/facts.py` et le double kernel pour vérifier si des snapshots source attestés avant/après et `RepoFact` ont été publiés ; dès qu'ils le sont, implémenter `run(criterion, facts)` en croisant leurs empreintes et chemins sans lire le workspace. Sinon faire trancher la forme de ces faits et la liaison outil → modèle Pydantic déclaré ; les demandes précises figurent dans le point de reprise du 07:09 ci-dessous.

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
| `run(criterion, facts)` complet | `kernel.Fact = FileFact` ne porte que des empreintes et une plage ; aucun contenu avant/après, aucun RepoFact. Lire `FileFact.path` violerait la frontière. | Contrat kernel pour les sources attestées avant/après et RepoFact, puis doubles des producteurs. | — |
| `schema_conform` | Le modèle Pydantic déclaré du produit n'a aucun champ/règle de liaison à `tool` dans l'interface actuelle. Dériver son schéma des annotations est explicitement exclu. | Définir la liaison outil → modèle de sortie déclaré dans un contrat typé. | — |
| Reçu durable | `tests/doubles/journal.py` et le Protocol du journal sont absents au démarrage. | Publication de la frontière et du double journal avec `emit` vrai/faux. | — |
| Emplacement des tests partagés | AGENTS §6 permet seulement les tests locaux et le double ; §11 exige `tests/contracts/` et `tests/boundaries/`. | Autorisation de déposer les tests propres à verifier dans ces deux dossiers. | — |
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
| Gate complète `run(criterion, facts)` | Les seules empreintes FileFact ne permettent pas d'exécuter les états avant/après ; RepoFact absent. | Kernel doit publier des snapshots source bornés, liés aux octets/empreintes avant/après et au chemin FileFact, plus un RepoFact attestant les chemins effectivement modifiés et la complétude du diff/status. Publier les doubles correspondants. | — |
| `schema_conform` | Aucune liaison définie entre le symbole outil et son modèle Pydantic explicitement déclaré. | Définir cette liaison dans un fait/contrat approuvé. La source du schéma doit venir du produit, jamais d'un littéral proposé par le modèle ni d'une inférence des annotations. | — |
| Appelant et reçu final de nœud | La preuve de changement effectif croisée avec RepoFact manque. | Composer les axes dans `run`, puis bloquer mécaniquement si reçu absent. Le reçu actuel annonce expressément son effet non attesté. | — |
| Placement des deux tests partagés | AGENTS §6 interdit les destinations exigées par §11. | Autorisation pour `tests/contracts/test_verifier_double.py` et `tests/boundaries/test_verifier.py`, ou décision commune sur cette contradiction. Les deux fichiers locaux sont autonomes et déplaçables. | — |
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
