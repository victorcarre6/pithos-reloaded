# Propositions Git — banc audio

Aucune commande exécutée. L’initialisation du dépôt cible est proposée séparément dans README.md.

## Proposé le 13:09 — adapter le visualiseur aux essais

**Intention** : Publier un banc local reproductible pour la nano-étape de stabilisation audio.

```sh
ga experiments/visualizer/PROJECT.md \
   experiments/visualizer/README.md \
   experiments/visualizer/STATE.md \
   experiments/visualizer/seed/audio_visualizer.py \
   experiments/visualizer/run.py \
   experiments/visualizer/git.md
gcmsg "experiments: adapte le noyau audio aux essais locaux"
```

**Contient** : Cadrage, seed faux explicite, selftest à trois scénarios, sonde et trial avec ports réels. Les preuves restent sur disque dans runs ; le dépôt cible est préparé mais non initialisé.
**Tests verts** : tests/test_visualizer_trial.py : 5 passed en 3,01 s ; sonde Ollama probe-z20hc14z conforme. Suite complète **1 402 passed, 3 skipped, 7 warnings en 40,64 s** dans Python 3.12.9/pithos.
**Exécuté** : —


## Proposé le 13:09 — entrée unique avec panneaux terminal

**Intention** : Exposer le banc Pithos par une entrée unique avec suivi dynamique des preuves.

```sh
ga src/main.py \
   src/tui.py \
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

**Contient** : parseur partagé, quatre panneaux, usage sans doublon, sortie JSON sans TUI,
interruption conservée avec code 130, restauration du terminal et tests de vrai SIGINT après splice.
Les chemins src racine et documentaires correspondent à la demande explicite d'entrée unique.
Le banc et certains documents étaient déjà non suivis/modifiés ; cette proposition suppose de relire
leurs propositions antérieures avant staging, car Git indexe les fichiers entiers.
**Ne contient pas** : changements métier parallèles des modules, dépôts tiers, preuves dans runs/.
**Tests verts** : 23 ciblés en 6,21 s ; suite complète 1 444 passed, 3 skipped, 7 warnings en 44,62 s,
Python 3.12.9/pithos ; tests.state_check et git diff --check passent.
**Exécuté** : —


## Proposé le 13:09 — consigner le trial réel et son observatoire

**Intention** : Rendre le refus réel du banc inspectable et reprenable.

```sh
ga experiments/visualizer/README.md \
   experiments/visualizer/STATE.md \
   experiments/visualizer/git.md
gcmsg "visualizer: consigne le refus réel du trial"
```

**Contient** : HEAD humain existant, cinq gates, rejet tautology, absence de reçu, restauration exacte et accès au dashboard. Les preuves runs/ restent append-only et exclues de cette proposition ; aucun nouveau trial réel exécuté.
**Tests verts** : Lecture HTTP du trial-44kcg6ig et comparaison SHA du fichier restauré. Suite complète : **1 444 passed, 3 skipped, 7 warnings en 43,83 s**, Python 3.12.9/pithos ; contrôle des onze STATE vert.
**Exécuté** : —
