# STATE — `workspace`

**Statut** : non commencé
**Mise à jour** : —
**Lignes** : 0 / ~200 L socle

## Prochaine action

Obtenir l'exception AGENTS § 6 pour déplacer `src/workspace/test_double_contract.py` vers `tests/contracts/test_workspace_double.py` et `src/workspace/test_import_boundaries.py` vers `tests/boundaries/test_workspace.py` ; après autorisation, déplacer ces deux fichiers, relancer les 119 tests workspace avec ces deux chemins explicites, puis consigner `fini` et transmettre à `engine`.

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

### 07:09 — préparation pure du splice

**Statut courant : en cours.** Python **3.12.9**, préfixe
`/Users/victorcarre/.pyenv/versions/pithos`. Git initial propre, HEAD `07bfd84`.

- Lecture complète AGENTS → STATE → MODULE ; sources Villani, Pi, Kilo, Ouroboros,
  Prime et SWE-agent relues avant adaptation. Aucun agent secondaire.
- Test initial : erreur de collection attendue, `workspace.splice` absent.
- Implémentation `prepare_splice` : une fonction de module, nom exact, signature
  compatible, décorateurs/async, compilation pure, no-op, empreintes et bilan.
- **37 tests verts en 0,20 s** : `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q
  -p no:cacheprovider src/workspace/test_splice.py`.
- Modèle Pydantic `SplicePlan` via le contrat kernel existant ; aucune dépendance ajoutée.

**Niveau de preuve : 4**, comportement pur testé ; pas encore d'écriture produit.

**Décisions locales de cet incrément.** Racine explicite dans la future façade
`Workspace(root)` ; aucune racine déduite du cwd. `compile(bytes, ..., "exec")`
utilise le compilateur de `py_compile` sans écrire de bytecode ni exécuter le code.
L'arité conserve la forme des appels (positions, noms utilisables comme mots-clés,
présence des défauts, keyword-only, variadiques et sync/async) ; valeurs des défauts
et annotations restent modifiables. Les enveloppes Markdown ne sont admises que
si elles couvrent toute la chaîne ; les préfixes de lignes doivent être consécutifs.
La décision 2 concerne les littéraux des critères ; le code candidat distinct est
explicitement prévu par EXPLANATIONS § workspace (l. 2636). Ce module ne l'exécute pas.

**Blocages relevés, indépendants de ce socle.** `FileFact` n'a ni snapshots source ni
champ de lignes ajoutées : conserver ces données dans `SplicePlan`, sans modifier
kernel ni prétendre débloquer le `run` complet du verifier. AGENTS § 6 interdit
l'écriture dans `tests/contracts/` et `tests/boundaries/`, exigée par § 11 : préparer
les tests dans `src/workspace/`, puis demander une exception pour leurs deux déplacements.

### 07:09 — transaction, confinement et traces de tentative

**Statut courant : en cours.** `Workspace(root, view=..., trace=...)` porte la racine
explicite et les dépendances injectables. Transaction mono-usage, snapshot à l'entrée,
staging unique dans le répertoire cible, mode conservé, flush/fsync puis `os.replace`.
CAS avant staging et juste avant rename, sous un verrou local commun au processus.
`restore()` rétablit les octets ; `__exit__` le fait sur exception après une écriture
réalisée par cette transaction. Une transaction qui perd son CAS n'efface pas le gagnant.
Utiliser `transaction.splice(...)` pour rattacher la mutation au rollback de ce contexte.

- Première collecte rouge : exports `StaleContentError` / `Transaction` absents.
- **31 tests verts en 0,16 s**, puis **68 en 0,19 s** après raccordement du journal.
- Le double officiel journal reçoit les sources candidates (même invalides), puis les
  snapshots avant/après hexadécimaux avant CAS. Sans confirmation durable, pas d'écriture.
  Les temporaires ne sont que des copies de ces données déjà conservées, leur nettoyage
  n'efface pas les traces brutes. Le rollback reste possible si le journal tombe ensuite.
- Vérifications supplémentaires : **2 rouges / 77 verts en 0,22 s**. Un décorateur
  parenthésé commence avant le `lineno` de son expression ; correction de la plage.
  Un cookie Latin-1 pouvait réinterpréter silencieusement une insertion UTF-8 ; refus
  explicite des encodages autres que UTF-8/BOM UTF-8. Échecs conservés ici.
- **79 tests verts** après correction, mêmes options pytest et même venv.
- Concurrence réelle par deux threads : exactement une écriture et un StaleContentError.
  Redirection de symlink pendant staging refusée. Pannes mkstemp/fsync/replace injectées.
  Un échec de restauration garde l'erreur originale dans un BaseExceptionGroup.

**Niveau de preuve : 5**, filesystem réel de test et doubles officiels kernel/journal.
Pas d'Ollama, de dépôt de campagne ni de test des implémentations voisines.

**Limites explicites.** Le verrou couvre les mutations coopérantes du même processus,
pas une écriture extérieure dans l'intervalle ultime CAS/rename. Le socle travaille sur
un fichier existant, dans une campagne exclusive ; création/rollback d'absence, feuilles
concurrentes, reprise après SIGKILL et confinement OS restent hors de ce socle.
Aucune commande Git ni aucun subprocess ; aucun code candidat exécuté.

**Écart de taille en cours.** Le budget indicatif de ~200 L est dépassé : les gardes
pures, la préservation binaire, les traces avant mutation et la transaction avec pannes
ne tiennent pas dans le prototype de dix lignes. Comptage final et justification par
fichier à ajouter après le double ; cible non relevée.

### 07:09 — interface, double et livraison du socle

**Statut courant : bloqué uniquement sur le placement des deux tests partagés.**
Cette entrée est l'état courant ; l'en-tête « non commencé » est historique,
conservé parce que seul « Prochaine action » est mutable en place.

**Production : 388 lignes physiques / ~200**, voir la justification détaillée dans
MODULE § Décisions locales. Cinq fichiers : `__init__.py` 38, `paths.py` 36,
`protocol.py` 27, `splice.py` 125, `transaction.py` 162. Aucun code P7bis ni dépôt
Git fantôme ; aucune nouvelle dépendance. Tous les changements sont dans
`src/workspace/` et `tests/doubles/workspace.py`.

**Avancement actuel — Fini quand.**

- [x] Blob JSON refusé avant écriture, incident v1 rejoué.
- [x] Deux `def` de module ou zéro `def` refusés.
- [x] Arity incompatible refusée avec les deux signatures.
- [x] Candidate non compilable refusée, empreinte disque inchangée.
- [x] No-op refusé avec `n_replacements=0`.
- [x] Commentaires/formatage hors plage, CRLF/LF/CR/BOM préservés à l'octet.
- [x] Concurrence avant écriture et pendant staging détectée, StaleContentError typé.
- [x] Rollback exact par comparaison SHA-256 ; timeout/KeyboardInterrupt également.
- [x] Même politique authoritative à l'écriture et à la projection.
- [x] Sorties par `..` et symlink refusées, racine elle-même résolue.
- [x] WorkspacePort/TransactionPort et double mémoire conformes : **21 tests communs**.
- [x] Graphe d'import testé localement, y compris **16 violations injectées**.
- [ ] Tests situés dans `tests/contracts/` et `tests/boundaries/` (exception requise).

**Vérifications.**

1. Double seul : **21 passed in 0.15s** ; mêmes cinq premières gardes et CAS,
   FileFact sérialisable cohérent, restauration et projection. Aucun I/O du double.
2. Revue de l'encodage : un nouveau cookie dans la fonction de tête pouvait changer
   l'encodage du module ; **1 failed, 41 deselected in 0.13s**, puis contrôle du
   cookie de la candidate complète. Résultat conservé, correctif partagé.
3. Suite complète intermédiaire : **118 passed in 0.25s**.
4. Vérification de l'API bas niveau : `cas_write` acceptait plus de 2 000 000 octets,
   puis la lecture bornée empêchait le rollback. **1 failed, 25 deselected in 0.13s**,
   BaseExceptionGroup conservant le refus manquant et l'échec de restauration.
   Correctif : même borne avant écriture dans le réel et le double.
5. Suite finale : **119 passed in 0.27s**, Python **3.12.9** / venv **pithos**.
   `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider src/workspace`.
   Aucun test des autres modules exécuté.

**Preuve conservée hors rétention pytest.**
`/private/var/folders/g5/gfzgn6710bl4fnkqby736jyh0000gn/T/pithos-workspace-proof-5lfqsjuy/`
contient `before.py`, `after.py`, `restored.py`, `report.json`, `events.jsonl`, et
`campaign/tool.py`. Splice mesuré puis restore ; les deux événements du double
journal contiennent la tentative et les snapshots exacts.

- SHA avant = restauré : `ad4f2b6fc5d170f67e233019c0868c1979d7f9aecb49166d851905362301faf6`.
- SHA après : `0e61365b29f436229ab4bd1bb376f6af2fc5953bf89039dbc471ff76446a8aec`.
- **Niveau de preuve : 5** : effet disque réel + frontières contre doubles officiels.
  Pas de preuve de campagne de bout en bout, ni de fonctionnement du voisin réel.

**Blocages et résolution.**

| Quoi | Pourquoi | Ce qui débloque | Résolu le |
|---|---|---|---|
| Emplacement des deux tests | AGENTS § 6 restreint les écritures au module/double, § 11 impose des dossiers partagés | Exception explicite pour les deux déplacements ci-dessous | — |
| Champs FileFact absents | Snapshots source et lignes ajoutées ne sont pas dans le contrat partagé actuel | Données disponibles dans before/SplicePlan ; évolution kernel distincte pour le verifier complet, sans bloquer le splice | Socle couvert le 07:09 |
| Cible indicative dépassée | 388 lignes pour interfaces, gardes binaires, CAS/staging, journal préalable et pannes explicites | Justification par fichier dans MODULE, cible ~200 non augmentée | Justifié le 07:09 |

Les deux fichiers de test sont autonomes ; ils résolvent la racine avec `parents[2]`
dans l'emplacement actuel comme dans l'emplacement final. **Commandes préparées,
non exécutées**, à utiliser seulement après l'exception de périmètre :

```sh
mkdir -p tests/contracts tests/boundaries
mv src/workspace/test_double_contract.py tests/contracts/test_workspace_double.py
mv src/workspace/test_import_boundaries.py tests/boundaries/test_workspace.py
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider src/workspace tests/contracts/test_workspace_double.py tests/boundaries/test_workspace.py
```

**Reprises traitées.**

| Source lue | Verdict du catalogue | Traitement au socle |
|---|---|---|
| Villani state_tooling.py:44-86,177-207,236-291 | Copier/Adapter | Enveloppe entière, sanitizer sans effacement de `..`, diagnostic compile avant écriture |
| Villani patch_apply.py:68-106,330-333 | Copier | Valider avant appliquer ; style local de newline, hors-plage laissé en octets |
| Pi edit.ts et edit-diff.ts:270-400 | Adapter | BOM, no-op, diff, validation unique ; aucun fuzzy importé |
| Pi utils/paths.ts:96-128 | Adapter | Confinement par composants ; prédicat kernel utilisé |
| Kilo packages/core/src/file-mutation.ts:144-158 | Traduire | CAS typé sous verrou, notice MIT conservée dans transaction.py |
| Prime prime-agent-runtime/src/rlm/repl.py:660-695 | Copier | Notion de temporaire unique même répertoire ; réécriture propre, aucun runtime copié |
| Ouroboros ouroboros/tools/edit_ops.py:79-157,678-730 | Copier | Canonicalisation et diagnostic de compilation ; approche adaptée, pas son outil batch |
| SWE-agent tools/windowed/lib/windowed_file.py:36-52 | Adapter | Bilan mesuré via FileFact et SplicePlan, pas de remplacement par motif |
| Sandbox, checkpoints persistants, dépôt fantôme | Reporté | Non implémentés conformément au socle/P7bis |
| Permissions, shell, patch, fuzzy, seuils de réécriture | Écarté | Non réintroduits |
| Reprises réseau, serveurs, hooks, stockage distant du catalogue large | Hors autorité nominale | Aucune surface correspondante dans cette façade ; pas de code spéculatif |

**Transmission à engine après levée du placement.** Racine et cible sélectionnées
par le harness ; journal lié avant usage. `transaction.splice` pour associer la
mutation à son rollback ; `restore` explicite pour un verdict rouge sans exception.
`FileFact` est une mesure, jamais un reçu. `before` et `last_plan` sont inspectables
sans relire la cible ; verifier garde son autorité de vérité.

**Skills.** Aucun apprentissage nouveau suffisamment général pour modifier
`autonomous-work` : garde-fous et conservation des résultats négatifs déjà couverts.
Aucun skill modifié, aucune commande Git en écriture exécutée.

**Contrôle final de livraison — 07:09.** `git diff --check` sans diagnostic ; contrôle
`git diff --no-index --check /dev/null <fichier>` sur les **15 fichiers** du périmètre,
y compris non suivis : **zéro défaut d’espacement**. Statut Git final limité à ces
15 fichiers workspace ; aucune modification des autres modules ni des dossiers partagés.
