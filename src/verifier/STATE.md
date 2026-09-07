# STATE — `verifier`

**Statut** : non commencé
**Mise à jour** : —
**Lignes** : 0 / ~800 L socle / ~950 L cible

## Prochaine action

Tester le double de la tranche `check_sources`, raccorder l'émission de reçu au nouveau double journal et vérifier son échec `emit=False` ; terminer les contrôles locaux de frontières avant de documenter les interfaces kernel encore manquantes.

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
