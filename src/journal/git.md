# git — commits proposés pour `journal`

**Aucun agent ne commite.** Ce fichier **propose** ; un humain **exécute**. Voir
[`AGENTS.md`](../../AGENTS.md) § 7.

Append-only : on ajoute une proposition, on ne réécrit pas les précédentes. Une proposition exécutée est
**marquée**, jamais supprimée.

**Rappels de format** — un commit une intention · chemins explicites, jamais `gaa` · message
`journal: <ce que ça fait>` en minuscules, sans point final · uniquement du travail dont les tests passent ·
uniquement `src/journal/` et `tests/doubles/journal.py`.

---

## Proposé le 06:09 — rédaction

**Intention** : rédiger une structure imbriquée en rendant aussi la liste des chemins rédigés.

```sh
ga src/journal/redact.py \
   src/journal/test_redact.py
gcmsg "journal: rédaction par liste de motifs nommée"
```

**Contient** : `redact`, les deux listes de motifs nommées, et le remplacement d'un sous-arbre secret entier.
**Ne contient pas** : les motifs de *valeur* d'Ouroboros — voir `STATE.md` § Décisions locales.
**Tests verts** : `src/journal/test_redact.py` — 6 tests, autonomes.
**Exécuté** : —

---

## Proposé le 06:09 — sens lecture

**Intention** : lire les traces durables et diagnostiquer une queue déchirée sans jamais la réparer.

```sh
ga src/journal/read.py \
   src/journal/test_read.py
gcmsg "journal: lecture des traces et détection de queue déchirée"
```

**Contient** : `read`, `tail` avec son drapeau d'omission, `next_event_id`, `torn_tail`, `generation_signature`.
**Ne contient pas** : `write.py` — l'écriture importe la lecture, l'inverse n'est pas vrai ; commit séparé.
**Tests verts** : `src/journal/test_read.py` — 12 tests, autonomes (aucune dépendance à `conftest.py`).
**Exécuté** : —

---

## Proposé le 06:09 — sens écriture

**Intention** : écrire une preuve JSONL durable et sa projection `live.log` sans jamais lever.

```sh
ga src/journal/write.py \
   src/journal/conftest.py \
   src/journal/test_write.py
gcmsg "journal: écriture durable et read-modify-write verrouillé"
```

**Contient** : `bind`, `emit`, `update_json_locked`, le verrou global unique, l'écriture atomique
temp+rename, et la reprise par segment lié sur queue déchirée.
**Ne contient pas** : le `Protocol` ni le double — ils arrivent avec l'interface, commit suivant.
**Tests verts** : `src/journal/test_write.py` — 18 tests, dont un `SIGKILL` réel en sous-processus et
une écriture concurrente sous verrou.
**Exécuté** : —

---

## Proposé le 06:09 — interface et double

**Intention** : publier le `Protocol` du journal et le double conforme contre lequel les autres modules se testent.

```sh
ga src/journal/__init__.py \
   src/journal/test_interface.py \
   tests/doubles/journal.py
gcmsg "journal: interface, double conforme et frontière d'import"
```

**Contient** : `Journal` (membres statiques), le double en mémoire avec ses deux pannes simulables,
la conformité protocole + signatures, et le test de frontière mutation-checké.
**Ne contient pas** : `tests/contracts/` ni `tests/boundaries/` — hors périmètre, voir `STATE.md` § Blocages 2 et 3.
**Tests verts** : `src/journal/test_interface.py` — 4 tests.
**Exécuté** : —

---

## Proposé le 06:09 — état du module

**Intention** : consigner l'état repris­able du module, ses écarts et ses reprises traitées.

```sh
ga src/journal/STATE.md \
   src/journal/git.md
gcmsg "journal: état du socle, écarts mesurés et reprises traitées"
```

**Contient** : `STATE.md` complet — avancement, journal avec niveaux de preuve, quatre blocages,
décisions locales et les 34 reprises tranchées ; et ce fichier.
**Ne contient pas** : `MODULE.md`, inchangé.
**Tests verts** : sans objet — documentation. La suite du module est verte au moment de la proposition
(`python -m pytest src/journal` → **40 passed**).
**Exécuté** : —


<!-- Gabarit d'une proposition — copie ce bloc, ne le supprime pas.

## Proposé le JJ:MM — <titre court>

**Intention** : une phrase — ce que ce commit fait, et rien d'autre.

```sh
ga src/journal/<fichier_a>.py \
   src/journal/<fichier_b>.py \
   tests/doubles/journal.py
gcmsg "journal: <ce que ça fait>"
```

**Contient** : …
**Ne contient pas** : …
**Tests verts** : …
**Exécuté** : —

-->
