# Prime Agent — pointeur

L'extraction complète (**~110 mappages**) a été consignée dans
**[`IMPORT_REPORT.md`](IMPORT_REPORT.md) § Partie E** : catalogue par module
(`cible -> prime/<chemin>:<ligne> -> notion`, verdict Porter / Transposer / Inspirer), ce que chaque reprise a
changé dans la documentation, les huit conflits frontaux et leur arbitrage, et l'ordre de portage.

Les notions qui ont donné lieu à une décision d'architecture sont détaillées dans
[`../docs/EXPLANATIONS.md`](../docs/EXPLANATIONS.md) — décisions 6 et 7 amendées, **décision 26**.

**L'apport principal** — *« A Self-Improving RLM Harness »* est le **seul des cinq dépôts à implémenter
l'auto-amélioration au fil du cycle de vie de bout en bout**. Magasin d'état scopé, versionné, rollbackable,
injecté au contexte, avec l'immuabilité du prompt de base en trois lignes. Son défaut : **c'est une boucle
ouverte** — rien ne vérifie qu'un raffinement améliore quoi que ce soit. Notre `verifier` la ferme, et cette
combinaison est ce qui donne le neuvième module `refinery` et la phase P9.

`prime-agent-runtime/src/rlm/harness.py` (820 L) est **l'implémentation Python de référence** et se porte sans
réécriture. Le reste est du TypeScript à transposer.

`resources/prime-agent-main/` est sous **licence MIT** (*Copyright (c) 2025 Mario Zechner /
Copyright (c) 2026 Prime Intellect*). Portage littéral licite avec conservation de la notice.

Ce dossier ne contient plus que le dépôt source, monté en lecture.
