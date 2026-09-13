# STATE — `engine`

**Statut** : en cours
**Mise à jour** : 13:09
**Lignes** : 673 code / 1050 cible · 930 physiques
**Empreinte** : 6ec4de1075b2deb88480af06acf8b474670177a0781210ad4fcbd9cde15549d6

## Prochaine action

Terminer la validation transverse de l'instrumentation, puis composer walk autour de run_attempt : reprise/réconciliation, finalisation des verts et baseline, sans réexécuter un nœud running. Le trial-44kcg6ig a été exécuté en réel et refusé sur tautology ; ses octets ont été restaurés, aucune nouvelle initialisation Git n'est nécessaire.

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
| Source candidate du modèle | `AGENTS.md` contrainte dure n°1 interdit tout littéral du modèle à l'exécution ; `workspace/MODULE.md` § 1 prévoit `{function_name, new_source}` généré. Les décisions 2 et 21 de `docs/EXPLANATIONS.md` ne lèvent pas explicitement cette contradiction. | Arbitrer la contrainte ou publier un catalogue fermé de transformations ; aucune route de génération de code ne sera inventée ici. Question posée le 10:09. | **Résolu le 12:09** — l'utilisateur autorise le code candidat sous critères et entrées contrôlés par le harness. |
| Attestation de l'effet réel | `SourceVerifier.check_sources` et `emit_receipt` attestent seulement les sources, avec `effect=unproven`. `kernel.Fact` ne porte pas les snapshots source ni `RepoFact` attendus par verifier. | Publier ces contrats dans kernel et leurs producteurs/doubles, puis la gate complète de verifier. | **Résolu le 12:09** — faits canoniques, producteurs et `Verifier.run` ; 1 349 tests verts avant la dernière garde de budget. |
| Placement des tests transverses | `AGENTS.md` § 11 exige `tests/contracts/` et `tests/boundaries/`, mais § 6 interdit leur écriture par engine. | Tests locaux dans `src/engine/` en attendant une autorisation de placement ou un agent chargé de ces répertoires. | **Résolu le 10:09** — déplacés par la passe transverse ; suite complète verte. |

## Décisions locales

_Choix d'implémentation pris ici, qu'un successeur doit connaître et ne doit pas défaire sans raison._

## Reprises traitées

| Source | Verdict | Fait ? | Note |
|---|---|---|---|

### Journal ajouté — 10:09 — inspection des frontières

**Statut courant : en cours.** Python **3.12.9**, préfixe du venv mesuré :
`/Users/victorcarre/.pyenv/versions/pithos`. Aucun code engine préexistant.
Les doubles kernel, journal, workspace, verifier et bridge ont été lus ; aucun test
de leur implémentation n'a été exécuté. Le chemin d'exécution est suspendu aux
contrats ci-dessus, les items budget et contexte restent indépendants.
**Niveau de preuve : 2** — lecture des signatures et des modèles, aucune exécution métier.

### Journal ajouté — 10:09 — budget et contexte purs

Tests écrits avant l'implémentation : **2 erreurs de collecte**, modules absents.
Après implémentation : **29 tests verts en 0,22 s** dans Python 3.12.9 / pithos.
Commande : `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider src/engine/test_budget.py src/engine/test_context.py`.
Budget à ancre unique, fermeture de l'admission dans la réserve ; inventaire intégral,
raisons exclusives, FIFO, paliers, débordement irréductible et passation périmée testés.
**Niveau de preuve : 5** — nœuds fournis par le double kernel, horloge pilotée ; aucune mission réelle.

### Décisions locales ajoutées — 10:09 — budget et contexte

- Réserve fixe **5 s**, valeur initiale de politique, **non calibrée**. Aucun EWMA.
- `ContextItem.estimated_units` est fourni par le harness dans l'unité de son budget ;
  ce nombre n'est pas présenté comme un usage tokenizer mesuré. Le producteur doit
  inclure les instructions, le critère, les séparateurs et la place de sortie dans son préflight.
- Le contexte reçoit contenus et empreintes explicitement ; il n'ouvre pas les fichiers
  de workspace. Une passation exige des empreintes. L'absence d'une empreinte actuelle
  vaut dérive ; un élément obligatoire périmé ferme l'admission.
- Sous pression ≥ 0,75, FIFO sur les éléments optionnels. L'irréductible à 1,0 est admis,
  au-delà il est bloqué. Les contenus exclus restent entiers dans l'inventaire.
- Sources relues : Villani `context_governance.py:11-71,200-220,252-266`, Unsloth
  `dataprep/synthetic.py:172-177`, Ouroboros `task_pacing.py:199-224`. Aucune compaction reprise.

### Journal ajouté — 10:09 — admission et scission bornée

Test de l'arbre avant code : **1 erreur de collecte**, module absent. Premier résultat :
**21 tests verts en 0,22 s**, avertissement attendu d'un objet Pydantic forgé par le test.
Ajout de cas adverses : concurrence de publication, panne de verrou journal, collision
d'identifiants et disposition du parent. Revue du contexte : **1 rouge / 54 verts**,
un doublon optionnel pouvait masquer un élément obligatoire de même identifiant.
Correction : un doublon contradictoire est rejeté avant assemblage.
Suite locale finale : **55 verts en 0,25 s**, Python 3.12.9 / pithos.
**Production mesurée : 394 lignes physiques** (38 budget, 168 contexte, 72 arbre, 116 admission).
**Niveau de preuve : 5** — kernel et journal sur doubles ; aucune exécution de nano-étape.

### Décisions locales ajoutées — 10:09 — arbre

- `Tree` est un instantané validé ; une transition retourne un nouvel arbre après publication
  par `journal.update_json_locked`. Le chemin `tree.json` vient explicitement du harness.
- Une intention (`phase=intent`) précède la publication. Un CAS compare l'état relu à
  l'instantané attendu. Pas d'appel imbriqué à `journal.emit` sous son verrou global.
- `split_node` prend les cibles déterministes du harness. Une largeur excessive bloque
  entièrement le parent avec `Cause.unverifiable` et trace la liste complète des candidats.
- Un enfant bloqué produit une disposition `deferred` liée au SHA-256 de son résultat
  **structurel**. Ce hash ne remplace pas le futur lien au reçu de vérification.
- `is_verifiable` ne prouve que la présence d'un `Criterion` revalidé ; il n'autorise pas
  à lui seul un effet. L'AST, les symboles et la double gate restent l'autorité de verifier.
  La fonction publique complète `walk(tree, budget, deps)` n'existe pas encore.
- Sources relues : Pi `drive.ts`, `drive/generation.ts:132-184` ; Ouroboros
  `task_tree_ledger.py:108-168,384-433`. Structures adaptées, aucun ledger parallèle repris.

### Journal ajouté — 10:09 — classifieur, frontières et revue finale

Classifieur : test avant code (**1 erreur de collecte**), puis **1 rouge / 13 verts**.
Le rouge venait d'une hypothèse erronée du test : kernel ne classe pas `logs/` comme
runtime. Le corpus utilise maintenant `.villani_code/`, catégorie explicitement publiée
par kernel ; aucune politique de chemins nouvelle n'a été inventée.
Les cinq enums sont calculées, tracées et branchées à `decompose` ; une demande de
lecture ne produit pas d'enfants de modification. Aucune cible absente de l'index.

Frontières : **2 rouges / 74 verts** lors du premier test sans Prefect, causés par
`importlib.reload` qui changeait l'identité de l'exception déjà importée par les autres
tests. Le test charge maintenant une copie isolée du module, sans muter les imports
des tests voisins. Résultat : **76 verts en 0,25 s**.

Revue finale : **5 rouges / 25 deselected** montrent qu'un JSON faux mais valide
(`null`, `false`, `0`, `[]`, `""`) était pris pour un état absent. Le CAS n'accepte
désormais que `{}` comme sentinelle d'absence définie par le contrat journal ; les
autres valeurs sont revalidées et refusées sans écrasement.
Résultat final : **81 verts en 0,30 s**, commande
`PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider src/engine`.
`git diff --check -- src/engine tests/doubles/engine.py` passe.
**Niveau de preuve : 5** — frontières kernel/journal sur doubles ; aucune invocation
de workspace, verifier ou bridge, aucun subprocess ni Ollama. Pas de mission réelle.

### Point de reprise — 10:09

**Statut courant : en cours, exécution bloquée par contrat.**
**Production : 619 lignes physiques / ~1 050 L** : `budget.py` 38, `context.py` 168,
`tree.py` 72, `walk.py` 144, `classify.py` 197. Aucune dépendance ajoutée.
Seul `src/engine/` a été écrit pendant cette session. Aucun Git en écriture.

**Avancement selon « Fini quand » :**

- [ ] Nœud sans critère jamais exécuté : tous les états sont couverts au préflight,
  mais le marcheur exécutant reste absent ; pas de preuve end-to-end.
- [x] Profondeur 3 et `cap_children` appliqués à `split_node`, y compris à un arbre rechargé.
- [ ] Expiration de mission, finalisation des verts, arbre reprenable : budget pur testé,
  mais finalisation non implémentée.
- [ ] `walk` complet sans Prefect : seule l'admission est testée sous import interdit.
- [x] Inventaire typé, une raison d'inclusion ou d'exclusion par élément.
- [x] FIFO ; chaque éviction reste dans l'inventaire avec sa raison.
- [x] Débordement irréductible : `ContextPacket.blocked_cause=context_overflow` et refus de rendu.
  La propagation au statut du nœud attend le marcheur.
- [ ] Incident du brief périmé via `CONTEXT.md` : détection testée sur une passation en mémoire,
  fichier de passation et producteur d'empreintes fraîches pas encore raccordés.
- [ ] Baseline de fin de mission : pas encore implémentée.
- [ ] Dispositions par enfant : blocages structurels couverts, résultats exécutés non couverts.
- [ ] Placement dans `tests/boundaries/` : contrôle local vert sur les huit modules inférieurs ;
  placement partagé toujours hors périmètre.
- [ ] Protocol engine complet, double scénarisé, tests de contrat : à établir avec `walk` complet.

**Choix locaux supplémentaires :** le classifieur adapte les cinq enums de Villani
`planning.py:11-57,154-332,388-400`, relues. `RepoIndex.files` vient du harness ;
pas de parcours filesystem ici. Les règles lexicales sont celles de la source anglaise,
sans prétendre comprendre toute instruction française. Les chemins complets gardent
leur précision, les noms seuls peuvent sélectionner des homonymes ; le cap s'applique
ensuite. Aucun fallback vers des fichiers non mentionnés. Les labels sont heuristiques,
pas des mesures de confiance ni des autorisations d'exécution.

**Travail restant indépendant :** sélection avec raisons et fermeture d'imports (`select.py`),
publication append-only du contexte (`dump.py`). Ils ne doivent pas servir à masquer les
blocages d'exécution. Ne pas créer un faux executor ni inventer une attestation pour
faire passer le test du « premier vert ».


### 11:09 — mesure de production et en-tête courant

Passe transverse demandée via TEMPO.md. Aucun code métier ni case de livraison modifié.
Mesure AST/tokenize : **455 lignes de code**, **625 physiques**, cible globale **1050**. Sous-paquets et __init__.py inclus ; tests et doubles exclus.
L’empreinte de l’en-tête couvre les chemins et octets de toute la production.
La nouvelle métrique ne valide aucun item métier et ne relève aucune cible numérique.

**En-tête antérieur conservé** :

```text
**Statut** : en cours — code livré et vert, statut corrigé par la passe transverse du 10:09 (il portait `non commencé`)
**Mise à jour** : —
**Lignes** : 507 / ~1 050 L — **mesuré par la passe transverse du 10:09** ; l'agent du module ne l'avait pas actualisé
```

**Niveau de preuve : 2** pour la mesure documentaire ; la suite initiale complète du 11:09 a rendu 1 215 passed et 3 skipped hors sandbox. Le détail des nouvelles validations vit dans tests/STATE.md.

### 12:09 — sélection déterministe et fermeture d'imports

Test avant code : **une erreur de collecte**, `engine.select` absent. Après implémentation : **96 passed en 0,33 s** dans pithos Python 3.12.9, module et frontière. Cibles conservées, distances minimales, cycles, sens des imports, profondeur non coercée, arêtes étrangères, filtrage runtime et absence d'I/O vérifiés. L'index reste fourni par le harness ; pas de résolution de modules ni de score sémantique inventé.

Source Ouroboros relue au chemin réel `ouroboros/code_intelligence.py:737-800` (le raccourci `our/` des documents n'est pas un répertoire). Son remplacement de frontier pouvait perdre la cible ; la version portée la conserve dès la distance zéro. Notice MIT incluse. Villani relu pour le filtrage de contexte, délégué au prédicat kernel déjà public.

Mesure : **512 code / 1050**, **736 physiques**. Aucun `walk` exécuteur, Prefect, modèle, baseline de mission ni premier vert revendiqué. Contrat source candidate toujours en attente de réponse utilisateur. Suite complète à relancer après dernière garde de budget verifier.
**Niveau de preuve : 5** sur kernel/journal injectés et frontière ; sélection pure niveau 4.

### 12:09 — preuve finale de la chaîne de faits et de la sélection

Suite complète finale dans **pithos / Python 3.12.9** : **1 367 passed, 3 skipped, 7 warnings en 37,10 s**.
Les contrôles d'en-têtes STATE et `git diff --check` passent. Aucune dépendance installée, aucun Git d'écriture, aucun bytecode suivi modifié. Les propositions sont dans les git.md ; les contrats transverses ont leur lot dans tests/git.md.
**Niveau de preuve : 5**, avec subprocess et fichiers de test effectivement exercés. Le marcheur complet et le premier vert avec modèle local restent à démontrer. La source candidate attend l'arbitrage utilisateur.

### 12:09 — arbitrage reçu et essai audio autorisé

L'utilisateur confirme explicitement le code candidat sous critères et entrées exclusivement contrôlés par le harness. Il demande de reprendre seulement l'idée globale de `pithos/experiments/visualizer-dry-run/PROJECT.md`, lu intégralement, et de l'adapter aux essais. La contrainte n°1 est amendée dans AGENTS/CLAUDE/PROJECT ; les anciens constats restent historiques.

Hypothèse d'essai : petit noyau audio Python pur, sans matériel, interface ni dépendance nouvelle. Premier exercice sur une fonction scalaire compatible avec les domaines fermés actuels ; les bandes FFT et le lissage restent des incréments ultérieurs. Publication du schéma de candidat bridge avant l'orchestration engine. Aucun Git d'écriture autorisé ou réalisé.
**Niveau de preuve : 2** — cadrage lu et décision explicite, implémentation à venir.

### 12:09 — première nano-étape sur doubles

Test avant code : **une erreur de collecte**, engine.attempt absent. Premier passage : **11 passed en
0,27 s** ; corpus complété : **112 passed en 0,47 s** (module, contrat NanoEngine et frontière).
Les deux warnings de tests venaient de model_copy injectant des chaînes à la place d'enums ; fixtures
corrigées avec les enums publiées. Aucun changement de production destiné à masquer un avertissement.

Couverts : reçu vert, reçu absent/étranger, rejet, crash gate, échec CAS final après reçu, schéma candidat
rejeté, aucun critère, relation inexécutable, budget consommé par le modèle, intention non durable,
concurrence sur tree.json et running non réexécuté. Les fichiers du double sont restaurés à l'octet près.
**Mesure : 652 code / 1050**, 904 physiques. **Niveau de preuve : 5** ; les observations Git et
verdicts restent scénarisés, aucun premier vert avec modèle local revendiqué. Banc réel à préparer.

### 13:09 — validation finale du banc audio

Suite complète dans **pithos / Python 3.12.9** : **1 402 passed, 3 skipped, 7 warnings en 40,64 s**.
La suite intermédiaire après run_attempt avait rendu **1 397 passed, 3 skipped, 7 warnings en 37,46 s**.
Les cinq tests ajoutés relisent effets disque, reçus et artefacts du banc ; aucun nouveau skip.
Skips : variantes réelles non scénarisables bridge/campaign/refinery. Warnings Starlette/httpx et
fork après threads conservés. Les onze mesures STATE passent : **4 570 code, 7 106 physiques**.
Aucune dépendance installée ni commande Git d'écriture. Aucun module déclaré fini.
**Niveau de preuve : 5** sur contrats et composition ; la sonde de critère Ollama, mesurée séparément,
atteint le niveau 6 pour ce seul appel. Le premier trial réel attend le HEAD du dépôt dédié.

### 13:09 — rapports conservés et omissions budgétées

Chaque retour de verifier.run est enregistré sous status/verification_report avec RecordKey,
avant décision, sans recopier facts et sans fabriquer de reçu. Si ce journal refuse l'écriture,
la transaction restaure les octets ; l'état running reste à réconcilier.
Le contexte rendu annonce comptes et raisons d'exclusion. La notice et son séparateur consomment
le budget estimé ; un irréductible de 99 unités plus cette notice dépasse correctement 100.
La fixture FIFO passe de 70 unités/1 éviction à 48 unités/2 évictions : la notice coûte 8 unités.
Les anciens contenus exclus restent conservés dans l'inventaire, jamais dans le rendu modèle.

Avant implémentation : **5 échecs, 35 succès** ; après : **116 passed en 0,50 s** sur module,
contrat et frontière. Les quatre anciennes attentes de rendu/budget ont été adaptées explicitement.
**Niveau 5 sur doubles**. 673 lignes de code sur 1050. La suite globale reste à consigner à la clôture.
La provenance de capacité est transmise au Deadline de bridge. Le branchement de ContextPacket au
marcheur complet et la garde de non-progrès fondée sur les faits restent dans le backlog de walk ;
aucune boucle ou limite de tours écartée n'est réintroduite.
