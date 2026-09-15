# Sensibilité du banc audio — 15:09

Le refus `tautology` de `trial-44kcg6ig` est reproductible. Le runner fonctionne selon le contrat
archivé : le candidat est idempotent, comme chacun des trois mutants disponibles. Cette observation
ne suffit pas à conclure que le critère est vrai pour toute implémentation.

## Rejeu des preuves conservées

Le critère archivé est `idempotent / clamp_level / floats_finite`. La copie avant, dans
`invariant-0g0qjhke`, rend `level + 0.1` ; la copie après, dans `invariant-ul9xdyau`, rend
`max(0.0, min(1.0, level))`. Le rejeu exact constate avant rouge, après vert, puis trois survies :

| Mutant | Expression de retour | Pourquoi l'idempotence tient |
|---|---|---|
| `return_none:6:4` | `None` | Une fonction constante reste inchangée à la seconde application. |
| `shift_number:6:15` | `max(1.0, min(1.0, level))` | La sortie vaut toujours 1 pour un flottant fini. |
| `shift_number:6:24` | `max(0.0, min(2.0, level))` | Une projection sur [0, 2] est aussi idempotente. |

Les **44 fichiers historiques sont inchangés**, SHA-256 comparés avant/après. Le nouveau verdict
et ses cinq gates sont conservés dans `/private/tmp/pithos-sensitivity-kvhdkqos/` ; les originaux
restent dans `experiments/visualizer/runs/trial-44kcg6ig/`. Aucun nouvel appel Ollama.

## Limite démontrée par un corpus réduit

| Source candidate | Double gate observée |
|---|---|
| Projection [0, 1] écrite avec `min`/`max` | Rejet `tautology` : les trois mutants survivent. |
| Même projection écrite avec des branches `if` | Acceptation : avant rouge, après vert, mutant tué. |
| Projection sur [0, 2] écrite avec ces mêmes branches | Acceptation également. Les bornes exactes ne sont pas prouvées. |

La sensibilité dépend de l'inventaire AST. Un mutant tué atteste que la relation distingue cette
variante ; il ne démontre pas le contrat produit complet. Le critère du premier banc décrit
explicitement cette limite dans [son cadrage](../../experiments/visualizer/PROJECT.md).
Les tests ne fabriquent aucun reçu ni attestation d'effet : `effect` reste `unproven`.

```sh
# corpus autonome, sans dépendre des artefacts ignorés du trial
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider src/verifier/test_sensitivity.py
```

## Conséquence pour la suite

Le catalogue, les gates et les causes fermées restent inchangés. Ajouter un opérateur uniquement
pour faire passer ce candidat ne résoudrait pas l'absence de preuve sur les bornes. Le banc actuel
reste utilisable pour éprouver le protocole, avec la portée limitée de son reçu.

Étendre la preuve au contrat produit serait une autre unité : une déclaration de sortie appartenant
au harness peut porter les bornes via `schema_conform`, mais ne suffit pas à assurer la projection
exacte (une sortie constante bornée satisferait le schéma). Il faudrait aussi définir les relations
qui préservent les valeurs déjà dans l'intervalle et caractérisent la saturation. Le modèle ne
doit choisir ni ces bornes, ni les entrées, ni une valeur attendue.

## Extension approuvée et vérifiée — 15:09

L'utilisateur a choisi la projection exacte sur [0, 1]. La relation fermée `unit_projection`
caractérise les points fixes dans l'intervalle et la saturation hors de l'intervalle, impose une
sortie numérique bornée et l'idempotence. Elle ne reçoit ni borne ni tolérance du modèle.
Onze exemples fixes, dont les voisins immédiats des bornes, complètent Hypothesis seedé.

Les deux écritures correctes passent la double gate ; les 19 variantes incorrectes du corpus
sont refusées, dont [0, 2], les constantes, les booléens, NaN/inf et les erreurs d'un flottant
aux frontières. Le test historique test_sensitivity.py reste vert sous l'ancien critère.

Le rejeu des copies exactes du trial est conservé dans
`experiments/visualizer/runs/projection-replay-6k9y5dc3/` : avant rouge, après vert, mutant tué.
Les 44 fichiers originaux sont inchangés, SHA-256 comparés et archivés dans replay.json.
Ce rejeu ne produit aucun reçu, aucun effet workspace et aucun nouvel appel Ollama. Il ne
transforme pas le trial historique refusé en un essai accepté.

```sh
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider src/verifier/test_projection.py src/verifier/test_sensitivity.py
```

Un nouvel appel au modèle a ensuite été exercé séparément : `trial-25ugxn94` est vert sous
unit_projection en 44,898 s, avec trois gates et un reçu durable `effect: confirmed`. Le fichier
workspace est réellement modifié. Ce résultat est distinct du rejeu, et les anciennes preuves
restent intactes. Le protocole complet de mission et sa finalisation Git n'ont pas été lancés
sur le dépôt opérateur.
