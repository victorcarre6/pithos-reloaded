# git — commits proposés pour `lifecycle`

**Aucun agent ne commite.** Ce fichier **propose** ; un humain **exécute**. Voir
[`AGENTS.md`](../../AGENTS.md) § 7.

Append-only : on ajoute une proposition, on ne réécrit pas les précédentes. Une proposition exécutée est
**marquée**, jamais supprimée.

**Rappels de format** — un commit une intention · chemins explicites, jamais `gaa` · message
`lifecycle: <ce que ça fait>` en minuscules, sans point final · uniquement du travail dont les tests passent ·
uniquement `src/lifecycle/` et `tests/doubles/lifecycle.py`.

---

_Aucune proposition. Le module n'a pas encore de code._

<!-- Gabarit d'une proposition — copie ce bloc, ne le supprime pas.

## Proposé le JJ:MM — <titre court>

**Intention** : une phrase — ce que ce commit fait, et rien d'autre.

```sh
ga src/lifecycle/<fichier_a>.py \
   src/lifecycle/<fichier_b>.py \
   tests/doubles/lifecycle.py
gcmsg "lifecycle: <ce que ça fait>"
```

**Contient** : …
**Ne contient pas** : …
**Tests verts** : …
**Exécuté** : —

-->

## Proposé le 07:09 — arbitrage du verrou de mission

**Intention** : protéger l'admission d'une mission contre les acquisitions concurrentes.

```sh
ga src/lifecycle/lock.py \
   src/lifecycle/conftest.py \
   src/lifecycle/test_lock.py \
   src/lifecycle/STATE.md \
   src/lifecycle/git.md
gcmsg "lifecycle: arbitre le verrou par génération persistée"
```

**Contient** : RunLock, LockState, LockPort, identité ps, retrait conservé et journalisé, tests de concurrence.
**Ne contient pas** : ticks, custody, readiness et garde disque.
**Tests verts** : `src/lifecycle/test_lock.py` — 16 tests, Python 3.12.9 / pithos, hors sandbox pour ps.
**Exécuté** : —

## Proposé le 07:09 — admission persistée des réveils

**Intention** : consommer chaque tick avant de livrer une mission.

```sh
ga src/lifecycle/launchd.py \
   src/lifecycle/test_launchd.py \
   src/lifecycle/STATE.md \
   src/lifecycle/git.md
gcmsg "lifecycle: coalesce les ticks sous le verrou de mission"
```

**Contient** : claim_tick, anti-rejeu des ticks consommés, fermeture sur panne de journal.
**Ne contient pas** : installation de LaunchAgent, qui reste à préciser.
**Tests verts** : `src/lifecycle/test_launchd.py` — 4 tests, Python 3.12.9 / pithos.
**Exécuté** : —

## Proposé le 07:09 — attente bornée de disponibilité

**Intention** : constater la readiness avant l'expiration du délai.

```sh
ga src/lifecycle/custody.py \
   src/lifecycle/test_readiness.py \
   src/lifecycle/STATE.md \
   src/lifecycle/git.md
gcmsg "lifecycle: borne la probe de readiness dans un processus jetable"
```

**Contient** : Readiness, wait_ready, arrêt et récolte d'une probe bloquée.
**Ne contient pas** : custody des processus de mission.
**Tests verts** : `src/lifecycle/test_readiness.py` — 7 tests, Python 3.12.9 / pithos.
**Exécuté** : —

## Proposé le 14:09 — worker sous custody exclusive

**Intention** : borner une mission dans un worker dont le groupe est arrêté avant libération du verrou.

```sh
ga src/lifecycle/execution.py \
   src/lifecycle/custody.py \
   src/lifecycle/lock.py \
   src/lifecycle/test_execution.py \
   src/lifecycle/test_lock.py \
   tests/doubles/lifecycle.py \
   src/lifecycle/MODULE.md \
   src/lifecycle/STATE.md \
   src/lifecycle/git.md
gcmsg "lifecycle: supervise un worker sous custody exclusive"
```

**Contient** : worker spawn, admission durable, récolte, reprise fermée et correction du vol de verrou vivant.
**Tests verts** : 50 tests lifecycle/frontière ; suite racine 1 545 passed, 3 skipped, 7 warnings.
Le contrat/frontière partagé possède son lot dans tests/git.md.
**Exécuté** : —

### Complément le 14:09 — preuve finale de composition

Les mêmes chemins proposés incluent les dernières gardes et les STATE à jour. Suite finale :
**1 548 passed, 3 skipped, 7 warnings en 87,81 s** ; contrôle des onze STATE et diff-check verts.
Les lots broker, lifecycle, experiment et leur support partagé tests forment l'état vérifié ensemble.
Aucun commit ni push exécuté par l'agent.

### Suspension le 14:09 — contre-preuve des groupes verifier

Les propositions de composition ci-dessus attendent la correction décrite dans STATE : un invariant
lancé dans sa propre session survit au watchdog du worker (sonde : 1 failed en 2,22 s). La suite
racine verte ne couvrait pas ce cas. Le lot broker indépendant reste vérifié ; aucun commit exécuté.

### Suspension levée le 14:09 — custody des gates vérifiée

L'extension à verifier est autorisée et livrée. Le test coupe un invariant réel et son descendant ;
le sweep après mort du superviseur et la reprise de la CLI réelle passent. Suite complète **1 556 passed, 3 skipped, 7 warnings en 100,50 s**,
Python 3.12.9/pithos ; STATE et diff-check verts. Les mêmes chemins proposés incluent la correction
et leurs preuves actualisées. Le lot verifier ajouté ce jour est un prérequis à la composition ;
les lots lifecycle, experiment et tests partagés se relisent ensemble. Aucun commit exécuté.

## Proposé le 15:09 — réconcilier un leader zombie

**Intention** : clore sans signal la custody d'un groupe déjà sorti dont le leader est encore zombie.

```sh
ga src/lifecycle/custody.py \
   src/lifecycle/test_custody.py \
   src/lifecycle/MODULE.md \
   src/lifecycle/STATE.md \
   src/lifecycle/git.md
gcmsg "lifecycle: réconcilie les groupes dont le leader est zombie"
```

**Contient** : constat de sortie du groupe malgré l'empreinte macOS devenue illisible ; refus
préservé d'une identité inconnue avec des membres vivants. Régression native rouge avant/verte
après, issue de l'échec de reprise dans la suite complète. Production réduite à 494 lignes.
Ces fichiers portent aussi la composition précédente : appliquer ou regrouper ses propositions.
**Tests verts** : suite complète **1 602 passed, 3 skipped, 7 warnings en 114,64 s**, Python 3.12.9 / pithos ; STATE et diff-check verts.
**Exécuté** : —
