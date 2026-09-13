# git — commits proposés pour `campaign`

**Aucun agent ne commite.** Ce fichier **propose** ; un humain **exécute**. Voir
[`AGENTS.md`](../../AGENTS.md) § 7.

Append-only : on ajoute une proposition, on ne réécrit pas les précédentes. Une proposition exécutée est
**marquée**, jamais supprimée.

**Rappels de format** — un commit une intention · chemins explicites, jamais `gaa` · message
`campaign: <ce que ça fait>` en minuscules, sans point final · uniquement du travail dont les tests passent ·
uniquement `src/campaign/` et `tests/doubles/campaign.py`.

---

## Proposé le 10:09 — le magasin et sa relecture défensive

**Intention** : publier le magasin à deux familles dont la relecture ne lève jamais.

```sh
ga src/campaign/__init__.py \
   src/campaign/store.py \
   src/campaign/conftest.py \
   src/campaign/test_store.py
gcmsg "campaign: magasin à deux familles dont la relecture ne lève jamais"
```

**Contient** : `Family`, `Source`, `Entry`, `Store`, `bind`, `load`, `put`, `render_compact`, la
coercition champ par champ, le journal des entrées ignorées, et le harnais de corruption systématique.
**Ne contient pas** : `registry`, `admit`, `propose`, `stop`, `mcpconfig` et le double — encore à écrire.
**Tests verts** : `src/campaign/test_store.py` — 107 cas, venv `pithos`, Python 3.12.9.
**Exécuté** : —

## Proposé le 10:09 — le registre et la péremption par empreinte

**Intention** : publier le registre d'outils, ses sept états et sa satisfaction périssable.

```sh
ga src/campaign/registry.py \
   src/campaign/test_registry.py
gcmsg "campaign: registre d'outils à sept états et satisfaction périssable"
```

**Contient** : `TaskLifecycle` et ses trois formes d'échec, `ToolEntry`, la primitive `fingerprint`,
`diverged`, `is_satisfied`, et `project` — la surface appelable plus la raison typée de chaque absence.
**Ne contient pas** : `admit`, `propose`, `stop`, `mcpconfig` et le double — encore à écrire.
**Tests verts** : `src/campaign/test_registry.py` — 19 cas, 126 avec `test_store.py`, venv `pithos`.
**Exécuté** : —

## Proposé le 10:09 — les règles d'admission déclarative

**Intention** : publier l'admission qui rend toutes les violations d'une proposition en une seule passe.

```sh
ga src/campaign/admit.py \
   src/campaign/test_admit.py
gcmsg "campaign: admission rendant toutes les violations avec leur chemin de champ"
```

**Contient** : `Proposal`, `Violation`, `Ok`/`Err`, et les quatre règles — nom d'outil, noms d'arguments,
préfixe de module, gabarit à placeholders fermés sans expression évaluable.
**Ne contient pas** : `propose`, `stop`, `mcpconfig` et le double — encore à écrire.
**Tests verts** : `src/campaign/test_admit.py` — 58 cas, 184 avec `test_store.py` et `test_registry.py`.
**Exécuté** : —

## Proposé le 10:09 — la redondance en deux temps et le classement par axes

**Intention** : publier la détection de redondance sans appel modèle et le classement lexicographique.

```sh
ga src/campaign/propose.py \
   src/campaign/test_propose.py
gcmsg "campaign: redondance en deux temps et classement par axes nommés"
```

**Contient** : `terms`, `related`, `contract_fingerprint`, `dedup`, `remember`, `axes`, `rank`,
`Signal`, `derive` et sa porte à trois rejets, `counters`.
**Ne contient pas** : `stop`, `mcpconfig`, le double et les deux tests transverses.
**Tests verts** : `src/campaign/test_propose.py` — 25 cas, 209 avec les précédents, venv `pithos`.
**Exécuté** : —

---

## Proposé le 10:09 — l'arrêt auditable et la couche MCP managed

**Intention** : publier la proposition d'arrêt et l'écriture de la couche `managed` de la config MCP.

```sh
ga src/campaign/stop.py \
   src/campaign/test_stop.py \
   src/campaign/mcpconfig.py \
   src/campaign/test_mcpconfig.py
gcmsg "campaign: arrêt énumérant ce qui a été examiné et couche mcp managed"
```

**Contient** : `StopCause` (taxonomie fermée à cinq membres), `StopProposal`, `should_stop`,
`managed_layer` et `write_managed` — exécutable plus liste d'arguments exacte, sans shell ni env.
**Ne contient pas** : le double et les deux tests transverses — proposition suivante.
**Tests verts** : `src/campaign/test_stop.py`, `src/campaign/test_mcpconfig.py` — 226 cas au total.
**Exécuté** : —

---

## Proposé le 10:09 — le double, le contrat de frontière et le graphe d'imports

**Intention** : publier le double de la politique et les deux tests qui verrouillent sa frontière.

```sh
ga src/campaign/__init__.py \
   src/campaign/test_double_contract.py \
   src/campaign/test_import_boundaries.py \
   tests/doubles/campaign.py
gcmsg "campaign: double en mémoire, contrat de frontière et graphe d'imports"
```

**Contient** : le `Protocol` `Campaign`, le double à magasin mémoire et `admit` pilotable, le corpus
partagé politique/double, et le test d'imports qui rend mécanique l'absence d'appel modèle.
**Ne contient pas** : le déplacement des deux tests vers `tests/contracts/` et `tests/boundaries/` —
il est hors de mon périmètre et attend une dérogation (`STATE.md` § Blocages).
**Tests verts** : `src/campaign` en entier — 266 passed, 1 skipped, venv `pithos`, Python 3.12.9.
**Exécuté** : —

<!-- Gabarit d'une proposition — copie ce bloc, ne le supprime pas.

## Proposé le JJ:MM — <titre court>

**Intention** : une phrase — ce que ce commit fait, et rien d'autre.

```sh
ga src/campaign/<fichier_a>.py \
   src/campaign/<fichier_b>.py \
   tests/doubles/campaign.py
gcmsg "campaign: <ce que ça fait>"
```

**Contient** : …
**Ne contient pas** : …
**Tests verts** : …
**Exécuté** : —

-->
