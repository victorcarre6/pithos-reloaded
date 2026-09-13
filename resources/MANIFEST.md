# Manifeste des dépôts de référence

Les onze dépôts inspectés pour construire Pithos Reloaded. **Ils ne sont pas versionnés** — les archives de code
tiers dans l'historique du projet n'apporteraient rien — mais tout pointeur `fichier:ligne` de
[`IMPORT_REPORT.md`](IMPORT_REPORT.md) se lit contre l'archive décrite ici.

| Partie | Dépôt | Taille | Fichiers | Licence | Reprises |
|---|---|---:|---:|---|---:|
| **A** | `villani-code-main/` | 5,8 Mo | 886 | **aucun fichier de licence** — projet personnel, copie libre accordée | ~90 |
| **B** | `pi-main/` | 24 Mo | 1 673 | MIT (`LICENSE`) | 185 |
| **C** | `kilocode-main/` | 128 Mo | 10 005 | MIT (`LICENSE`) | 173 |
| **D** | `ouroboros-main/` | 46 Mo | 1 499 | MIT (`LICENSE`) — `CITATION.cff` demande la citation du papier | ~200 |
| **E** | `prime-agent-main/` | 24 Mo | 1 244 | MIT (`LICENSE`) | ~110 |
| **F** | `unsloth-main/` | 136 Mo | 5 011 | **mixte : `LICENSE` + `COPYING`, AGPL pour `studio/`** | ~110 |
| **G** | `OpenHands-main/` | 19 Mo | 2 212 | `LICENSE` — à vérifier avant tout portage littéral, aucun prévu | ~110 |
| **H** | `SWE-agent-main/` | 35 Mo | 414 | MIT (`LICENSE`) | ~95 |
| **I** | `langfuse-main/` | 56 Mo | 5 704 | MIT hors `ee/` (`LICENSE`) | 105 |
| **J** | `GVS5H-master/` | 285 Mo | 28 997 | MIT code ; CC BY 4.0 données ; énoncés tiers exclus (`NOTICE.md`) | 8 décisions |
| **K** | `graphify-main/` | 18 Mo | 873 | Apache 2.0 ; contributions MIT antérieures (`NOTICE`) | 5 décisions |

**A–I : 475 Mo, 28 648 fichiers, ~1 180 reprises cataloguées** (mesures historiques).
J–K ajoutés le **13:09**, volumes repris des extractions locales. Seules les notions sélectionnées
entrent dans le harness ; aucune archive copiée ni dépendance GVS5H/Graphify installée.

## Ce que la licence impose, dépôt par dépôt

- **Copie littérale licite avec conservation de la notice** — B, C, D, E, H. Ce sont les seuls dépôts dont
  des lignes atteignent le code du projet sous verdict `Copier` ou `Traduire`.
- **A (Villani)** — aucun fichier de licence, ni mention dans le `README`. Projet personnel, copie libre
  accordée explicitement. C'est la source du plus grand nombre de `Copier`.
- **F (Unsloth)** — les reprises les plus utiles vivent sous `studio/`, qui est en **AGPL**. Décision
  retenue : **notions reprises, code réécrit, aucune copie littérale.** Les obligations AGPL se déclenchent
  à la distribution ou à la mise à disposition réseau ; un harness personnel local ne les déclenche pas,
  mais la règle est appliquée quand même.
- **G (OpenHands)** — reprises explicitement conceptuelles. Aucune copie prévue.
- **I (Langfuse)** — MIT hors `ee/`, et **aucune reprise n'est proposée depuis ces chemins**.

## Fiabilité des extractions

Deux extractions ont été **auditées contre leur dépôt monté** avant absorption, avec des résultats opposés.

| | H — SWE-agent | I — Langfuse |
|---|---|---|
| Ancres | valides, **descriptions décalées d'une classe** par endroits | **15/15 exactes**, définitions canoniques |
| Couverture | **trois zones entières omises**, ~3 000 lignes, dont la plus utile | carte de couverture par famille, fichiers cités comptés |
| Honnêteté | affirme une couverture qu'elle n'a pas | **déclare ses propres limites** |

**La forme d'une extraction complète ne prouve pas sa complétude.** La seule extraction auditable est celle
qui quantifie ce qu'elle n'a pas couvert — la décision 13 appliquée au travail documentaire. Les sept autres
extractions n'ont pas été auditées de cette façon.

## Rétablir le répertoire

Chaque dépôt est une archive publique décompressée à la racine de `resources/`, sans modification. Les
fichiers `<source>.md` de ce répertoire sont les **pointeurs de sortie** de chaque extraction : ce qu'elle a
produit, où son contenu a été absorbé, et pour deux d'entre elles le résultat de l'audit.

## Intégration J–K — 13:09

[GVS5H.md](GVS5H.md) et [graphify.md](graphify.md) conservent leur évaluation initiale et ses limites.
La décision courante est dans IMPORT_REPORT § J/K : métriques/historique, notices d'omission
budgétées et contrôle des interfaces livrées. Notes réécrites, regrades remplaçables et marqueurs
hors budget ne sont pas copiés. Aucun benchmark de tiers n'a été rejoué.
