# Ouroboros — pointeur

L'extraction complète (**~200 mappages**) a été consignée dans
**[`IMPORT_REPORT.md`](IMPORT_REPORT.md) § Partie D** : catalogue par module
(`cible -> our/<chemin>:<ligne> -> notion`, verdict Porter / Adapter / Inspirer), ce que chaque reprise a
changé dans la documentation, les écarts, **les neuf conflits frontaux avec les décisions actées** et leur
arbitrage, et l'ordre de portage.

Les notions qui ont donné lieu à une décision d'architecture sont détaillées dans
[`../docs/EXPLANATIONS.md`](../docs/EXPLANATIONS.md) — décisions 5, 8, 13 et 17 amendées, décisions 22 à 25.

**Les trois découvertes majeures :**

- **`response_format` est une intention, pas une garantie** — certaines routes l'ignorent, la ladder de retry
  a le droit de le retirer. La revalidation locale contre le schéma exact envoyé est obligatoire quoi qu'il
  arrive. Le spike n°2 a été reformulé en conséquence. § D2.1.
- **Le reçu attesté par l'hôte et les trois capteurs de faux-vert** — le seul des quatre dépôts à avoir
  construit l'appareil de preuve complet autour du code de retour. § D2.2.
- **« A chain is not an equivalence relation »** — une identité est une clé typée, jamais une chaîne de repli.
  Notre clé anti-redondance avait exactement la forme fautive. § D2.3, actée en décision 22.

`resources/ouroboros-main/` est sous **licence MIT** (`Copyright (c) 2026 Anton Razzhigaev`) et son
`CITATION.cff` demande la citation du papier (🔗 [arXiv 2608.08311](https://arxiv.org/abs/2608.08311)) en cas
d'usage en recherche. **Tout est en Python** : le portage est littéral, avec conservation de la notice MIT
dans le fichier dérivé.

Ce dossier ne contient plus que le dépôt source, monté en lecture.
