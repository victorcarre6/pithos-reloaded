# git — commits proposés pour `kernel`

**Aucun agent ne commite.** Ce fichier **propose** ; un humain **exécute**. Voir
[`AGENTS.md`](../../AGENTS.md) § 7.

Append-only : on ajoute une proposition, on ne réécrit pas les précédentes. Une proposition exécutée est
**marquée**, jamais supprimée.

**Rappels de format** — un commit une intention · chemins explicites, jamais `gaa` · message
`kernel: <ce que ça fait>` en minuscules, sans point final · uniquement du travail dont les tests passent ·
uniquement `src/kernel/` et `tests/doubles/kernel.py`.

---

_Aucune proposition. Le module n'a pas encore de code._

<!-- Gabarit d'une proposition — copie ce bloc, ne le supprime pas.

## Proposé le JJ:MM — <titre court>

**Intention** : une phrase — ce que ce commit fait, et rien d'autre.

```sh
ga src/kernel/<fichier_a>.py \
   src/kernel/<fichier_b>.py \
   tests/doubles/kernel.py
gcmsg "kernel: <ce que ça fait>"
```

**Contient** : …
**Ne contient pas** : …
**Tests verts** : …
**Exécuté** : —

## Proposé le 06:09 — inspection structurelle bornée

**Intention** : fournir des faits AST et des lectures bornées sur les chemins du dépôt.

```sh
ga src/kernel/codeview.py \
   src/kernel/test_codeview.py \
   src/kernel/STATE.md \
   src/kernel/git.md
gcmsg "kernel: inspecter les sources avec des lectures bornées"
```

**Contient** : signatures complètes, définitions, snippet, détection binaire, classification conservatrice et confinement résolu.
**Ne contient pas** : index, sélection du contexte, gate de compatibilité des domaines.
**Tests verts** : `src/kernel/test_codeview.py` — **67 tests** dans l'exécution commune avec identité (**78 passed**), Python 3.12.9 / venv `pithos`.
**Exécuté** : —

## Proposé le 06:09 — identité de vérification

**Intention** : comparer les vérifications par une clé typée sans repli.

```sh
ga src/kernel/facts.py \
   src/kernel/test_identity.py \
   src/kernel/STATE.md \
   src/kernel/git.md
gcmsg "kernel: identifier les vérifications sans chaîne de repli"
```

**Contient** : `RecordKey`, `same_identity`, tests d'équivalence et refus des identités partielles.
**Ne contient pas** : attribution d'identité par verifier, identité de transport par broker.
**Tests verts** : `src/kernel/test_identity.py` — **11 tests** dans l'exécution commune avec codeview (**78 passed**), Python 3.12.9 / venv `pithos`.
**Exécuté** : —

-->

## Proposé le 06:09 — vocabulaire strict du socle

**Intention** : définir les données échangeables du socle avec leurs rejets explicites.

```sh
ga src/kernel/contracts.py \
   src/kernel/facts.py \
   src/kernel/errors.py \
   src/kernel/test_contracts.py \
   src/kernel/test_errors.py \
   src/kernel/STATE.md \
   src/kernel/git.md
gcmsg "kernel: valider le vocabulaire du socle"
```

**Contient** : cinq modèles, enums fermées, JSON fini, erreurs agrégées, tests et état de reprise.
**Ne contient pas** : codeview, identité, double — prochaines unités.
**Tests verts** : `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider src/kernel/test_contracts.py src/kernel/test_errors.py` — **80 passed**, Python 3.12.9 / venv `pithos`.
**Exécuté** : —

## État des propositions — 06:09

Les propositions antérieures ne sont pas exécutées. Les deux propositions « inspection » et « identité »
ont été ajoutées par erreur dans le commentaire du gabarit ; elles y restent conservées. Les trois
propositions visibles suivantes les remplacent pour **l'état final du worktree**, dans cet ordre.
Les tests partagés sont encore dans kernel ; après leur déplacement autorisé, ajouter une proposition
avec les destinations effectives avant de commiter. Aucun `ga`/`gcmsg` n'a été exécuté par l'agent.

## Proposé le 06:09 — contrats validés du kernel

**Intention** : définir le vocabulaire validé du socle.

```sh
ga src/kernel/contracts.py \
   src/kernel/errors.py \
   src/kernel/facts.py \
   src/kernel/test_contracts.py \
   src/kernel/test_errors.py \
   src/kernel/test_identity.py
gcmsg "kernel: définir les contrats validés du socle"
```

**Contient** : les cinq modèles, leurs choix fermés, la clé de vérification sans repli, les erreurs agrégées
et les tests de rejets, sérialisation et équivalence. Le JSON fini utilise désormais un TypeAdapter Python
aussi à la lecture JSON ; aucune coercition de tuple/set/Decimal.
**Ne contient pas** : émission de reçu ou règles d'admission de campagne.
**Tests verts** : `src/kernel/test_contracts.py`, `src/kernel/test_errors.py`,
`src/kernel/test_identity.py`, dans le run final **193 passed in 0.32s** — Python 3.12.9 / venv `pithos`.
**Exécuté** : —

## Proposé le 06:09 — interface de lecture structurelle

**Intention** : exposer une inspection Python bornée et testable derrière CodeView.

```sh
ga src/kernel/codeview.py \
   src/kernel/protocol.py \
   src/kernel/test_codeview.py
gcmsg "kernel: exposer la lecture structurelle bornée"
```

**Contient** : signatures AST, définitions, snippet, détection binaire, classes de chemins, confinement,
Protocol et notice de la reprise Kilo. `snippet` lit le préfixe de 8 000 octets ; les chemins cachés sans
classe sûre sont refusés explicitement.
**Ne contient pas** : index, sélection du contexte ou exécution des symboles.
**Tests verts** : `src/kernel/test_codeview.py`, dans le run final **193 passed in 0.32s** — Python 3.12.9 /
venv `pithos`.
**Exécuté** : —

## Proposé le 06:09 — preuve des frontières du kernel

**Intention** : fournir les contrôles reproductibles des frontières du kernel.

```sh
ga tests/doubles/kernel.py \
   src/kernel/test_double_contract.py \
   src/kernel/test_import_boundaries.py \
   src/kernel/MODULE.md \
   src/kernel/STATE.md \
   src/kernel/git.md
gcmsg "kernel: vérifier les frontières avec un double mémoire"
```

**Contient** : cinq constructeurs, CodeView mémoire, corpus contractuel, contrôle AST des imports/I/O,
tests qui détectent des violations injectées, documentation des choix et du blocage de placement.
**Ne contient pas** : les deux déplacements hors périmètre ni une validation d'intégration de campagne.
**Tests verts** : `src/kernel/test_double_contract.py`, `src/kernel/test_import_boundaries.py`, dans le run
final **193 passed in 0.32s** — Python 3.12.9 / venv `pithos`. **Niveau de preuve : 5, sur double.**
**Exécuté** : —
