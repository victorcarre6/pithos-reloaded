# Propositions Git — entrée Pithos et TUI

**Mise à jour** : 13:09

Ce fichier est **append-only**. Les commandes sont proposées à l'opérateur et n'ont pas été
exécutées par l'agent, conformément à [AGENTS.md § 7](../AGENTS.md#7-git--tu-ne-commites-jamais).
La documentation du lanceur est dans [TUI.md](TUI.md).

## Proposé le 13:09 — entrée unique avec panneaux terminal

**Intention** : Exposer le banc Pithos par une entrée unique avec suivi dynamique des preuves.

Cette proposition reprend le lot « entrée unique avec panneaux terminal » de
[experiments/visualizer/git.md](../experiments/visualizer/git.md), avec `src/TUI.md` et
`src/GIT.md` ajoutés. **C'est le même lot, à exécuter une seule fois.** La proposition historique
reste conservée ; son champ d'exécution devra aussi être renseigné si l'opérateur applique ce lot.

Depuis la racine du dépôt, après revue des fichiers complets :

```sh
ga src/main.py \
   src/tui.py \
   src/TUI.md \
   src/GIT.md \
   experiments/visualizer/run.py \
   tests/test_main.py \
   README.md \
   experiments/visualizer/README.md \
   experiments/visualizer/STATE.md \
   experiments/visualizer/git.md \
   docs/QUICK_CATCH.md \
   docs/ROADMAP.md \
   docs/EXPLANATIONS.md
gcmsg "cli: ajoute une entrée pithos avec suivi terminal"
```

**Contient** : point d'entrée `src/main.py`, parseur partagé avec le banc, quatre panneaux fixes,
usage sans doublon, JSON hors terminal, interruption conservée avec code 130, restauration du
terminal, tests et documentation associée.

**Ne contient pas** : implémentations métier parallèles des onze modules, dépôts tiers sous
`resources/`, preuves et workspaces sous `experiments/visualizer/runs/`.

**Revue nécessaire** : le banc et plusieurs documents étaient déjà non suivis ou modifiés avant
ce chantier. Les fichiers documentaires contiennent aussi des contributions parallèles ; le staging
porte sur leur contenu complet. Relire les propositions antérieures et le diff avant de composer
le commit. Ce lot suppose les modules déjà présents dans le worktree ; il ne propose pas leur publication.

**Tests verts à la livraison du 13:09** :

- `tests/test_main.py` et `tests/test_visualizer_trial.py` : **23 passed en 6,21 s**.
- Suite complète : **1 444 passed, 3 skipped, 7 warnings en 44,62 s**, Python **3.12.9 / pithos**.
- `python -m tests.state_check` et `git diff --check` passent.
- Vrai SIGINT en pseudo-terminal après splice : restauration du seed, rapport durable, code 130,
  curseur restauré ; modèle scénarisé.

Ces mesures sont archivées dans le [STATE du banc](../experiments/visualizer/STATE.md).
La création de `TUI.md` et `GIT.md` est documentaire : contenu et liens locaux vérifiés, sans
nouvelle exécution de la suite métier.

**Exécuté** : —

## Lot du 15:09 — projection exacte

Le changement de libellé du TUI et son critère partagé sont proposés une seule fois dans
[experiments/visualizer/git.md](../experiments/visualizer/git.md), lot « utiliser le critère
de projection exacte ». Ses contrôles CLI et les critères de reprise sont dans
[tests/git.md](../tests/git.md). Suite finale : 1 602 passed, 3 skipped, 7 warnings en 114,64 s.
Aucune commande Git d'écriture exécutée.
