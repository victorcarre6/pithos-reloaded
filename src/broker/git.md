# git — commits proposés pour `broker`

**Aucun agent ne commite.** Ce fichier **propose** ; un humain **exécute**. Voir
[`AGENTS.md`](../../AGENTS.md) § 7.

Append-only : on ajoute une proposition, on ne réécrit pas les précédentes. Une proposition exécutée est
**marquée**, jamais supprimée.

**Rappels de format** — un commit une intention · chemins explicites, jamais `gaa` · message
`broker: <ce que ça fait>` en minuscules, sans point final · uniquement du travail dont les tests passent ·
uniquement `src/broker/` et `tests/doubles/broker.py`.

---

_Aucune proposition. Le module n'a pas encore de code._

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
