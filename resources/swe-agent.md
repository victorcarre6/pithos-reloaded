# SWE-agent — pointeur

L'extraction complète (**~95 mappages**) a été consignée dans
**[`IMPORT_REPORT.md`](IMPORT_REPORT.md) § Partie H**, **après audit et complétion**.

## Audit de l'extraction initiale

Ce document avait été produit par un petit modèle. La vérification avant absorption a donné :

| Point | Verdict |
|---|---|
| Ancres `fichier:ligne` | **Toutes valides** — 22 vérifiées, zéro chemin mort, zéro ligne hors fichier |
| Volumétrie | 414 fichiers ✓ · lignes surestimées d'environ 15 % |
| Licence MIT | ✓ |
| **Descriptions** | **Décalées d'une classe** dans `tools/parsing.py` — 3 ancres sur 8 nomment la classe voisine |
| **Ancres canoniques** | Plusieurs pointent au milieu d'un corps plutôt que sur une définition |
| **Couverture** | **Trois zones entières omises** — `tools/` (~900 L), `tests/` (~1 700 L), `sweagent/types.py` — soit ~3 000 lignes |

**Les quatre reprises les plus utiles du dépôt venaient de la zone omise** : la projection de fichier qui
déclare ce qu'elle cache, le bilan chiffré d'une mutation, la fusion d'intervalles avant projection, et
`thought`/`action`/`observation` comme champs typés distincts.

Les omissions ont été comblées et les descriptions corrigées ; les entrées concernées portent la mention
*(hors extraction)* dans le catalogue. Détail complet en § H1.

**Leçon de méthode** : une extraction par petit modèle produit des ancres fiables et des descriptions
approximatives, et couvre le répertoire principal en ignorant la périphérie. **La forme d'une extraction
complète ne prouve pas sa complétude** — exactement le mode d'échec que la décision 13 anticipe.

## Où trouver quoi

Les notions qui ont donné lieu à une décision sont dans
[`../docs/EXPLANATIONS.md`](../docs/EXPLANATIONS.md) — décisions 9 et 14 amendées, **décision 29**.

`resources/SWE-agent-main/` est sous **MIT** : portage littéral licite avec conservation de la notice.

Ce dossier ne contient plus que les dépôts sources et leurs pointeurs.
