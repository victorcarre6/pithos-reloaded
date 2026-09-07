# STATE — `lifecycle`

**Statut** : non commencé
**Mise à jour** : —
**Lignes** : 0 / ~250 L

## Prochaine action

Écrire `lock.py` : verrou-répertoire atomique portant `(pid, heure de démarrage)`, trois états dont `unavailable` qui bloque, péremption par durée maximale. Le premier test est celui de deux acquisitions concurrentes par `fork` réel — une seule doit réussir.

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
