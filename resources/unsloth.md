# Unsloth — pointeur

L'extraction complète (**~110 mappages**) a été consignée dans
**[`IMPORT_REPORT.md`](IMPORT_REPORT.md) § Partie F** : catalogue par module
(`cible -> <chemin>:<ligne> -> notion`, statuts S / A / I / X), ce que chaque reprise a changé dans la
documentation, les écarts, et l'ordre de portage.

Les notions qui ont donné lieu à une décision d'architecture sont détaillées dans
[`../docs/EXPLANATIONS.md`](../docs/EXPLANATIONS.md) — décisions 8, 12 et 21 amendées, **décision 27**.

**Nature de la source.** Unsloth n'est **pas** un runtime d'orchestration : c'est une bibliothèque de
fine-tuning. Kernels CUDA, entraînement RL et optimisation MoE sont hors périmètre. **Sa valeur est dans
`unsloth_cli/` et `studio/backend/`** — le seul des six dépôts à traiter frontalement la question « à quelles
conditions un service local a-t-il le droit d'être joignable de l'extérieur ».

> **Licence — le seul point ouvert des six sources.** Le dépôt **mélange une licence AGPL pour `studio/`**
> avec d'autres notices, et ce sont précisément les fichiers de `studio/` qui portent les reprises les plus
> utiles. Décision retenue : **reprendre les notions, réécrire le code. Aucune copie littérale depuis
> `studio/`.** Détail en § F1.1.

Ce dossier ne contient plus que le dépôt source, monté en lecture.
