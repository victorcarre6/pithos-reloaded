# STATE — `lifecycle`

**Statut** : en cours
**Mise à jour** : 14:09
**Lignes** : 494 code / 250 cible · 679 physiques
**Empreinte** : 1c46c671d260884e24af27a2e20596617d081c3fcd22e695f8948e2c9e467a3e

## Prochaine action

Implémenter disk.ensure_space(path, needed) selon MODULE.md : commencer par les tests d’espace insuffisant et d’erreur disk_usage, puis refuser l’admission sans supprimer les données brutes. La réconciliation des leaders zombies est corrigée et vérifiée.

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
| Custody des invariants détachés | verifier/runner.py crée une nouvelle session ; le groupe survit au watchdog du worker (sonde rouge du 14:09). | Accord pour étendre le périmètre à verifier, port de lancement sous custody, vraie gate coupée puis tous ses groupes confirmés arrêtés. | 14:09 — extension autorisée, gate réelle arrêtée puis reprise sans reçu ; sweep du propriétaire mort vérifié. Suite complète verte : 1 556 passed, 3 skipped. |
| `HostFact` absent du socle | `kernel/facts.py` ne publie que `FileFact` ; le producteur lifecycle ne peut pas définir le contrat à la place de kernel. | Faire publier le contrat HostFact par kernel avant de produire une attestation consommable par verifier. | — |
| Cause disque absente | `kernel.errors.Cause` ne contient pas de cause disque plein ou mesure disque impossible ; détourner `unverifiable` masquerait le diagnostic. | Ajouter les causes fermées et leur contrat blocked dans kernel ; ensuite implémenter `ensure_space`. | — |
| Tests partagés hors périmètre | Les répertoires `tests/contracts/` et `tests/boundaries/` sont absents et interdits en écriture au module. | Un agent autorisé y installe les tests locaux de contrat et de frontière. | **Résolu le 10:09** — déplacés par la passe transverse ; suite complète verte. |

## Décisions locales

_Choix d'implémentation pris ici, qu'un successeur doit connaître et ne doit pas défaire sans raison._

## Reprises traitées

| Source | Verdict | Fait ? | Note |
|---|---|---|---|

## État courant — 07:09, unité verrou

**Statut** : en cours. **Production** : 171 lignes physiques (`lock.py`) / cible globale ~250 L.
La cible initiale de 60 L pour le verrou est dépassée : validation des données persistées,
identité OS, journalisation et protection de la course entre retrait et reprise sont incluses.
Pas de heartbeat, de breaker ni de thread écrivain.

- [x] Deux acquisitions concurrentes : une seule réussit, vérifié par deux `fork` réels.
- [x] Un PID réutilisé ne permet pas à l'ancien objet verrou de retirer la nouvelle génération.
- [x] État illisible : `unavailable` ; admission de l'appelant à vérifier avec les ticks.
- [x] Péremption réclamée et journalisée sur double du journal.
- [ ] Custody, ticks, disque, readiness, fermeture après bind, frontières et double.

### Journal ajouté — 07:09 — verrou local

Le test a précédé l'implémentation : erreur de collecte `lifecycle.lock` absent.
Premier lancement avec le code : **11 verts, 5 rouges**, car `/bin/ps` est interdit dans la sandbox
(`operation not permitted`, confirmé directement). Relance autorisée hors sandbox :
**16 tests verts**, Python **3.12.9**, venv **pithos**, en **0,27 s**.
Commande : `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider src/lifecycle/test_lock.py`.
**Niveau de preuve atteint : 5** pour le contrat journal sur double ; effets filesystem et fork réels,
sans prétendre à une mission complète ni à launchd réel.

### Décisions locales ajoutées — 07:09

- `held` et `stale_reclaimed` accordent le verrou ; `unavailable` ferme l'admission, y compris si détenu
  par autrui. Ne pas tester la truthiness du StrEnum.
- Une génération retirée est renommée vers `<lock>.retired-<token>` et conservée avec son owner.json.
  La destination non vide interdit qu'un prétendant retardé y déplace une génération suivante.
  Le même nom sert à release et à reclaim ; ne jamais supprimer ces archives.
- `mkdir` avant owner.json : un crash dans cet intervalle laisse un verrou illisible et bloquant,
  à diagnostiquer par l'opérateur ; aucun délai seul ne rend un owner absent fiable.
- Identité macOS issue de `/bin/ps -o lstart=` avec locale C et TZ UTC, sans shell. Sa précision est
  la seconde : la collision d'un PID recyclé dans la même seconde n'est pas éliminée par cette source.
  Le token protège le retrait des générations. Une identité plus fine serait nécessaire pour une
  preuve OS stricte de custody. Toute identité absente ferme l'admission.
- Sources relues : Prime `packages/coding-agent/src/core/session-lease.ts:160-324`, Langfuse
  `worker/src/utils/RedisLock.ts`. L'adaptation conserve les archives au lieu de reprendre leur suppression.

### Journal ajouté — 07:09 — admission des ticks et readiness

Tests écrits avant les modules : **2 erreurs de collecte**, modules absents. Après implémentation :
**11 tests verts en 0,54 s**, Python 3.12.9 / pithos. Deux ticks proches conservent le premier verrou,
les ticks réclamés ou coalescés ne sont pas rejoués, une panne du journal ne rend jamais True.
Une probe qui dort 10 s est arrêtée par le parent sous deadline (assertion mesurée < 1 s), puis récoltée.
**Niveau de preuve : 5** pour l'admission sur double ; readiness sur processus local jetable,
sans serveur réel ni launchd activé.

Correction de comptage de l'entrée précédente : `wc -l` mesure **165 lignes** pour lock.py,
et non 171. Cette première valeur était erronée, pas une mesure.

### Décisions locales ajoutées — 07:09 — ticks et probes

- `claim_tick` reçoit un verrou et un chemin de journal communs aux réveils ; au succès, le caller
  garde le verrou jusqu'à la fin de la mission et appelle `release`. Une réclamation n'atteste pas
  l'exécution ; un tick réclamé sans résultat reste à réconcilier, jamais redélivré automatiquement.
- Le journal est relu une fois par démarrage launchd ; ne pas appeler cette fonction en poller permanent.
- Deadline de readiness : float monotone absolu local, en attendant un contrat commun `Deadline`.
  La probe s'exécute dans un enfant fork jetable ; aucun effet mémoire de la probe n'est propagé au parent.
  Elle ne doit ni créer d'enfants ni détenir de ressources du processus appelant. Le parent impose
  la deadline même si la probe bloque ; budget supplémentaire de récolte borné à 0,5 s.
- Sources relues : Prime cron-jobs.ts:1591-1640 et Unsloth cloudflare_tunnel.py:507-555.


### 11:09 — mesure de production et en-tête courant

Passe transverse demandée via TEMPO.md. Aucun code métier ni case de livraison modifié.
Mesure AST/tokenize : **325 lignes de code**, **464 physiques**, cible globale **250**. Sous-paquets et __init__.py inclus ; tests et doubles exclus.
L’empreinte de l’en-tête couvre les chemins et octets de toute la production.
La nouvelle métrique ne valide aucun item métier et ne relève aucune cible numérique.

**En-tête antérieur conservé** :

```text
**Statut** : en cours — code livré et vert, statut corrigé par la passe transverse du 10:09 (il portait `non commencé`)
**Mise à jour** : —
**Lignes** : 386 / ~250 L — **mesuré par la passe transverse du 10:09** ; l'agent du module ne l'avait pas actualisé
```

**Plafond justifié** : 325 code
**Justification** : Le verrou générationnel et ses archives, l’identité macOS, la custody, les ticks et la readiness bornée totalisent 325 lignes de code. Les 75 lignes au-delà de 250 préservent les contrôles de propriétaire, l’admission fermée et la récolte ; aucun heartbeat ni breaker ajouté.

**Niveau de preuve : 2** pour la mesure documentaire ; la suite initiale complète du 11:09 a rendu 1 215 passed et 3 skipped hors sandbox. Le détail des nouvelles validations vit dans tests/STATE.md.

### 11:09 — prochaine action recoupée avec les fichiers

La prochaine action demandait encore la custody ; `process.py`, `custody.py` et les cinq tests
`test_custody.py` sont présents. Ils étaient déjà là avant la passe transverse. Les fonctions
`ensure_space` et `install_agent` du contrat ne sont pas encore définies ; la garde disque devient
l’entrée suivante. Aucun item métier coché et aucun statut fini attribué par cette observation.

**Prochaine action antérieure conservée** :

```text
Vérifier l'identité macOS en microsecondes via proc_pidinfo, puis implémenter la custody avec appariement strict, test d'un petit-enfant réel et journal d'orphelins sur double.
```

### 14:09 — verrou vivant et worker sous custody

Avant correction : test de péremption **1 failed en 0,17 s** ; le verrou vivant était repris
après simple TTL. Le test worker a d'abord échoué à la collecte (module absent, 0,24 s).
Après correction et composition locale : **50 passed en 3,67 s**, Python 3.12.9 / pithos hors
sandbox. Succès, exception et blocage du callback : le worker spawn et son descendant réel
sont arrêtés avant libération du verrou. Journal indisponible et custody inconnue ferment
l'admission. Aucun fork du runtime Prefect : chaque tâche démarre dans un interpréteur neuf.

**Plafond justifié** : 441 code
**Justification** : +116 lignes pour l'admission en deux temps, la garde de custody avant reprise,
le worker spawn, le maintien du leader jusqu'à récolte, le SIGINT doux et la borne OS finale.
La lecture de custody est partagée avec sweep ; aucune boucle réseau ou framework ajouté.
Le contrôle STATE a détecté les anciennes lignes/empreinte/plafond avant leur mise à jour.
**Niveau de preuve : 5**, journal sur double et processus macOS réels ; composition métier à vérifier.

### 14:09 — unité lifecycle vérifiée

Suite racine hors sandbox : **1 545 passed, 3 skipped, 7 warnings en 61,72 s**.
Les trois skips existants et les warnings Starlette/fork sont inchangés. Contrôle STATE vert.
**Niveau de preuve : 5** ; les nouveaux ports possèdent leurs doubles et tests de signature mordants.

### 14:09 — coupure et disparition du superviseur

Intégration plus lifecycle/contrat : **46 passed en 29,70 s**. Une coupure OS pendant la
vérification laisse le candidat observé et le nœud running ; le walk suivant restaure exactement
le seed sans appel modèle ni reçu. Un superviseur tué laisse son worker enregistré : la prochaine
admission reprend son verrou, sweep le groupe, confirme l'arrêt puis démarre son propre worker.
Le leader terminé est récolté avant interrogation OS pour ne pas confondre un zombie avec une
identité inconnue. Une transition de custody non durable et un PID interdit restent fermés.

**Plafond justifié** : 450 code
**Justification** : +9 lignes depuis 441 : contrôle de durabilité, permission OS fermée, récolte d'un
leader déjà terminé et conservation de l'issue completed/failed/unknown dans process_stopped.
La dernière suite ciblée précède l'ajout de cette issue aux événements ; la suite finale doit la vérifier.
**Niveau de preuve : 5 pour la chaîne complète** (modèle seul simulé), **6 limité** aux composants
locaux Git/Prefect/verifier/workspace/journal/lifecycle effectivement exécutés sur dépôts jetables.

### 14:09 — livraison intégrée vérifiée

Suite complète finale : **1 548 passed, 3 skipped, 7 warnings en 87,81 s**, Python **3.12.9 / pithos**,
hors sandbox. Les trois skips existants restent bridge:77, campaign:170, refinery:82 (scénarios
propres aux doubles) ; warnings Starlette/httpx et les six anciens forks après threads.
Contrôle des onze STATE et `git diff --check` verts. Aucun paquet installé, aucun Git d'écriture
sur le harness ou le dépôt de campagne, aucun service opérateur sollicité, dashboard intact.
Les effets Git réels sont limités aux dépôts temporaires des tests. Le test d'intégration garde
le modèle simulé : le premier vert Ollama reste à démontrer, trial-44kcg6ig demeure négatif.
**Niveau de preuve : 5 pour la mission complète**, **6 limité aux composants locaux** effectivement
exercés. La commande et la reprise sur même --run sont décrites dans experiments/visualizer/README.md.

### 14:09 — contre-preuve finale : groupe d'invariant détaché

La revue de src/verifier/runner.py:113 constate start_new_session=True. La sonde jetable
/private/tmp/test_pithos_detached.py reproduit ce lancement sous MissionProcess : **1 failed en
2,22 s**, le groupe d'invariant survit à la coupure du worker. La sonde nettoie ensuite explicitement
son groupe ; aucun processus de ce diagnostic n'est laissé en marche.

Cette contre-preuve limite la suite verte précédente : le scénario cut suspendait verifier.run
avant le spawn réel et ne couvrait pas ses groupes séparés. Le groupe du worker et ses descendants
restant dans ce groupe sont bien récoltés ; l'arrêt de tous les groupes du verifier n'est PAS prouvé.
La composition n'est donc pas prête pour un essai opérateur. GreenFinalizer reste vérifié indépendamment.

Correction requise : admission durable et récolte des groupes séparés d'invariants, sans modifier
les critères, les entrées, les gates ou l'autorité du reçu. Le port de lancement correspondant manque
à verifier. L'extension du périmètre à src/verifier a été demandée à l'utilisateur conformément à
AGENTS.md § 6 ; aucune production verifier n'a été modifiée avant sa réponse.
**Niveau de preuve : 4 pour ce défaut reproduit** ; la preuve positive d'arrêt global est retirée.


### 14:09 — admission opérateur suspendue

La CLI mission ferme désormais l'admission avant création de preuves/worker tant que les groupes
verifier ne sont pas possédés. Les scénarios contrôlés d'intégration restent accessibles par injection
du worker de test ; ils ne sont pas une autorisation d'essai réel. Plan de correction après accord :
port d'exécution des commandes de gate dans verifier, fourni par lifecycle depuis la composition ;
aucun import lifecycle dans verifier, aucune modification des critères ni des reçus. Enregistrement
avant admission et sortie confirmée de chaque groupe, y compris après disparition du worker.

### 14:09 — état sûr en attente d'extension de périmètre

Après suspension de l'entrée opérateur : suite complète **1 549 passed, 3 skipped, 7 warnings en
89,05 s**, pithos/Python 3.12.9. Le nouveau test constate le refus AVANT création de preuves ou
worker. STATE et diff-check verts. Cette suite ne résout pas la sonde négative du groupe détaché
(1 failed en 2,22 s) : la composition reste suspendue et l'accord src/verifier reste en attente.
GreenFinalizer demeure livrable indépendamment ; les propositions de composition restent suspendues.

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

**Plafond justifié** : 503 code
**Justification** : +53 lignes depuis 450 pour réutiliser l'admission et la récolte du worker avec
les gardiens de gates : relais IPC, propriétaire commun, timeout individuel borné par la mission,
refus de réponse après deadline globale et verrou conservé tant qu'une custody reste active.
Aucun second superviseur, heartbeat ou moteur de verdict ajouté.

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

### 15:09 — contre-preuve lors de la vérification finale

La seconde suite complète rend **1 failed, 1 599 passed, 3 skipped, 7 warnings en 115,87 s**.
Échec exact : tests/test_visualizer_mission.py::test_dead_supervisor_is_swept_before_admitting_another_worker,
RuntimeError unresolved mission custody à la reprise. Le même test passait dans la première suite
et le corpus ciblé ; l'intermittence doit être expliquée avant clôture. Preuves conservées dans
pytest-191/test_dead_supervisor_is_swept_0 sous le tmpdir système. L'avertissement Pydantic
ajouté par le test est bien résolu. Le trial réel vert et ses reçus restent valides et inchangés.

### 15:09 — identité absente d'un zombie macOS

Reproduction native : une fois Z, proc_pidinfo ne rend plus son démarrage (None), mais
kill(pid, 0) réussit tant que le parent ne l'a pas récolté. La première sonde qui attendait
un démarrage encore lisible échoue (1 failed, 5 deselected, 0,22 s) ; corrigée selon
l'observation OS, elle reproduit le sweep vide (1 failed, 5 deselected, 0,17 s).

Le sweep laisse kill_group constater l'absence de membres vivants lorsque l'empreinte
est absente. Aucun signal n'est alors envoyé. Une empreinte différente, ou une empreinte
inconnue avec des membres vivants, reste refusée. Deux tests natifs couvrent le zombie et
le groupe vivant illisible. Le contrôle répété pid/kill(0) est retiré ; le code diminue.
Vérification ciblée en cours, puis suite complète à relancer.

### 15:09 — course de custody corrigée et corpus ciblé vert

Les **64 tests lifecycle, mission composée, contrat et frontière passent en 55,26 s**.
Le test natif reproduit la fenêtre zombie sans attente artificielle de récolte ; le groupe
vivant à empreinte illisible reste refusé sans signal. La suite complète est relancée.
Production lifecycle réduite à 494 lignes de code / 679 physiques, sans changement de cible.

**Plafond justifié** : 494 code
**Justification** : reprise du plafond 503 de la composition worker/gates ; le contrôle de groupe vide remplace les sondes pid redondantes et retire neuf lignes de code. Le plafond baisse avec cette correction de la course zombie.

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
