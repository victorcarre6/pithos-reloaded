# STATE — `observatory`

**Statut** : non commencé
**Mise à jour** : —
**Lignes** : 0 / ~550 L API + ~700 L web

## Prochaine action

Écrire `api/index.py` : reconstruire l'index mémoire depuis les JSONL au démarrage, en lisant **par `journal`**, avec séparation catalogue / détail. Le premier test lit un JSONL à queue déchirée et vérifie que l'index se construit quand même.

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

## Blocages

| Quoi | Pourquoi | Ce qui débloquerait | Résolu le |
|---|---|---|---|

## Décisions locales

_Choix d'implémentation pris ici, qu'un successeur doit connaître et ne doit pas défaire sans raison._

## Reprises traitées

| Source | Verdict | Fait ? | Note |
|---|---|---|---|
