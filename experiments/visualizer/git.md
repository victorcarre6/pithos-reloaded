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

## Proposé le 14:09 — mission audio reprenable

**Intention** : raccorder le banc à walk/flow sous worker lifecycle avec finalisation verte broker.

```sh
ga experiments/visualizer/mission.py \
   experiments/visualizer/README.md \
   experiments/visualizer/STATE.md \
   experiments/visualizer/git.md
gcmsg "experiment: compose la mission audio reprenable"
```

**Contient** : CLI séparée du trial, relecture du même arbre, budget commun, prérequis opérateur.
**Tests verts** : intégration Git/Prefect/lifecycle/verifier réels, modèle simulé ; coupure et reprise.
Suite complète **1 548 passed, 3 skipped, 7 warnings en 87,81 s**, STATE et diff-check verts.
Les tests partagés sont proposés dans tests/git.md. Aucun artefact runs/ ou workspace inclus.
**Exécuté** : —

### Suspension le 14:09 — contre-preuve des groupes verifier

Les propositions de composition ci-dessus attendent la correction décrite dans STATE : un invariant
lancé dans sa propre session survit au watchdog du worker (sonde : 1 failed en 2,22 s). La suite
racine verte ne couvrait pas ce cas. Le lot broker indépendant reste vérifié ; aucun commit exécuté.

### Suspension levée le 14:09 — custody des gates vérifiée

L'extension à verifier est autorisée et livrée. Le test coupe un invariant réel et son descendant ;
le sweep après mort du superviseur et la reprise de la CLI réelle passent. Suite complète **1 556 passed, 3 skipped, 7 warnings en 100,50 s**,
Python 3.12.9/pithos ; STATE et diff-check verts. Les mêmes chemins proposés incluent la correction
et leurs preuves actualisées. Le lot verifier ajouté ce jour est un prérequis à la composition ;
les lots lifecycle, experiment et tests partagés se relisent ensemble. Aucun commit exécuté.

## Proposé le 15:09 — utiliser le critère de projection exacte

**Intention** : soumettre les nouveaux essais audio au contrat exact de projection unité.

```sh
ga experiments/visualizer/run.py \
   experiments/visualizer/mission.py \
   experiments/visualizer/PROJECT.md \
   experiments/visualizer/README.md \
   experiments/visualizer/STATE.md \
   experiments/visualizer/git.md \
   src/tui.py \
   src/TUI.md \
   src/GIT.md
gcmsg "experiment: vérifie la projection unité dans les nouveaux essais"
```

**Contient** : critère partagé, selftest min/max, refus de [0, 2], reprise des anciens critères
sans requalification des reçus, relation exposée dans le JSON et le terminal. Cadrage amendé
sur décision explicite de l'utilisateur. Prérequis : kernel/verifier et composition lifecycle.
Les tests partagés et la documentation racine sont proposés dans tests/git.md. Les fichiers
mission/README/STATE portent aussi la composition antérieure ; composer ces lots après revue.
Les artefacts runs/ et le dépôt workspace ne sont pas inclus dans ce commit du harness.
**Tests verts** : suite complète **1 602 passed, 3 skipped, 7 warnings en 114,64 s**, Python 3.12.9 / pithos ; STATE et diff-check verts.
**Exécuté** : —

## Proposé le 15:09 — conserver le fichier vert dans le dépôt d'essai

**Intention** : versionner la correction effectivement validée par trial-25ugxn94.

Commandes réservées à l'opérateur, dans le dépôt d'essai distinct du harness :

```sh
git -C experiments/visualizer/workspace add audio_visualizer.py
git -C experiments/visualizer/workspace commit -m "visualizer: projette les niveaux sur l’intervalle unité"
```

**Contient** : uniquement audio_visualizer.py tel que produit et vérifié dans le trial vert.
**Preuve réelle** : trois gates, un reçu durable effect confirmed ; SHA-256 du fichier
2699717e89232fcd6ae0eee5395eb8122e67d2ffe9b3f39c9439f83c065f1b29.
Ne pas confondre ce commit humain avec une finalisation de mission GreenFinalizer :
le trial n'a pas exercé ce chemin. Aucune réinitialisation du seed ni suppression de preuve.
**Exécuté** : —
