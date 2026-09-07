# git — commits proposés pour `bridge`

**Aucun agent ne commite.** Ce fichier **propose** ; un humain **exécute**. Voir
[`AGENTS.md`](../../AGENTS.md) § 7.

Append-only : on ajoute une proposition, on ne réécrit pas les précédentes. Une proposition exécutée est
**marquée**, jamais supprimée.

**Rappels de format** — un commit une intention · chemins explicites, jamais `gaa` · message
`bridge: <ce que ça fait>` en minuscules, sans point final · uniquement du travail dont les tests passent ·
uniquement `src/bridge/` et `tests/doubles/bridge.py`.

---

## Proposé le 06:09 — normalisation de schéma

**Intention** : rendre le schéma d'un modèle Pydantic réellement applicable par une grammaire de décodage.

```sh
ga src/bridge/schema.py \
   src/bridge/test_schema.py
gcmsg "bridge: normalisation du schéma en JSON Schema décodable"
```

**Contient** : résolution des `$defs`/`$ref`, bornes explicites sur les integers, sous-ensemble de
mots-clés déclaré, et le refus avant envoi d'une référence non résolue.
**Ne contient pas** : la revalidation, commit suivant.
**Tests verts** : `src/bridge/test_schema.py` — 9 tests, autonomes.
**Exécuté** : —

---

## Proposé le 06:09 — revalidation locale

**Intention** : rejeter localement toute sortie non conforme au schéma exact envoyé, avec un code fermé.

```sh
ga src/bridge/revalidate.py \
   src/bridge/test_revalidate.py
gcmsg "bridge: revalidation locale à cinq codes fermés"
```

**Contient** : les cinq codes, `parse_constant` refusant `NaN`/`Infinity`, la garde d'identité
schéma ↔ modèle, et l'empreinte qui lie chaque verdict au schéma envoyé.
**Ne contient pas** : `jsonschema` — non déclaré dans `requirements.txt`, voir `STATE.md` § Blocages 3.
**Tests verts** : `src/bridge/test_revalidate.py` — 11 tests.
**Exécuté** : —

---

## Proposé le 06:09 — appel borné

**Intention** : envoyer un POST unique, borné et non rejoué, et n'en rendre qu'une issue typée.

```sh
ga src/bridge/client.py \
   src/bridge/conftest.py \
   src/bridge/test_client.py
gcmsg "bridge: appel bloquant borné et issue discriminée"
```

**Contient** : `Deadline`, `RawResponse`, `Outcome`, l'insertion stricte de `response_format`, la
réservation de sortie avant appel, la séparation du thinking, le refus hors loopback et
l'enregistrement du payload effectif.
**Ne contient pas** : la sonde, commit suivant.
**Tests verts** : `src/bridge/test_client.py` — 13 tests contre une vraie route HTTP locale.
**Exécuté** : —

---

## Proposé le 06:09 — sonde d'avant-campagne

**Intention** : refuser de démarrer une campagne tant que la fenêtre et le schéma ne sont pas prouvés.

```sh
ga src/bridge/probe.py \
   src/bridge/prompt/ling.md \
   src/bridge/test_probe.py
gcmsg "bridge: sonde d'avant-campagne fail-closed"
```

**Contient** : lecture de `n_ctx_train` sur `/v1/models`, les trois provenances dont `unprobeable`
fail-closed, l'envoi d'un vrai `Criterion`, et le prompt système comme donnée versionnée.
**Ne contient pas** : `test_tool_calling`, écarté par le `MODULE.md` § 9.
**Tests verts** : `src/bridge/test_probe.py` — 8 tests.
**Exécuté** : —

---

## Proposé le 06:09 — interface et double

**Intention** : publier le `Protocol` de la frontière et le faux fournisseur scénarisé qu'`engine` utilisera.

```sh
ga src/bridge/__init__.py \
   src/bridge/test_interface.py \
   tests/doubles/bridge.py
gcmsg "bridge: interface, double scénarisé et frontière d'import"
```

**Contient** : `Bridge` à membres statiques, la file de réponses et ses quatre fabriques, la
conformité protocole + signatures, et les trois tests de frontière — dont l'interdit d'`engine`.
**Ne contient pas** : `tests/boundaries/` — hors périmètre, voir `STATE.md` § Blocages 1.
**Tests verts** : `src/bridge/test_interface.py` — 6 tests, mutation-checkés.
**Exécuté** : —

---

## Proposé le 06:09 — état du module

**Intention** : consigner l'état repris­able du module, ses écarts et ses reprises tranchées.

```sh
ga src/bridge/STATE.md \
   src/bridge/git.md
gcmsg "bridge: état du socle, écarts mesurés et reprises traitées"
```

**Contient** : avancement, journal avec niveaux de preuve, trois blocages, décisions locales et le
tri des ~110 lignes de reprises entre ce module et ceux qui les portent réellement.
**Ne contient pas** : `MODULE.md`, inchangé.
**Tests verts** : sans objet — documentation. La suite du module est verte au moment de la proposition
(`python -m pytest src/bridge` → **47 passed**).
**Exécuté** : —


<!-- Gabarit d'une proposition — copie ce bloc, ne le supprime pas.

## Proposé le JJ:MM — <titre court>

**Intention** : une phrase — ce que ce commit fait, et rien d'autre.

```sh
ga src/bridge/<fichier_a>.py \
   src/bridge/<fichier_b>.py \
   tests/doubles/bridge.py
gcmsg "bridge: <ce que ça fait>"
```

**Contient** : …
**Ne contient pas** : …
**Tests verts** : …
**Exécuté** : —

-->
