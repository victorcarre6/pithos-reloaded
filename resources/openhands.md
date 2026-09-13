# OpenHands Agent Canvas — pointeur

L'extraction complète (**~110 mappages**) a été consignée dans
**[`IMPORT_REPORT.md`](IMPORT_REPORT.md) § Partie G** : catalogue par module
(`cible -> <chemin>:<ligne> -> notion`, statuts S / A / I / X), ce que chaque reprise a changé dans la
documentation, les écarts, et l'ordre de portage.

Les notions qui ont donné lieu à une décision d'architecture sont détaillées dans
[`../docs/EXPLANATIONS.md`](../docs/EXPLANATIONS.md) — décisions 16, 17 et 27 amendées, **décision 28**.

**L'apport principal — l'admission déclarative.** Seul des sept dépôts à formaliser de bout en bout le
contrat entre « une donnée déclarative est bien typée » et « elle est admissible » : identifiants validés par
regex, markup interdit, commandes restreintes à un alphabet **sans métacaractères shell**, chemins vérifiés
relatifs, énumérations fermées, bornes dures de longueur — et surtout un **accumulateur d'erreurs par chemin
de champ qui retourne toutes les violations en une fois**, là où nos rejets s'arrêtaient à la première.

**Une opposition frontale tranchée.** Pi exécute les commandes contenues dans une valeur de configuration
(écarté en partie B) ; OpenHands interdit toute expression évaluable dans un placeholder (repris ici). Même
question, deux réponses — la nôtre est la seconde, et elle est désormais écrite.

Le dépôt inspecté est le **frontend** ; le SDK Python et l'agent-server vivent ailleurs. **Aucune copie de
code** : toutes les reprises sont conceptuelles.

Ce dossier ne contient plus que les dépôts sources et leurs pointeurs.
