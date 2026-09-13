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
