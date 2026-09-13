# Langfuse — pointeur

L'extraction complète (**105 mappages**, 67 fichiers cités, neuf modules couverts) a été consignée dans
**[`IMPORT_REPORT.md`](IMPORT_REPORT.md) § Partie I**.

## Audit de l'extraction — verdict positif

Vérifiée avant absorption, comme la partie H. **Résultat opposé.**

| Contrôle | Résultat |
|---|---|
| 5 704 fichiers réguliers · 9 liens symboliques · version 4.30.0 | **exacts** |
| Lignes de texte | écart de **1 %** (20 fichiers binaires exclus par le document) |
| **15 ancres `fichier:ligne` vérifiées** | **15 exactes** — définitions canoniques, notions correspondantes |
| Empreinte SHA-256 de l'inventaire | **non reproduite** avec la convention devinée : le format de chemin et l'ordre de tri ne sont pas spécifiés. Le compte de fichiers étant exact, c'est un défaut de documentation, pas un inventaire divergent |

Le document **déclare ses propres limites** (« l'inventaire est exhaustif ; l'analyse sémantique est
ciblée ») et fournit une **carte de couverture par famille avec le nombre de fichiers cités** — il rend donc
visible ce qu'il ne couvre pas. C'est exactement ce qui manquait à l'extraction SWE-agent.

## L'apport principal

La chaîne **observation → évaluation identifiée → résultat versionné → lecture reproductible**, et quatre
zones sans équivalent dans les huit autres sources :

- **l'identité d'un résultat, distincte de son identité de transport** — republier sans recompter ;
- **le cycle de vie d'un run avec fencing** — heartbeat à perte de propriété explicite, et réconciliation qui
  ne tue jamais une nouvelle incarnation ;
- **la lecture bornée de grosses traces** — arbre résistant aux doublons, durée de nœud distincte de
  l'enveloppe du sous-arbre ;
- **le versionnement à label mobile**, qui donne à `refinery` la forme exacte de sa paire `shadow`/`active`.

Les décisions concernées sont dans [`../docs/EXPLANATIONS.md`](../docs/EXPLANATIONS.md) — décisions 13, 16,
26, 27 et 28 amendées, **décision 30**.

## Licence

**MIT pour le socle** (`LICENSE:5`), avec exceptions commerciales sous `ee/`, `web/src/ee/` et
`worker/src/ee/` (`ee/LICENSE:13`). **Aucune reprise n'est proposée depuis ces chemins.**

Ce dossier ne contient plus que les dépôts sources et leurs pointeurs.
