# git — commits proposés pour `broker`

**Aucun agent ne commite.** Ce fichier **propose** ; un humain **exécute**. Voir
[`AGENTS.md`](../../AGENTS.md) § 7.

Append-only : on ajoute une proposition, on ne réécrit pas les précédentes. Une proposition exécutée est
**marquée**, jamais supprimée.

**Rappels de format** — un commit une intention · chemins explicites, jamais `gaa` · message
`broker: <ce que ça fait>` en minuscules, sans point final · uniquement du travail dont les tests passent ·
uniquement `src/broker/` et `tests/doubles/broker.py`.

---

## Proposé le 07:09 — fait de dépôt, préflight, commit borné, PR

**Intention** : porter la couche Git de `broker` — `RepoFact`, préflight de dépôt sale, commit borné aux
chemins désignés, ouverture de PR et auto-merge conditionné à un rollup vert.

```sh
ga src/broker/git.py \
   src/broker/test_git.py \
   src/broker/STATE.md \
   src/broker/git.md
gcmsg "broker: fait de dépôt, préflight et commit borné aux chemins désignés"
```

**Contient** : `git.py` (246 L) — modèles `Change`, `RepoFact`, `PullRequest` ; `parse_status` avec les deux
côtés d'un rename ; `checked_repo_path` / `checked_ref` / `checked_text` ; `repo_fact`, `preflight`,
`commit`, `open_pr`, `automerge`. Et ses 39 tests.
**Ne contient pas** : `identity.py`, `intent.py`, `telegram.py`, ni `tests/doubles/broker.py` — pas encore
écrits, chacun fera l'objet d'une proposition séparée.
**Tests verts** : `src/broker/test_git.py` — 39 cas, venv `pithos`, Python 3.12.9.
**Exécuté** : —

---


## Proposé le 07:09 — identité d'un effet sortant et intention persistée

**Intention** : rendre un effet sortant rejouable sans être recompté — identité de résultat déterministe,
identité de transport renouvelée, intention écrite avant l'effet et résultat après.

```sh
ga src/broker/identity.py \
   src/broker/intent.py \
   src/broker/conftest.py \
   src/broker/test_identity.py \
   src/broker/test_intent.py
gcmsg "broker: identité de résultat déterministe et intention persistée avant l'effet"
```

**Contient** : `identity.py` (53 L) — `Effect`, `EffectIdentity`, `result_key`, `transport_key`,
`same_result` ; `intent.py` (83 L) — `Stage`, `record_intent`, `record_result`, `stage`, `resume` ;
`conftest.py`, qui porte le chargeur de doubles et la route Telegram locale utilisée plus loin.
**Ne contient pas** : `telegram.py`, qui consomme `read_ledger` — commit suivant.
**Tests verts** : `src/broker/test_identity.py` (6 cas), `src/broker/test_intent.py` (9 cas).
**Exécuté** : —

---

## Proposé le 07:09 — Telegram bidirectionnel

**Intention** : porter la frontière Telegram — deux erreurs typées, backoff monotone partagé, découpe en
unités UTF-16, allowlist, cinq commandes, offsets persistants et signal d'interruption.

```sh
ga src/broker/telegram.py \
   src/broker/test_telegram.py
gcmsg "broker: telegram bidirectionnel, backoff partagé et offsets persistants"
```

**Contient** : `telegram.py` (320 L) et ses 28 cas, exécutés contre une vraie route HTTP locale.
**Ne contient pas** : la boucle de polling elle-même — elle appartient à `lifecycle` (`STATE.md`
§ *Blocages*). `broker` n'en publie que les unités : `poll`, `saved_offset`, `remember_offset`.
**Tests verts** : `src/broker/test_telegram.py` — 28 cas.
**Exécuté** : —

---

## Proposé le 07:09 — frontière publiée, double conforme, graphe d'imports

**Intention** : publier le `Protocol` `Broker`, son double en mémoire, et le test qui ferme la contrainte
dure n°5 sur tout `src/`.

```sh
ga src/broker/__init__.py \
   tests/doubles/broker.py \
   src/broker/test_double_contract.py \
   src/broker/test_import_boundaries.py \
   src/broker/STATE.md \
   src/broker/git.md
gcmsg "broker: protocol publié, double en mémoire et graphe d'imports de l'egress"
```

**Contient** : `__init__.py` (53 L, `Protocol` à 7 membres) ; `tests/doubles/broker.py` (126 L) jouant les
trois scénarios de `MODULE.md` § 9 ; le test de conformité du double ; le test de graphe d'imports, qui
mesure que **seuls `bridge` et `broker` parlent HTTP** et qu'aucun module n'importe `socket`.
**Ne contient pas** : le déplacement de ces deux tests vers `tests/boundaries/` et `tests/contracts/` —
hors périmètre, consigné en blocage.
**Tests verts** : `src/broker/test_double_contract.py` (8 cas), `src/broker/test_import_boundaries.py`
(16 cas). Suite complète du dépôt : 738 verts.
**Exécuté** : —

---

<!-- Gabarit d'une proposition — copie ce bloc, ne le supprime pas.

## Proposé le JJ:MM — <titre court>

**Intention** : une phrase — ce que ce commit fait, et rien d'autre.

```sh
ga src/broker/<fichier_a>.py \
   src/broker/<fichier_b>.py \
   tests/doubles/broker.py
gcmsg "broker: <ce que ça fait>"
```

**Contient** : …
**Ne contient pas** : …
**Tests verts** : …
**Exécuté** : —

-->

## Proposé le 12:09 — faits de dépôt canoniques

**Intention** : publier les observations Git au contrat kernel avec leur complétude explicite.

```sh
ga src/broker/git.py \
   src/broker/test_git.py \
   tests/doubles/broker.py \
   src/broker/MODULE.md \
   src/broker/STATE.md \
   src/broker/git.md
gcmsg "broker: publie les faits canoniques et leur complétude"
```

**Contient** : aliases kernel, collecte sans textconv, refus des statuts tronqués et chemins hors dépôt, incomplétude explicite sans HEAD ou avec non-suivis, double.
**Tests verts** : 69 tests Git/contrat/frontière ; suite complète 1 325 passed, 3 skipped, 7 warnings.
**Exécuté** : —

### Complément le 12:09 — proposition « faits de dépôt canoniques »

Les mêmes chemins incluent maintenant le helper `agree_with(fact, repo=...)` du double et deux tests
pour les FileFact absolus : racine explicite, refus hors dépôt, aucun diff inventé. Validation finale
broker : **114 passed en 1,99 s** hors sandbox ; suite globale **1 367 passed, 3 skipped, 7 warnings en 37,10 s**.
La tentative refusée par la sandbox (93 passed, 21 erreurs de bind) reste consignée dans STATE.
**Exécuté** : —

## Proposé le 14:09 — finalisation verte réconciliable

**Intention** : publier une modification attestée une seule fois malgré une perte d'acquittement.

```sh
ga src/broker/finalize.py \
   src/broker/test_finalize.py \
   src/broker/__init__.py \
   tests/doubles/broker.py \
   src/broker/MODULE.md \
   src/broker/STATE.md \
   src/broker/git.md
gcmsg "broker: réconcilie les commits verts sous deadline"
```

**Contient** : port, adaptateur Git local, preuve durable, deadline partagée et double.
**Tests verts** : 45 tests ciblés ; suite racine 1 534 passed, 3 skipped, 7 warnings.
Le contrat/frontière partagé possède son lot dans tests/git.md.
**Exécuté** : —

### Complément le 14:09 — preuve finale de composition

Les mêmes chemins proposés incluent les dernières gardes et les STATE à jour. Suite finale :
**1 548 passed, 3 skipped, 7 warnings en 87,81 s** ; contrôle des onze STATE et diff-check verts.
Les lots broker, lifecycle, experiment et leur support partagé tests forment l'état vérifié ensemble.
Aucun commit ni push exécuté par l'agent.
