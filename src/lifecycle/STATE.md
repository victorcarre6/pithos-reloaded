# STATE — `lifecycle`

**Statut** : en cours
**Mise à jour** : 11:09
**Lignes** : 325 code / 250 cible · 464 physiques
**Empreinte** : 565e90a037031ab6737904b05c6e6d6ad453f8e1ac323470f7811d00b45cdbf2

## Prochaine action

Écrire le test de `ensure_space(path, needed)` sur les seuils de disque du MODULE.md, puis implémenter la garde absente. `process.py` et `custody.py` existent déjà ; l’identité microseconde, le petit-enfant et le sweep ont leurs tests. Restent aussi `install_agent`, le contrat HostFact et la publication du Protocol/double lifecycle.

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
