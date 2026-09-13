# git — commits proposés pour `observatory`

**Aucun agent ne commite.** Ce fichier **propose** ; un humain **exécute**. Voir
[`AGENTS.md`](../../AGENTS.md) § 7.

Append-only : on ajoute une proposition, on ne réécrit pas les précédentes. Une proposition exécutée est
**marquée**, jamais supprimée.

**Rappels de format** — un commit une intention · chemins explicites, jamais `gaa` · message
`observatory: <ce que ça fait>` en minuscules, sans point final · uniquement du travail dont les tests passent ·
uniquement `src/observatory/` et `tests/doubles/observatory.py`.

---

## Proposé le 07:09 — index mémoire des JSONL

**Intention** : reconstruire le catalogue des missions depuis le disque au démarrage, sans collecteur.

```sh
ga src/observatory/__init__.py \
   src/observatory/api/__init__.py \
   src/observatory/api/index.py \
   src/observatory/conftest.py \
   src/observatory/test_index.py
gcmsg "observatory: index mémoire des JSONL, segments et suivi mtime"
```

**Contient** : `MissionRow`, `Index`, `segments`, `signature`, `read_events`, `scan`, `refresh`,
`build_index`, `mission_events`, le protocole `Observatory` et les fixtures partagées.
**Ne contient pas** : l'arbre, les agrégats et les routes — trois commits séparés ci-dessous.
**Tests verts** : `src/observatory/test_index.py` (10 tests).
**Exécuté** : —

## Proposé le 07:09 — arbre aplati et rendu texte compact

**Intention** : servir un arbre résistant aux identifiants dupliqués, aux cycles et aux durées négatives.

```sh
ga src/observatory/api/render.py \
   src/observatory/test_render.py
gcmsg "observatory: arbre aplati, durées séparées et rendu texte compact"
```

**Contient** : `TreeRow`, `flatten_tree` (dédup, `visited`, enveloppe de sous-arbre), `window` (décision 29),
`status_text` réutilisable par le CLI et Telegram, `label` borné à 80 caractères.
**Ne contient pas** : les routes qui les servent.
**Tests verts** : `src/observatory/test_render.py` (11 tests).
**Exécuté** : —

## Proposé le 07:09 — agrégats et cinq indicateurs

**Intention** : calculer les agrégats d'analyse et les cinq indicateurs depuis les seuls événements.

```sh
ga src/observatory/api/stats.py \
   src/observatory/test_stats.py
gcmsg "observatory: agrégats journaliers, outils, contexte et cinq indicateurs"
```

**Contient** : `daily`, `tools` avec l'inflation de splice, `context` avec les quatre paliers de la
décision 14, `indicators`, et `validate` qui rend toutes les violations d'un coup.
**Ne contient pas** : la fenêtre de contexte lue depuis le payload — `bridge` ne la consigne pas encore
(`STATE.md` § *Blocages* n°2, `TODO` posé dans le fichier).
**Tests verts** : `src/observatory/test_stats.py` (14 tests).
**Exécuté** : —

## Proposé le 07:09 — routes de lecture bornées

**Intention** : servir catalogue, détail, arbre, artefacts, agrégats et readiness sur la loopback seule.

```sh
ga src/observatory/api/routes.py \
   src/observatory/test_routes.py \
   src/observatory/test_readonly.py \
   src/observatory/test_import_boundaries.py
gcmsg "observatory: routes de lecture bornées, bind loopback en dur"
```

**Contient** : les dix routes, le manifeste d'artefacts, l'enveloppe `freshness`, le 404 typé qui empêche
un identifiant de mission de devenir un chemin, et les trois tests statiques — aucune écriture, aucun
rendu HTML, aucun appel aux écrivains de `journal`.
**Ne contient pas** : `web/`, non porté.
**Tests verts** : `src/observatory/test_routes.py` (20 tests), `test_readonly.py` (10),
`test_import_boundaries.py` (24). Vérification réelle : `uvicorn` sur `127.0.0.1:8823`, connexion refusée
depuis l'adresse LAN.
**Exécuté** : —

## Proposé le 07:09 — double mémoire et contrat de frontière

**Intention** : rendre l'observatoire consommable sans disque et vérifier qu'il tient le même protocole.

```sh
ga tests/doubles/observatory.py \
   src/observatory/test_double_contract.py
gcmsg "observatory: double mémoire conforme au protocole"
```

**Contient** : le double scriptable par `missions` et `anomalies`, et le test de contrat qui vérifie
protocole, signatures, égalité de projection et absence totale d'I/O.
**Ne contient pas** : le déplacement vers `tests/contracts/`, en attente de dérogation
(`STATE.md` § *Blocages* n°4).
**Tests verts** : `src/observatory/test_double_contract.py` (4 tests).
**Exécuté** : —

<!-- Gabarit d'une proposition — copie ce bloc, ne le supprime pas.

## Proposé le JJ:MM — <titre court>

**Intention** : une phrase — ce que ce commit fait, et rien d'autre.

```sh
ga src/observatory/<fichier_a>.py \
   src/observatory/<fichier_b>.py \
   tests/doubles/observatory.py
gcmsg "observatory: <ce que ça fait>"
```

**Contient** : …
**Ne contient pas** : …
**Tests verts** : …
**Exécuté** : —

-->


## Proposé le 13:09 — projeter les preuves du banc

**Intention** : Rendre les essais du banc lisibles depuis leurs preuves publiées.

```sh
ga src/observatory/__init__.py \
   src/observatory/__main__.py \
   src/observatory/api/index.py \
   src/observatory/api/evidence.py \
   src/observatory/api/render.py \
   src/observatory/api/routes.py \
   src/observatory/api/stats.py \
   src/observatory/conftest.py \
   src/observatory/test_index.py \
   src/observatory/test_stats.py \
   src/observatory/test_trials.py \
   tests/doubles/observatory.py \
   src/observatory/MODULE.md \
   src/observatory/STATE.md \
   src/observatory/git.md
gcmsg "observatory: projette les preuves publiées des essais"
```

**Contient** : Collection directe, snapshot prioritaire, gates sans reçu, historique de vérification, aperçus bornés et métriques sourcées. Les corpus partagés sont proposés dans tests/git.md. Prérequis : socle observatory et instrumentation bridge/engine des propositions précédentes.
**Tests verts** : src/observatory, tests/contracts/test_observatory_double.py, tests/boundaries/test_observatory.py ; lecture HTTP réelle du trial-44kcg6ig. Suite complète : **1 444 passed, 3 skipped, 7 warnings en 43,83 s**, Python 3.12.9/pithos ; contrôle des onze STATE vert.
**Exécuté** : —


## Proposé le 13:09 — dashboard local des essais

**Intention** : Explorer les preuves des essais depuis une interface locale en lecture seule.

```sh
ga src/observatory/web/.gitignore \
   src/observatory/web/package.json \
   src/observatory/web/package-lock.json \
   src/observatory/web/tsconfig.json \
   src/observatory/web/vite.config.ts \
   src/observatory/web/index.html \
   src/observatory/web/src/main.tsx \
   src/observatory/web/src/App.tsx \
   src/observatory/web/src/data.ts \
   src/observatory/web/src/ui.tsx \
   src/observatory/web/src/style.css \
   src/observatory/web/src/dashboard.test.tsx
gcmsg "observatory: ajoute le dashboard local des essais"
```

**Contient** : Navigation paginée, arbre, preuves, contexte, statistiques, timeline, aperçus et polling annulable. Stack déclarée dans MODULE.md du lot API. node_modules et dist ignorés. Inspection visuelle encore ouverte faute de navigateur accessible.
**Tests verts** : npm --prefix src/observatory/web test : 8 tests ; npm --prefix src/observatory/web run build : typage et build verts sous Node 26.7.0. Lecture HTTP du build et de son proxy constatée.
**Exécuté** : —
