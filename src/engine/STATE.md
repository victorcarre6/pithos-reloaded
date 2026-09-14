# STATE — `engine`

**Statut** : bloqué
**Mise à jour** : 14:09
**Lignes** : 1125 code / 1050 cible · 1500 physiques
**Empreinte** : f9dfb89e5b2afd7700c240e6d936c9bf6b3a89069617fbeacd75862ddd3d7a9e
**Plafond justifié** : 1125 code
**Justification** : L'enveloppe ajoute 46 lignes à la base de 1079 : entrée Prefect à appel unique, contrat, garde locale des connexions et du contexte, désactivation des traces secondaires et interruption de secours. Pas de second marcheur, de configuration métier ou de dépendance ajoutée. Dépassement global de 75 lignes ; la justification antérieure de la passation reste au journal.

## Prochaine action

Faire publier l'adaptateur GreenFinalizer côté broker/composition : reconcile(key, receipt, timeout), finalize(key, receipt, timeout), interrogation avant rejeu et observation complète du dépôt. La composition doit détenir le verrou lifecycle et fournir le serveur Prefect local sans analytics, avec watchdog de processus ; voir Blocages. Après ces ports, vérifier une reprise/finalisation via flow.mission sous verrou réel. Faire déplacer les contrats locaux et la garde de flow par la passe transverse. L'enveloppe est livrée et sa proposition Git est prête ; aucun travail indépendant restant n'autorise à élargir le périmètre engine.

## Avancement

- [x] Un nœud sans critère exécutable n'atteint jamais le modèle ; états légaux testés, running/passed sans critère refusés par kernel.
- [x] Profondeur 3 et cap_children appliqués, y compris après relecture de l'arbre.
- [x] Réserve souple : finalisation des verts sur port injecté ; arbre et frères non commencés reprenables.
- [x] Walk complet sans import Prefect, subprocess ou Ollama dans son corpus.
- [x] Inventaire typé, une raison par élément ; contexte minimal courant raccordé à run_attempt.
- [x] Éviction FIFO et inventaire conservé dans les tests du contexte.
- [x] Irréductible trop volumineux : blocked/context_overflow avant le modèle.
- [x] Projection CONTEXT.md puis exclusion d'une section périmée jusque dans le prompt réel du port bridge.
- [x] Baseline durable à chaque sortie dont le journal accepte encore les écritures.
- [x] Disposition par enfant, liée au reçu pour les résultats exécutés ; historique conservé.
- [x] Frontière et contrat NanoEngine partagés verts ; contrat Walker testé localement, placement transverse restant à effectuer.
- [x] Enveloppe Prefect locale : appel unique, budget conservé, aucun paramètre/résultat métier persisté, timeout de secours exercé en réel.

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
| Finalisation réelle de walk | `broker.commit` ne reçoit ni identité logique de vérification, ni deadline ; `broker.intent.resume` fournit les primitives mais aucun adaptateur ne compose interrogation, commit borné et observation. Engine ne peut importer broker ni modifier son code. | Publier côté composition/broker un objet conforme à GreenFinalizer : reconcile(key, receipt, timeout) interroge l'effet par identité et rend RepoFact ou None ; finalize(key, receipt, timeout) publie les seuls chemins attestés, persiste l'effet puis rend un RepoFact complet propre. Fournir le verrou de mission lifecycle autour de walk. | — ; niveau 5 sur MemoryFinalizer uniquement. |
| Placement du nouveau contrat Walker | Le contrat NanoEngine partagé demeure intact ; le nouveau corpus Walker/GreenFinalizer est dans src/engine/test_walk.py, seul périmètre autorisé. | Passe transverse : déplacer ce corpus dans tests/contracts/test_engine_double.py et marquer walk livré dans docs/ARCHITECTURE.md avec la signature de MODULE.md. | — |
| Placement du contrat ContextArchive | Le port et le double sont testés dans src/engine/test_dump.py, avec mutation des deux signatures ; tests/contracts reste hors périmètre engine. | Passe transverse : déplacer ce contrôle dans tests/contracts/test_engine_double.py, sans changer le métier. | — |
| Composition du runtime Prefect | flow.py nécessite un serveur local déjà lancé, sans analytics serveur, un thread principal avec SIGALRM libre et le verrou exclusif de mission. Le timeout Prefect n'est pas un SIGKILL et ne borne pas son propre démarrage/arrêt. | Composition/lifecycle : fournir cette entrée locale avec arrêt du propriétaire précédent et watchdog de processus ; le flow ne crée pas d'infrastructure implicite. | — ; serveur temporaire et alarme réellement testés, aucune mission Git/Ollama. |
| Placement du contrat MissionRunner | Le nouveau contrat et sa dérive de signature sont testés dans src/engine/test_flow.py ; tests/contracts reste hors périmètre. La frontière locale de flow complète l'exemption Prefect du scanner partagé. | Passe transverse : déplacer le contrat vers tests/contracts/test_engine_double.py avec Walker et ContextArchive ; reprendre la garde locale de flow dans tests/boundaries/test_engine.py. | — |

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

### 13:09 — instrumentation vérifiée dans le dépôt commun

Suite complète **1 444 passed, 3 skipped, 7 warnings en 43,83 s**, Python 3.12.9/pithos,
après intégration de l'entrée TUI parallèle ; aucun nouveau skip. Les onze STATE passent.
Le selftest-wo3aa7e5 conserve un événement verification_report avec son verdict de mutation,
relu par HTTP dans l'observatoire. Ce cas garde bridge et Git scénarisés : **niveau 5** pour
la composition, **niveau 6 limité à la lecture locale**. Le trial historique reste inchangé.
Les 673 lignes de production tiennent la cible 1050. La prochaine unité est walk avec réconciliation,
pas un nouvel essai destiné à transformer le refus historique en vert.

### 14:09 — walk vérifié sur doubles : reprise, finalisation et baseline

Le dashboard est déclaré terminé pour le moment par l'utilisateur ; aucun fichier observatory n'a été
modifié. État Git initial propre, branche baseline-harness synchronisée avec origin. Python **3.12.9**
du venv pithos confirmé avant tests. Aucun Git d'écriture, aucune dépendance ajoutée.

Tests écrits avant code : **1 erreur de collecte** pour recovery absent, puis **1 erreur de collecte**
pour WalkDeps absent. Première composition : **4 failed / 128 passed** ; les SourceFact stricts encodés
en hex exigeaient une relecture JSON, corrigée dans le CAS partagé et la relecture de clôture.
Deux régressions de restauration ont été observées séparément (**1 failed / 8 passed**, puis
**1 failed / 9 passed**) : reçu invalide et dépôt contradictoire empêchaient de restaurer le candidat
connu. Le chemin commun restaure maintenant ce candidat avant de publier le blocage. Les octets étrangers
restent conservés. Préflight du contexte : **2 failed / 16 passed** avant raccordement de l'inventaire.

Le marcheur réclame une identité nouvelle par admission, réconcilie les running sans nouvel appel modèle,
finalise chaque vert avant le frère suivant, conserve dispositions et baseline. Scénarios observés :
deux verts successifs, réserve souple, deadline dure sans nouvel effet, timeout sans boucle dans la même
invocation, reprise budget_limited, modèle interrompu, reçu verifier sans acquittement engine, perte
d'acquittement de publication, dépôt sale/étranger, source modifiée pendant finalisation, CAS concurrent,
restauration survivant à une panne du tree.json, baseline relisant la tentative durable après exception.
Le reçu participe au hash de disposition ; les anciennes dispositions ne sont pas supprimées.

Contrôles ciblés finaux : **152 passed en 0,75 s** sur src/engine, contrat NanoEngine et frontière.
Un import Prefect forcé indisponible couvre aussi le walk complet. Dérive de signature détectée pour Walker
et les deux méthodes GreenFinalizer. **961 code / 1050 cible**, **1278 physiques**.

Première suite complète : **1477 passed, 3 skipped, 7 warnings en 44,34 s**, avant les trois dernières
régressions de finalisation/contrat/reprise. Le contrôle des onze STATE passait à 959 lignes engine.
La suite finale après ces corrections est en cours ; son résultat sera ajouté avant proposition Git.

**Niveau de preuve : 5** — workspace, bridge, verifier, journal et publication sur doubles officiels.
Le port réel de finalisation reste un blocage explicite de composition/broker ; aucun commit Git ni
premier vert avec Ollama n'est revendiqué. Le refus réel historique sur tautology reste inchangé.

### 14:09 — clôture vérifiée de l'unité walk

Suite complète finale dans **pithos / Python 3.12.9** : **1480 passed, 3 skipped, 7 warnings en 43,90 s**.
Skips conservés : tests/contracts/test_bridge_double.py:77 (frontière réelle sans file scénarisable),
test_campaign_double.py:170 et test_refinery_double.py:82 (politiques réelles sans scénario à charger).
Warnings conservés : Starlette/httpx, six avertissements macOS de fork après threads. Aucun nouveau skip.
Le contrôle **des onze STATE** et `git diff --check` passent. Le diff est limité à engine et son double.
Production finale **961 code / 1050**, **1278 physiques**, sans relèvement de cible.

La proposition du 14:09 dans git.md couvre les onze fichiers de cette unité et reste non exécutée.
**Niveau de preuve : 5 pour walk**, aucune publication Git réelle exercée. La prochaine unité engine
indépendante est la passation CONTEXT.md ; le port broker manquant reste décrit sans modification voisine.

### 14:09 — passation append-only raccordée aux tentatives

Reprise dans Python **3.12.9/pithos** ; les onze fichiers walk non commités sont conservés. Aucun Git
d'écriture et aucun changement du dashboard. Les sources Villani context_projection.py,
context_governance.py et summarizer.py ne sont plus présentes sous resources ; lectures négatives
conservées. dump.py est une implémentation originale sur ContextPacket existant, sans nouvelle copie
de source tierce ni réintroduction de compaction.

Tests avant code : **1 erreur de collecte**, engine.dump absent ; puis **4 passed / 4 errors**, fixture
appelant kernel_double.record_key inexistant. Correction par construction du RecordKey canonique,
sans changement de kernel. Première série **8 passed / 1 warning** ; enum de fixture corrigée.
Branchement avant implémentation de Deps.archive : **9 passed / 22 errors** (argument archive absent).
Après raccordement : **165 passed en 0,89 s** ; corpus complété : **172 passed en 0,88 s** sur src/engine,
contrat NanoEngine et frontière, sans warning.

Chaque tentative ayant assemblé son contexte ajoute sa section après sortie de transaction, donc après
restauration éventuelle. Les tests observent les empreintes AFTER sur vert et BEFORE sur les quatre
sorties non vertes ; crash de gate sans verdict synthétique, conflit CAS sans écriture de passation,
panne d'archive après vert sans retour arrière d'un effet déjà acquitté. Un verdict d'un autre critère
reste dans verification_report et bloque ; il n'est pas attaché à la passation du critère courant.

Sur fichier temporaire réel : ajout préservant tous les octets antérieurs, archive complète relisible,
refus des formats inconnus et queues déchirées, fsync en échec visible, identité étrangère refusée avant
append. Les clôtures Markdown dans un ancien contenu ne créent pas de section supplémentaire.
Sur bridge officiel scénarisé : passation fraîche admise, ancienne source absente du prompt, passation
périmée exclue avec stale, passation trop grande évincée avec budget_pressure. L'inventaire conserve
les contenus écartés. Le double mémoire satisfait ContextArchive ; une signature divergente est détectée.

**Mesure : 1079 code / 1050 cible, 1435 physiques**, dépassement justifié ci-dessus. **Niveau de preuve : 5**
pour la composition sur doubles ; effet disque de l'archive réellement constaté. Aucun essai Ollama ni
finalisation Git réelle. Suite complète et contrôle des onze STATE à consigner avant livraison.

### 14:09 — clôture vérifiée de la passation

Suite complète hors sandbox, sockets locales et processus macOS autorisés : **1500 passed, 3 skipped,
7 warnings en 44,03 s**, dans **pithos / Python 3.12.9**. Les trois skips restent ceux des contrats
bridge:77, campaign:170 et refinery:82 : implémentations réelles sans scénario à charger. Warnings
inchangés : Starlette/httpx et six avertissements fork après threads. Aucun nouveau skip.
Contrôle des **onze STATE** et `git diff --check` verts. Production **1079 code, 1435 physiques**,
plafond justifié 1079 ; aucune marge de croissance ajoutée. **Niveau 5 sur doubles** pour la chaîne.

La dernière proposition git.md couvre l'état courant complet des treize fichiers : walk n'a pas été
commité et ses fichiers partagés importent désormais dump.py. Elle remplace opérationnellement la
proposition walk seule, conservée dans l'historique, afin d'éviter un commit sans le nouveau module.
Aucune commande Git d'écriture exécutée. La prochaine unité est l'enveloppe flow.py ; la finalisation
réelle et le placement des contrats restent les blocages externes documentés.

### 14:09 — enveloppe flow.py vérifiée sur SDK local

Worktree initial propre ; commits walk eb028ee et passation daee504 observés en lecture seule. Python
**3.12.9/pithos**, Prefect **3.8.5** déjà installé. Aucune installation ni commande Git d'écriture.
La borne SDK et ses effets ont été relus dans le code installé et la documentation officielle ;
une recherche de telemetry/bootstrap.py a constaté son absence, résolue par lecture de run_telemetry.py.

Tests avant implémentation : **1 failed / 10 errors**, import engine.flow absent. Après implémentation :
**11 passed en 1,95 s** ; ajout de la finalisation en réserve : **12 passed, 1 deselected en 1,15 s**.
Le contrat MissionRunner est publié avec son double ; une signature divergente est détectée.
Un appel conserve le même Budget et sa deadline ; aucun arbre ou port n'entre dans les paramètres du flow.
Échec et timeout transport sont propagés sans deuxième walk. Refus observés avant création du flow :
API absente/distante/DNS trompeur, proxy, contexte hérité, thread secondaire et SIGALRM déjà occupé.

Runtime autorisé hors sandbox : **1 passed, 12 deselected en 12,93 s** sur un serveur Prefect temporaire,
analytics coupées avant lancement. Le profil active volontairement retries, persistance et log_prints :
l'enveloppe les désactive. Relecture API : paramètres vides, état Completed et state.data absent.
Une exception ne rejoue pas walk ; une alarme de 0,05 s interrompt un sleep de 1 s, exécute son finally
et restaure SIGALRM. La marge de production reste 60 s, non calibrée. Aucun SIGKILL revendiqué.

Mesure **1125 code / 1050 cible, 1500 physiques** : 46 lignes de code nouvelles, plafond justifié exact.
La base précédente dépassait déjà la cible de 29 lignes pour la passation typée append-only, ses
empreintes après restauration et la garde de conflit ; cette justification reste conservée ici.
**Niveau de preuve : 5** pour la composition métier sur doubles ; **6 limité au runtime Prefect local**
et à son interruption. Les contrôles ciblés complets et la suite racine restent à consigner avant Git.

### 14:09 — incompatibilité de coexistence avec fork constatée

Corpus engine/contrat/frontière : **185 passed en 11,31 s** avant le dernier test de frontière de flow.
Ce contrôle local refuse broker/campaign/lifecycle et l'I/O réseau directe ; chaque import interdit
injecté rend le contrôle rouge. Après ajout : **13 passed, 1 deselected en 1,19 s** sur test_flow hors
runtime réel. Les onze STATE et diff-check passent.

Première suite complète : **1 failed, 1513 passed, 3 skipped, 7 warnings en 54,54 s**. Échec exact :
`src/lifecycle/test_lock.py::test_two_real_forks_have_one_winner`, un enfant observe correctement le
verrou mais termine avec exitcode 1 après le test Prefect. Le runtime SDK a tourné dans le pytest
parent ; hypothèse à vérifier : ses threads/services de fond perturbent le fork ultérieur.
Correction dans le seul corpus engine : lancer le test réel Prefect dans un interpréteur enfant dédié,
borné à 45 s, avant de relancer la coexistence. Aucun changement de lifecycle ni skip de contournement.
**Niveau 5** pour le contrat ; la coexistence globale n'est pas encore verte, proposition Git suspendue.

### 14:09 — isolation du smoke test Prefect

La commande ciblée `src/engine/test_flow.py src/lifecycle/test_lock.py` rend **30 passed en 11,46 s**
hors sandbox. Le test Prefect réel est exécuté intégralement dans un interpréteur enfant et son exitcode
reste une assertion du corpus ; aucun test n'est désactivé. Le processus dédié se termine avant les
forks lifecycle, désormais verts. Aucune production ni aucun test lifecycle n'a été modifié pour corriger
l'échec de coexistence. La suite complète finale est relancée sur cet état.
**Niveau 6 limité** à ces runtimes locaux ; métier toujours sur doubles.

### 14:09 — clôture vérifiée de l'enveloppe

Suite complète finale, Python **3.12.9/pithos**, hors sandbox : **1514 passed, 3 skipped, 7 warnings
en 55,93 s**. Skips inchangés : contrats bridge:77 (frontière réelle sans file à charger), campaign:170
et refinery:82 (politiques réelles sans scénario). Warnings inchangés : Starlette/httpx et six avertissements
macOS de fork après threads. L'échec de coexistence précédent reste conservé ; aucun skip ajouté.
Les **onze STATE** et `git diff --check` sont verts. Production **1125 code, 1500 physiques**,
plafond justifié 1125. Pas d'installation, d'édition voisine, de modification dashboard ni de Git d'écriture.

Le lot de git.md porte uniquement flow.py, son test, le double engine et les trois documents de module.
Les anciens lots walk et CONTEXT.md sont observés commités ; aucune répétition de leurs propositions.
**Niveau 5** pour la composition métier ; **6 limité** au runtime Prefect local et à son alarme.
Statut **bloqué** pour l'intégration restante, pas fini : finaliseur broker, composition lifecycle et
placement transverse des nouveaux contrats manquent encore. Aucun choix métier utilisateur nouveau
n'est nécessaire pour l'enveloppe livrée ; le prochain agent doit prendre le chantier broker explicité.
